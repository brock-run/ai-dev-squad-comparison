"""
Tests for cost tracking and token counting system.

This module tests the comprehensive cost tracking capabilities including
token counting, pricing models, budget management, and usage analytics.
"""

import json
import tempfile
import time
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, MagicMock

from common.telemetry.cost_tracker import (
    CostTracker,
    ModelProvider,
    ModelPricing,
    TokenUsage,
    CostEntry,
    UsageStats,
    TokenCounter,
    BudgetManager,
    configure_cost_tracking,
    get_cost_tracker
)


class TestModelPricing(TestCase):
    """Test cases for ModelPricing functionality."""
    
    def test_model_pricing_creation(self):
        """Test ModelPricing creation and cost calculation."""
        
        pricing = ModelPricing(
            model_name="gpt-4",
            provider=ModelProvider.OPENAI,
            input_cost_per_1k_tokens=0.03,
            output_cost_per_1k_tokens=0.06,
            context_window=8192,
            max_output_tokens=4096
        )
        
        self.assertEqual(pricing.model_name, "gpt-4")
        self.assertEqual(pricing.provider, ModelProvider.OPENAI)
        self.assertEqual(pricing.input_cost_per_1k_tokens, 0.03)
        self.assertEqual(pricing.output_cost_per_1k_tokens, 0.06)
    
    def test_cost_calculation(self):
        """Test cost calculation for different token amounts."""
        
        pricing = ModelPricing(
            model_name="gpt-3.5-turbo",
            provider=ModelProvider.OPENAI,
            input_cost_per_1k_tokens=0.001,
            output_cost_per_1k_tokens=0.002
        )
        
        # Test basic calculation
        cost = pricing.calculate_cost(1000, 500)  # 1k input, 500 output
        expected_cost = (1000/1000 * 0.001) + (500/1000 * 0.002)
        self.assertAlmostEqual(cost, expected_cost, places=6)
        
        # Test with request cost
        pricing.request_cost = 0.01
        cost_with_request = pricing.calculate_cost(1000, 500, 2)
        expected_with_request = expected_cost + (2 * 0.01)
        self.assertAlmostEqual(cost_with_request, expected_with_request, places=6)
    
    def test_free_model_pricing(self):
        """Test pricing for free models like Ollama."""
        
        pricing = ModelPricing(
            model_name="llama3.1:8b",
            provider=ModelProvider.OLLAMA,
            input_cost_per_1k_tokens=0.0,
            output_cost_per_1k_tokens=0.0
        )
        
        cost = pricing.calculate_cost(5000, 2000)
        self.assertEqual(cost, 0.0)


class TestTokenUsage(TestCase):
    """Test cases for TokenUsage functionality."""
    
    def test_token_usage_creation(self):
        """Test TokenUsage creation and validation."""
        
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            model_name="gpt-3.5-turbo",
            provider=ModelProvider.OPENAI,
            session_id="session_123",
            agent_id="agent_456"
        )
        
        self.assertEqual(usage.input_tokens, 100)
        self.assertEqual(usage.output_tokens, 50)
        self.assertEqual(usage.total_tokens, 150)
        self.assertEqual(usage.model_name, "gpt-3.5-turbo")
        self.assertEqual(usage.provider, ModelProvider.OPENAI)
        self.assertEqual(usage.session_id, "session_123")
        self.assertEqual(usage.agent_id, "agent_456")
    
    def test_token_usage_auto_correction(self):
        """Test automatic correction of total tokens."""
        
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=200,  # Incorrect total
            model_name="test_model",
            provider=ModelProvider.OPENAI
        )
        
        # Should be auto-corrected to 150
        self.assertEqual(usage.total_tokens, 150)


