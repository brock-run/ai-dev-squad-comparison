#!/usr/bin/env python3
"""
Demo script for Enhanced Ollama Integration

This script demonstrates the new intelligent model routing, performance profiling,
and fallback capabilities of the enhanced Ollama integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.ollama_integration import (
    create_agent, 
    get_model_recommendations, 
    health_check_models,
    TaskType,
    EnhancedOllamaManager
)

def demo_intelligent_routing():
    """Demonstrate intelligent model routing."""
    print("🧠 Intelligent Model Routing Demo")
    print("=" * 50)
    
    # Different types of tasks
    tasks = [
        ("Write a Python function to sort a list", TaskType.CODING),
        ("Design a microservices architecture", TaskType.ARCHITECTURE),
        ("Create unit tests for a calculator", TaskType.TESTING),
        ("Debug this error: IndexError", TaskType.DEBUGGING),
        ("Explain how REST APIs work", TaskType.DOCUMENTATION),
    ]
    
    for task_description, task_type in tasks:
        print(f"\nTask: {task_description}")
        print(f"Type: {task_type.value}")
        
        try:
            recommendations = get_model_recommendations(task_description, task_type)
            print(f"Recommended model: {recommendations['primary_recommendation']}")
            print(f"Reasoning: {recommendations['reasoning']}")
            print(f"Fallbacks: {', '.join(recommendations['fallback_options'][:2])}")
        except Exception as e:
            print(f"Error getting recommendations: {e}")

def demo_agent_with_fallback():
    """Demonstrate agent with automatic fallback."""
    print("\n🔄 Agent Fallback Demo")
    print("=" * 50)
    
    try:
        # Create a developer agent
        agent = create_agent("developer")
        print(f"Created developer agent")
        
        # Test with a coding task
        prompt = "Create a simple REST API endpoint in Python using Flask"
        print(f"\nPrompt: {prompt}")
        
        response = agent.generate(prompt, task_type=TaskType.CODING)
        print(f"\nResponse length: {len(response)} characters")
        print(f"Response preview: {response[:200]}...")
        
        # Show model status
        status = agent.get_model_status()
        print(f"\nUsed model from available: {status['current_model']}")
        
    except Exception as e:
        print(f"Error in agent demo: {e}")

def demo_performance_tracking():
    """Demonstrate performance tracking."""
    print("\n📊 Performance Tracking Demo")
    print("=" * 50)
    
    try:
        manager = EnhancedOllamaManager()
        
        # Get performance summary
        summary = manager.get_performance_summary()
        
        if summary.get('total_requests', 0) > 0:
            print(f"Total requests tracked: {summary['total_requests']}")
            print(f"Average response time: {summary['avg_response_time']:.2f}s")
            print(f"Average success rate: {summary['avg_success_rate']:.1%}")
            print(f"Average quality score: {summary['avg_quality_score']:.1f}/10")
            print(f"Models tracked: {summary['model_count']}")
            print(f"Task types: {', '.join(summary['task_types'])}")
        else:
            print("No performance data available yet. Run some tasks first!")
            
    except Exception as e:
        print(f"Error getting performance data: {e}")

def demo_health_monitoring():
    """Demonstrate health monitoring."""
    print("\n🏥 Health Monitoring Demo")
    print("=" * 50)
    
    try:
        print("Checking health of all models...")
        health_status = health_check_models()
        
        if health_status:
            for model, status in health_status.items():
                status_emoji = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
                print(f"{status_emoji} {model}: {status}")
        else:
            print("No models found or health check failed")
            
    except Exception as e:
        print(f"Error during health check: {e}")

def demo_task_analysis():
    """Demonstrate task characteristic analysis."""
    print("\n🔍 Task Analysis Demo")
    print("=" * 50)
    
    test_prompts = [
        "Fix this bug in my code",
        "Write a comprehensive system design document for a chat application",
        "Quick function to add two numbers",
        "Create detailed unit tests with edge cases and mocking",
    ]
    
    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        
        try:
            recommendations = get_model_recommendations(prompt)
            characteristics = recommendations['task_characteristics']
            
            print(f"  Detected type: {characteristics['task_type']}")
            print(f"  Complexity: {characteristics['complexity']}")
            print(f"  Context size: {characteristics['context_size']}")
            print(f"  Requires accuracy: {characteristics['requires_accuracy']}")
            print(f"  Requires speed: {characteristics['requires_speed']}")
            print(f"  Requires creativity: {characteristics['requires_creativity']}")
            
        except Exception as e:
            print(f"  Error analyzing task: {e}")

def main():
    """Run all demos."""
    print("🚀 Enhanced Ollama Integration Demo")
    print("=" * 60)
    
    try:
        # Check if Ollama is available
        manager = EnhancedOllamaManager()
        if not manager.client.is_healthy():
            print("❌ Ollama is not available. Please start Ollama and try again.")
            return
        
        print("✅ Ollama is available")
        
        # Run demos
        demo_intelligent_routing()
        demo_health_monitoring()
        demo_task_analysis()
        demo_performance_tracking()
        demo_agent_with_fallback()
        
        print("\n🎉 Demo completed!")
        print("\nKey features demonstrated:")
        print("- Intelligent model routing based on task characteristics")
        print("- Automatic fallback to alternative models")
        print("- Performance profiling and tracking")
        print("- Health monitoring and status checking")
        print("- Task analysis and model recommendations")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Ollama is running (ollama serve)")
        print("2. Ensure you have models installed (ollama pull llama3.1:8b)")
        print("3. Check network connectivity to Ollama")

if __name__ == "__main__":
    main()