"""
Cost and Token Tracking for AI Dev Squad platform.

This module provides comprehensive cost tracking and token counting capabilities
for all LLM interactions, with support for both API-based and local model usage,
real-time monitoring, budget alerts, and cost optimization recommendations.
"""

import json
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from collections import defaultdict

from .schema import EventType, LogLevel, create_event
from .logger import get_logger


class ModelProvider(Enum):
    """Enumeration of supported model providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    COHERE = "cohere"
    LOCAL = "local"
    UNKNOWN = "unknown"


class CostUnit(Enum):
    """Enumeration of cost units."""
    
    USD = "usd"
    TOKENS = "tokens"
    REQUESTS = "requests"
    COMPUTE_HOURS = "compute_hours"


@dataclass
class ModelPricing:
    """Pricing information for a specific model."""
    
    model_name: str
    provider: ModelProvider
    input_cost_per_1k_tokens: float = 0.0
    output_cost_per_1k_tokens: float = 0.0
    request_cost: float = 0.0
    context_window: int = 4096
    max_output_tokens: int = 2048
    currency: str = "USD"
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        num_requests: int = 1
    ) -> float:
        """Calculate total cost for given token usage."""
        
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k_tokens
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k_tokens
        request_cost = num_requests * self.request_cost
        
        return input_cost + output_cost + request_cost


@dataclass
class TokenUsage:
    """Token usage information for a single interaction."""
    
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model_name: str
    provider: ModelProvider
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    framework: Optional[str] = None
    
    def __post_init__(self):
        """Validate token counts."""
        if self.total_tokens != self.input_tokens + self.output_tokens:
            self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class CostEntry:
    """Cost entry for a single interaction."""
    
    cost_usd: float
    tokens: TokenUsage
    duration_ms: float
    pricing_model: ModelPricing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageStats:
    """Aggregated usage statistics."""
    
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    total_requests: int = 0
    total_duration_ms: float = 0.0
    
    # Per-model breakdown
    model_stats: Dict[str, Dict[str, Union[int, float]]] = field(default_factory=dict)
    
    # Per-provider breakdown
    provider_stats: Dict[str, Dict[str, Union[int, float]]] = field(default_factory=dict)
    
    # Time-based stats
    hourly_stats: Dict[str, Dict[str, Union[int, float]]] = field(default_factory=dict)
    daily_stats: Dict[str, Dict[str, Union[int, float]]] = field(default_factory=dict)
    
    def add_entry(self, entry: CostEntry):
        """Add a cost entry to the statistics."""
        
        # Update totals
        self.total_tokens += entry.tokens.total_tokens
        self.total_input_tokens += entry.tokens.input_tokens
        self.total_output_tokens += entry.tokens.output_tokens
        self.total_cost_usd += entry.cost_usd
        self.total_requests += 1
        self.total_duration_ms += entry.duration_ms
        
        # Update model stats
        model_name = entry.tokens.model_name
        if model_name not in self.model_stats:
            self.model_stats[model_name] = {
                "tokens": 0, "input_tokens": 0, "output_tokens": 0,
                "cost_usd": 0.0, "requests": 0, "duration_ms": 0.0
            }
        
        model_stat = self.model_stats[model_name]
        model_stat["tokens"] += entry.tokens.total_tokens
        model_stat["input_tokens"] += entry.tokens.input_tokens
        model_stat["output_tokens"] += entry.tokens.output_tokens
        model_stat["cost_usd"] += entry.cost_usd
        model_stat["requests"] += 1
        model_stat["duration_ms"] += entry.duration_ms
        
        # Update provider stats
        provider_name = entry.tokens.provider.value
        if provider_name not in self.provider_stats:
            self.provider_stats[provider_name] = {
                "tokens": 0, "input_tokens": 0, "output_tokens": 0,
                "cost_usd": 0.0, "requests": 0, "duration_ms": 0.0
            }
        
        provider_stat = self.provider_stats[provider_name]
        provider_stat["tokens"] += entry.tokens.total_tokens
        provider_stat["input_tokens"] += entry.tokens.input_tokens
        provider_stat["output_tokens"] += entry.tokens.output_tokens
        provider_stat["cost_usd"] += entry.cost_usd
        provider_stat["requests"] += 1
        provider_stat["duration_ms"] += entry.duration_ms
        
        # Update time-based stats
        hour_key = entry.timestamp.strftime("%Y-%m-%d-%H")
        day_key = entry.timestamp.strftime("%Y-%m-%d")
        
        for time_key, time_stats in [(hour_key, self.hourly_stats), (day_key, self.daily_stats)]:
            if time_key not in time_stats:
                time_stats[time_key] = {
                    "tokens": 0, "input_tokens": 0, "output_tokens": 0,
                    "cost_usd": 0.0, "requests": 0, "duration_ms": 0.0
                }
            
            time_stat = time_stats[time_key]
            time_stat["tokens"] += entry.tokens.total_tokens
            time_stat["input_tokens"] += entry.tokens.input_tokens
            time_stat["output_tokens"] += entry.tokens.output_tokens
            time_stat["cost_usd"] += entry.cost_usd
            time_stat["requests"] += 1
            time_stat["duration_ms"] += entry.duration_ms


class TokenCounter:
    """Token counting utilities for different model types."""
    
    def __init__(self):
        self.encoding_cache = {}
    
    def count_tokens(
        self,
        text: str,
        model_name: str,
        provider: ModelProvider = ModelProvider.UNKNOWN
    ) -> int:
        """Count tokens in text for a specific model."""
        
        # For now, use a simple approximation
        # In production, you'd use model-specific tokenizers
        if provider == ModelProvider.OPENAI:
            return self._count_openai_tokens(text, model_name)
        elif provider == ModelProvider.ANTHROPIC:
            return self._count_anthropic_tokens(text, model_name)
        elif provider == ModelProvider.OLLAMA:
            return self._count_ollama_tokens(text, model_name)
        else:
            return self._count_generic_tokens(text)
    
    def _count_openai_tokens(self, text: str, model_name: str) -> int:
        """Count tokens for OpenAI models."""
        try:
            import tiktoken
            
            # Get encoding for model
            if model_name not in self.encoding_cache:
                if "gpt-4" in model_name.lower():
                    encoding = tiktoken.encoding_for_model("gpt-4")
                elif "gpt-3.5" in model_name.lower():
                    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                else:
                    encoding = tiktoken.get_encoding("cl100k_base")
                self.encoding_cache[model_name] = encoding
            
            encoding = self.encoding_cache[model_name]
            return len(encoding.encode(text))
            
        except ImportError:
            # Fallback to approximation if tiktoken not available
            return self._count_generic_tokens(text)
    
    def _count_anthropic_tokens(self, text: str, model_name: str) -> int:
        """Count tokens for Anthropic models."""
        try:
            import anthropic
            
            # Anthropic uses a different tokenizer
            # For now, use approximation
            return self._count_generic_tokens(text)
            
        except ImportError:
            return self._count_generic_tokens(text)
    
    def _count_ollama_tokens(self, text: str, model_name: str) -> int:
        """Count tokens for Ollama models."""
        # Ollama models vary, use generic approximation
        return self._count_generic_tokens(text)
    
    def _count_generic_tokens(self, text: str) -> int:
        """Generic token counting approximation."""
        # Rough approximation: 1 token ≈ 4 characters for English text
        return max(1, len(text) // 4)


class BudgetManager:
    """Budget management and alerting system."""
    
    def __init__(self):
        self.budgets: Dict[str, Dict[str, Any]] = {}
        self.alert_callbacks: List[Callable] = []
    
    def set_budget(
        self,
        name: str,
        limit_usd: float,
        period: str = "daily",  # daily, weekly, monthly
        alert_thresholds: List[float] = None
    ):
        """Set a budget with optional alert thresholds."""
        
        if alert_thresholds is None:
            alert_thresholds = [0.5, 0.8, 0.9]  # 50%, 80%, 90%
        
        self.budgets[name] = {
            "limit_usd": limit_usd,
            "period": period,
            "alert_thresholds": alert_thresholds,
            "current_spend": 0.0,
            "alerts_sent": set(),
            "created_at": datetime.utcnow()
        }
    
    def add_spend(self, budget_name: str, amount_usd: float):
        """Add spending to a budget and check for alerts."""
        
        if budget_name not in self.budgets:
            return
        
        budget = self.budgets[budget_name]
        budget["current_spend"] += amount_usd
        
        # Check alert thresholds
        spend_ratio = budget["current_spend"] / budget["limit_usd"]
        
        for threshold in budget["alert_thresholds"]:
            if spend_ratio >= threshold and threshold not in budget["alerts_sent"]:
                self._send_budget_alert(budget_name, spend_ratio, threshold)
                budget["alerts_sent"].add(threshold)
    
    def _send_budget_alert(self, budget_name: str, spend_ratio: float, threshold: float):
        """Send budget alert to registered callbacks."""
        
        alert_data = {
            "budget_name": budget_name,
            "spend_ratio": spend_ratio,
            "threshold": threshold,
            "timestamp": datetime.utcnow()
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                print(f"Error in budget alert callback: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Add a callback for budget alerts."""
        self.alert_callbacks.append(callback)
    
    def get_budget_status(self, budget_name: str) -> Optional[Dict[str, Any]]:
        """Get current budget status."""
        
        if budget_name not in self.budgets:
            return None
        
        budget = self.budgets[budget_name]
        return {
            "name": budget_name,
            "limit_usd": budget["limit_usd"],
            "current_spend": budget["current_spend"],
            "remaining_usd": budget["limit_usd"] - budget["current_spend"],
            "spend_ratio": budget["current_spend"] / budget["limit_usd"],
            "period": budget["period"],
            "alerts_sent": list(budget["alerts_sent"])
        }


