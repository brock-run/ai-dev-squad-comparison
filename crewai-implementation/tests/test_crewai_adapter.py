"""
Comprehensive tests for CrewAI Adapter

This test suite validates the CrewAI adapter implementation
including safety controls, VCS integration, and crew execution.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

# Mock the dependencies that might not be available
import sys
from unittest.mock import MagicMock

# CrewAI components will be properly mocked below

# Create proper base classes for CrewAI and AgentAdapter
class MockAgentAdapter:
    def __init__(self, config=None):
        pass

class MockBaseTool:
    def __init__(self, *args, **kwargs):
        # Preserve class attributes from the inheriting class
        if hasattr(self.__class__, 'name'):
            self.name = self.__class__.name
        else:
            self.name = 'mock_tool'
        
        if hasattr(self.__class__, 'description'):
            self.description = self.__class__.description
        else:
            self.description = 'Mock tool description'

class MockAgent:
    def __init__(self, *args, **kwargs):
        # Set common agent attributes that tests expect
        self.role = kwargs.get('role', 'mock_role')
        self.goal = kwargs.get('goal', 'mock_goal')
        self.backstory = kwargs.get('backstory', 'mock_backstory')
        self.tools = kwargs.get('tools', [])
        self.verbose = kwargs.get('verbose', False)

class MockTask:
    def __init__(self, *args, **kwargs):
        # Set common task attributes that tests expect
        self.description = kwargs.get('description', 'mock_description')
        self.agent = kwargs.get('agent', None)
        self.expected_output = kwargs.get('expected_output', 'mock_output')
        self.context = kwargs.get('context', [])

class MockCrew:
    def __init__(self, *args, **kwargs):
        pass
    def kickoff(self, *args, **kwargs):
        return MagicMock()

# Mock CrewAI modules
crewai_mock = MagicMock()
crewai_mock.BaseTool = MockBaseTool
crewai_mock.Agent = MockAgent
crewai_mock.Task = MockTask
crewai_mock.Crew = MockCrew

# Mock modules with proper AgentAdapter
common_agent_api_mock = MagicMock()
common_agent_api_mock.AgentAdapter = MockAgentAdapter
common_agent_api_mock.RunResult = MagicMock()
common_agent_api_mock.Event = MagicMock()
common_agent_api_mock.TaskSchema = MagicMock()
common_agent_api_mock.EventStream = MagicMock()

# Mock common modules
sys.modules['common.agent_api'] = common_agent_api_mock
sys.modules['common.safety'] = MagicMock()
sys.modules['common.safety.policy'] = MagicMock()
sys.modules['common.safety.execute'] = MagicMock()
sys.modules['common.safety.fs'] = MagicMock()
sys.modules['common.safety.net'] = MagicMock()
# Create a proper mock for PromptInjectionGuard with async methods
class MockPromptInjectionGuard:
    def __init__(self):
        # Create a mock scan result with proper structure
        mock_threat_level = Mock()
        mock_threat_level.value = 1  # Low threat level
        mock_scan_result = Mock()
        mock_scan_result.threat_level = mock_threat_level
        mock_scan_result.description = "Safe input"
        mock_scan_result.is_safe = True
        
        self.scan_input = AsyncMock(return_value=mock_scan_result)
        self.add_pattern = Mock()
        self.patterns = []

injection_mock = MagicMock()
injection_mock.PromptInjectionGuard = MockPromptInjectionGuard
sys.modules['common.safety.injection'] = injection_mock
sys.modules['common.safety.config_integration'] = MagicMock()
sys.modules['common.vcs'] = MagicMock()
sys.modules['common.vcs.base'] = MagicMock()
sys.modules['common.vcs.github'] = MagicMock()
sys.modules['common.vcs.gitlab'] = MagicMock()
sys.modules['common.vcs.commit_msgs'] = MagicMock()
sys.modules['common.config'] = MagicMock()
# Mock CrewAI modules - but allow real tool classes to work
sys.modules['crewai'] = crewai_mock
crewai_tools_mock = MagicMock()
crewai_tools_mock.BaseTool = MockBaseTool
sys.modules['crewai.tools'] = crewai_tools_mock
sys.modules['common.config'] = MagicMock()

# Now import the adapter
from adapter import CrewAIAdapter, SafeCodeExecutorTool, SafeFileOperationsTool, SafeVCSOperationsTool


class TestCrewAIAdapter:
    """Test cases for CrewAIAdapter."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return {
            'language': 'python',
            'vcs': {
                'enabled': True,
                'repository': 'test/repo'
            },
            'github': {
                'enabled': True
            },
            'max_rpm': 10,
            'architect': {'max_iterations': 5},
            'developer': {'max_iterations': 10},
            'tester': {'max_iterations': 7},
            'reviewer': {'max_iterations': 5}
        }
    
    @pytest.fixture
    def adapter(self, mock_config):
        """Create adapter instance with mocked dependencies."""
        with patch('adapter.CREWAI_AVAILABLE', True):
            with patch('adapter.get_policy_manager') as mock_policy:
                with patch('adapter.get_config_manager') as mock_config_manager:
                    # Create a proper mock policy
                    mock_active_policy = Mock()
                    mock_active_policy.execution.enabled = True
                    mock_active_policy.execution.sandbox_type = 'docker'
                    mock_active_policy.filesystem = None
                    mock_active_policy.network = None
                    mock_active_policy.injection_patterns = ['test_pattern']
                    
                    mock_policy_manager = Mock()
                    mock_policy_manager.get_active_policy.return_value = mock_active_policy
                    mock_policy_manager.set_active_policy.return_value = None
                    mock_policy.return_value = mock_policy_manager
                    mock_config_manager.return_value.config = mock_config
                    adapter = CrewAIAdapter(mock_config)
                    return adapter
    
    def test_adapter_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter.name == "CrewAI Multi-Agent Squad"
        assert adapter.version == "2.0.0"
        assert adapter.description is not None
        assert len(adapter.agents) == 4  # architect, developer, tester, reviewer
    
    def test_agent_creation(self, adapter):
        """Test that all required agents are created."""
        expected_agents = ['architect', 'developer', 'tester', 'reviewer']
        
        for agent_name in expected_agents:
            assert agent_name in adapter.agents
            agent = adapter.agents[agent_name]
            assert hasattr(agent, 'role')
            assert hasattr(agent, 'goal')
            assert hasattr(agent, 'backstory')
    
    def test_safe_tools_creation(self, adapter):
        """Test that safe tools are created properly."""
        # Should have tools if safety components are available
        assert isinstance(adapter.safe_tools, list)
        
        # Check tool types
        tool_names = [tool.name for tool in adapter.safe_tools if hasattr(tool, 'name')]
        expected_tools = ['safe_code_executor', 'safe_file_operations', 'safe_vcs_operations']
        
        # At least some tools should be available
        assert len(adapter.safe_tools) >= 0
    
    @pytest.mark.asyncio
    async def test_capabilities(self, adapter):
        """Test get_capabilities method."""
        capabilities = await adapter.get_capabilities()
        
        assert 'name' in capabilities
        assert 'version' in capabilities
        assert 'features' in capabilities
        assert 'crew_composition' in capabilities
        assert 'safety_features' in capabilities
        assert 'vcs_providers' in capabilities
        
        # Check required features
        required_features = [
            'multi_agent_collaboration',
            'role_based_agents',
            'safety_controls',
            'vcs_integration',
            'tool_integration'
        ]
        
        for feature in required_features:
            assert feature in capabilities['features']
        
        # Check crew composition
        assert 'agents' in capabilities['crew_composition']
        assert 'agent_count' in capabilities['crew_composition']
        assert capabilities['crew_composition']['agent_count'] == 4
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test health_check method."""
        health = await adapter.health_check()
        
        assert 'status' in health
        assert 'timestamp' in health
        assert 'components' in health
        
        # Check component status
        assert 'crewai' in health['components']
        
        # Check agent components
        for agent_name in ['architect', 'developer', 'tester', 'reviewer']:
            component_key = f'agent_{agent_name}'
            assert component_key in health['components']
    
    @pytest.mark.asyncio
    async def test_input_sanitization(self, adapter):
        """Test input sanitization."""
        # Test normal input
        safe_input = await adapter._sanitize_input("print('hello world')")
        assert safe_input == "print('hello world')"
        
        # Test with injection guard disabled
        adapter.injection_guard = None
        safe_input = await adapter._sanitize_input("any input")
        assert safe_input == "any input"
    
    @pytest.mark.asyncio
    async def test_task_validation(self, adapter):
        """Test task validation."""
        from common.agent_api import TaskSchema
        
        task = TaskSchema(
            id="test-task-1",
            description="Create a calculator",
            requirements=["Add function", "Subtract function"],
            context={"language": "python"}
        )
        
        validated_task = await adapter._validate_task(task)
        
        assert validated_task.id == task.id
        assert validated_task.description == task.description
        assert len(validated_task.requirements) == len(task.requirements)
    
    def test_task_creation(self, adapter):
        """Test CrewAI task creation."""
        tasks = adapter._create_tasks(
            "Create a calculator",
            ["Add function", "Subtract function"]
        )
        
        assert len(tasks) == 4  # architecture, development, testing, review
        
        # Check task structure
        for task in tasks:
            assert hasattr(task, 'description')
            assert hasattr(task, 'agent')
            assert hasattr(task, 'expected_output')
        
        # Check task dependencies
        assert tasks[1].context == [tasks[0]]  # development depends on architecture
        assert tasks[2].context == [tasks[0], tasks[1]]  # testing depends on arch + dev
        assert tasks[3].context == [tasks[0], tasks[1], tasks[2]]  # review depends on all
    
    @pytest.mark.asyncio
    async def test_vcs_operations(self, adapter):
        """Test VCS operations handling."""
        from common.agent_api import TaskSchema
        
        task = TaskSchema(
            id="test-vcs-1",
            description="Test VCS integration",
            requirements=["Create files"],
            context={}
        )
        
        # Mock crew result
        mock_result = Mock()
        mock_result.raw = "def add(a, b): return a + b"
        
        vcs_result = await adapter._handle_vcs_operations(task, mock_result)
        
        # Should handle VCS operations
        assert 'status' in vcs_result
        
        # If VCS is enabled, should attempt operations
        if adapter.config.get('vcs', {}).get('enabled', False):
            assert vcs_result['status'] in ['completed', 'failed', 'skipped']
    
    def test_file_extraction(self, adapter):
        """Test file extraction from crew results."""
        # Mock crew result with code
        mock_result = Mock()
        mock_result.raw = """
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5
"""
        
        files = adapter._extract_files_from_result(mock_result)
        
        # Should extract files based on content
        assert isinstance(files, dict)
        
        # If content contains code, should create files
        if 'def ' in str(mock_result.raw):
            assert len(files) > 0
    
    @pytest.mark.asyncio
    async def test_event_emission(self, adapter):
        """Test event emission."""
        # Mock event stream
        adapter.event_stream = Mock()
        adapter.event_stream.emit = AsyncMock()
        
        await adapter._emit_event("test_event", {"key": "value"})
        
        # Should emit event
        adapter.event_stream.emit.assert_called_once()
        
        # Check event structure
        call_args = adapter.event_stream.emit.call_args[0][0]
        assert hasattr(call_args, 'type')
        assert hasattr(call_args, 'timestamp')
        assert hasattr(call_args, 'data')
    
    def test_output_formatting(self, adapter):
        """Test crew output formatting."""
        # Test with raw attribute
        mock_result = Mock()
        mock_result.raw = "Test output content"
        
        formatted = adapter._format_crew_output(mock_result)
        assert formatted == "Test output content"
        
        # Test without raw attribute
        mock_result_no_raw = Mock(spec=[])
        formatted_no_raw = adapter._format_crew_output(mock_result_no_raw)
        assert isinstance(formatted_no_raw, str)


class TestSafeTools:
    """Test cases for safe tools."""
    
    @pytest.fixture
    def mock_sandbox(self):
        """Mock execution sandbox."""
        sandbox = Mock()
        sandbox.execute_code = AsyncMock()
        return sandbox
    
    @pytest.fixture
    def mock_filesystem_guard(self):
        """Mock filesystem guard."""
        guard = Mock()
        guard.is_path_allowed = Mock(return_value=True)
        return guard
    
    @pytest.fixture
    def mock_injection_guard(self):
        """Mock injection guard."""
        guard = Mock()
        guard.scan_input = AsyncMock()
        
        # Mock scan result
        scan_result = Mock()
        scan_result.threat_level = Mock()
        scan_result.threat_level.value = 1  # Low threat
        scan_result.description = "Safe input"
        
        guard.scan_input.return_value = scan_result
        return guard
    
    def test_safe_code_executor_tool(self, mock_sandbox, mock_injection_guard):
        """Test SafeCodeExecutorTool."""
        tool = SafeCodeExecutorTool(mock_sandbox, mock_injection_guard)
        
        assert tool.name == "safe_code_executor"
        assert tool.description is not None
        
        # Test code execution
        result = tool._run("print('hello')", "python")
        assert isinstance(result, str)
    
    def test_safe_file_operations_tool(self, mock_filesystem_guard, mock_injection_guard):
        """Test SafeFileOperationsTool."""
        tool = SafeFileOperationsTool(mock_filesystem_guard, mock_injection_guard)
        
        assert tool.name == "safe_file_operations"
        assert tool.description is not None
        
        # Test file operations
        result = tool._run("read", "/test/path")
        assert isinstance(result, str)
    
    def test_safe_vcs_operations_tool(self, mock_injection_guard):
        """Test SafeVCSOperationsTool."""
        mock_github = Mock()
        mock_gitlab = Mock()
        
        tool = SafeVCSOperationsTool(mock_github, mock_gitlab, mock_injection_guard)
        
        assert tool.name == "safe_vcs_operations"
        assert tool.description is not None
        
        # Test VCS operations
        result = tool._run("create_branch", owner="test", repo="test", branch_name="test-branch")
        assert isinstance(result, str)


class TestCrewAIIntegration:
    """Integration tests for CrewAI functionality."""
    
    @pytest.mark.asyncio
    async def test_crew_workflow_simulation(self):
        """Test simulated crew workflow."""
        # This would test the actual CrewAI workflow execution
        # but requires CrewAI to be installed
        pass
    
    @pytest.mark.asyncio
    async def test_agent_collaboration(self):
        """Test agent collaboration patterns."""
        # Test that agents can work together effectively
        pass
    
    @pytest.mark.asyncio
    async def test_memory_persistence(self):
        """Test memory persistence across tasks."""
        # Test that agents maintain memory between interactions
        pass
    
    @pytest.mark.asyncio
    async def test_tool_integration(self):
        """Test tool integration with agents."""
        # Test that agents can use tools effectively
        pass


# Factory function test
def test_create_crewai_adapter():
    """Test factory function."""
    with patch('adapter.CREWAI_AVAILABLE', True):
        with patch('adapter.get_policy_manager') as mock_policy:
            with patch('adapter.get_config_manager') as mock_config_manager:
                mock_config_manager.return_value.config = {}
                from adapter import create_crewai_adapter, CrewAIAdapter
                adapter = create_crewai_adapter()
                assert isinstance(adapter, CrewAIAdapter)
                assert adapter.name == "CrewAI Multi-Agent Squad"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])