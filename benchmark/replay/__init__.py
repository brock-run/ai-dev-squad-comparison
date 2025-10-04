"""
Record-Replay System for AI Agent Interactions

This module provides record-replay functionality for deterministic testing,
debugging, and demonstration of AI agent interactions, based on the existing
telemetry infrastructure (ADR-008, ADR-009).

Key Components:
- Recorder: Records agent interactions using telemetry events
- Player: Replays recorded sessions deterministically  
- Storage: Manages recording artifacts and manifests
"""

from .recorder import Recorder
from .player import Player
from .storage import StorageManager

__all__ = ['Recorder', 'Player', 'StorageManager']
__version__ = '1.0.0'