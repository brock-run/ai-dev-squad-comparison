#!/usr/bin/env python3
"""
Benchmark Task Definitions and Suite Builder

This module contains predefined benchmark tasks and utilities for building
comprehensive benchmark suites for AI agent frameworks.
"""

from typing import List, Dict, Any
from .benchmarking import BenchmarkTask, BenchmarkSuite, BenchmarkType, TaskType, MessageImportance


class BenchmarkSuiteBuilder:
    """Builder for creating comprehensive benchmark suites."""
    
    def __init__(self):
        self.tasks = []
        self.frameworks = []
        self.benchmark_types = []
        self.configuration = {}
    
    def add_coding_tasks(self) -> 'BenchmarkSuiteBuilder':
        """Add standard coding benchmark tasks."""
        coding_tasks = [
            BenchmarkTask(
                task_id="coding_001",
                name="Simple Function Implementation",
                description="Implement a basic utility function",
                task_type=TaskType.CODING,
                prompt="Write a Python function that calculates the factorial of a number. Include error handling for negative numbers and non-integers.",
                expected_output="def factorial(n):",
                evaluation_criteria={
                    'length_check': {'min_length': 100, 'max_length': 500, 'optimal_length': 200},
                    'keyword_presence': {'required': ['def', 'factorial', 'return'], 'forbidden': ['import']},
                    'structure_check': {'expect_code': True},
                    'code_quality': {},
                    'completeness': {'expected_elements': ['error handling', 'docstring', 'function definition']}
                }
            ),
            BenchmarkTask(
                task_id="coding_002",
                name="Class Design",
                description="Design and implement a class with methods",
                task_type=TaskType.CODING,
                prompt="Create a Python class called 'BankAccount' with methods for deposit, withdraw, and get_balance. Include proper validation and error handling.",
                evaluation_criteria={
                    'length_check': {'min_length': 200, 'max_length': 800, 'optimal_length': 400},
                    'keyword_presence': {'required': ['class', 'BankAccount', 'def', 'deposit', 'withdraw'], 'forbidden': []},
                    'structure_check': {'expect_code': True},
                    'code_quality': {},
                    'completeness': {'expected_elements': ['class definition', 'deposit method', 'withdraw method', 'balance tracking']}
                }
            ),
            BenchmarkTask(
                task_id="coding_003",
                name="Algorithm Implementation",
                description="Implement a sorting algorithm",
                task_type=TaskType.CODING,
                prompt="Implement the quicksort algorithm in Python. Include comments explaining the logic and handle edge cases.",
                evaluation_criteria={
                    'length_check': {'min_length': 300, 'max_length': 1000, 'optimal_length': 500},
                    'keyword_presence': {'required': ['def', 'quicksort', 'partition'], 'forbidden': ['sorted', 'sort']},
                    'structure_check': {'expect_code': True},
                    'code_quality': {},
                    'completeness': {'expected_elements': ['recursive calls', 'partition logic', 'base case']}
                }
            ),
            BenchmarkTask(
                task_id="coding_004",
                name="Data Structure Implementation",
                description="Implement a custom data structure",
                task_type=TaskType.CODING,
                prompt="Implement a binary search tree in Python with insert, search, and delete operations. Include proper tree balancing considerations.",
                evaluation_criteria={
                    'length_check': {'min_length': 400, 'max_length': 1200, 'optimal_length': 600},
                    'keyword_presence': {'required': ['class', 'insert', 'search', 'delete'], 'forbidden': []},
                    'structure_check': {'expect_code': True},
                    'code_quality': {},
                    'completeness': {'expected_elements': ['tree structure', 'insert method', 'search method', 'delete method']}
                }
            ),
            BenchmarkTask(
                task_id="coding_005",
                name="API Integration",
                description="Create code for API integration",
                task_type=TaskType.CODING,
                prompt="Write Python code to interact with a REST API. Include error handling, authentication, and response parsing for a weather service.",
                evaluation_criteria={
                    'length_check': {'min_length': 250, 'max_length': 700, 'optimal_length': 400},
                    'keyword_presence': {'required': ['requests', 'json', 'error'], 'optional': ['auth', 'headers']},
                    'structure_check': {'expect_code': True},
                    'code_quality': {},
                    'completeness': {'expected_elements': ['HTTP request', 'error handling', 'response parsing', 'authentication']}
                }
            )
        ]
        
        self.tasks.extend(coding_tasks)
        if BenchmarkType.PERFORMANCE not in self.benchmark_types:
            self.benchmark_types.append(BenchmarkType.PERFORMANCE)
        if BenchmarkType.QUALITY not in self.benchmark_types:
            self.benchmark_types.append(BenchmarkType.QUALITY)
        
        return self
    
    def add_architecture_tasks(self) -> 'BenchmarkSuiteBuilder':
        """Add architecture and design benchmark tasks."""
        architecture_tasks = [
            BenchmarkTask(
                task_id="arch_001",
                name="System Design",
                description="Design a scalable web application architecture",
                task_type=TaskType.ARCHITECTURE,
                prompt="Design the architecture for a social media platform that needs to handle 1 million users. Include database design, caching strategy, and scalability considerations.",
                evaluation_criteria={
                    'length_check': {'min_length': 500, 'max_length': 2000, 'optimal_length': 1000},
                    'keyword_presence': {'required': ['database', 'cache', 'scalability', 'architecture'], 'optional': ['microservices', 'load balancer', 'CDN']},
                    'structure_check': {'expect_sections': True, 'expect_list': True},
                    'completeness': {'expected_elements': ['database design', 'caching strategy', 'scalability plan', 'component diagram']}
                }
            ),
            BenchmarkTask(
                task_id="arch_002",
                name="API Design",
                description="Design RESTful API endpoints",
                task_type=TaskType.ARCHITECTURE,
                prompt="Design RESTful API endpoints for a task management system. Include CRUD operations, authentication, and proper HTTP status codes.",
                evaluation_criteria={
                    'length_check': {'min_length': 300, 'max_length': 1200, 'optimal_length': 600},
                    'keyword_presence': {'required': ['GET', 'POST', 'PUT', 'DELETE', 'API'], 'optional': ['authentication', 'JWT', 'OAuth']},
                    'structure_check': {'expect_list': True},
                    'completeness': {'expected_elements': ['CRUD endpoints', 'authentication', 'status codes', 'request/response format']}
                }
            ),
            BenchmarkTask(
                task_id="arch_003",
                name="Microservices Architecture",
                description="Design a microservices architecture",
                task_type=TaskType.ARCHITECTURE,
                prompt="Design a microservices architecture for an e-commerce platform. Include service boundaries, communication patterns, and data consistency strategies.",
                evaluation_criteria={
                    'length_check': {'min_length': 600, 'max_length': 1800, 'optimal_length': 900},
                    'keyword_presence': {'required': ['microservices', 'service', 'communication', 'data'], 'optional': ['event-driven', 'saga', 'CQRS']},
                    'structure_check': {'expect_sections': True, 'expect_list': True},
                    'completeness': {'expected_elements': ['service boundaries', 'communication patterns', 'data strategy', 'deployment considerations']}
                }
            )
        ]
        
        self.tasks.extend(architecture_tasks)
        if BenchmarkType.FEATURE_PARITY not in self.benchmark_types:
            self.benchmark_types.append(BenchmarkType.FEATURE_PARITY)
        
        return self
    
    def add_testing_tasks(self) -> 'BenchmarkSuiteBuilder':
        """Add testing and quality assurance benchmark tasks."""
        testing_tasks = [
            BenchmarkTask(
                task_id="test_001",
                name="Unit Test Creation",
                description="Write comprehensive unit tests",
                task_type=TaskType.TESTING,
                prompt="Write unit tests for a calculator class with methods add, subtract, multiply, and divide. Include edge cases and error conditions.",
                evaluation_criteria={
                    'length_check': {'min_length': 200, 'max_length': 800, 'optimal_length': 400},
                    'keyword_presence': {'required': ['test', 'assert', 'def'], 'optional': ['unittest', 'pytest', 'mock']},
                    'structure_check': {'expect_code': True},
                    'code_quality': {},
                    'completeness': {'expected_elements': ['test methods', 'edge cases', 'error handling tests']}
                }
            ),
            BenchmarkTask(
                task_id="test_002",
                name="Test Strategy",
                description="Design a comprehensive testing strategy",
                task_type=TaskType.TESTING,
                prompt="Create a testing strategy for a web application including unit tests, integration tests, and end-to-end tests. Include tools and best practices.",
                evaluation_criteria={
                    'length_check': {'min_length': 400, 'max_length': 1500, 'optimal_length': 800},
                    'keyword_presence': {'required': ['unit test', 'integration', 'end-to-end'], 'optional': ['CI/CD', 'automation', 'coverage']},
                    'structure_check': {'expect_sections': True, 'expect_list': True},
                    'completeness': {'expected_elements': ['test types', 'tools', 'best practices', 'automation strategy']}
                }
            ),
            BenchmarkTask(
                task_id="test_003",
                name="Performance Testing",
                description="Design performance testing approach",
                task_type=TaskType.TESTING,
                prompt="Design a performance testing strategy for a high-traffic web application. Include load testing, stress testing, and monitoring approaches.",
                evaluation_criteria={
                    'length_check': {'min_length': 350, 'max_length': 1000, 'optimal_length': 600},
                    'keyword_presence': {'required': ['performance', 'load', 'stress', 'monitoring'], 'optional': ['JMeter', 'Gatling', 'metrics']},
                    'structure_check': {'expect_sections': True, 'expect_list': True},
                    'completeness': {'expected_elements': ['load testing', 'stress testing', 'monitoring', 'tools']}
                }
            )
        ]
        
        self.tasks.extend(testing_tasks)
        if BenchmarkType.RELIABILITY not in self.benchmark_types:
            self.benchmark_types.append(BenchmarkType.RELIABILITY)
        
        return self
    
    def add_debugging_tasks(self) -> 'BenchmarkSuiteBuilder':
        """Add debugging and troubleshooting benchmark tasks."""
        debugging_tasks = [
            BenchmarkTask(
                task_id="debug_001",
                name="Bug Analysis",
                description="Analyze and fix a code bug",
                task_type=TaskType.DEBUGGING,
                prompt="Here's a Python function with a bug:\n\ndef calculate_average(numbers):\n    total = 0\n    for num in numbers:\n        total += num\n    return total / len(numbers)\n\nIdentify the bug and provide a fixed version with proper error handling.",
                evaluation_criteria={
                    'length_check': {'min_length': 150, 'max_length': 600, 'optimal_length': 300},
                    'keyword_presence': {'required': ['bug', 'fix', 'error'], 'optional': ['exception', 'validation', 'empty']},
                    'structure_check': {'expect_code': True},
                    'code_quality': {},
                    'completeness': {'expected_elements': ['bug identification', 'fixed code', 'error handling']}
                }
            ),
            BenchmarkTask(
                task_id="debug_002",
                name="Performance Issue Analysis",
                description="Identify and fix performance issues",
                task_type=TaskType.DEBUGGING,
                prompt="Analyze this slow Python code and suggest optimizations:\n\ndef find_duplicates(lst):\n    duplicates = []\n    for i in range(len(lst)):\n        for j in range(i+1, len(lst)):\n            if lst[i] == lst[j] and lst[i] not in duplicates:\n                duplicates.append(lst[i])\n    return duplicates",
                evaluation_criteria={
                    'length_check': {'min_length': 200, 'max_length': 700, 'optimal_length': 400},
                    'keyword_presence': {'required': ['performance', 'optimization', 'complexity'], 'optional': ['set', 'hash', 'O(n)']},
                    'structure_check': {'expect_code': True},
                    'code_quality': {},
                    'completeness': {'expected_elements': ['performance analysis', 'optimized code', 'complexity explanation']}
                }
            )
        ]
        
        self.tasks.extend(debugging_tasks)
        return self
    
    def add_documentation_tasks(self) -> 'BenchmarkSuiteBuilder':
        """Add documentation and communication benchmark tasks."""
        documentation_tasks = [
            BenchmarkTask(
                task_id="doc_001",
                name="API Documentation",
                description="Create comprehensive API documentation",
                task_type=TaskType.DOCUMENTATION,
                prompt="Create documentation for a user management API with endpoints for creating, reading, updating, and deleting users. Include examples and error responses.",
                evaluation_criteria={
                    'length_check': {'min_length': 400, 'max_length': 1200, 'optimal_length': 700},
                    'keyword_presence': {'required': ['API', 'endpoint', 'example', 'error'], 'optional': ['OpenAPI', 'Swagger', 'JSON']},
                    'structure_check': {'expect_sections': True, 'expect_list': True},
                    'completeness': {'expected_elements': ['endpoint descriptions', 'request examples', 'response examples', 'error codes']}
                }
            ),
            BenchmarkTask(
                task_id="doc_002",
                name="Technical Specification",
                description="Write a technical specification document",
                task_type=TaskType.DOCUMENTATION,
                prompt="Write a technical specification for implementing a real-time chat feature in a web application. Include requirements, architecture, and implementation details.",
                evaluation_criteria={
                    'length_check': {'min_length': 500, 'max_length': 1500, 'optimal_length': 900},
                    'keyword_presence': {'required': ['specification', 'requirements', 'architecture', 'implementation'], 'optional': ['WebSocket', 'real-time', 'scalability']},
                    'structure_check': {'expect_sections': True, 'expect_list': True},
                    'completeness': {'expected_elements': ['requirements', 'architecture', 'implementation plan', 'technical details']}
                }
            )
        ]
        
        self.tasks.extend(documentation_tasks)
        return self
    
    def add_frameworks(self, frameworks: List[str]) -> 'BenchmarkSuiteBuilder':
        """Add frameworks to test."""
        self.frameworks.extend(frameworks)
        return self
    
    def add_configuration(self, config: Dict[str, Any]) -> 'BenchmarkSuiteBuilder':
        """Add configuration options."""
        self.configuration.update(config)
        return self
    
    def build(self, suite_id: str, name: str, description: str) -> BenchmarkSuite:
        """Build the benchmark suite."""
        return BenchmarkSuite(
            suite_id=suite_id,
            name=name,
            description=description,
            tasks=self.tasks.copy(),
            frameworks=self.frameworks.copy(),
            benchmark_types=self.benchmark_types.copy(),
            configuration=self.configuration.copy()
        )