class CostTracker:
    """Main cost tracking and analysis system."""
    
    def __init__(
        self,
        pricing_file: Optional[str] = None,
        enable_real_time_tracking: bool = True,
        enable_budget_alerts: bool = True
    ):
        self.pricing_models: Dict[str, ModelPricing] = {}
        self.token_counter = TokenCounter()
        self.budget_manager = BudgetManager()
        self.usage_stats = UsageStats()
        self.cost_entries: List[CostEntry] = []
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Configuration
        self.enable_real_time_tracking = enable_real_time_tracking
        self.enable_budget_alerts = enable_budget_alerts
        
        # Load pricing models
        if pricing_file:
            self.load_pricing_models(pricing_file)
        else:
            self._load_default_pricing()
        
        # Setup budget alert callback
        if enable_budget_alerts:
            self.budget_manager.add_alert_callback(self._handle_budget_alert)
    
    def _load_default_pricing(self):
        """Load default pricing models for common providers."""
        
        # OpenAI pricing (as of 2024)
        self.add_pricing_model(ModelPricing(
            model_name="gpt-4",
            provider=ModelProvider.OPENAI,
            input_cost_per_1k_tokens=0.03,
            output_cost_per_1k_tokens=0.06,
            context_window=8192,
            max_output_tokens=4096
        ))
        
        self.add_pricing_model(ModelPricing(
            model_name="gpt-3.5-turbo",
            provider=ModelProvider.OPENAI,
            input_cost_per_1k_tokens=0.001,
            output_cost_per_1k_tokens=0.002,
            context_window=4096,
            max_output_tokens=2048
        ))
        
        # Anthropic pricing
        self.add_pricing_model(ModelPricing(
            model_name="claude-3-opus",
            provider=ModelProvider.ANTHROPIC,
            input_cost_per_1k_tokens=0.015,
            output_cost_per_1k_tokens=0.075,
            context_window=200000,
            max_output_tokens=4096
        ))
        
        self.add_pricing_model(ModelPricing(
            model_name="claude-3-sonnet",
            provider=ModelProvider.ANTHROPIC,
            input_cost_per_1k_tokens=0.003,
            output_cost_per_1k_tokens=0.015,
            context_window=200000,
            max_output_tokens=4096
        ))
        
        # Local models (Ollama) - free but track tokens
        self.add_pricing_model(ModelPricing(
            model_name="llama3.1:8b",
            provider=ModelProvider.OLLAMA,
            input_cost_per_1k_tokens=0.0,
            output_cost_per_1k_tokens=0.0,
            context_window=8192,
            max_output_tokens=2048
        ))
        
        self.add_pricing_model(ModelPricing(
            model_name="llama3.1:70b",
            provider=ModelProvider.OLLAMA,
            input_cost_per_1k_tokens=0.0,
            output_cost_per_1k_tokens=0.0,
            context_window=8192,
            max_output_tokens=2048
        ))
    
    def add_pricing_model(self, pricing: ModelPricing):
        """Add or update a pricing model."""
        with self.lock:
            key = f"{pricing.provider.value}:{pricing.model_name}"
            self.pricing_models[key] = pricing
    
    def load_pricing_models(self, file_path: str):
        """Load pricing models from JSON file."""
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for model_data in data.get("models", []):
                pricing = ModelPricing(
                    model_name=model_data["model_name"],
                    provider=ModelProvider(model_data["provider"]),
                    input_cost_per_1k_tokens=model_data.get("input_cost_per_1k_tokens", 0.0),
                    output_cost_per_1k_tokens=model_data.get("output_cost_per_1k_tokens", 0.0),
                    request_cost=model_data.get("request_cost", 0.0),
                    context_window=model_data.get("context_window", 4096),
                    max_output_tokens=model_data.get("max_output_tokens", 2048)
                )
                self.add_pricing_model(pricing)
                
        except Exception as e:
            print(f"Error loading pricing models: {e}")
            self._load_default_pricing()
    
    def track_llm_usage(
        self,
        model_name: str,
        provider: Union[str, ModelProvider],
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        framework: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostEntry:
        """Track LLM usage and calculate costs."""
        
        if isinstance(provider, str):
            try:
                provider = ModelProvider(provider.lower())
            except ValueError:
                provider = ModelProvider.UNKNOWN
        
        # Create token usage record
        token_usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            model_name=model_name,
            provider=provider,
            session_id=session_id,
            agent_id=agent_id,
            task_id=task_id,
            framework=framework
        )
        
        # Get pricing model
        pricing_key = f"{provider.value}:{model_name}"
        pricing_model = self.pricing_models.get(pricing_key)
        
        if not pricing_model:
            # Create default pricing for unknown models
            pricing_model = ModelPricing(
                model_name=model_name,
                provider=provider,
                input_cost_per_1k_tokens=0.0,
                output_cost_per_1k_tokens=0.0
            )
        
        # Calculate cost
        cost_usd = pricing_model.calculate_cost(input_tokens, output_tokens)
        
        # Create cost entry
        cost_entry = CostEntry(
            cost_usd=cost_usd,
            tokens=token_usage,
            duration_ms=duration_ms,
            pricing_model=pricing_model,
            metadata=metadata or {}
        )
        
        # Update statistics
        with self.lock:
            self.cost_entries.append(cost_entry)
            self.usage_stats.add_entry(cost_entry)
        
        # Update budgets
        if self.enable_budget_alerts and cost_usd > 0:
            for budget_name in self.budget_manager.budgets:
                self.budget_manager.add_spend(budget_name, cost_usd)
        
        # Log the usage
        if self.enable_real_time_tracking:
            self._log_usage_event(cost_entry)
        
        return cost_entry
    
    def estimate_cost(
        self,
        text: str,
        model_name: str,
        provider: Union[str, ModelProvider],
        estimated_output_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Estimate cost for a given text input."""
        
        if isinstance(provider, str):
            try:
                provider = ModelProvider(provider.lower())
            except ValueError:
                provider = ModelProvider.UNKNOWN
        
        # Count input tokens
        input_tokens = self.token_counter.count_tokens(text, model_name, provider)
        
        # Estimate output tokens if not provided
        if estimated_output_tokens is None:
            # Simple heuristic: output is typically 20-50% of input
            estimated_output_tokens = max(10, int(input_tokens * 0.3))
        
        # Get pricing
        pricing_key = f"{provider.value}:{model_name}"
        pricing_model = self.pricing_models.get(pricing_key)
        
        if not pricing_model:
            return {
                "input_tokens": input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "estimated_cost_usd": 0.0,
                "pricing_available": False
            }
        
        estimated_cost = pricing_model.calculate_cost(input_tokens, estimated_output_tokens)
        
        return {
            "input_tokens": input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "total_tokens": input_tokens + estimated_output_tokens,
            "estimated_cost_usd": estimated_cost,
            "pricing_available": True,
            "model_info": {
                "context_window": pricing_model.context_window,
                "max_output_tokens": pricing_model.max_output_tokens,
                "input_cost_per_1k": pricing_model.input_cost_per_1k_tokens,
                "output_cost_per_1k": pricing_model.output_cost_per_1k_tokens
            }
        }
    
    def get_usage_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "total"  # total, model, provider, day, hour
    ) -> Dict[str, Any]:
        """Get usage summary with optional filtering and grouping."""
        
        with self.lock:
            filtered_entries = self.cost_entries
            
            # Apply date filters
            if start_date:
                filtered_entries = [e for e in filtered_entries if e.timestamp >= start_date]
            if end_date:
                filtered_entries = [e for e in filtered_entries if e.timestamp <= end_date]
            
            if not filtered_entries:
                return {"total_entries": 0, "summary": {}}
            
            # Calculate summary based on grouping
            if group_by == "total":
                return self._calculate_total_summary(filtered_entries)
            elif group_by == "model":
                return self._calculate_model_summary(filtered_entries)
            elif group_by == "provider":
                return self._calculate_provider_summary(filtered_entries)
            elif group_by == "day":
                return self._calculate_daily_summary(filtered_entries)
            elif group_by == "hour":
                return self._calculate_hourly_summary(filtered_entries)
            else:
                return self._calculate_total_summary(filtered_entries)
    
    def _calculate_total_summary(self, entries: List[CostEntry]) -> Dict[str, Any]:
        """Calculate total summary across all entries."""
        
        total_cost = sum(e.cost_usd for e in entries)
        total_tokens = sum(e.tokens.total_tokens for e in entries)
        total_input_tokens = sum(e.tokens.input_tokens for e in entries)
        total_output_tokens = sum(e.tokens.output_tokens for e in entries)
        total_duration = sum(e.duration_ms for e in entries)
        
        return {
            "total_entries": len(entries),
            "summary": {
                "total_cost_usd": round(total_cost, 4),
                "total_tokens": total_tokens,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_requests": len(entries),
                "total_duration_ms": total_duration,
                "average_cost_per_request": round(total_cost / len(entries), 4) if entries else 0,
                "average_tokens_per_request": total_tokens // len(entries) if entries else 0,
                "cost_per_1k_tokens": round((total_cost / total_tokens) * 1000, 4) if total_tokens > 0 else 0
            }
        }
    
    def _calculate_model_summary(self, entries: List[CostEntry]) -> Dict[str, Any]:
        """Calculate summary grouped by model."""
        
        model_stats = defaultdict(lambda: {
            "cost_usd": 0.0, "tokens": 0, "input_tokens": 0,
            "output_tokens": 0, "requests": 0, "duration_ms": 0.0
        })
        
        for entry in entries:
            model = entry.tokens.model_name
            stats = model_stats[model]
            stats["cost_usd"] += entry.cost_usd
            stats["tokens"] += entry.tokens.total_tokens
            stats["input_tokens"] += entry.tokens.input_tokens
            stats["output_tokens"] += entry.tokens.output_tokens
            stats["requests"] += 1
            stats["duration_ms"] += entry.duration_ms
        
        # Round costs
        for stats in model_stats.values():
            stats["cost_usd"] = round(stats["cost_usd"], 4)
        
        return {
            "total_entries": len(entries),
            "summary": dict(model_stats)
        }
    
    def _calculate_provider_summary(self, entries: List[CostEntry]) -> Dict[str, Any]:
        """Calculate summary grouped by provider."""
        
        provider_stats = defaultdict(lambda: {
            "cost_usd": 0.0, "tokens": 0, "input_tokens": 0,
            "output_tokens": 0, "requests": 0, "duration_ms": 0.0
        })
        
        for entry in entries:
            provider = entry.tokens.provider.value
            stats = provider_stats[provider]
            stats["cost_usd"] += entry.cost_usd
            stats["tokens"] += entry.tokens.total_tokens
            stats["input_tokens"] += entry.tokens.input_tokens
            stats["output_tokens"] += entry.tokens.output_tokens
            stats["requests"] += 1
            stats["duration_ms"] += entry.duration_ms
        
        # Round costs
        for stats in provider_stats.values():
            stats["cost_usd"] = round(stats["cost_usd"], 4)
        
        return {
            "total_entries": len(entries),
            "summary": dict(provider_stats)
        }
    
    def _calculate_daily_summary(self, entries: List[CostEntry]) -> Dict[str, Any]:
        """Calculate summary grouped by day."""
        
        daily_stats = defaultdict(lambda: {
            "cost_usd": 0.0, "tokens": 0, "input_tokens": 0,
            "output_tokens": 0, "requests": 0, "duration_ms": 0.0
        })
        
        for entry in entries:
            day = entry.timestamp.strftime("%Y-%m-%d")
            stats = daily_stats[day]
            stats["cost_usd"] += entry.cost_usd
            stats["tokens"] += entry.tokens.total_tokens
            stats["input_tokens"] += entry.tokens.input_tokens
            stats["output_tokens"] += entry.tokens.output_tokens
            stats["requests"] += 1
            stats["duration_ms"] += entry.duration_ms
        
        # Round costs and sort by date
        for stats in daily_stats.values():
            stats["cost_usd"] = round(stats["cost_usd"], 4)
        
        sorted_daily = dict(sorted(daily_stats.items()))
        
        return {
            "total_entries": len(entries),
            "summary": sorted_daily
        }
    
    def _calculate_hourly_summary(self, entries: List[CostEntry]) -> Dict[str, Any]:
        """Calculate summary grouped by hour."""
        
        hourly_stats = defaultdict(lambda: {
            "cost_usd": 0.0, "tokens": 0, "input_tokens": 0,
            "output_tokens": 0, "requests": 0, "duration_ms": 0.0
        })
        
        for entry in entries:
            hour = entry.timestamp.strftime("%Y-%m-%d %H:00")
            stats = hourly_stats[hour]
            stats["cost_usd"] += entry.cost_usd
            stats["tokens"] += entry.tokens.total_tokens
            stats["input_tokens"] += entry.tokens.input_tokens
            stats["output_tokens"] += entry.tokens.output_tokens
            stats["requests"] += 1
            stats["duration_ms"] += entry.duration_ms
        
        # Round costs and sort by time
        for stats in hourly_stats.values():
            stats["cost_usd"] = round(stats["cost_usd"], 4)
        
        sorted_hourly = dict(sorted(hourly_stats.items()))
        
        return {
            "total_entries": len(entries),
            "summary": sorted_hourly
        }
    
    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations based on usage patterns."""
        
        recommendations = []
        
        with self.lock:
            if not self.cost_entries:
                return recommendations
            
            # Analyze model usage
            model_costs = defaultdict(float)
            model_requests = defaultdict(int)
            
            for entry in self.cost_entries:
                model_costs[entry.tokens.model_name] += entry.cost_usd
                model_requests[entry.tokens.model_name] += 1
            
            # Recommend cheaper alternatives for expensive models
            for model, cost in model_costs.items():
                if cost > 10.0:  # If spending more than $10 on a model
                    if "gpt-4" in model.lower():
                        recommendations.append({
                            "type": "model_substitution",
                            "priority": "high",
                            "current_model": model,
                            "suggested_model": "gpt-3.5-turbo",
                            "potential_savings_usd": cost * 0.9,  # Rough estimate
                            "description": "Consider using GPT-3.5-turbo for simpler tasks"
                        })
                    elif "claude-3-opus" in model.lower():
                        recommendations.append({
                            "type": "model_substitution",
                            "priority": "medium",
                            "current_model": model,
                            "suggested_model": "claude-3-sonnet",
                            "potential_savings_usd": cost * 0.8,
                            "description": "Consider using Claude-3-Sonnet for most tasks"
                        })
            
            # Recommend local models for high-volume usage
            total_api_cost = sum(e.cost_usd for e in self.cost_entries if e.cost_usd > 0)
            if total_api_cost > 50.0:  # If spending more than $50 on API calls
                recommendations.append({
                    "type": "local_deployment",
                    "priority": "high",
                    "current_cost": total_api_cost,
                    "suggested_solution": "Deploy Ollama with Llama 3.1",
                    "potential_savings_usd": total_api_cost * 0.95,
                    "description": "Consider deploying local models for high-volume usage"
                })
            
            # Recommend prompt optimization
            avg_input_tokens = sum(e.tokens.input_tokens for e in self.cost_entries) / len(self.cost_entries)
            if avg_input_tokens > 1000:
                recommendations.append({
                    "type": "prompt_optimization",
                    "priority": "medium",
                    "current_avg_input_tokens": int(avg_input_tokens),
                    "suggested_reduction": "20-30%",
                    "potential_savings_usd": total_api_cost * 0.25,
                    "description": "Optimize prompts to reduce input token usage"
                })
        
        return recommendations
    
    def _log_usage_event(self, cost_entry: CostEntry):
        """Log usage event to structured logger."""
        
        logger = get_logger()
        if logger:
            logger.log_llm_interaction(
                model_name=cost_entry.tokens.model_name,
                provider=cost_entry.tokens.provider.value,
                prompt_tokens=cost_entry.tokens.input_tokens,
                completion_tokens=cost_entry.tokens.output_tokens,
                duration_ms=cost_entry.duration_ms,
                cost_usd=cost_entry.cost_usd,
                agent_id=cost_entry.tokens.agent_id
            )
    
    def _handle_budget_alert(self, alert_data: Dict[str, Any]):
        """Handle budget alert by logging and notifying."""
        
        logger = get_logger()
        if logger:
            alert_event = create_event(
                EventType.SYSTEM_ERROR,  # Using system error for budget alerts
                level=LogLevel.WARNING,
                message=f"Budget alert: {alert_data['budget_name']} at {alert_data['spend_ratio']:.1%}",
                metadata={
                    "alert_type": "budget_threshold",
                    "budget_name": alert_data["budget_name"],
                    "spend_ratio": alert_data["spend_ratio"],
                    "threshold": alert_data["threshold"]
                }
            )
            logger.log_event(alert_event)
    
    def export_usage_data(
        self,
        file_path: str,
        format: str = "json",  # json, csv
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """Export usage data to file."""
        
        with self.lock:
            filtered_entries = self.cost_entries
            
            # Apply date filters
            if start_date:
                filtered_entries = [e for e in filtered_entries if e.timestamp >= start_date]
            if end_date:
                filtered_entries = [e for e in filtered_entries if e.timestamp <= end_date]
            
            if format.lower() == "json":
                self._export_json(filtered_entries, file_path)
            elif format.lower() == "csv":
                self._export_csv(filtered_entries, file_path)
            else:
                raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, entries: List[CostEntry], file_path: str):
        """Export entries to JSON format."""
        
        data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_entries": len(entries),
            "entries": []
        }
        
        for entry in entries:
            data["entries"].append({
                "timestamp": entry.timestamp.isoformat(),
                "model_name": entry.tokens.model_name,
                "provider": entry.tokens.provider.value,
                "input_tokens": entry.tokens.input_tokens,
                "output_tokens": entry.tokens.output_tokens,
                "total_tokens": entry.tokens.total_tokens,
                "cost_usd": entry.cost_usd,
                "duration_ms": entry.duration_ms,
                "session_id": entry.tokens.session_id,
                "agent_id": entry.tokens.agent_id,
                "task_id": entry.tokens.task_id,
                "framework": entry.tokens.framework,
                "metadata": entry.metadata
            })
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _export_csv(self, entries: List[CostEntry], file_path: str):
        """Export entries to CSV format."""
        
        import csv
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "timestamp", "model_name", "provider", "input_tokens",
                "output_tokens", "total_tokens", "cost_usd", "duration_ms",
                "session_id", "agent_id", "task_id", "framework"
            ])
            
            # Write data
            for entry in entries:
                writer.writerow([
                    entry.timestamp.isoformat(),
                    entry.tokens.model_name,
                    entry.tokens.provider.value,
                    entry.tokens.input_tokens,
                    entry.tokens.output_tokens,
                    entry.tokens.total_tokens,
                    entry.cost_usd,
                    entry.duration_ms,
                    entry.tokens.session_id or "",
                    entry.tokens.agent_id or "",
                    entry.tokens.task_id or "",
                    entry.tokens.framework or ""
                ])


# Global cost tracker instance
_global_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> Optional[CostTracker]:
    """Get the global cost tracker instance."""
    return _global_cost_tracker


def configure_cost_tracking(
    pricing_file: Optional[str] = None,
    enable_real_time_tracking: bool = True,
    enable_budget_alerts: bool = True
) -> CostTracker:
    """Configure global cost tracking."""
    global _global_cost_tracker
    
    _global_cost_tracker = CostTracker(
        pricing_file=pricing_file,
        enable_real_time_tracking=enable_real_time_tracking,
        enable_budget_alerts=enable_budget_alerts
    )
    
    return _global_cost_tracker