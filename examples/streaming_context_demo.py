#!/usr/bin/env python3
"""
Demo script for Streaming and Context Management

This script demonstrates the streaming response capabilities and intelligent
context management features of the enhanced Ollama system.
"""

import sys
import os
import time
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.ollama_integration import create_agent, TaskType
from common.context_management import ContextStrategy, MessageImportance

def demo_basic_streaming():
    """Demonstrate basic streaming functionality."""
    print("🌊 Basic Streaming Demo")
    print("=" * 50)
    
    try:
        # Create agent with streaming support
        agent = create_agent("developer", enable_context_management=True)
        
        print("✅ Created developer agent with streaming support")
        
        # Test streaming generation
        prompt = "Write a detailed explanation of how Python generators work, including examples"
        
        print(f"\n📝 Streaming prompt: {prompt}")
        print("🌊 Streaming response:")
        print("-" * 40)
        
        start_time = time.time()
        complete_response = ""
        chunk_count = 0
        
        # Stream the response
        for chunk in agent.generate_streaming(prompt, task_type=TaskType.DOCUMENTATION):
            print(chunk, end='', flush=True)
            complete_response += chunk
            chunk_count += 1
        
        end_time = time.time()
        
        print("\n" + "-" * 40)
        print(f"✅ Streaming completed!")
        print(f"⏱️ Total time: {end_time - start_time:.2f}s")
        print(f"📦 Total chunks: {chunk_count}")
        print(f"📄 Response length: {len(complete_response)} characters")
        print(f"🚀 Chunks per second: {chunk_count / (end_time - start_time):.1f}")
        
    except Exception as e:
        print(f"❌ Error in streaming demo: {e}")

def demo_streaming_with_callback():
    """Demonstrate streaming with callback function."""
    print("\n📞 Streaming with Callback Demo")
    print("=" * 50)
    
    try:
        agent = create_agent("architect")
        
        # Callback to process chunks
        chunk_lengths = []
        def chunk_callback(chunk: str):
            chunk_lengths.append(len(chunk))
            if len(chunk) > 10:  # Only print substantial chunks
                print(f"[CHUNK: {len(chunk)} chars]", end='')
        
        prompt = "Design a microservices architecture for a real-time chat application"
        
        print(f"📝 Prompt: {prompt}")
        print("🌊 Streaming with callback processing:")
        print("-" * 40)
        
        complete_response = ""
        for chunk in agent.generate_streaming(
            prompt, 
            task_type=TaskType.ARCHITECTURE,
            callback=chunk_callback
        ):
            complete_response += chunk
        
        print("\n" + "-" * 40)
        print(f"✅ Streaming with callback completed!")
        print(f"📊 Chunk statistics:")
        print(f"   Total chunks: {len(chunk_lengths)}")
        print(f"   Average chunk size: {sum(chunk_lengths) / len(chunk_lengths):.1f} chars")
        print(f"   Largest chunk: {max(chunk_lengths)} chars")
        print(f"   Smallest chunk: {min(chunk_lengths)} chars")
        
    except Exception as e:
        print(f"❌ Error in callback streaming demo: {e}")