def create_quick_suite(frameworks: List[str]) -> BenchmarkSuite:
    """Create a quick benchmark suite with essential tasks."""
    quick_tasks = [
        BenchmarkTask(
            task_id="quick_001",
            name="Simple Coding Task",
            description="Basic function implementation",
            task_type=TaskType.CODING,
            prompt="Write a Python function that reverses a string.",
            evaluation_criteria={
                'length_check': {'min_length': 50, 'max_length': 300, 'optimal_length': 150},
                'keyword_presence': {'required': ['def', 'return']},
                'structure_check': {'expect_code': True}
            }
        ),
        BenchmarkTask(
            task_id="quick_002",
            name="Simple Architecture Task",
            description="Basic system design",
            task_type=TaskType.ARCHITECTURE,
            prompt="Describe the components needed for a simple web application with user authentication.",
            evaluation_criteria={
                'length_check': {'min_length': 100, 'max_length': 500, 'optimal_length': 250},
                'keyword_presence': {'required': ['authentication', 'database', 'web']},
                'structure_check': {'expect_list': True}
            }
        ),
        BenchmarkTask(
            task_id="quick_003",
            name="Simple Testing Task",
            description="Basic test creation",
            task_type=TaskType.TESTING,
            prompt="Write a simple unit test for a function that adds two numbers.",
            evaluation_criteria={
                'length_check': {'min_length': 80, 'max_length': 400, 'optimal_length': 200},
                'keyword_presence': {'required': ['test', 'assert', 'def']},
                'structure_check': {'expect_code': True}
            }
        )
    ]
    
    return BenchmarkSuite(
        suite_id="quick_v1",
        name="Quick Framework Benchmark",
        description="Fast benchmark for basic framework comparison",
        tasks=quick_tasks,
        frameworks=frameworks,
        benchmark_types=[BenchmarkType.PERFORMANCE, BenchmarkType.QUALITY],
        configuration={'timeout_seconds': 120, 'parallel_execution': True}
    )


