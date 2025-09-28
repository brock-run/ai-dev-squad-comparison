"""
Tests for enhanced dashboard functionality.

This module tests the dashboard data collection, metrics aggregation,
parity matrix generation, and API endpoints.
"""

import json
from unittest import TestCase
from unittest.mock import patch, MagicMock

from common.telemetry.dashboard import (
    DashboardMetrics,
    DashboardDataCollector,
    ParityMatrixEntry,
    EnhancedDashboard
)
from common.telemetry.cost_tracker import CostTracker, ModelProvider


class TestDashboardMetrics(TestCase):
    """Test cases for DashboardMetrics data structure."""
    
    def test_dashboard_metrics_creation(self):
        """Test DashboardMetrics creation with default values."""
        
        metrics = DashboardMetrics()
        
        self.assertEqual(metrics.total_requests, 0)
        self.assertEqual(metrics.total_tokens, 0)
        self.assertEqual(metrics.total_cost_usd, 0.0)
        self.assertEqual(metrics.total_duration_ms, 0.0)
        self.assertEqual(metrics.avg_response_time, 0.0)
        self.assertEqual(metrics.success_rate, 0.0)
        self.assertEqual(metrics.error_rate, 0.0)
        
        # Check that collections are initialized
        self.assertIsInstance(metrics.framework_stats, dict)
        self.assertIsInstance(metrics.model_stats, dict)
        self.assertIsInstance(metrics.provider_stats, dict)
        self.assertIsInstance(metrics.hourly_stats, dict)
        self.assertIsInstance(metrics.daily_stats, dict)
        self.assertIsInstance(metrics.cost_trends, list)
        self.assertIsInstance(metrics.budget_status, list)
        self.assertIsInstance(metrics.optimization_recommendations, list)
    
    def test_dashboard_metrics_with_data(self):
        """Test DashboardMetrics with actual data."""
        
        metrics = DashboardMetrics(
            total_requests=100,
            total_tokens=50000,
            total_cost_usd=25.50,
            total_duration_ms=120000.0,
            avg_response_time=1200.0,
            success_rate=0.95,
            error_rate=0.05
        )
        
        self.assertEqual(metrics.total_requests, 100)
        self.assertEqual(metrics.total_tokens, 50000)
        self.assertEqual(metrics.total_cost_usd, 25.50)
        self.assertEqual(metrics.avg_response_time, 1200.0)
        self.assertEqual(metrics.success_rate, 0.95)
        self.assertEqual(metrics.error_rate, 0.05)


class TestParityMatrixEntry(TestCase):
    """Test cases for ParityMatrixEntry data structure."""
    
    def test_parity_matrix_entry_creation(self):
        """Test ParityMatrixEntry creation."""
        
        entry = ParityMatrixEntry(
            framework="LangGraph",
            feature="Agent Lifecycle Management",
            status="supported",
            notes="Full lifecycle with state persistence",
            version_added="1.0.0",
            performance_score=0.9,
            cost_efficiency=0.85
        )
        
        self.assertEqual(entry.framework, "LangGraph")
        self.assertEqual(entry.feature, "Agent Lifecycle Management")
        self.assertEqual(entry.status, "supported")
        self.assertEqual(entry.notes, "Full lifecycle with state persistence")
        self.assertEqual(entry.version_added, "1.0.0")
        self.assertEqual(entry.performance_score, 0.9)
        self.assertEqual(entry.cost_efficiency, 0.85)


