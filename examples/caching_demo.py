#!/usr/bin/env python3
"""
Demo script for Intelligent Caching System

This script demonstrates the caching capabilities integrated with the enhanced
Ollama system, showing performance improvements and cache management features.
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.ollama_integration import create_agent, TaskType
from common.caching import get_cache, configure_cache, CacheStrategy

def demo_basic_caching():
    """Demonstrate basic caching functionality."""
    print("🗄️ Basic Caching Demo")
    print("=" * 50)
    
    try:
        # Create agent with caching enabled
        agent = create_agent("developer", enable_caching=True)
        
        if not agent.enable_caching:
            print("❌ Caching not available - install required dependencies")
            return
        
        print("✅ Created developer agent with caching enabled")
        
        # Test prompt
        prompt = "Write a simple Python function to calculate the factorial of a number"
        
        # First request (cache miss)
        print(f"\n📝 First request: {prompt}")
        start_time = time.time()
        response1 = agent.generate(prompt, task_type=TaskType.CODING)
        first_time = time.time() - start_time
        print(f"⏱️ First response time: {first_time:.2f}s")
        print(f"📄 Response length: {len(response1)} characters")
        
        # Second request (should be cache hit)
        print(f"\n📝 Second request (same prompt)")
        start_time = time.time()
        response2 = agent.generate(prompt, task_type=TaskType.CODING)
        second_time = time.time() - start_time
        print(f"⏱️ Second response time: {second_time:.2f}s")
        print(f"📄 Response length: {len(response2)} characters")
        
        # Compare responses and times
        if response1 == response2:
            print("✅ Responses are identical (cache hit)")
        else:
            print("⚠️ Responses differ (possible cache miss)")
        
        speedup = first_time / second_time if second_time > 0 else float('inf')
        print(f"🚀 Speedup: {speedup:.1f}x faster")
        
        # Show cache stats
        status = agent.get_model_status()
        if "cache_stats" in status:
            cache_stats = status["cache_stats"]
            print(f"\n📊 Cache Statistics:")
            print(f"   Hit rate: {cache_stats['hit_rate']:.1%}")
            print(f"   Total requests: {cache_stats['total_requests']}")
            print(f"   Cache size: {cache_stats['cache_size']} entries")
            print(f"   Cache size: {cache_stats['total_size_mb']:.2f} MB")
        
    except Exception as e:
        print(f"❌ Error in basic caching demo: {e}")

def demo_cache_strategies():
    """Demonstrate different caching strategies."""
    print("\n🎯 Cache Strategies Demo")
    print("=" * 50)
    
    strategies = [
        (CacheStrategy.PERFORMANCE_BASED, "Performance-based caching"),
        (CacheStrategy.LRU, "Least Recently Used"),
        (CacheStrategy.TTL, "Time To Live"),
    ]
    
    for strategy, description in strategies:
        print(f"\n🔧 Testing {description}")
        
        try:
            # Configure cache with specific strategy
            cache = configure_cache(
                cache_dir=f"cache_{strategy.value}",
                max_size_mb=50,
                strategy=strategy
            )
            
            agent = create_agent("tester", enable_caching=True)
            
            # Test with different prompts
            prompts = [
                "Create unit tests for a calculator function",
                "Write integration tests for a REST API",
                "Design test cases for user authentication"
            ]
            
            for i, prompt in enumerate(prompts):
                response = agent.generate(prompt, task_type=TaskType.TESTING)
                print(f"   ✅ Processed prompt {i+1}: {len(response)} chars")
            
            # Show strategy-specific stats
            stats = cache.get_stats()
            print(f"   📊 Strategy stats: {stats.hit_rate:.1%} hit rate, {stats.cache_size} entries")
            
        except Exception as e:
            print(f"   ❌ Error with {description}: {e}")

def demo_cache_invalidation():
    """Demonstrate cache invalidation scenarios."""
    print("\n🗑️ Cache Invalidation Demo")
    print("=" * 50)
    
    try:
        agent = create_agent("architect", enable_caching=True)
        
        if not agent.enable_caching:
            print("❌ Caching not available")
            return
        
        # Generate some cached responses
        prompts = [
            "Design a microservices architecture",
            "Create a database schema for e-commerce",
            "Plan a scalable web application structure"
        ]
        
        print("📝 Generating responses to cache...")
        for prompt in prompts:
            agent.generate(prompt, task_type=TaskType.ARCHITECTURE)
        
        # Show initial cache state
        status = agent.get_model_status()
        initial_size = status.get("cache_stats", {}).get("cache_size", 0)
        print(f"📊 Initial cache size: {initial_size} entries")
        
        # Test model-specific invalidation
        current_model = agent.model
        invalidated = agent.invalidate_model_cache(current_model)
        print(f"🗑️ Invalidated {invalidated} entries for model {current_model}")
        
        # Show cache state after invalidation
        status = agent.get_model_status()
        final_size = status.get("cache_stats", {}).get("cache_size", 0)
        print(f"📊 Final cache size: {final_size} entries")
        
        # Test cache clearing
        agent.clear_cache()
        print("🧹 Cleared entire cache")
        
        status = agent.get_model_status()
        cleared_size = status.get("cache_stats", {}).get("cache_size", 0)
        print(f"📊 Cache size after clearing: {cleared_size} entries")
        
    except Exception as e:
        print(f"❌ Error in cache invalidation demo: {e}")

def demo_cache_optimization():
    """Demonstrate cache optimization features."""
    print("\n⚡ Cache Optimization Demo")
    print("=" * 50)
    
    try:
        agent = create_agent("general", enable_caching=True)
        
        if not agent.enable_caching:
            print("❌ Caching not available")
            return
        
        # Generate various types of requests
        test_cases = [
            ("What is Python?", TaskType.GENERAL),
            ("Explain object-oriented programming", TaskType.DOCUMENTATION),
            ("Write a sorting algorithm", TaskType.CODING),
            ("Debug this error: NameError", TaskType.DEBUGGING),
            ("Plan a software project", TaskType.PLANNING)
        ]
        
        print("📝 Generating diverse requests...")
        for prompt, task_type in test_cases:
            try:
                agent.generate(prompt, task_type=task_type)
                print(f"   ✅ {task_type.value}: {prompt[:30]}...")
            except Exception as e:
                print(f"   ❌ Failed {task_type.value}: {e}")
        
        # Get optimization recommendations
        recommendations = agent.get_cache_recommendations()
        print(f"\n💡 Cache Recommendations:")
        for rec in recommendations:
            print(f"   • {rec}")
        
        # Run optimization
        optimization_results = agent.optimize_cache()
        print(f"\n🔧 Optimization Results:")
        print(f"   Expired entries removed: {optimization_results.get('expired_removed', 0)}")
        
        if optimization_results.get('recommendations'):
            print("   Additional recommendations:")
            for rec in optimization_results['recommendations']:
                print(f"   • {rec}")
        
        # Show final cache performance
        status = agent.get_model_status()
        if "cache_stats" in status:
            cache_stats = status["cache_stats"]
            print(f"\n📈 Final Cache Performance:")
            print(f"   Hit rate: {cache_stats['hit_rate']:.1%}")
            print(f"   Performance improvement: {cache_stats['performance_improvement']:.1%}")
            print(f"   Cache efficiency: {'Excellent' if cache_stats['hit_rate'] > 0.7 else 'Good' if cache_stats['hit_rate'] > 0.4 else 'Needs improvement'}")
        
    except Exception as e:
        print(f"❌ Error in cache optimization demo: {e}")

def demo_chat_caching():
    """Demonstrate caching for chat conversations."""
    print("\n💬 Chat Caching Demo")
    print("=" * 50)
    
    try:
        agent = create_agent("general", enable_caching=True)
        
        if not agent.enable_caching:
            print("❌ Caching not available")
            return
        
        # Test conversation caching
        conversation = [
            {"role": "system", "content": "You are a helpful programming assistant."},
            {"role": "user", "content": "What is the difference between a list and a tuple in Python?"}
        ]
        
        print("💬 First chat request...")
        start_time = time.time()
        response1 = agent.chat(conversation, task_type=TaskType.GENERAL)
        first_time = time.time() - start_time
        print(f"⏱️ First response time: {first_time:.2f}s")
        
        print("💬 Second chat request (same conversation)...")
        start_time = time.time()
        response2 = agent.chat(conversation, task_type=TaskType.GENERAL)
        second_time = time.time() - start_time
        print(f"⏱️ Second response time: {second_time:.2f}s")
        
        if response1 == response2:
            print("✅ Chat responses cached successfully")
            speedup = first_time / second_time if second_time > 0 else float('inf')
            print(f"🚀 Chat speedup: {speedup:.1f}x faster")
        else:
            print("⚠️ Chat responses differ (caching may be disabled for this conversation)")
        
        # Test longer conversation (should not be cached)
        long_conversation = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me about Python"},
            {"role": "assistant", "content": "Python is a programming language..."},
            {"role": "user", "content": "What about its history?"},
            {"role": "assistant", "content": "Python was created by Guido van Rossum..."},
            {"role": "user", "content": "How is it used in data science?"},
            {"role": "assistant", "content": "Python is widely used in data science..."},
            {"role": "user", "content": "What are some popular libraries?"}
        ]
        
        print("\n💬 Testing long conversation (should not cache)...")
        response3 = agent.chat(long_conversation, task_type=TaskType.GENERAL)
        print(f"📄 Long conversation response: {len(response3)} characters")
        
    except Exception as e:
        print(f"❌ Error in chat caching demo: {e}")

def main():
    """Run all caching demos."""
    print("🚀 Intelligent Caching System Demo")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_basic_caching()
        demo_cache_strategies()
        demo_cache_invalidation()
        demo_cache_optimization()
        demo_chat_caching()
        
        print("\n🎉 Caching Demo Completed!")
        print("\nKey features demonstrated:")
        print("- Automatic response caching with intelligent TTL")
        print("- Multiple caching strategies (Performance, LRU, TTL)")
        print("- Cache invalidation and management")
        print("- Performance optimization and recommendations")
        print("- Chat conversation caching with context awareness")
        print("- Real-time cache statistics and monitoring")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Ollama is running (ollama serve)")
        print("2. Ensure you have models installed (ollama pull llama3.1:8b)")
        print("3. Check that SQLite is available for cache storage")

if __name__ == "__main__":
    main()