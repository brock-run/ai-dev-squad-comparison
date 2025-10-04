"""
Event Ordering and Concurrency Control for Record-Replay

Provides thread-safe event ordering with per-agent queues and monotonic
step tracking to ensure deterministic replay under concurrent execution.

Following ADR-008 specifications for event ordering and concurrency safety.
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Deque
from queue import Queue, Empty
import uuid


@dataclass
class OrderedEvent:
    """Event with ordering information for deterministic replay."""
    
    # Core event data
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: str = ""
    
    # Ordering information
    step: int = 0  # Global step counter
    parent_step: Optional[int] = None  # Parent operation step
    agent_id: str = ""
    call_index: int = 0  # Per-agent, per-tool monotonic counter
    
    # Event payload
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "step": self.step,
            "parent_step": self.parent_step,
            "agent_id": self.agent_id,
            "call_index": self.call_index,
            "data": self.data
        }


class EventOrderingManager:
    """Manages event ordering and concurrency for deterministic record-replay."""
    
    def __init__(self):
        """Initialize event ordering manager."""
        self._lock = threading.RLock()
        self._global_step_counter = 0
        self._agent_call_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._agent_queues: Dict[str, Deque[OrderedEvent]] = defaultdict(deque)
        self._step_stack: List[int] = []  # For tracking parent steps
        self._active_agents: set = set()
        
        # Single writer thread for deterministic ordering
        self._write_queue: Queue = Queue()
        self._writer_thread: Optional[threading.Thread] = None
        self._shutdown = False
        
    def start_writer(self):
        """Start the single writer thread for deterministic event ordering."""
        if self._writer_thread is None or not self._writer_thread.is_alive():
            self._shutdown = False
            self._writer_thread = threading.Thread(
                target=self._writer_loop,
                name="EventWriter",
                daemon=True
            )
            self._writer_thread.start()
    
    def stop_writer(self):
        """Stop the writer thread."""
        self._shutdown = True
        if self._writer_thread and self._writer_thread.is_alive():
            # Signal shutdown
            self._write_queue.put(None)
            self._writer_thread.join(timeout=5.0)
    
    def _writer_loop(self):
        """Single writer thread loop for deterministic event ordering."""
        while not self._shutdown:
            try:
                item = self._write_queue.get(timeout=1.0)
                if item is None:  # Shutdown signal
                    break
                
                event, callback = item
                
                # Process event with deterministic ordering
                with self._lock:
                    self._process_event_ordered(event)
                
                # Call callback if provided
                if callback:
                    callback(event)
                    
            except Empty:
                continue
            except Exception as e:
                # Log error but continue processing
                print(f"Error in event writer: {e}")
    
    def create_ordered_event(self,
                           event_type: str,
                           agent_id: str,
                           tool_name: str = "",
                           data: Optional[Dict[str, Any]] = None,
                           parent_step: Optional[int] = None) -> OrderedEvent:
        """
        Create an event with proper ordering information.
        
        Args:
            event_type: Type of event
            agent_id: Agent generating the event
            tool_name: Tool name for call index tracking
            data: Event payload data
            parent_step: Parent operation step (optional)
            
        Returns:
            OrderedEvent with proper step and call index
        """
        with self._lock:
            # Increment global step counter
            self._global_step_counter += 1
            step = self._global_step_counter
            
            # Get call index for this agent/tool combination
            call_index = self._agent_call_counters[agent_id][tool_name]
            self._agent_call_counters[agent_id][tool_name] += 1
            
            # Use provided parent_step or current stack top
            if parent_step is None and self._step_stack:
                parent_step = self._step_stack[-1]
            
            # Create ordered event
            event = OrderedEvent(
                event_type=event_type,
                step=step,
                parent_step=parent_step,
                agent_id=agent_id,
                call_index=call_index,
                data=data or {}
            )
            
            return event
    
    def queue_event(self,
                   event: OrderedEvent,
                   callback: Optional[callable] = None):
        """
        Queue an event for ordered processing.
        
        Args:
            event: Event to queue
            callback: Optional callback to call after processing
        """
        self._write_queue.put((event, callback))
    
    def _process_event_ordered(self, event: OrderedEvent):
        """Process event with deterministic ordering (called by writer thread)."""
        # Add to agent queue
        self._agent_queues[event.agent_id].append(event)
        self._active_agents.add(event.agent_id)
    
    def push_step_context(self, step: int):
        """Push a step onto the context stack for parent tracking."""
        with self._lock:
            self._step_stack.append(step)
    
    def pop_step_context(self) -> Optional[int]:
        """Pop a step from the context stack."""
        with self._lock:
            return self._step_stack.pop() if self._step_stack else None
    
    def get_agent_events(self, agent_id: str) -> List[OrderedEvent]:
        """Get all events for a specific agent in order."""
        with self._lock:
            return list(self._agent_queues[agent_id])
    
    def get_all_events_ordered(self) -> List[OrderedEvent]:
        """Get all events across all agents in global step order."""
        with self._lock:
            all_events = []
            for agent_queue in self._agent_queues.values():
                all_events.extend(agent_queue)
            
            # Sort by global step
            return sorted(all_events, key=lambda e: e.step)
    
    def get_call_index(self, agent_id: str, tool_name: str) -> int:
        """Get current call index for agent/tool combination."""
        with self._lock:
            return self._agent_call_counters[agent_id][tool_name]
    
    def reset_agent(self, agent_id: str):
        """Reset counters and queue for a specific agent."""
        with self._lock:
            self._agent_call_counters[agent_id].clear()
            self._agent_queues[agent_id].clear()
            self._active_agents.discard(agent_id)
    
    def reset_all(self):
        """Reset all counters and queues."""
        with self._lock:
            self._global_step_counter = 0
            self._agent_call_counters.clear()
            self._agent_queues.clear()
            self._step_stack.clear()
            self._active_agents.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ordering manager statistics."""
        with self._lock:
            return {
                "global_step": self._global_step_counter,
                "active_agents": len(self._active_agents),
                "total_events": sum(len(queue) for queue in self._agent_queues.values()),
                "agent_call_counts": {
                    agent_id: dict(counters)
                    for agent_id, counters in self._agent_call_counters.items()
                }
            }


class StepContext:
    """Context manager for tracking parent-child step relationships."""
    
    def __init__(self, ordering_manager: EventOrderingManager, step: int):
        """
        Initialize step context.
        
        Args:
            ordering_manager: Event ordering manager
            step: Step number to push onto context stack
        """
        self.ordering_manager = ordering_manager
        self.step = step
    
    def __enter__(self):
        """Enter step context."""
        self.ordering_manager.push_step_context(self.step)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit step context."""
        self.ordering_manager.pop_step_context()


# Global instance for use across the application
_global_ordering_manager = EventOrderingManager()


def get_ordering_manager() -> EventOrderingManager:
    """Get the global event ordering manager."""
    return _global_ordering_manager


def create_ordered_event(event_type: str,
                        agent_id: str,
                        tool_name: str = "",
                        data: Optional[Dict[str, Any]] = None,
                        parent_step: Optional[int] = None) -> OrderedEvent:
    """Create an ordered event using the global ordering manager."""
    return _global_ordering_manager.create_ordered_event(
        event_type=event_type,
        agent_id=agent_id,
        tool_name=tool_name,
        data=data,
        parent_step=parent_step
    )


def queue_event(event: OrderedEvent, callback: Optional[callable] = None):
    """Queue an event using the global ordering manager."""
    _global_ordering_manager.queue_event(event, callback)


def step_context(step: int) -> StepContext:
    """Create a step context for parent-child tracking."""
    return StepContext(_global_ordering_manager, step)