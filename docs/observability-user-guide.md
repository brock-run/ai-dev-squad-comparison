# AI Dev Squad Observability - User Guide

This guide helps you get started with the AI Dev Squad observability features quickly and effectively.

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
# Core observability (always required)
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

# Dashboard (optional, for web interface)
pip install flask flask-socketio

# Token counting (optional, for accurate OpenAI token counts)
pip install tiktoken
```

### 2. Basic Setup
Create a simple script to test observability:

```python
# quick_start.py
from common.telemetry import (
    configure_logging,
    configure_tracing,
    configure_cost_tracking
)

# Configure all systems
logger = configure_logging(log_dir="logs", enable_console=True)
tracer = configure_tracing(service_name="my-app", console_export=True)
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
```

### 3. Run the Test
```bash
python quick_start.py
```

You should see:
- ✅ Confirmation messages
- 🔍 Trace output in console
- 💰 Cost tracking results
- 📁 Log files created in `logs/` directory

## 📊 Start the Dashboard (Optional)

### 1. Run the Dashboard Demo
```bash
python examples/dashboard_demo.py
```

### 2. Open Your Browser
Navigate to: http://localhost:8080

You'll see:
- 📈 Real-time metrics
- 📊 Framework comparison matrix
- 💰 Cost analysis
- 🔍 Trace visualization

## 🚨 Troubleshooting

### Issue: No logs appearing
**Solution:**
```python
from common.telemetry import configure_logging
# Enable console output to see logs immediately
logger = configure_logging(enable_console=True, log_dir="logs")
```

### Issue: Dashboard won't start
**Solution:**
```bash
# Install required dependencies
pip install flask flask-socketio

# Check if port is available
lsof -i :8080

# Try a different port
python -c "
from common.telemetry import create_dashboard
dashboard = create_dashboard(port=8081)
dashboard.run()
"
```

## 📚 Next Steps

Once you have observability working:

1. **Explore the Dashboard**: Visit all the different views
2. **Set Up Alerts**: Configure budget and performance alerts
3. **Optimize Costs**: Use the recommendations to reduce spending
4. **Monitor Performance**: Watch for slow operations and errors
5. **Share Insights**: Use the dashboard to share metrics with your team

## 🔗 Related Documentation

- [Full Observability Guide](observability.md) - Complete technical reference
- [Developer Guide](observability-developer-guide.md) - Advanced integration patterns
- [Configuration Guide](configuration.md) - System configuration
- [Safety Documentation](safety.md) - Security considerations