def demo_context_management():
    """Demonstrate context management features."""
    print("\n🧠 Context Management Demo")
    print("=" * 50)
    
    try:
        # Create agent with context management
        agent = create_agent(
            "general", 
            enable_context_management=True,
            max_context_tokens=2048
        )
        
        if not agent.enable_context_management:
            print("❌ Context management not available")
            return
        
        print("✅ Created agent with context management")
        
        # Start a conversation
        conversation_id = agent.start_conversation(
            context_strategy=ContextStrategy.SLIDING_WINDOW
        )
        print(f"🆔 Started conversation: {conversation_id}")
        
        # Have a multi-turn conversation
        conversation_turns = [
            ("What is Python?", MessageImportance.HIGH),
            ("Can you give me an example of a Python function?", MessageImportance.HIGH),
            ("How do I handle errors in Python?", MessageImportance.MEDIUM),
            ("What about async programming?", MessageImportance.MEDIUM),
            ("Can you summarize what we've discussed?", MessageImportance.HIGH)
        ]
        
        for i, (message, importance) in enumerate(conversation_turns, 1):
            print(f"\n💬 Turn {i}: {message}")
            
            response = agent.chat_with_context(
                conversation_id=conversation_id,
                message=message,
                task_type=TaskType.GENERAL,
                importance=importance
            )
            
            print(f"🤖 Response: {response[:100]}...")
            
            # Show context stats after each turn
            summary = agent.get_conversation_summary(conversation_id)
            print(f"📊 Context: {summary['message_count']} messages, "
                  f"{summary['current_tokens']} tokens "
                  f"({summary['utilization']:.1%} utilization)")
        
        # Optimize context
        print(f"\n🔧 Optimizing context...")
        optimization = agent.optimize_conversation_context(conversation_id)
        print(f"📈 Optimization results:")
        print(f"   Tokens saved: {optimization.get('tokens_saved', 0)}")
        print(f"   Messages removed: {optimization.get('messages_removed', 0)}")
        print(f"   Strategy used: {optimization.get('strategy_used', 'unknown')}")
        
        # End conversation
        agent.end_conversation(conversation_id)
        print(f"✅ Ended conversation {conversation_id}")
        
    except Exception as e:
        print(f"❌ Error in context management demo: {e}")

def demo_streaming_with_context():
    """Demonstrate streaming combined with context management."""
    print("\n🌊🧠 Streaming + Context Management Demo")
    print("=" * 50)
    
    try:
        agent = create_agent(
            "developer",
            enable_context_management=True,
            max_context_tokens=3000
        )
        
        if not agent.enable_context_management:
            print("❌ Context management not available")
            return
        
        # Start conversation
        conversation_id = agent.start_conversation(
            context_strategy=ContextStrategy.IMPORTANCE_BASED
        )
        print(f"🆔 Started streaming conversation: {conversation_id}")
        
        # Streaming conversation turns
        streaming_turns = [
            "Explain how to implement a REST API in Python",
            "Now show me how to add authentication to that API",
            "What about rate limiting and error handling?"
        ]
        
        for i, message in enumerate(streaming_turns, 1):
            print(f"\n💬 Streaming Turn {i}: {message}")
            print("🌊 Streaming response:")
            print("-" * 40)
            
            complete_response = ""
            chunk_count = 0
            
            for chunk in agent.chat_streaming_with_context(
                conversation_id=conversation_id,
                message=message,
                task_type=TaskType.CODING,
                importance=MessageImportance.HIGH
            ):
                print(chunk, end='', flush=True)
                complete_response += chunk
                chunk_count += 1
            
            print("\n" + "-" * 40)
            print(f"📦 Chunks: {chunk_count}, Length: {len(complete_response)} chars")
            
            # Show context after each turn
            summary = agent.get_conversation_summary(conversation_id)
            print(f"📊 Context: {summary['message_count']} messages, "
                  f"{summary['current_tokens']} tokens")
        
        # End conversation
        agent.end_conversation(conversation_id)
        print(f"✅ Ended streaming conversation")
        
    except Exception as e:
        print(f"❌ Error in streaming + context demo: {e}")

def demo_context_strategies():
    """Demonstrate different context management strategies."""
    print("\n🎯 Context Strategies Demo")
    print("=" * 50)
    
    strategies = [
        (ContextStrategy.SLIDING_WINDOW, "Sliding Window"),
        (ContextStrategy.IMPORTANCE_BASED, "Importance Based"),
        (ContextStrategy.TRUNCATE_OLDEST, "Truncate Oldest")
    ]
    
    for strategy, description in strategies:
        print(f"\n🔧 Testing {description} Strategy")
        
        try:
            agent = create_agent(
                "tester",
                enable_context_management=True,
                max_context_tokens=1000  # Small context to trigger management
            )
            
            conversation_id = agent.start_conversation(context_strategy=strategy)
            
            # Add many messages to trigger context management
            messages = [
                "What is unit testing?",
                "How do I write test cases?",
                "What about integration testing?",
                "Can you explain mocking?",
                "What are test fixtures?",
                "How do I test async code?",
                "What about performance testing?",
                "How do I measure test coverage?"
            ]
            
            for message in messages:
                agent.chat_with_context(
                    conversation_id=conversation_id,
                    message=message,
                    task_type=TaskType.TESTING
                )
            
            # Check final context state
            summary = agent.get_conversation_summary(conversation_id)
            print(f"   📊 Final state: {summary['message_count']} messages, "
                  f"{summary['current_tokens']} tokens")
            print(f"   📈 Utilization: {summary['utilization']:.1%}")
            
            agent.end_conversation(conversation_id)
            
        except Exception as e:
            print(f"   ❌ Error with {description}: {e}")

