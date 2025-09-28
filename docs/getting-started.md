# Getting Started with AI Dev Squad

This guide will help you get up and running with the AI Dev Squad platform quickly, including setting up observability to monitor your AI agents.

## 🚀 Quick Setup (10 Minutes)

### 1. Prerequisites

- **Python 3.8+** for Python-based implementations
- **Node.js 14+** for n8n and JavaScript implementations  
- **[Ollama](https://ollama.ai/)** for local model execution
- **Git** for version control

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-dev-squad-comparison.git
cd ai-dev-squad-comparison

# Set up Ollama (if using local models)
# Install Ollama following instructions at https://ollama.ai/
ollama pull llama3.1:8b
ollama pull codellama:13b
```

### 3. Choose Your Framework

Pick one of the supported frameworks to start with:

#### Option A: LangGraph (Recommended for Beginners)
```bash
cd langgraph-implementation
pip install -r requirements.txt
python simple_test.py
```

#### Option B: CrewAI (Great for Role-Based Agents)
```bash
cd crewai-implementation  
pip install -r requirements.txt
python simple_integration_test.py
```

#### Option C: AutoGen (Multi-Agent Conversations)
```bash
cd autogen-implementation
pip install -r requirements.txt
python simple_integration_test.py
```

### 4. Set Up Observability (Optional but Recommended)

Enable monitoring and cost tracking for your AI agents:

```bash
# Install observability dependencies
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
pip install flask flask-socketio  # For dashboard
pip install tiktoken  # For accurate token counting
```

Create a test script to verify observability:

```python
# test_observability.py
from common.telemetry import (
    configure_logging,
    configure_tracing, 
    configure_cost_tracking,
    create_dashboard
)

# Configure all observability components
logger = configure_logging(log_dir="logs", enable_console=True)
tracer = configure_tracing(service_name="ai-dev-squad-test")
cost_tracker = configure_cost_tracking()

print("✅ Observability configured!")

# Test logging
logger.log_agent_start("test_agent", "developer", "test_framework")

# Test tracing  
with tracer.trace_operation("test_operation"):
    print("🔍 This operation is being traced!")

# Test cost tracking
cost_entry = cost_tracker.track_llm_usage(
    model_name="gpt-3.5-turbo",
    provider="openai", 
    input_tokens=100,
    output_tokens=50,
    duration_ms=1500
)
print(f"💰 Tracked cost: ${cost_entry.cost_usd:.6f}")

# Start dashboard (optional)
print("🚀 Starting dashboard at http://localhost:8080")
dashboard = create_dashboard()
# dashboard.run()  # Uncomment to start dashboard
```

Run the test:
```bash
python test_observability.py
```

## 🎯 Your First AI Agent

Let's create a simple AI agent with observability:

```python
# my_first_agent.py
from common.telemetry import get_logger, get_trace_manager, get_cost_tracker

# Get observability instances
logger = get_logger()
tracer = get_trace_manager() 
cost_tracker = get_cost_tracker()

class MyFirstAgent:
    def __init__(self, agent_id="my_first_agent"):
        self.agent_id = agent_id
        
    def process_task(self, task_description):
        # Start tracing the operation
        with tracer.trace_agent_operation(self.agent_id, "custom", "task_processing"):
            # Log the start of the task
            logger.log_task_start("process_task", task_description, self.agent_id, "custom")
            
            try:
                # Your agent logic here
                result = f"Processed: {task_description}"
                
                # Simulate LLM usage tracking
                cost_tracker.track_llm_usage(
                    model_name="gpt-3.5-turbo",
                    provider="openai",
                    input_tokens=len(task_description.split()) * 1.3,  # Rough estimate
                    output_tokens=len(result.split()) * 1.3,
                    duration_ms=1500,
                    agent_id=self.agent_id,
                    framework="custom"
                )
                
                # Log successful completion
                logger.log_task_complete("process_task", task_description, self.agent_id, "custom", 1500)
                
                return result
                
            except Exception as e:
                # Log errors
                logger.log_task_error("process_task", task_description, self.agent_id, "custom", str(e))
                raise

# Use the agent
if __name__ == "__main__":
    agent = MyFirstAgent()
    result = agent.process_task("Create a simple web application")
    print(f"Result: {result}")
```

## 📊 Monitor Your Agents

### 1. View Logs
```bash
# View structured logs
tail -f logs/ai_dev_squad.jsonl | jq '.'

# Filter for your agent
grep '"agent_id":"my_first_agent"' logs/ai_dev_squad.jsonl | jq '.'
```

### 2. Start the Dashboard
```python
# dashboard_start.py
from common.telemetry import create_dashboard

dashboard = create_dashboard(host="localhost", port=8080)
print("🚀 Dashboard starting at http://localhost:8080")
dashboard.run()
```

Visit http://localhost:8080 to see:
- Real-time metrics
- Cost analysis
- Framework comparisons
- Trace visualization

### 3. Set Up Cost Alerts
```python
# cost_alerts.py
from common.telemetry import get_cost_tracker

cost_tracker = get_cost_tracker()

# Set a daily budget
cost_tracker.budget_manager.set_budget(
    name="daily_development",
    limit_usd=5.00,  # $5 per day
    period="daily",
    alert_thresholds=[0.5, 0.8, 0.9]  # Alert at 50%, 80%, 90%
)

# Add alert handler
def budget_alert(alert_data):
    print(f"🚨 Budget Alert: {alert_data['budget_name']} at {alert_data['spend_ratio']:.1%}")

cost_tracker.budget_manager.add_alert_callback(budget_alert)
```

## 🔧 Framework-Specific Examples

### LangGraph with Observability
```python
from langgraph import StateGraph
from common.telemetry import get_logger, get_trace_manager

logger = get_logger()
tracer = get_trace_manager()

def my_agent_node(state):
    with tracer.trace_agent_operation("langgraph_agent", "langgraph", "node_execution"):
        logger.log_task_start("node_task", "processing", "langgraph_agent", "langgraph")
        
        # Your LangGraph node logic
        result = {"output": f"Processed: {state.get('input', '')}"}
        
        logger.log_task_complete("node_task", "processing", "langgraph_agent", "langgraph", 1000)
        return result

# Build graph
graph = StateGraph(dict)
graph.add_node("agent", my_agent_node)
graph.set_entry_point("agent")
graph.set_finish_point("agent")

# Compile and run
app = graph.compile()
result = app.invoke({"input": "Hello, LangGraph!"})
```

### CrewAI with Observability
```python
from crewai import Agent, Task, Crew
from common.telemetry import get_logger, get_trace_manager

logger = get_logger()
tracer = get_trace_manager()

# Create agent with observability wrapper
class ObservableAgent(Agent):
    def execute_task(self, task):
        agent_id = f"crewai_{self.role.lower().replace(' ', '_')}"
        
        with tracer.trace_agent_operation(agent_id, "crewai", "task_execution"):
            logger.log_agent_start(agent_id, self.role, "crewai")
            
            result = super().execute_task(task)
            
            logger.log_agent_stop(agent_id, "crewai")
            return result

# Create agents
developer = ObservableAgent(
    role='Developer',
    goal='Write high-quality code',
    backstory='You are an experienced developer...'
)

# Create and run crew
crew = Crew(agents=[developer], tasks=[...])
result = crew.kickoff()
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Make sure you're in the right directory
cd ai-dev-squad-comparison

# Install missing dependencies
pip install -r requirements.txt
```

#### 2. Ollama Not Found
```bash
# Check if Ollama is installed
ollama --version

# If not installed, visit https://ollama.ai/
# Then pull required models
ollama pull llama3.1:8b
```

#### 3. Dashboard Won't Start
```bash
# Install dashboard dependencies
pip install flask flask-socketio

# Check if port is available
lsof -i :8080

# Try different port
python -c "
from common.telemetry import create_dashboard
dashboard = create_dashboard(port=8081)
dashboard.run()
"
```

#### 4. No Logs Appearing
```python
# Enable console logging
from common.telemetry import configure_logging
logger = configure_logging(enable_console=True)
```

## 📚 Next Steps

Now that you have the basics working:

1. **Explore Frameworks**: Try different implementations in each framework directory
2. **Run Benchmarks**: Use `python benchmark/benchmark_suite.py` to compare frameworks
3. **Customize Agents**: Modify the agent implementations for your use case
4. **Monitor Costs**: Set up budget alerts and optimization recommendations
5. **Scale Up**: Deploy to production with the deployment guides

## 🔗 Additional Resources

- [Observability User Guide](observability-user-guide.md) - Detailed observability setup
- [Observability Developer Guide](observability-developer-guide.md) - Advanced integration
- [Framework Documentation](../README.md#framework-implementations) - Specific framework guides
- [Configuration Guide](configuration.md) - System configuration options
- [Safety Documentation](safety.md) - Security best practices

## 💬 Getting Help

If you run into issues:

1. Check the troubleshooting section above
2. Look at the example files in each framework directory
3. Run the simple integration tests to verify setup
4. Check the logs for error messages
5. Review the framework-specific README files

Welcome to AI Dev Squad! 🎉