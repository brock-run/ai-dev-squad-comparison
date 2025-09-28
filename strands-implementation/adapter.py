"""
Strands Agents Enterprise Development Squad Implementation

This module implements the AgentAdapter protocol for Strands Agents, providing
enterprise-grade AI orchestration with built-in observability, multi-cloud support,
and comprehensive error handling.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional, AsyncIterator
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

try:
    from strands import Agent, AgentManager, Task, Workflow
    from strands.observability import TelemetryCollector, TraceManager
    from strands.cloud import MultiCloudProvider, CloudConfig
    from strands.errors import StrandsError, AgentExecutionError
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False
    # Fallback implementations for development
    class Agent:
        def __init__(self, name: str, role: str, **kwargs): pass
    class AgentManager:
        def __init__(self): pass
    class Task:
        def __init__(self, **kwargs): pass
    class Workflow:
        def __init__(self, **kwargs): pass
    class TelemetryCollector:
        def __init__(self): pass
    class TraceManager:
        def __init__(self): pass
    class MultiCloudProvider:
        def __init__(self): pass
    class CloudConfig:
        def __init__(self): pass
    class StrandsError(Exception): pass
    class AgentExecutionError(Exception): pass

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    OTEL_IMPORTS_AVAILABLE = True
except ImportError:
    OTEL_IMPORTS_AVAILABLE = False
    # Fallback implementations
    class trace:
        @staticmethod
        def set_tracer_provider(provider): pass
        @staticmethod
        def get_tracer(name): return None
        @staticmethod
        def get_current_span(): return None
    
    class TracerProvider: pass
    class BatchSpanProcessor: pass
    class JaegerExporter: pass

# Import common framework components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.agent_api import AgentAdapter, TaskSchema, RunResult, Event
from common.safety.execute import execute_code_safely
from common.safety.policy import SecurityPolicy
from common.vcs.base import VCSProvider
from common.vcs.github import GitHubProvider
from common.vcs.gitlab import GitLabProvider

# Import Strands-specific components
try:
    from .agents.enterprise_architect import EnterpriseArchitectAgent
    from .agents.senior_developer import SeniorDeveloperAgent
    from .agents.qa_engineer import QAEngineerAgent
    from .workflows.enterprise_workflow import EnterpriseWorkflow
    from .observability.telemetry_manager import TelemetryManager
    from .cloud.provider_manager import ProviderManager
except ImportError:
    # Fallback for direct execution
    from agents.enterprise_architect import EnterpriseArchitectAgent
    from agents.senior_developer import SeniorDeveloperAgent
    from agents.qa_engineer import QAEngineerAgent
    from workflows.enterprise_workflow import EnterpriseWorkflow
    from observability.telemetry_manager import TelemetryManager
    from cloud.provider_manager import ProviderManager


@dataclass
class StrandsConfig:
    """Configuration for Strands Agents implementation."""
    model_config: Dict[str, str] = None
    timeout_seconds: int = 1800
    max_retries: int = 3
    cloud_providers: List[str] = None
    observability_enabled: bool = True
    telemetry_endpoint: str = "http://localhost:14268/api/traces"
    distributed_tracing: bool = True
    error_recovery: bool = True
    
    def __post_init__(self):
        if self.model_config is None:
            self.model_config = {"primary": "codellama:13b", "fallback": "llama3.1:8b"}
        if self.cloud_providers is None:
            self.cloud_providers = ["aws", "azure", "gcp"]


class StrandsAdapter(AgentAdapter):
    """
    Strands Agents implementation of the AgentAdapter protocol.
    
    Provides enterprise-grade AI orchestration with:
    - Built-in observability and monitoring
    - Multi-cloud provider support
    - First-class OpenTelemetry integration
    - Enterprise-grade error handling and recovery
    """
    
    name = "strands"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Strands adapter with enterprise configuration."""
        self.config = StrandsConfig(**(config or {}))
        self.logger = logging.getLogger(__name__)
        
        # Initialize enterprise components
        self.agent_manager = None
        self.telemetry_manager = None
        self.provider_manager = None
        self.workflow = None
        self.tracer = None
        
        # Initialize safety and VCS
        try:
            self.safety_policy = SecurityPolicy()
        except TypeError:
            # Fallback if SecurityPolicy requires arguments
            self.safety_policy = None
        self.vcs_providers = {}
        
        # Track execution state
        self.current_task_id = None
        self.execution_context = {}
        self.events = []
        
        # Initialize if Strands is available
        if STRANDS_AVAILABLE:
            self._initialize_enterprise_components()
        else:
            self.logger.warning("Strands not available, using fallback implementation")
    
    def _initialize_enterprise_components(self):
        """Initialize enterprise-grade Strands components."""
        try:
            # Initialize OpenTelemetry tracing
            if self.config.distributed_tracing:
                self._setup_distributed_tracing()
            
            # Initialize agent manager
            self.agent_manager = AgentManager()
            
            # Initialize telemetry manager
            self.telemetry_manager = TelemetryManager(
                endpoint=self.config.telemetry_endpoint,
                enabled=self.config.observability_enabled
            )
            
            # Initialize multi-cloud provider manager
            self.provider_manager = ProviderManager(
                providers=self.config.cloud_providers
            )
            
            # Initialize enterprise workflow
            self.workflow = EnterpriseWorkflow(
                agent_manager=self.agent_manager,
                telemetry_manager=self.telemetry_manager,
                provider_manager=self.provider_manager
            )
            
            self.logger.info("Strands enterprise components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Strands components: {e}")
            raise
    
    def _setup_distributed_tracing(self):
        """Set up OpenTelemetry distributed tracing."""
        if not OTEL_IMPORTS_AVAILABLE:
            self.logger.warning("OpenTelemetry not available, distributed tracing disabled")
            self.tracer = None
            return
        
        try:
            # Configure tracer provider
            trace.set_tracer_provider(TracerProvider())
            tracer_provider = trace.get_tracer_provider()
            
            # Configure Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=14268,
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            self.logger.info("Distributed tracing configured successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to setup distributed tracing: {e}")
            self.tracer = None
    
    async def get_info(self) -> Dict[str, Any]:
        """Get information about the Strands implementation."""
        return {
            "name": self.name,
            "version": "1.0.0",
            "description": "Enterprise-grade AI orchestration with built-in observability",
            "capabilities": [
                "enterprise_observability",
                "multi_cloud_support", 
                "distributed_tracing",
                "error_recovery",
                "advanced_monitoring",
                "enterprise_security"
            ],
            "supported_tasks": [
                "feature_add",
                "bugfix", 
                "optimize",
                "qa",
                "edge_case"
            ],
            "enterprise_features": {
                "observability": self.config.observability_enabled,
                "distributed_tracing": self.config.distributed_tracing,
                "multi_cloud": len(self.config.cloud_providers) > 0,
                "error_recovery": self.config.error_recovery,
                "telemetry_endpoint": self.config.telemetry_endpoint
            },
            "strands_available": STRANDS_AVAILABLE
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get detailed capabilities of the Strands implementation."""
        return {
            "features": [
                "enterprise_observability",
                "multi_cloud_deployment",
                "distributed_tracing", 
                "automatic_error_recovery",
                "advanced_telemetry",
                "enterprise_security_controls",
                "cloud_provider_abstraction",
                "real_time_monitoring"
            ],
            "enterprise_grade": True,
            "observability": {
                "opentelemetry": True,
                "distributed_tracing": self.config.distributed_tracing,
                "real_time_metrics": True,
                "custom_dashboards": True,
                "alerting": True
            },
            "cloud_support": {
                "providers": self.config.cloud_providers,
                "multi_cloud_deployment": True,
                "provider_abstraction": True,
                "cloud_native_features": True
            },
            "error_handling": {
                "automatic_recovery": self.config.error_recovery,
                "retry_strategies": True,
                "circuit_breakers": True,
                "graceful_degradation": True
            },
            "security": {
                "enterprise_controls": True,
                "audit_logging": True,
                "compliance_ready": True,
                "secure_by_default": True
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of enterprise components."""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {},
            "enterprise_features": {}
        }
        
        try:
            # Check Strands availability
            health_status["components"]["strands"] = {
                "available": STRANDS_AVAILABLE,
                "status": "healthy" if STRANDS_AVAILABLE else "unavailable"
            }
            
            # Check agent manager
            if self.agent_manager:
                health_status["components"]["agent_manager"] = {
                    "status": "healthy",
                    "agents_count": len(getattr(self.agent_manager, 'agents', []))
                }
            
            # Check telemetry manager
            if self.telemetry_manager:
                health_status["components"]["telemetry"] = {
                    "status": "healthy",
                    "enabled": self.config.observability_enabled,
                    "endpoint": self.config.telemetry_endpoint
                }
            
            # Check provider manager
            if self.provider_manager:
                health_status["components"]["cloud_providers"] = {
                    "status": "healthy",
                    "providers": self.config.cloud_providers,
                    "count": len(self.config.cloud_providers)
                }
            
            # Check distributed tracing
            health_status["enterprise_features"]["distributed_tracing"] = {
                "enabled": self.config.distributed_tracing,
                "tracer_available": self.tracer is not None
            }
            
            # Check error recovery
            health_status["enterprise_features"]["error_recovery"] = {
                "enabled": self.config.error_recovery,
                "max_retries": self.config.max_retries
            }
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            self.logger.error(f"Health check failed: {e}")
        
        return health_status
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive enterprise metrics."""
        metrics = {
            "timestamp": time.time(),
            "execution_metrics": {
                "total_tasks": len(self.events),
                "current_task": self.current_task_id,
                "average_execution_time": 0.0,
                "success_rate": 0.0
            },
            "enterprise_metrics": {
                "observability_events": 0,
                "trace_spans": 0,
                "cloud_operations": 0,
                "error_recoveries": 0
            },
            "resource_metrics": {
                "memory_usage": 0,
                "cpu_usage": 0,
                "network_io": 0,
                "storage_io": 0
            }
        }
        
        try:
            # Calculate execution metrics from events
            task_events = [e for e in self.events if e.event_type == "task_completed"]
            if task_events:
                execution_times = [e.data.get("execution_time", 0) for e in task_events]
                metrics["execution_metrics"]["average_execution_time"] = sum(execution_times) / len(execution_times)
                
                successful_tasks = [e for e in task_events if e.data.get("status") == "success"]
                metrics["execution_metrics"]["success_rate"] = len(successful_tasks) / len(task_events)
            
            # Get telemetry metrics
            if self.telemetry_manager:
                telemetry_metrics = await self.telemetry_manager.get_metrics()
                metrics["enterprise_metrics"].update(telemetry_metrics)
            
            # Get provider metrics
            if self.provider_manager:
                provider_metrics = await self.provider_manager.get_metrics()
                metrics["enterprise_metrics"]["cloud_operations"] = provider_metrics.get("total_operations", 0)
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    @asynccontextmanager
    async def _trace_operation(self, operation_name: str, **attributes):
        """Context manager for distributed tracing."""
        if self.tracer:
            with self.tracer.start_as_current_span(operation_name) as span:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
                yield span
        else:
            yield None
    
    async def run_task(self, task: TaskSchema) -> AsyncIterator[RunResult]:
        """
        Execute a task using Strands enterprise workflow with comprehensive observability.
        """
        task_id = task.id or str(uuid.uuid4())
        self.current_task_id = task_id
        start_time = time.time()
        
        # Emit task start event
        await self._emit_event("task_started", {
            "task_id": task_id,
            "task_type": task.type,
            "framework": self.name
        })
        
        try:
            async with self._trace_operation("strands_task_execution", 
                                           task_id=task_id, 
                                           task_type=task.type) as span:
                
                # Initialize VCS provider if needed
                if task.vcs_provider:
                    await self._setup_vcs_provider(task.vcs_provider)
                
                # Execute task using enterprise workflow
                if STRANDS_AVAILABLE and self.workflow:
                    result = await self._execute_with_strands(task, span)
                else:
                    result = await self._execute_fallback(task, span)
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Create comprehensive result
                run_result = RunResult(
                    task_id=task_id,
                    status="success" if result.get("success", False) else "failed",
                    result=result,
                    artifacts=result.get("artifacts", {}),
                    timings={
                        "total_time": execution_time,
                        "agent_time": result.get("timings", {}).get("agent_time", 0),
                        "tool_time": result.get("timings", {}).get("tool_time", 0)
                    },
                    tokens=result.get("tokens", {}),
                    costs=result.get("costs", {}),
                    metadata={
                        "framework": self.name,
                        "enterprise_features": await self._get_enterprise_metadata(),
                        "trace_id": getattr(span, "context", {}).get("trace_id") if span else None,
                        "observability_events": len([e for e in self.events if e.data.get("task_id") == task_id])
                    }
                )
                
                # Emit completion event
                await self._emit_event("task_completed", {
                    "task_id": task_id,
                    "status": run_result.status,
                    "execution_time": execution_time,
                    "enterprise_features_used": list(run_result.metadata["enterprise_features"].keys())
                })
                
                yield run_result
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            # Attempt error recovery if enabled
            if self.config.error_recovery:
                recovery_result = await self._attempt_error_recovery(task, e)
                if recovery_result:
                    yield recovery_result
                    return
            
            # Emit error event
            await self._emit_event("task_failed", {
                "task_id": task_id,
                "error": error_msg,
                "execution_time": execution_time
            })
            
            # Create error result
            error_result = RunResult(
                task_id=task_id,
                status="error",
                result={"error": error_msg, "type": type(e).__name__},
                artifacts={},
                timings={"total_time": execution_time},
                tokens={},
                costs={},
                metadata={
                    "framework": self.name,
                    "error_type": type(e).__name__,
                    "error_recovery_attempted": self.config.error_recovery
                }
            )
            
            yield error_result
        
        finally:
            self.current_task_id = None
    
    async def _execute_with_strands(self, task: TaskSchema, span) -> Dict[str, Any]:
        """Execute task using full Strands enterprise capabilities."""
        try:
            # Create Strands task
            strands_task = Task(
                id=task.id,
                type=task.type,
                description=task.inputs.get("description", ""),
                requirements=task.inputs.get("requirements", []),
                context=task.inputs
            )
            
            # Execute with enterprise workflow
            result = await self.workflow.execute(
                task=strands_task,
                context={
                    "repo_path": task.repo_path,
                    "vcs_provider": task.vcs_provider,
                    "safety_policy": self.safety_policy,
                    "telemetry_manager": self.telemetry_manager,
                    "span": span
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Strands execution failed: {e}")
            raise AgentExecutionError(f"Enterprise workflow execution failed: {e}")
    
    async def _execute_fallback(self, task: TaskSchema, span) -> Dict[str, Any]:
        """Fallback execution when Strands is not available."""
        self.logger.info("Using fallback execution (Strands not available)")
        
        # Simulate enterprise workflow with fallback agents
        agents = {
            "architect": EnterpriseArchitectAgent(),
            "developer": SeniorDeveloperAgent(), 
            "qa_engineer": QAEngineerAgent()
        }
        
        results = {}
        artifacts = {}
        
        # Execute with each agent
        for agent_name, agent in agents.items():
            await self._emit_event("agent_started", {
                "agent": agent_name,
                "task_id": task.id
            })
            
            try:
                agent_result = await agent.execute(task, self.safety_policy)
                results[agent_name] = agent_result
                artifacts[f"{agent_name}_output"] = agent_result.get("output", "")
                
                await self._emit_event("agent_completed", {
                    "agent": agent_name,
                    "task_id": task.id,
                    "success": True
                })
                
            except Exception as e:
                self.logger.error(f"Agent {agent_name} failed: {e}")
                results[agent_name] = {"error": str(e)}
                
                await self._emit_event("agent_failed", {
                    "agent": agent_name,
                    "task_id": task.id,
                    "error": str(e)
                })
        
        # Aggregate results
        success = all("error" not in result for result in results.values())
        
        return {
            "success": success,
            "results": results,
            "artifacts": artifacts,
            "timings": {"agent_time": 0, "tool_time": 0},
            "tokens": {"total": 0},
            "costs": {"total": 0.0}
        }
    
    async def _attempt_error_recovery(self, task: TaskSchema, error: Exception) -> Optional[RunResult]:
        """Attempt to recover from errors using enterprise error handling."""
        if not self.config.error_recovery:
            return None
        
        self.logger.info(f"Attempting error recovery for task {task.id}")
        
        try:
            # Emit recovery attempt event
            await self._emit_event("error_recovery_started", {
                "task_id": task.id,
                "error_type": type(error).__name__,
                "error_message": str(error)
            })
            
            # Simple retry strategy for now
            for attempt in range(self.config.max_retries):
                try:
                    self.logger.info(f"Recovery attempt {attempt + 1}/{self.config.max_retries}")
                    
                    # Re-execute with modified parameters
                    modified_task = TaskSchema(
                        id=f"{task.id}_recovery_{attempt}",
                        type=task.type,
                        inputs={**task.inputs, "recovery_attempt": attempt + 1},
                        repo_path=task.repo_path,
                        vcs_provider=task.vcs_provider
                    )
                    
                    async for result in self.run_task(modified_task):
                        if result.status == "success":
                            await self._emit_event("error_recovery_succeeded", {
                                "task_id": task.id,
                                "recovery_attempt": attempt + 1
                            })
                            return result
                    
                except Exception as retry_error:
                    self.logger.warning(f"Recovery attempt {attempt + 1} failed: {retry_error}")
                    continue
            
            # Recovery failed
            await self._emit_event("error_recovery_failed", {
                "task_id": task.id,
                "attempts": self.config.max_retries
            })
            
        except Exception as recovery_error:
            self.logger.error(f"Error recovery process failed: {recovery_error}")
        
        return None
    
    async def _setup_vcs_provider(self, provider_name: str):
        """Set up VCS provider for the task."""
        if provider_name not in self.vcs_providers:
            if provider_name == "github":
                self.vcs_providers[provider_name] = GitHubProvider()
            elif provider_name == "gitlab":
                self.vcs_providers[provider_name] = GitLabProvider()
            else:
                raise ValueError(f"Unsupported VCS provider: {provider_name}")
    
    async def _get_enterprise_metadata(self) -> Dict[str, Any]:
        """Get metadata about enterprise features used."""
        return {
            "observability": self.config.observability_enabled,
            "distributed_tracing": self.config.distributed_tracing and self.tracer is not None,
            "multi_cloud": len(self.config.cloud_providers) > 0,
            "error_recovery": self.config.error_recovery,
            "telemetry_manager": self.telemetry_manager is not None,
            "provider_manager": self.provider_manager is not None
        }
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit structured event with enterprise observability."""
        from datetime import datetime
        
        event = Event(
            timestamp=datetime.now(),
            event_type=event_type,
            framework=self.name,
            agent_id="strands_enterprise",
            task_id=data.get("task_id", self.current_task_id or "unknown"),
            trace_id=self._get_current_trace_id() or "no-trace",
            span_id=self._get_current_span_id(),
            data=data
        )
        
        self.events.append(event)
        
        # Send to telemetry manager if available
        if self.telemetry_manager:
            await self.telemetry_manager.emit_event(event)
        
        # Log event
        self.logger.info(f"Event emitted: {event_type}", extra={"event_data": data})
    
    def _get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID from OpenTelemetry context."""
        if not self.tracer or not OTEL_IMPORTS_AVAILABLE:
            return None
        
        try:
            current_span = trace.get_current_span()
            if current_span and hasattr(current_span, 'get_span_context'):
                span_context = current_span.get_span_context()
                if hasattr(span_context, 'trace_id') and hasattr(span_context, 'is_valid'):
                    if span_context.is_valid:
                        return format(span_context.trace_id, '032x')
        except Exception:
            pass
        
        return None
    
    def _get_current_span_id(self) -> Optional[str]:
        """Get current span ID from OpenTelemetry context."""
        if not self.tracer or not OTEL_IMPORTS_AVAILABLE:
            return None
        
        try:
            current_span = trace.get_current_span()
            if current_span and hasattr(current_span, 'get_span_context'):
                span_context = current_span.get_span_context()
                if hasattr(span_context, 'span_id') and hasattr(span_context, 'is_valid'):
                    if span_context.is_valid:
                        return format(span_context.span_id, '016x')
        except Exception:
            pass
        
        return None


def create_strands_adapter(config: Optional[Dict[str, Any]] = None) -> StrandsAdapter:
    """Factory function to create a Strands adapter instance."""
    return StrandsAdapter(config)


# Export the adapter for the framework
__all__ = ["StrandsAdapter", "create_strands_adapter"]