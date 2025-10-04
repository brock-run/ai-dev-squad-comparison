"""
Deterministic Time and Randomness Control for Record-Replay

Provides controllable time and randomness sources that can be frozen
during replay to ensure deterministic execution across runs.

Following ADR-011 specifications for seed governance and deterministic sampling.
"""

import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
import threading
from contextlib import contextmanager


class ClockProvider(ABC):
    """Abstract base class for time providers."""
    
    @abstractmethod
    def now(self) -> datetime:
        """Get current datetime."""
        pass
    
    @abstractmethod
    def time(self) -> float:
        """Get current timestamp."""
        pass
    
    @abstractmethod
    def sleep(self, seconds: float):
        """Sleep for specified seconds."""
        pass


class SystemClockProvider(ClockProvider):
    """System clock provider using real time."""
    
    def now(self) -> datetime:
        """Get current system datetime."""
        return datetime.now(timezone.utc)
    
    def time(self) -> float:
        """Get current system timestamp."""
        return time.time()
    
    def sleep(self, seconds: float):
        """Sleep using system time."""
        time.sleep(seconds)


class FrozenClockProvider(ClockProvider):
    """Frozen clock provider for deterministic replay."""
    
    def __init__(self, frozen_time: datetime):
        """
        Initialize frozen clock.
        
        Args:
            frozen_time: Fixed datetime to return
        """
        self.frozen_time = frozen_time
        self.frozen_timestamp = frozen_time.timestamp()
    
    def now(self) -> datetime:
        """Get frozen datetime."""
        return self.frozen_time
    
    def time(self) -> float:
        """Get frozen timestamp."""
        return self.frozen_timestamp
    
    def sleep(self, seconds: float):
        """No-op sleep for frozen time."""
        pass  # Don't actually sleep during replay


class RecordingClockProvider(ClockProvider):
    """Clock provider that records timestamps for later replay."""
    
    def __init__(self):
        """Initialize recording clock."""
        self.recorded_times: List[datetime] = []
        self.recorded_timestamps: List[float] = []
        self.system_clock = SystemClockProvider()
    
    def now(self) -> datetime:
        """Get current time and record it."""
        current_time = self.system_clock.now()
        self.recorded_times.append(current_time)
        return current_time
    
    def time(self) -> float:
        """Get current timestamp and record it."""
        current_timestamp = self.system_clock.time()
        self.recorded_timestamps.append(current_timestamp)
        return current_timestamp
    
    def sleep(self, seconds: float):
        """Sleep and record the duration."""
        self.system_clock.sleep(seconds)
    
    def get_recorded_times(self) -> List[datetime]:
        """Get all recorded datetimes."""
        return self.recorded_times.copy()
    
    def get_recorded_timestamps(self) -> List[float]:
        """Get all recorded timestamps."""
        return self.recorded_timestamps.copy()


class RngProvider(ABC):
    """Abstract base class for random number generators."""
    
    @abstractmethod
    def seed(self, seed_value: int):
        """Set random seed."""
        pass
    
    @abstractmethod
    def random(self) -> float:
        """Generate random float [0.0, 1.0)."""
        pass
    
    @abstractmethod
    def randint(self, a: int, b: int) -> int:
        """Generate random integer [a, b]."""
        pass
    
    @abstractmethod
    def choice(self, sequence: List[Any]) -> Any:
        """Choose random element from sequence."""
        pass
    
    @abstractmethod
    def uuid4(self) -> str:
        """Generate random UUID4 string."""
        pass


class SystemRngProvider(RngProvider):
    """System RNG provider using Python's random module."""
    
    def __init__(self, seed_value: Optional[int] = None):
        """
        Initialize system RNG.
        
        Args:
            seed_value: Optional seed for deterministic behavior
        """
        self._rng = random.Random()
        if seed_value is not None:
            self.seed(seed_value)
    
    def seed(self, seed_value: int):
        """Set random seed."""
        self._rng.seed(seed_value)
    
    def random(self) -> float:
        """Generate random float."""
        return self._rng.random()
    
    def randint(self, a: int, b: int) -> int:
        """Generate random integer."""
        return self._rng.randint(a, b)
    
    def choice(self, sequence: List[Any]) -> Any:
        """Choose random element."""
        return self._rng.choice(sequence)
    
    def uuid4(self) -> str:
        """Generate UUID4 using seeded randomness."""
        # Generate deterministic UUID using seeded random bytes
        random_bytes = bytes([self._rng.randint(0, 255) for _ in range(16)])
        # Set version and variant bits for UUID4
        random_bytes = bytearray(random_bytes)
        random_bytes[6] = (random_bytes[6] & 0x0f) | 0x40  # Version 4
        random_bytes[8] = (random_bytes[8] & 0x3f) | 0x80  # Variant bits
        
        # Format as UUID string
        hex_string = random_bytes.hex()
        return f"{hex_string[:8]}-{hex_string[8:12]}-{hex_string[12:16]}-{hex_string[16:20]}-{hex_string[20:]}"