def create_performance_focused_suite(frameworks: List[str]) -> BenchmarkSuite:
    """Create a benchmark suite focused on performance testing."""
    performance_tasks = [
        BenchmarkTask(
            task_id="perf_001",
            name="Fast Response Task",
            description="Task optimized for response time measurement",
            task_type=TaskType.CODING,
            prompt="Write a simple function to check if a number is prime.",
            evaluation_criteria={
                'length_check': {'min_length': 50, 'max_length': 200, 'optimal_length': 100},
                'keyword_presence': {'required': ['def', 'prime']},
                'structure_check': {'expect_code': True}
            },
            importance=MessageImportance.HIGH
        ),
        BenchmarkTask(
            task_id="perf_002",
            name="Complex Algorithm Task",
            description="More complex task for throughput measurement",
            task_type=TaskType.CODING,
            prompt="Implement a function to find the longest common subsequence between two strings using dynamic programming.",
            evaluation_criteria={
                'length_check': {'min_length': 200, 'max_length': 800, 'optimal_length': 400},
                'keyword_presence': {'required': ['def', 'dynamic', 'subsequence']},
                'structure_check': {'expect_code': True}
            },
            importance=MessageImportance.HIGH
        )
    ]
    
    return BenchmarkSuite(
        suite_id="performance_v1",
        name="Performance Benchmark Suite",
        description="Benchmark suite focused on performance metrics",
        tasks=performance_tasks,
        frameworks=frameworks,
        benchmark_types=[BenchmarkType.PERFORMANCE],
        configuration={
            'timeout_seconds': 60,
            'parallel_execution': True,
            'max_workers': 8,
            'enable_performance_profiling': True
        }
    )