class TestDashboardDataCollector(TestCase):
    """Test cases for DashboardDataCollector functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.collector = DashboardDataCollector()
    
    def test_data_collector_creation(self):
        """Test DashboardDataCollector creation."""
        
        self.assertIsNotNone(self.collector)
        # Note: logger, cost_tracker, and trace_manager may be None if not configured
    
    @patch('common.telemetry.dashboard.get_cost_tracker')
    def test_collect_metrics_with_cost_tracker(self, mock_get_cost_tracker):
        """Test metrics collection with cost tracker data."""
        
        # Mock cost tracker
        mock_cost_tracker = MagicMock()
        mock_cost_tracker.get_usage_summary.return_value = {
            "total_entries": 10,
            "summary": {
                "total_requests": 10,
                "total_tokens": 5000,
                "total_cost_usd": 2.50,
                "total_duration_ms": 15000.0
            }
        }
        mock_cost_tracker.budget_manager.budgets = {}
        mock_cost_tracker.get_cost_optimization_recommendations.return_value = []
        
        mock_get_cost_tracker.return_value = mock_cost_tracker
        
        # Create new collector to pick up mocked cost tracker
        collector = DashboardDataCollector()
        
        metrics = collector.collect_metrics(time_range="24h")
        
        self.assertEqual(metrics.total_requests, 10)
        self.assertEqual(metrics.total_tokens, 5000)
        self.assertEqual(metrics.total_cost_usd, 2.50)
        self.assertEqual(metrics.total_duration_ms, 15000.0)
        self.assertEqual(metrics.avg_response_time, 1500.0)  # 15000 / 10
    
    def test_collect_metrics_without_trackers(self):
        """Test metrics collection without configured trackers."""
        
        metrics = self.collector.collect_metrics(time_range="1h")
        
        # Should return default metrics
        self.assertEqual(metrics.total_requests, 0)
        self.assertEqual(metrics.total_tokens, 0)
        self.assertEqual(metrics.total_cost_usd, 0.0)
    
    def test_get_parity_matrix(self):
        """Test parity matrix generation."""
        
        matrix = self.collector.get_parity_matrix()
        
        self.assertIsInstance(matrix, list)
        self.assertGreater(len(matrix), 0)
        
        # Check that all entries are ParityMatrixEntry instances
        for entry in matrix:
            self.assertIsInstance(entry, ParityMatrixEntry)
            self.assertIn(entry.framework, ["LangGraph", "CrewAI", "AutoGen", "Langroid", "LlamaIndex", "Haystack"])
            self.assertIn(entry.status, ["supported", "partial", "not_supported", "planned"])
            self.assertIsInstance(entry.performance_score, (int, float))
            self.assertIsInstance(entry.cost_efficiency, (int, float))
    
    def test_get_trace_visualization_data(self):
        """Test trace visualization data generation."""
        
        # Test without specific trace ID
        trace_data = self.collector.get_trace_visualization_data()
        
        self.assertIsInstance(trace_data, dict)
        self.assertIn("total_traces", trace_data)
        self.assertIn("avg_duration_ms", trace_data)
        self.assertIn("error_rate", trace_data)
        self.assertIn("top_operations", trace_data)
        
        # Test with specific trace ID
        trace_data_specific = self.collector.get_trace_visualization_data(trace_id="test_trace_123")
        
        self.assertIsInstance(trace_data_specific, dict)
        self.assertIn("trace_id", trace_data_specific)
        self.assertIn("spans", trace_data_specific)
        self.assertEqual(trace_data_specific["trace_id"], "test_trace_123")
    
    def test_calculate_performance_score(self):
        """Test performance score calculation."""
        
        score = self.collector._calculate_performance_score("LangGraph", "Agent Lifecycle Management")
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_calculate_cost_efficiency(self):
        """Test cost efficiency calculation."""
        
        efficiency = self.collector._calculate_cost_efficiency("CrewAI", "Task Orchestration")
        
        self.assertIsInstance(efficiency, float)
        self.assertGreaterEqual(efficiency, 0.0)
        self.assertLessEqual(efficiency, 1.0)
    
    def test_generate_cost_trends(self):
        """Test cost trends generation."""
        
        from datetime import datetime, timedelta
        
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow()
        
        trends = self.collector._generate_cost_trends(start_time, end_time)
        
        self.assertIsInstance(trends, list)
        self.assertGreater(len(trends), 0)
        
        # Check trend data structure
        for trend in trends:
            self.assertIn("timestamp", trend)
            self.assertIn("cost_usd", trend)
            self.assertIn("tokens", trend)
            self.assertIn("requests", trend)


class TestEnhancedDashboard(TestCase):
    """Test cases for EnhancedDashboard functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset global dashboard
        import common.telemetry.dashboard
        common.telemetry.dashboard._global_dashboard = None
    
    def tearDown(self):
        """Clean up test environment."""
        # Reset global dashboard
        import common.telemetry.dashboard
        common.telemetry.dashboard._global_dashboard = None
    
    def test_dashboard_creation_without_flask(self):
        """Test dashboard creation when Flask is not available."""
        
        with patch('common.telemetry.dashboard.FLASK_AVAILABLE', False):
            with self.assertRaises(ImportError):
                EnhancedDashboard()
    
    @patch('common.telemetry.dashboard.FLASK_AVAILABLE', True)
    @patch('common.telemetry.dashboard.Flask')
    @patch('common.telemetry.dashboard.SocketIO')
    def test_dashboard_creation_with_flask(self, mock_socketio, mock_flask):
        """Test dashboard creation when Flask is available."""
        
        # Mock Flask app
        mock_app = MagicMock()
        mock_flask.return_value = mock_app
        
        # Mock SocketIO
        mock_socketio_instance = MagicMock()
        mock_socketio.return_value = mock_socketio_instance
        
        dashboard = EnhancedDashboard(host="localhost", port=8080, debug=False)
        
        self.assertEqual(dashboard.host, "localhost")
        self.assertEqual(dashboard.port, 8080)
        self.assertEqual(dashboard.debug, False)
        
        # Verify Flask app was created
        mock_flask.assert_called_once()
        mock_socketio.assert_called_once()
    
    @patch('common.telemetry.dashboard.FLASK_AVAILABLE', True)
    @patch('common.telemetry.dashboard.Flask')
    @patch('common.telemetry.dashboard.SocketIO')
    def test_dashboard_routes_setup(self, mock_socketio, mock_flask):
        """Test that dashboard routes are properly set up."""
        
        # Mock Flask app
        mock_app = MagicMock()
        mock_flask.return_value = mock_app
        
        # Mock SocketIO
        mock_socketio_instance = MagicMock()
        mock_socketio.return_value = mock_socketio_instance
        
        dashboard = EnhancedDashboard()
        
        # Verify routes were registered (Flask app.route should have been called)
        self.assertTrue(mock_app.route.called)
        
        # Verify SocketIO events were registered
        self.assertTrue(mock_socketio_instance.on.called)