class RecordingRngProvider(RngProvider):
    """RNG provider that records values for later replay."""
    
    def __init__(self, seed_value: Optional[int] = None):
        """
        Initialize recording RNG.
        
        Args:
            seed_value: Optional seed for deterministic behavior
        """
        self.system_rng = SystemRngProvider(seed_value)
        self.recorded_values: Dict[str, List[Any]] = {
            'random': [],
            'randint': [],
            'choice': [],
            'uuid4': []
        }
    
    def seed(self, seed_value: int):
        """Set random seed."""
        self.system_rng.seed(seed_value)
    
    def random(self) -> float:
        """Generate and record random float."""
        value = self.system_rng.random()
        self.recorded_values['random'].append(value)
        return value
    
    def randint(self, a: int, b: int) -> int:
        """Generate and record random integer."""
        value = self.system_rng.randint(a, b)
        self.recorded_values['randint'].append((a, b, value))
        return value
    
    def choice(self, sequence: List[Any]) -> Any:
        """Choose and record random element."""
        value = self.system_rng.choice(sequence)
        self.recorded_values['choice'].append((sequence, value))
        return value
    
    def uuid4(self) -> str:
        """Generate and record UUID4."""
        value = self.system_rng.uuid4()
        self.recorded_values['uuid4'].append(value)
        return value
    
    def get_recorded_values(self) -> Dict[str, List[Any]]:
        """Get all recorded random values."""
        return {k: v.copy() for k, v in self.recorded_values.items()}


class ReplayRngProvider(RngProvider):
    """RNG provider that replays recorded values."""
    
    def __init__(self, recorded_values: Dict[str, List[Any]]):
        """
        Initialize replay RNG.
        
        Args:
            recorded_values: Previously recorded random values
        """
        self.recorded_values = recorded_values
        self.indices = {key: 0 for key in recorded_values.keys()}
    
    def seed(self, seed_value: int):
        """No-op for replay mode."""
        pass
    
    def random(self) -> float:
        """Replay recorded random float."""
        values = self.recorded_values.get('random', [])
        index = self.indices['random']
        
        if index >= len(values):
            raise ValueError(f"No more recorded random values (requested index {index})")
        
        value = values[index]
        self.indices['random'] += 1
        return value
    
    def randint(self, a: int, b: int) -> int:
        """Replay recorded random integer."""
        values = self.recorded_values.get('randint', [])
        index = self.indices['randint']
        
        if index >= len(values):
            raise ValueError(f"No more recorded randint values (requested index {index})")
        
        recorded_a, recorded_b, value = values[index]
        
        # Verify parameters match
        if (a, b) != (recorded_a, recorded_b):
            raise ValueError(f"randint parameters mismatch: expected ({recorded_a}, {recorded_b}), got ({a}, {b})")
        
        self.indices['randint'] += 1
        return value
    
    def choice(self, sequence: List[Any]) -> Any:
        """Replay recorded choice."""
        values = self.recorded_values.get('choice', [])
        index = self.indices['choice']
        
        if index >= len(values):
            raise ValueError(f"No more recorded choice values (requested index {index})")
        
        recorded_sequence, value = values[index]
        
        # Verify sequence contains the recorded choice
        if value not in sequence:
            raise ValueError(f"choice value {value} not in provided sequence")
        
        self.indices['choice'] += 1
        return value
    
    def uuid4(self) -> str:
        """Replay recorded UUID4."""
        values = self.recorded_values.get('uuid4', [])
        index = self.indices['uuid4']
        
        if index >= len(values):
            raise ValueError(f"No more recorded uuid4 values (requested index {index})")
        
        value = values[index]
        self.indices['uuid4'] += 1
        return value