class TestTokenCounter(TestCase):
    """Test cases for TokenCounter functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.counter = TokenCounter()
    
    def test_generic_token_counting(self):
        """Test generic token counting approximation."""
        
        text = "This is a test sentence with multiple words."
        tokens = self.counter.count_tokens(text, "unknown_model", ModelProvider.UNKNOWN)
        
        # Should return at least 1 token
        self.assertGreater(tokens, 0)
        
        # Longer text should have more tokens
        longer_text = text * 5
        longer_tokens = self.counter.count_tokens(longer_text, "unknown_model", ModelProvider.UNKNOWN)
        self.assertGreater(longer_tokens, tokens)
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        
        tokens = self.counter.count_tokens("", "test_model", ModelProvider.OPENAI)
        self.assertEqual(tokens, 1)  # Should return at least 1
    
    def test_different_providers(self):
        """Test token counting for different providers."""
        
        text = "Hello, world! This is a test."
        
        openai_tokens = self.counter.count_tokens(text, "gpt-4", ModelProvider.OPENAI)
        anthropic_tokens = self.counter.count_tokens(text, "claude-3", ModelProvider.ANTHROPIC)
        ollama_tokens = self.counter.count_tokens(text, "llama3.1", ModelProvider.OLLAMA)
        
        # All should return positive token counts
        self.assertGreater(openai_tokens, 0)
        self.assertGreater(anthropic_tokens, 0)
        self.assertGreater(ollama_tokens, 0)


class TestBudgetManager(TestCase):
    """Test cases for BudgetManager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.budget_manager = BudgetManager()
        self.alerts_received = []
        
        def alert_callback(alert_data):
            self.alerts_received.append(alert_data)
        
        self.budget_manager.add_alert_callback(alert_callback)
    
    def test_budget_creation(self):
        """Test budget creation and configuration."""
        
        self.budget_manager.set_budget(
            name="daily_budget",
            limit_usd=10.0,
            period="daily",
            alert_thresholds=[0.5, 0.8, 0.9]
        )
        
        budget_status = self.budget_manager.get_budget_status("daily_budget")
        
        self.assertIsNotNone(budget_status)
        self.assertEqual(budget_status["name"], "daily_budget")
        self.assertEqual(budget_status["limit_usd"], 10.0)
        self.assertEqual(budget_status["current_spend"], 0.0)
        self.assertEqual(budget_status["remaining_usd"], 10.0)
        self.assertEqual(budget_status["spend_ratio"], 0.0)
    
    def test_budget_spending_and_alerts(self):
        """Test budget spending tracking and alert generation."""
        
        self.budget_manager.set_budget(
            name="test_budget",
            limit_usd=10.0,
            alert_thresholds=[0.5, 0.8]
        )
        
        # Add spending below first threshold
        self.budget_manager.add_spend("test_budget", 3.0)
        self.assertEqual(len(self.alerts_received), 0)
        
        # Add spending to trigger first alert (50% threshold)
        self.budget_manager.add_spend("test_budget", 2.5)  # Total: 5.5 (55%)
        self.assertEqual(len(self.alerts_received), 1)
        self.assertEqual(self.alerts_received[0]["threshold"], 0.5)
        
        # Add spending to trigger second alert (80% threshold)
        self.budget_manager.add_spend("test_budget", 3.0)  # Total: 8.5 (85%)
        self.assertEqual(len(self.alerts_received), 2)
        self.assertEqual(self.alerts_received[1]["threshold"], 0.8)
        
        # Verify budget status
        status = self.budget_manager.get_budget_status("test_budget")
        self.assertEqual(status["current_spend"], 8.5)
        self.assertEqual(status["remaining_usd"], 1.5)
        self.assertAlmostEqual(status["spend_ratio"], 0.85, places=2)
    
    def test_nonexistent_budget(self):
        """Test handling of nonexistent budget."""
        
        # Should not raise error
        self.budget_manager.add_spend("nonexistent", 5.0)
        
        # Should return None
        status = self.budget_manager.get_budget_status("nonexistent")
        self.assertIsNone(status)


