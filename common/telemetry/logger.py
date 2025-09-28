"""
Structured logging system for AI Dev Squad platform.

This module provides a comprehensive logging system with JSON Lines output,
event aggregation, filtering, and rotation capabilities for observability.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Union
from queue import Queue, Empty
from logging.handlers import RotatingFileHandler

from .schema import BaseEvent, EventType, LogLevel, create_event


class JSONLinesFormatter(logging.Formatter):
    """Custom formatter for JSON Lines output format."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON Lines."""
        
        # Extract event data if present
        if hasattr(record, 'event_data'):
            event_data = record.event_data
        else:
            # Create basic event from log record
            event_data = {
                "event_id": getattr(record, 'event_id', None),
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": getattr(record, 'event_type', 'system.log'),
                "level": record.levelname,
                "message": record.getMessage(),
                "metadata": {
                    "logger_name": record.name,
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
            }
        
        return json.dumps(event_data, default=str, separators=(',', ':'))


class EventBuffer:
    """Thread-safe buffer for event aggregation and batch processing."""
    
    def __init__(self, max_size: int = 1000, flush_interval: float = 5.0):
        self.max_size = max_size
        self.flush_interval = flush_interval
        self.buffer: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.last_flush = time.time()
    
    def add_event(self, event_data: Dict[str, Any]) -> bool:
        """Add event to buffer. Returns True if buffer should be flushed."""
        with self.lock:
            self.buffer.append(event_data)
            
            # Check if we should flush
            should_flush = (
                len(self.buffer) >= self.max_size or
                time.time() - self.last_flush >= self.flush_interval
            )
            
            return should_flush
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get all events and clear buffer."""
        with self.lock:
            events = self.buffer.copy()
            self.buffer.clear()
            self.last_flush = time.time()
            return events
    
    def size(self) -> int:
        """Get current buffer size."""
        with self.lock:
            return len(self.buffer)


class EventFilter:
    """Filter for event processing based on various criteria."""
    
    def __init__(self):
        self.level_filter: Optional[LogLevel] = None
        self.event_type_filter: Optional[List[EventType]] = None
        self.framework_filter: Optional[List[str]] = None
        self.agent_filter: Optional[List[str]] = None
        self.custom_filters: List[callable] = []
    
    def set_level_filter(self, min_level: LogLevel):
        """Set minimum log level filter."""
        self.level_filter = min_level
    
    def set_event_type_filter(self, event_types: List[EventType]):
        """Set event type filter."""
        self.event_type_filter = event_types
    
    def set_framework_filter(self, frameworks: List[str]):
        """Set framework filter."""
        self.framework_filter = frameworks
    
    def set_agent_filter(self, agents: List[str]):
        """Set agent filter."""
        self.agent_filter = agents
    
    def add_custom_filter(self, filter_func: callable):
        """Add custom filter function."""
        self.custom_filters.append(filter_func)
    
    def should_process(self, event_data: Dict[str, Any]) -> bool:
        """Check if event should be processed based on filters."""
        
        # Level filter
        if self.level_filter:
            event_level = LogLevel(event_data.get('level', 'INFO'))
            level_order = {
                LogLevel.DEBUG: 0,
                LogLevel.INFO: 1,
                LogLevel.WARNING: 2,
                LogLevel.ERROR: 3,
                LogLevel.CRITICAL: 4
            }
            if level_order.get(event_level, 0) < level_order.get(self.level_filter, 0):
                return False
        
        # Event type filter
        if self.event_type_filter:
            event_type = event_data.get('event_type')
            if event_type not in [et.value for et in self.event_type_filter]:
                return False
        
        # Framework filter
        if self.framework_filter:
            framework = event_data.get('framework')
            if framework not in self.framework_filter:
                return False
        
        # Agent filter
        if self.agent_filter:
            agent_id = event_data.get('agent_id')
            if agent_id not in self.agent_filter:
                return False
        
        # Custom filters
        for filter_func in self.custom_filters:
            if not filter_func(event_data):
                return False
        
        return True


class StructuredLogger:
    """Main structured logger for the AI Dev Squad platform."""
    
    def __init__(
        self,
        name: str = "ai_dev_squad",
        log_dir: str = "logs",
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 5,
        buffer_size: int = 1000,
        flush_interval: float = 5.0,
        enable_console: bool = True
    ):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup file handler with rotation
        log_file = self.log_dir / f"{name}.jsonl"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(JSONLinesFormatter())
        self.logger.addHandler(file_handler)
        
        # Setup console handler if enabled
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(JSONLinesFormatter())
            self.logger.addHandler(console_handler)
        
        # Event processing components
        self.event_buffer = EventBuffer(buffer_size, flush_interval)
        self.event_filter = EventFilter()
        
        # Background processing
        self.processing_queue = Queue()
        self.processing_thread = None
        self.stop_processing = threading.Event()
        
        # Session tracking
        self.session_id = None
        self.correlation_id = None
        
        # Start background processing
        self._start_background_processing()
    
    def _start_background_processing(self):
        """Start background thread for event processing."""
        self.processing_thread = threading.Thread(
            target=self._process_events,
            daemon=True
        )
        self.processing_thread.start()
    
    def _process_events(self):
        """Background event processing loop."""
        while not self.stop_processing.is_set():
            try:
                # Process queued events
                while True:
                    try:
                        event_data = self.processing_queue.get_nowait()
                        if self.event_filter.should_process(event_data):
                            self._write_event(event_data)
                    except Empty:
                        break
                
                # Sleep briefly to avoid busy waiting
                time.sleep(0.1)
                
            except Exception as e:
                # Log processing errors to standard logger
                logging.getLogger("telemetry_error").error(
                    f"Error in event processing: {e}"
                )
    
    def _write_event(self, event_data: Dict[str, Any]):
        """Write event to log with proper formatting."""
        
        # Add session context if available
        if self.session_id:
            event_data['session_id'] = self.session_id
        if self.correlation_id:
            event_data['correlation_id'] = self.correlation_id
        
        # Create log record with event data
        record = logging.LogRecord(
            name=self.name,
            level=getattr(logging, event_data.get('level', 'INFO')),
            pathname="",
            lineno=0,
            msg="",
            args=(),
            exc_info=None
        )
        record.event_data = event_data
        
        # Log the event
        self.logger.handle(record)
    
    def set_session_context(self, session_id: str, correlation_id: Optional[str] = None):
        """Set session context for all subsequent events."""
        self.session_id = session_id
        self.correlation_id = correlation_id
    
    def log_event(self, event: Union[BaseEvent, Dict[str, Any]]):
        """Log a structured event."""
        
        if isinstance(event, BaseEvent):
            event_data = event.to_dict()
        else:
            event_data = event
        
        # Queue event for processing
        self.processing_queue.put(event_data)
    
    def log_agent_start(
        self,
        agent_id: str,
        agent_type: str,
        framework: str,
        capabilities: List[str] = None,
        config: Dict[str, Any] = None,
        **kwargs
    ):
        """Log agent start event."""
        event = create_event(
            EventType.AGENT_START,
            agent_id=agent_id,
            agent_type=agent_type,
            framework=framework,
            capabilities=capabilities or [],
            agent_config=config or {},
            message=f"Agent {agent_id} started",
            **kwargs
        )
        self.log_event(event)
    
    def log_agent_stop(
        self,
        agent_id: str,
        framework: str,
        duration_ms: Optional[float] = None,
        **kwargs
    ):
        """Log agent stop event."""
        event = create_event(
            EventType.AGENT_STOP,
            agent_id=agent_id,
            framework=framework,
            message=f"Agent {agent_id} stopped",
            metadata={"duration_ms": duration_ms} if duration_ms else {},
            **kwargs
        )
        self.log_event(event)
    
    def log_task_start(
        self,
        task_id: str,
        task_name: str,
        agent_id: str,
        framework: str,
        task_input: Dict[str, Any] = None,
        **kwargs
    ):
        """Log task start event."""
        event = create_event(
            EventType.TASK_START,
            task_id=task_id,
            task_name=task_name,
            agent_id=agent_id,
            framework=framework,
            task_input=task_input or {},
            message=f"Task {task_name} started",
            **kwargs
        )
        self.log_event(event)
    
    def log_task_complete(
        self,
        task_id: str,
        task_name: str,
        agent_id: str,
        framework: str,
        duration_ms: float,
        task_output: Dict[str, Any] = None,
        **kwargs
    ):
        """Log task completion event."""
        event = create_event(
            EventType.TASK_COMPLETE,
            task_id=task_id,
            task_name=task_name,
            agent_id=agent_id,
            framework=framework,
            duration_ms=duration_ms,
            task_output=task_output or {},
            success=True,
            message=f"Task {task_name} completed successfully",
            **kwargs
        )
        self.log_event(event)
    
    def log_task_error(
        self,
        task_id: str,
        task_name: str,
        agent_id: str,
        framework: str,
        error: str,
        duration_ms: Optional[float] = None,
        **kwargs
    ):
        """Log task error event."""
        event = create_event(
            EventType.TASK_FAIL,
            task_id=task_id,
            task_name=task_name,
            agent_id=agent_id,
            framework=framework,
            duration_ms=duration_ms,
            success=False,
            error_details=error,
            level=LogLevel.ERROR,
            message=f"Task {task_name} failed: {error}",
            **kwargs
        )
        self.log_event(event)
    
    def log_tool_call(
        self,
        tool_name: str,
        agent_id: str,
        framework: str,
        tool_input: Dict[str, Any] = None,
        **kwargs
    ):
        """Log tool call event."""
        event = create_event(
            EventType.TOOL_CALL,
            tool_name=tool_name,
            agent_id=agent_id,
            framework=framework,
            tool_input=tool_input or {},
            message=f"Tool {tool_name} called",
            **kwargs
        )
        self.log_event(event)
    
    def log_safety_violation(
        self,
        policy_name: str,
        violation_type: str,
        risk_level: str,
        action_taken: str,
        agent_id: Optional[str] = None,
        blocked_content: Optional[str] = None,
        **kwargs
    ):
        """Log safety violation event."""
        event = create_event(
            EventType.SAFETY_VIOLATION,
            policy_name=policy_name,
            violation_type=violation_type,
            risk_level=risk_level,
            action_taken=action_taken,
            agent_id=agent_id,
            blocked_content=blocked_content,
            level=LogLevel.WARNING,
            message=f"Safety violation: {violation_type}",
            **kwargs
        )
        self.log_event(event)
    
    def log_llm_interaction(
        self,
        model_name: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
        cost_usd: Optional[float] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ):
        """Log LLM interaction event."""
        event = create_event(
            EventType.LLM_RESPONSE,
            model_name=model_name,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration_ms=duration_ms,
            cost_usd=cost_usd,
            agent_id=agent_id,
            message=f"LLM interaction with {model_name}",
            **kwargs
        )
        self.log_event(event)
    
    def get_filter(self) -> EventFilter:
        """Get the event filter for configuration."""
        return self.event_filter
    
    def flush(self):
        """Flush all pending events."""
        # Process any remaining events in queue
        while not self.processing_queue.empty():
            try:
                event_data = self.processing_queue.get_nowait()
                if self.event_filter.should_process(event_data):
                    self._write_event(event_data)
            except Empty:
                break
        
        # Flush logger handlers
        for handler in self.logger.handlers:
            handler.flush()
    
    def close(self):
        """Close the logger and cleanup resources."""
        self.stop_processing.set()
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        self.flush()
        
        # Close handlers
        for handler in self.logger.handlers:
            handler.close()


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def get_logger(
    name: str = "ai_dev_squad",
    **kwargs
) -> StructuredLogger:
    """Get or create global structured logger instance."""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = StructuredLogger(name=name, **kwargs)
    
    return _global_logger


def configure_logging(
    log_dir: str = "logs",
    level: LogLevel = LogLevel.INFO,
    enable_console: bool = True,
    **kwargs
) -> StructuredLogger:
    """Configure global logging with specified parameters."""
    global _global_logger
    
    _global_logger = StructuredLogger(
        log_dir=log_dir,
        enable_console=enable_console,
        **kwargs
    )
    
    # Set filter level
    _global_logger.get_filter().set_level_filter(level)
    
    return _global_logger