def create_quality_focused_suite(frameworks: List[str]) -> BenchmarkSuite:
    """Create a benchmark suite focused on output quality."""
    quality_tasks = [
        BenchmarkTask(
            task_id="qual_001",
            name="Detailed Code Implementation",
            description="Task requiring high-quality, well-documented code",
            task_type=TaskType.CODING,
            prompt="Implement a comprehensive logging system in Python with different log levels, file rotation, and custom formatters. Include full documentation and error handling.",
            evaluation_criteria={
                'length_check': {'min_length': 500, 'max_length': 1500, 'optimal_length': 800},
                'keyword_presence': {'required': ['logging', 'class', 'def', 'error'], 'optional': ['rotation', 'formatter', 'handler']},
                'structure_check': {'expect_code': True},
                'code_quality': {},
                'completeness': {'expected_elements': ['log levels', 'file rotation', 'formatters', 'error handling', 'documentation']}
            },
            importance=MessageImportance.HIGH
        ),
        BenchmarkTask(
            task_id="qual_002",
            name="Architectural Design",
            description="Task requiring detailed architectural thinking",
            task_type=TaskType.ARCHITECTURE,
            prompt="Design a comprehensive disaster recovery plan for a distributed system handling financial transactions. Include RTO/RPO requirements, backup strategies, and failover procedures.",
            evaluation_criteria={
                'length_check': {'min_length': 800, 'max_length': 2500, 'optimal_length': 1500},
                'keyword_presence': {'required': ['disaster recovery', 'RTO', 'RPO', 'backup', 'failover'], 'optional': ['replication', 'monitoring', 'testing']},
                'structure_check': {'expect_sections': True, 'expect_list': True},
                'completeness': {'expected_elements': ['RTO/RPO requirements', 'backup strategy', 'failover procedures', 'testing plan', 'monitoring']}
            },
            importance=MessageImportance.HIGH
        )
    ]
    
    return BenchmarkSuite(
        suite_id="quality_v1",
        name="Quality Benchmark Suite",
        description="Benchmark suite focused on output quality and completeness",
        tasks=quality_tasks,
        frameworks=frameworks,
        benchmark_types=[BenchmarkType.QUALITY],
        configuration={
            'timeout_seconds': 600,
            'parallel_execution': False,  # Sequential for quality focus
            'enable_detailed_evaluation': True
        }
    )