class TestDashboardIntegration(TestCase):
    """Test cases for dashboard integration with other telemetry components."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset global instances
        import common.telemetry.dashboard
        common.telemetry.dashboard._global_dashboard = None
    
    def tearDown(self):
        """Clean up test environment."""
        # Reset global instances
        import common.telemetry.dashboard
        common.telemetry.dashboard._global_dashboard = None
    
    @patch('common.telemetry.dashboard.FLASK_AVAILABLE', True)
    @patch('common.telemetry.dashboard.Flask')
    @patch('common.telemetry.dashboard.SocketIO')
    def test_create_dashboard_global(self, mock_socketio, mock_flask):
        """Test global dashboard creation and retrieval."""
        
        # Mock Flask components
        mock_app = MagicMock()
        mock_flask.return_value = mock_app
        mock_socketio.return_value = MagicMock()
        
        from common.telemetry.dashboard import create_dashboard, get_dashboard
        
        # Create dashboard
        dashboard = create_dashboard(host="0.0.0.0", port=9090, debug=True)
        
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.host, "0.0.0.0")
        self.assertEqual(dashboard.port, 9090)
        self.assertEqual(dashboard.debug, True)
        
        # Retrieve global dashboard
        global_dashboard = get_dashboard()
        self.assertIs(dashboard, global_dashboard)
    
    def test_get_dashboard_when_not_created(self):
        """Test getting dashboard when not created."""
        
        from common.telemetry.dashboard import get_dashboard
        
        dashboard = get_dashboard()
        self.assertIsNone(dashboard)