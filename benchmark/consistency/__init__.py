"""
Self-Consistency Evaluation System

Implements multi-run evaluation with consensus analysis for reliable
framework comparison, following ADR-010 specifications.
"""

from .multi_run_executor import MultiRunExecutor
from .consensus_analyzer import ConsensusAnalyzer
from .variance_calculator import VarianceCalculator
from .consistency_reporter import ConsistencyReporter

__all__ = [
    'MultiRunExecutor',
    'ConsensusAnalyzer', 
    'VarianceCalculator',
    'ConsistencyReporter'
]
__version__ = '1.0.0'