class DeterminismManager:
    """Manages deterministic providers for record-replay."""
    
    def __init__(self):
        """Initialize determinism manager."""
        self._lock = threading.RLock()
        self._clock_provider: ClockProvider = SystemClockProvider()
        self._rng_provider: RngProvider = SystemRngProvider()
        self._mode = "live"  # live, recording, replay
    
    def set_live_mode(self, seed: Optional[int] = None):
        """Set live mode with optional seed."""
        with self._lock:
            self._mode = "live"
            self._clock_provider = SystemClockProvider()
            self._rng_provider = SystemRngProvider(seed)
    
    def set_recording_mode(self, seed: Optional[int] = None):
        """Set recording mode."""
        with self._lock:
            self._mode = "recording"
            self._clock_provider = RecordingClockProvider()
            self._rng_provider = RecordingRngProvider(seed)
    
    def set_replay_mode(self, 
                       frozen_time: datetime,
                       recorded_random_values: Dict[str, List[Any]]):
        """Set replay mode with frozen time and recorded values."""
        with self._lock:
            self._mode = "replay"
            self._clock_provider = FrozenClockProvider(frozen_time)
            self._rng_provider = ReplayRngProvider(recorded_random_values)
    
    def get_clock(self) -> ClockProvider:
        """Get current clock provider."""
        return self._clock_provider
    
    def get_rng(self) -> RngProvider:
        """Get current RNG provider."""
        return self._rng_provider
    
    def get_mode(self) -> str:
        """Get current mode."""
        return self._mode
    
    def get_recorded_data(self) -> Dict[str, Any]:
        """Get recorded data (only valid in recording mode)."""
        if self._mode != "recording":
            return {}
        
        data = {}
        
        if isinstance(self._clock_provider, RecordingClockProvider):
            data['times'] = [t.isoformat() for t in self._clock_provider.get_recorded_times()]
            data['timestamps'] = self._clock_provider.get_recorded_timestamps()
        
        if isinstance(self._rng_provider, RecordingRngProvider):
            data['random_values'] = self._rng_provider.get_recorded_values()
        
        return data


# Global determinism manager
_global_determinism_manager = DeterminismManager()


def get_determinism_manager() -> DeterminismManager:
    """Get the global determinism manager."""
    return _global_determinism_manager


def get_clock() -> ClockProvider:
    """Get the current clock provider."""
    return _global_determinism_manager.get_clock()


def get_rng() -> RngProvider:
    """Get the current RNG provider."""
    return _global_determinism_manager.get_rng()


@contextmanager
def deterministic_context(mode: str, **kwargs):
    """
    Context manager for deterministic execution.
    
    Args:
        mode: 'live', 'recording', or 'replay'
        **kwargs: Mode-specific arguments
    """
    manager = get_determinism_manager()
    original_mode = manager.get_mode()
    
    try:
        if mode == "live":
            manager.set_live_mode(kwargs.get('seed'))
        elif mode == "recording":
            manager.set_recording_mode(kwargs.get('seed'))
        elif mode == "replay":
            manager.set_replay_mode(
                kwargs['frozen_time'],
                kwargs['recorded_random_values']
            )
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        yield manager
        
    finally:
        # Restore original mode (simplified - would need to save full state)
        if original_mode == "live":
            manager.set_live_mode()


# Convenience functions that use the global providers
def now() -> datetime:
    """Get current datetime from global clock provider."""
    return get_clock().now()


def timestamp() -> float:
    """Get current timestamp from global clock provider."""
    return get_clock().time()


def sleep(seconds: float):
    """Sleep using global clock provider."""
    get_clock().sleep(seconds)


def random_float() -> float:
    """Get random float from global RNG provider."""
    return get_rng().random()


def random_int(a: int, b: int) -> int:
    """Get random integer from global RNG provider."""
    return get_rng().randint(a, b)


def random_choice(sequence: List[Any]) -> Any:
    """Choose random element from global RNG provider."""
    return get_rng().choice(sequence)


def random_uuid() -> str:
    """Generate UUID from global RNG provider."""
    return get_rng().uuid4()