def demo_performance_comparison():
    """Compare performance of different features."""
    print("\n⚡ Performance Comparison Demo")
    print("=" * 50)
    
    try:
        agent = create_agent("general", enable_context_management=True)
        
        prompt = "Explain the concept of machine learning in simple terms"
        
        # Test regular generation
        print("🔄 Regular generation...")
        start_time = time.time()
        regular_response = agent.generate(prompt, task_type=TaskType.GENERAL)
        regular_time = time.time() - start_time
        print(f"   ⏱️ Time: {regular_time:.2f}s")
        print(f"   📄 Length: {len(regular_response)} chars")
        
        # Test streaming generation
        print("\n🌊 Streaming generation...")
        start_time = time.time()
        streaming_response = ""
        chunk_count = 0
        
        for chunk in agent.generate_streaming(prompt, task_type=TaskType.GENERAL):
            streaming_response += chunk
            chunk_count += 1
        
        streaming_time = time.time() - start_time
        print(f"   ⏱️ Time: {streaming_time:.2f}s")
        print(f"   📄 Length: {len(streaming_response)} chars")
        print(f"   📦 Chunks: {chunk_count}")
        
        # Test with context management
        print("\n🧠 With context management...")
        conversation_id = agent.start_conversation()
        
        start_time = time.time()
        context_response = agent.chat_with_context(
            conversation_id=conversation_id,
            message=prompt,
            task_type=TaskType.GENERAL
        )
        context_time = time.time() - start_time
        print(f"   ⏱️ Time: {context_time:.2f}s")
        print(f"   📄 Length: {len(context_response)} chars")
        
        agent.end_conversation(conversation_id)
        
        # Compare results
        print(f"\n📊 Performance Summary:")
        print(f"   Regular: {regular_time:.2f}s")
        print(f"   Streaming: {streaming_time:.2f}s ({streaming_time/regular_time:.1f}x)")
        print(f"   Context: {context_time:.2f}s ({context_time/regular_time:.1f}x)")
        
        # Check if responses are similar
        if len(regular_response) > 0 and len(streaming_response) > 0:
            similarity = len(set(regular_response.split()) & set(streaming_response.split()))
            similarity_pct = similarity / len(set(regular_response.split())) * 100
            print(f"   📈 Response similarity: {similarity_pct:.1f}%")
        
    except Exception as e:
        print(f"❌ Error in performance comparison: {e}")

def main():
    """Run all streaming and context management demos."""
    print("🚀 Streaming and Context Management Demo")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_basic_streaming()
        demo_streaming_with_callback()
        demo_context_management()
        demo_streaming_with_context()
        demo_context_strategies()
        demo_performance_comparison()
        
        print("\n🎉 Streaming and Context Management Demo Completed!")
        print("\nKey features demonstrated:")
        print("- Real-time streaming responses with chunk processing")
        print("- Callback-based streaming for custom processing")
        print("- Intelligent context window management")
        print("- Multi-turn conversations with context preservation")
        print("- Multiple context management strategies")
        print("- Combined streaming + context management")
        print("- Performance optimization and comparison")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Ollama is running (ollama serve)")
        print("2. Ensure you have models installed (ollama pull llama3.1:8b)")
        print("3. Check that context management dependencies are available")

if __name__ == "__main__":
    main()