class TestUsageStats(TestCase):
    """Test cases for UsageStats functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.stats = UsageStats()
    
    def test_empty_stats(self):
        """Test initial empty statistics."""
        
        self.assertEqual(self.stats.total_tokens, 0)
        self.assertEqual(self.stats.total_cost_usd, 0.0)
        self.assertEqual(self.stats.total_requests, 0)
        self.assertEqual(len(self.stats.model_stats), 0)
        self.assertEqual(len(self.stats.provider_stats), 0)
    
    def test_adding_entries(self):
        """Test adding cost entries to statistics."""
        
        # Create test entries
        pricing = ModelPricing(
            model_name="gpt-3.5-turbo",
            provider=ModelProvider.OPENAI,
            input_cost_per_1k_tokens=0.001,
            output_cost_per_1k_tokens=0.002
        )
        
        token_usage = TokenUsage(
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            model_name="gpt-3.5-turbo",
            provider=ModelProvider.OPENAI
        )
        
        cost_entry = CostEntry(
            cost_usd=0.002,
            tokens=token_usage,
            duration_ms=1500.0,
            pricing_model=pricing
        )
        
        # Add entry
        self.stats.add_entry(cost_entry)
        
        # Verify totals
        self.assertEqual(self.stats.total_tokens, 1500)
        self.assertEqual(self.stats.total_input_tokens, 1000)
        self.assertEqual(self.stats.total_output_tokens, 500)
        self.assertEqual(self.stats.total_cost_usd, 0.002)
        self.assertEqual(self.stats.total_requests, 1)
        self.assertEqual(self.stats.total_duration_ms, 1500.0)
        
        # Verify model stats
        self.assertIn("gpt-3.5-turbo", self.stats.model_stats)
        model_stat = self.stats.model_stats["gpt-3.5-turbo"]
        self.assertEqual(model_stat["tokens"], 1500)
        self.assertEqual(model_stat["cost_usd"], 0.002)
        
        # Verify provider stats
        self.assertIn("openai", self.stats.provider_stats)
        provider_stat = self.stats.provider_stats["openai"]
        self.assertEqual(provider_stat["tokens"], 1500)
        self.assertEqual(provider_stat["cost_usd"], 0.002)


class TestCostTracker(TestCase):
    """Test cases for CostTracker functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.cost_tracker = CostTracker(enable_real_time_tracking=False)
    
    def tearDown(self):
        """Clean up test environment."""
        # Reset global tracker
        import common.telemetry.cost_tracker
        common.telemetry.cost_tracker._global_cost_tracker = None
    
    def test_cost_tracker_creation(self):
        """Test CostTracker creation with default pricing."""
        
        self.assertIsNotNone(self.cost_tracker.pricing_models)
        self.assertIsNotNone(self.cost_tracker.token_counter)
        self.assertIsNotNone(self.cost_tracker.budget_manager)
        
        # Should have default pricing models
        self.assertGreater(len(self.cost_tracker.pricing_models), 0)
        
        # Check for specific default models
        self.assertIn("openai:gpt-4", self.cost_tracker.pricing_models)
        self.assertIn("openai:gpt-3.5-turbo", self.cost_tracker.pricing_models)
        self.assertIn("ollama:llama3.1:8b", self.cost_tracker.pricing_models)
    
    def test_track_llm_usage(self):
        """Test LLM usage tracking and cost calculation."""
        
        cost_entry = self.cost_tracker.track_llm_usage(
            model_name="gpt-3.5-turbo",
            provider="openai",
            input_tokens=1000,
            output_tokens=500,
            duration_ms=2000.0,
            session_id="session_123",
            agent_id="agent_456"
        )
        
        # Verify cost entry
        self.assertIsInstance(cost_entry, CostEntry)
        self.assertEqual(cost_entry.tokens.input_tokens, 1000)
        self.assertEqual(cost_entry.tokens.output_tokens, 500)
        self.assertEqual(cost_entry.tokens.total_tokens, 1500)
        self.assertEqual(cost_entry.tokens.model_name, "gpt-3.5-turbo")
        self.assertEqual(cost_entry.tokens.provider, ModelProvider.OPENAI)
        self.assertEqual(cost_entry.duration_ms, 2000.0)
        self.assertGreater(cost_entry.cost_usd, 0)  # Should have calculated cost
        
        # Verify tracking
        self.assertEqual(len(self.cost_tracker.cost_entries), 1)
        self.assertEqual(self.cost_tracker.usage_stats.total_requests, 1)
        self.assertEqual(self.cost_tracker.usage_stats.total_tokens, 1500)
    
    def test_track_free_model_usage(self):
        """Test tracking usage for free models."""
        
        cost_entry = self.cost_tracker.track_llm_usage(
            model_name="llama3.1:8b",
            provider="ollama",
            input_tokens=2000,
            output_tokens=1000,
            duration_ms=3000.0
        )
        
        # Should track tokens but no cost
        self.assertEqual(cost_entry.cost_usd, 0.0)
        self.assertEqual(cost_entry.tokens.total_tokens, 3000)
        self.assertEqual(cost_entry.tokens.provider, ModelProvider.OLLAMA)
    
    def test_estimate_cost(self):
        """Test cost estimation for text input."""
        
        text = "This is a test prompt for cost estimation."
        
        estimate = self.cost_tracker.estimate_cost(
            text=text,
            model_name="gpt-3.5-turbo",
            provider="openai"
        )
        
        self.assertIn("input_tokens", estimate)
        self.assertIn("estimated_output_tokens", estimate)
        self.assertIn("estimated_cost_usd", estimate)
        self.assertIn("pricing_available", estimate)
        
        self.assertTrue(estimate["pricing_available"])
        self.assertGreater(estimate["input_tokens"], 0)
        self.assertGreater(estimate["estimated_output_tokens"], 0)
        self.assertGreaterEqual(estimate["estimated_cost_usd"], 0)
    
    def test_estimate_cost_unknown_model(self):
        """Test cost estimation for unknown model."""
        
        estimate = self.cost_tracker.estimate_cost(
            text="Test text",
            model_name="unknown_model",
            provider="unknown"
        )
        
        self.assertFalse(estimate["pricing_available"])
        self.assertEqual(estimate["estimated_cost_usd"], 0.0)
    
    def test_usage_summary_total(self):
        """Test usage summary generation."""
        
        # Add some usage data
        self.cost_tracker.track_llm_usage(
            model_name="gpt-3.5-turbo",
            provider="openai",
            input_tokens=1000,
            output_tokens=500,
            duration_ms=1500.0
        )
        
        self.cost_tracker.track_llm_usage(
            model_name="gpt-4",
            provider="openai",
            input_tokens=800,
            output_tokens=400,
            duration_ms=2000.0
        )
        
        summary = self.cost_tracker.get_usage_summary(group_by="total")
        
        self.assertEqual(summary["total_entries"], 2)
        self.assertIn("summary", summary)
        
        total_summary = summary["summary"]
        self.assertEqual(total_summary["total_tokens"], 2700)  # 1500 + 1200
        self.assertEqual(total_summary["total_input_tokens"], 1800)  # 1000 + 800
        self.assertEqual(total_summary["total_output_tokens"], 900)  # 500 + 400
        self.assertEqual(total_summary["total_requests"], 2)
        self.assertGreater(total_summary["total_cost_usd"], 0)
    
    def test_usage_summary_by_model(self):
        """Test usage summary grouped by model."""
        
        # Add usage for different models
        self.cost_tracker.track_llm_usage(
            model_name="gpt-3.5-turbo",
            provider="openai",
            input_tokens=1000,
            output_tokens=500,
            duration_ms=1500.0
        )
        
        self.cost_tracker.track_llm_usage(
            model_name="gpt-3.5-turbo",
            provider="openai",
            input_tokens=500,
            output_tokens=250,
            duration_ms=1000.0
        )
        
        self.cost_tracker.track_llm_usage(
            model_name="gpt-4",
            provider="openai",
            input_tokens=800,
            output_tokens=400,
            duration_ms=2000.0
        )
        
        summary = self.cost_tracker.get_usage_summary(group_by="model")
        
        self.assertEqual(summary["total_entries"], 3)
        model_summary = summary["summary"]
        
        # Check GPT-3.5-turbo stats (2 requests)
        self.assertIn("gpt-3.5-turbo", model_summary)
        gpt35_stats = model_summary["gpt-3.5-turbo"]
        self.assertEqual(gpt35_stats["requests"], 2)
        self.assertEqual(gpt35_stats["tokens"], 2250)  # 1500 + 750
        
        # Check GPT-4 stats (1 request)
        self.assertIn("gpt-4", model_summary)
        gpt4_stats = model_summary["gpt-4"]
        self.assertEqual(gpt4_stats["requests"], 1)
        self.assertEqual(gpt4_stats["tokens"], 1200)
    
    def test_cost_optimization_recommendations(self):
        """Test cost optimization recommendations."""
        
        # Add expensive usage to trigger recommendations
        for _ in range(10):
            self.cost_tracker.track_llm_usage(
                model_name="gpt-4",
                provider="openai",
                input_tokens=2000,
                output_tokens=1000,
                duration_ms=3000.0
            )
        
        recommendations = self.cost_tracker.get_cost_optimization_recommendations()
        
        self.assertIsInstance(recommendations, list)
        
        # Should have recommendations for expensive GPT-4 usage
        model_substitution_recs = [r for r in recommendations if r["type"] == "model_substitution"]
        self.assertGreater(len(model_substitution_recs), 0)
        
        # Check recommendation structure
        if model_substitution_recs:
            rec = model_substitution_recs[0]
            self.assertIn("current_model", rec)
            self.assertIn("suggested_model", rec)
            self.assertIn("potential_savings_usd", rec)
            self.assertIn("description", rec)
    
    def test_export_usage_data_json(self):
        """Test exporting usage data to JSON."""
        
        # Add some usage data
        self.cost_tracker.track_llm_usage(
            model_name="gpt-3.5-turbo",
            provider="openai",
            input_tokens=1000,
            output_tokens=500,
            duration_ms=1500.0,
            session_id="session_123"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            self.cost_tracker.export_usage_data(temp_file, format="json")
            
            # Verify file was created and contains data
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            self.assertIn("export_timestamp", data)
            self.assertIn("total_entries", data)
            self.assertIn("entries", data)
            self.assertEqual(data["total_entries"], 1)
            self.assertEqual(len(data["entries"]), 1)
            
            entry = data["entries"][0]
            self.assertEqual(entry["model_name"], "gpt-3.5-turbo")
            self.assertEqual(entry["provider"], "openai")
            self.assertEqual(entry["input_tokens"], 1000)
            self.assertEqual(entry["output_tokens"], 500)
            self.assertEqual(entry["session_id"], "session_123")
            
        finally:
            import os
            os.unlink(temp_file)
    
    def test_export_usage_data_csv(self):
        """Test exporting usage data to CSV."""
        
        # Add some usage data
        self.cost_tracker.track_llm_usage(
            model_name="gpt-4",
            provider="openai",
            input_tokens=800,
            output_tokens=400,
            duration_ms=2000.0,
            agent_id="agent_789"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        try:
            self.cost_tracker.export_usage_data(temp_file, format="csv")
            
            # Verify file was created and contains data
            with open(temp_file, 'r') as f:
                lines = f.readlines()
            
            self.assertGreater(len(lines), 1)  # Header + at least one data row
            
            # Check header
            header = lines[0].strip().split(',')
            self.assertIn("model_name", header)
            self.assertIn("provider", header)
            self.assertIn("input_tokens", header)
            self.assertIn("output_tokens", header)
            
            # Check data row
            data_row = lines[1].strip().split(',')
            self.assertEqual(data_row[header.index("model_name")], "gpt-4")
            self.assertEqual(data_row[header.index("provider")], "openai")
            self.assertEqual(data_row[header.index("input_tokens")], "800")
            self.assertEqual(data_row[header.index("output_tokens")], "400")
            
        finally:
            import os
            os.unlink(temp_file)


class TestGlobalCostTracking(TestCase):
    """Test cases for global cost tracking configuration."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset global tracker
        import common.telemetry.cost_tracker
        common.telemetry.cost_tracker._global_cost_tracker = None
    
    def tearDown(self):
        """Clean up test environment."""
        # Reset global tracker
        import common.telemetry.cost_tracker
        common.telemetry.cost_tracker._global_cost_tracker = None
    
    def test_configure_cost_tracking(self):
        """Test global cost tracking configuration."""
        
        tracker = configure_cost_tracking(
            enable_real_time_tracking=True,
            enable_budget_alerts=True
        )
        
        self.assertIsNotNone(tracker)
        self.assertIsInstance(tracker, CostTracker)
        
        # Should be accessible globally
        global_tracker = get_cost_tracker()
        self.assertIs(tracker, global_tracker)
    
    def test_get_cost_tracker_when_not_configured(self):
        """Test getting cost tracker when not configured."""
        
        tracker = get_cost_tracker()
        self.assertIsNone(tracker)