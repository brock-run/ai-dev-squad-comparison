"""
Multi-Run Executor for Self-Consistency Evaluation

Executes multiple benchmark runs with seed variation for reliability analysis,
following ADR-010 specifications.
"""

import asyncio
import time
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from common.benchmarking import BenchmarkResult
from common.config import get_config_manager

logger = logging.getLogger(__name__)


@dataclass
class MultiRunConfig:
    """Configuration for multi-run execution."""
    
    # Run parameters
    runs: int = 5
    parallel: bool = True
    max_workers: Optional[int] = None
    
    # Seed strategy (ADR-010)
    seed_strategy: str = "sequential"  # "sequential" | "random" | "user"
    base_seed: int = 42
    seed_list: Optional[List[int]] = None
    
    # Variation parameters (opt-in)
    temperature_variation: bool = False
    temperature_range: tuple = (0.1, 0.9)
    prompt_variation: bool = False
    
    # Timeout and retry
    timeout_per_run: int = 300  # seconds
    max_retries: int = 1


class MultiRunExecutor:
    """Executes multiple benchmark runs for consistency evaluation."""
    
    def __init__(self, config: MultiRunConfig):
        self.config = config
        self._results: List[BenchmarkResult] = []
        
    def execute_runs(self, 
                    benchmark_func: Callable,
                    framework: str,
                    task: str,
                    **base_kwargs) -> List[BenchmarkResult]:
        """
        Execute multiple benchmark runs with seed variation.
        
        Args:
            benchmark_func: Function to execute for each run
            framework: Framework name
            task: Task name  
            **base_kwargs: Base arguments for benchmark function
            
        Returns:
            List of BenchmarkResult objects
        """
        # Generate seeds
        seeds = self._generate_seeds()
        
        # Prepare run configurations
        run_configs = []
        for i, seed in enumerate(seeds):
            run_kwargs = base_kwargs.copy()
            run_kwargs.update({
                'seed': seed,
                'run_index': i,
                'framework': framework,
                'task': task
            })
            
            # Add variations if enabled
            if self.config.temperature_variation:
                temp_min, temp_max = self.config.temperature_range
                temperature = temp_min + (temp_max - temp_min) * (i / (len(seeds) - 1))
                run_kwargs['temperature'] = temperature
            
            run_configs.append(run_kwargs)
        
        # Execute runs
        if self.config.parallel and len(run_configs) > 1:
            results = self._execute_parallel(benchmark_func, run_configs)
        else:
            results = self._execute_sequential(benchmark_func, run_configs)
        
        self._results = results
        return results
    
    def _generate_seeds(self) -> List[int]:
        """Generate seeds based on strategy (ADR-010) using common/config seed system."""
        if self.config.seed_list:
            return self.config.seed_list[:self.config.runs]
        
        try:
            # Use the centralized seed configuration system
            config_manager = get_config_manager()
            seed_config = config_manager.config.seeds
            
            # Override seed config with our parameters
            seed_config.strategy = self.config.seed_strategy
            seed_config.base_seed = self.config.base_seed
            if self.config.seed_list:
                seed_config.user_seeds = self.config.seed_list
            
            # Generate seeds using the centralized system
            return seed_config.generate_seeds(self.config.runs)
            
        except ImportError:
            # Fallback to local implementation if config system not available
            logger.warning("Config system not available, using local seed generation")
            return self._generate_seeds_fallback()
    
    def _generate_seeds_fallback(self) -> List[int]:
        """Fallback seed generation when config system is not available."""
        if self.config.seed_strategy == "sequential":
            return [self.config.base_seed + i for i in range(self.config.runs)]
        elif self.config.seed_strategy == "random":
            import random
            random.seed(self.config.base_seed)
            return [random.randint(0, 2**31 - 1) for _ in range(self.config.runs)]
        elif self.config.seed_strategy == "user":
            # Use base_seed for all runs (user controls variation)
            return [self.config.base_seed] * self.config.runs
        else:
            raise ValueError(f"Unknown seed strategy: {self.config.seed_strategy}")
    
    def _execute_parallel(self, 
                         benchmark_func: Callable,
                         run_configs: List[Dict[str, Any]]) -> List[BenchmarkResult]:
        """Execute runs in parallel using ProcessPoolExecutor."""
        results = []
        max_workers = self.config.max_workers or min(len(run_configs), 4)
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all runs
            future_to_config = {
                executor.submit(self._execute_single_run, benchmark_func, config): config
                for config in run_configs
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_config, timeout=self.config.timeout_per_run * len(run_configs)):
                config = future_to_config[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Run failed for config {config}: {e}")
                    # Create failed result
                    failed_result = BenchmarkResult(
                        framework=config.get('framework', 'unknown'),
                        task=config.get('task', 'unknown'),
                        success=False,
                        error=str(e),
                        metadata={'seed': config.get('seed'), 'run_index': config.get('run_index')}
                    )
                    results.append(failed_result)
        
        # Sort by run_index to maintain order
        results.sort(key=lambda r: r.metadata.get('run_index', 0))
        return results
    
    def _execute_sequential(self,
                           benchmark_func: Callable,
                           run_configs: List[Dict[str, Any]]) -> List[BenchmarkResult]:
        """Execute runs sequentially."""
        results = []
        
        for config in run_configs:
            try:
                result = self._execute_single_run(benchmark_func, config)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Run failed for config {config}: {e}")
                # Create failed result
                failed_result = BenchmarkResult(
                    framework=config.get('framework', 'unknown'),
                    task=config.get('task', 'unknown'),
                    success=False,
                    error=str(e),
                    metadata={'seed': config.get('seed'), 'run_index': config.get('run_index')}
                )
                results.append(failed_result)
        
        return results
    
    def _execute_single_run(self, 
                           benchmark_func: Callable,
                           config: Dict[str, Any]) -> Optional[BenchmarkResult]:
        """Execute a single benchmark run with retry logic."""
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                start_time = time.time()
                
                # Execute benchmark function
                result = benchmark_func(**config)
                
                # Ensure result has required metadata
                if hasattr(result, 'metadata'):
                    result.metadata.update({
                        'seed': config.get('seed'),
                        'run_index': config.get('run_index'),
                        'attempt': attempt,
                        'execution_time': time.time() - start_time
                    })
                
                return result
                
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries:
                    print(f"Run attempt {attempt + 1} failed, retrying: {e}")
                    time.sleep(1)  # Brief delay before retry
                else:
                    print(f"Run failed after {attempt + 1} attempts: {e}")
        
        return None
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of execution results."""
        if not self._results:
            return {}
        
        successful_runs = [r for r in self._results if r.success]
        failed_runs = [r for r in self._results if not r.success]
        
        total_time = sum(
            r.metadata.get('execution_time', 0) 
            for r in self._results 
            if 'execution_time' in r.metadata
        )
        
        return {
            'total_runs': len(self._results),
            'successful_runs': len(successful_runs),
            'failed_runs': len(failed_runs),
            'success_rate': len(successful_runs) / len(self._results) if self._results else 0,
            'total_execution_time': total_time,
            'average_time_per_run': total_time / len(self._results) if self._results else 0,
            'seeds_used': [r.metadata.get('seed') for r in self._results if 'seed' in r.metadata]
        }
    
    def get_results(self) -> List[BenchmarkResult]:
        """Get all execution results."""
        return self._results.copy()
    
    def clear_results(self):
        """Clear stored results."""
        self._results.clear()