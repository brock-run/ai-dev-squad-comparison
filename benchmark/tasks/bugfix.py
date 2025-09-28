#!/usr/bin/env python3
"""
Bugfix benchmark tasks.

This module contains benchmark tasks focused on identifying and fixing bugs
in existing code. Tasks range from simple syntax errors to complex logic bugs.
"""

from .base import BenchmarkTask, TaskCategory, DifficultyLevel, register_task


class BugfixTasks:
    """Collection of bugfix benchmark tasks."""
    
    @staticmethod
    def create_all_tasks():
        """Create and register all bugfix tasks."""
        BugfixTasks.create_syntax_error_tasks()
        BugfixTasks.create_logic_error_tasks()
        BugfixTasks.create_runtime_error_tasks()
        BugfixTasks.create_performance_bug_tasks()
        BugfixTasks.create_integration_bug_tasks()
    
    @staticmethod
    def create_syntax_error_tasks():
        """Create syntax error fix tasks."""
        
        # Simple syntax error - missing colon
        task = BenchmarkTask(
            task_id="bugfix_syntax_001",
            name="Fix Missing Colon in Function Definition",
            description="Fix a simple syntax error where a colon is missing in a function definition.",
            category=TaskCategory.BUGFIX,
            difficulty=DifficultyLevel.TRIVIAL,
            input_files={
                "calculator.py": '''def add(a, b)
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

if __name__ == "__main__":
    print(add(5, 3))
    print(subtract(10, 4))
    print(multiply(6, 7))
'''
            },
            expected_outputs={
                "calculator.py": '''def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

if __name__ == "__main__":
    print(add(5, 3))
    print(subtract(10, 4))
    print(multiply(6, 7))
'''
            },
            validation_criteria={
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "calculator.py"
                },
                "runs_successfully": {
                    "type": "test_passes",
                    "command": "python calculator.py"
                }
            },
            timeout_seconds=60,
            tags=["syntax", "python", "beginner"]
        )
        register_task(task)
        
        # Indentation error
        task = BenchmarkTask(
            task_id="bugfix_syntax_002",
            name="Fix Indentation Error",
            description="Fix indentation errors in a Python class definition.",
            category=TaskCategory.BUGFIX,
            difficulty=DifficultyLevel.EASY,
            input_files={
                "user.py": '''class User:
def __init__(self, name, email):
self.name = name
self.email = email

def get_info(self):
return f"Name: {self.name}, Email: {self.email}"

    def update_email(self, new_email):
        self.email = new_email

if __name__ == "__main__":
    user = User("Alice", "alice@example.com")
    print(user.get_info())
    user.update_email("alice.new@example.com")
    print(user.get_info())
'''
            },
            expected_outputs={
                "user.py": '''class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def get_info(self):
        return f"Name: {self.name}, Email: {self.email}"

    def update_email(self, new_email):
        self.email = new_email

if __name__ == "__main__":
    user = User("Alice", "alice@example.com")
    print(user.get_info())
    user.update_email("alice.new@example.com")
    print(user.get_info())
'''
            },
            validation_criteria={
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "user.py"
                },
                "runs_successfully": {
                    "type": "test_passes",
                    "command": "python user.py"
                }
            },
            timeout_seconds=90,
            tags=["indentation", "python", "class"]
        )
        register_task(task)
    
    @staticmethod
    def create_logic_error_tasks():
        """Create logic error fix tasks."""
        
        # Off-by-one error
        task = BenchmarkTask(
            task_id="bugfix_logic_001",
            name="Fix Off-by-One Error in Loop",
            description="Fix an off-by-one error in a function that processes a list.",
            category=TaskCategory.BUGFIX,
            difficulty=DifficultyLevel.MEDIUM,
            input_files={
                "list_processor.py": '''def find_max_in_range(numbers, start, end):
    """Find the maximum number in a given range of indices."""
    if not numbers or start < 0 or end >= len(numbers):
        return None
    
    max_val = numbers[start]
    for i in range(start, end):  # Bug: should be end + 1
        if numbers[i] > max_val:
            max_val = numbers[i]
    
    return max_val

def test_find_max():
    numbers = [1, 5, 3, 9, 2, 7, 4]
    
    # Test case 1: Should find max in range [1, 4] (indices 1 to 4 inclusive)
    result = find_max_in_range(numbers, 1, 4)
    expected = 9  # max of [5, 3, 9, 2]
    print(f"Test 1: Expected {expected}, Got {result}")
    assert result == expected, f"Expected {expected}, but got {result}"
    
    # Test case 2: Should find max in range [0, 2] (indices 0 to 2 inclusive)
    result = find_max_in_range(numbers, 0, 2)
    expected = 5  # max of [1, 5, 3]
    print(f"Test 2: Expected {expected}, Got {result}")
    assert result == expected, f"Expected {expected}, but got {result}"
    
    print("All tests passed!")

if __name__ == "__main__":
    test_find_max()
''',
                "test_list_processor.py": '''import pytest
from list_processor import find_max_in_range

def test_find_max_in_range():
    numbers = [1, 5, 3, 9, 2, 7, 4]
    
    # Test inclusive range
    assert find_max_in_range(numbers, 1, 4) == 9
    assert find_max_in_range(numbers, 0, 2) == 5
    assert find_max_in_range(numbers, 3, 6) == 9
    
    # Test edge cases
    assert find_max_in_range(numbers, 0, 0) == 1
    assert find_max_in_range(numbers, 6, 6) == 4
    
    # Test invalid ranges
    assert find_max_in_range(numbers, -1, 2) is None
    assert find_max_in_range(numbers, 0, 10) is None
    assert find_max_in_range([], 0, 0) is None
'''
            },
            expected_outputs={
                "list_processor.py": '''def find_max_in_range(numbers, start, end):
    """Find the maximum number in a given range of indices."""
    if not numbers or start < 0 or end >= len(numbers):
        return None
    
    max_val = numbers[start]
    for i in range(start, end + 1):  # Fixed: now includes end index
        if numbers[i] > max_val:
            max_val = numbers[i]
    
    return max_val

def test_find_max():
    numbers = [1, 5, 3, 9, 2, 7, 4]
    
    # Test case 1: Should find max in range [1, 4] (indices 1 to 4 inclusive)
    result = find_max_in_range(numbers, 1, 4)
    expected = 9  # max of [5, 3, 9, 2]
    print(f"Test 1: Expected {expected}, Got {result}")
    assert result == expected, f"Expected {expected}, but got {result}"
    
    # Test case 2: Should find max in range [0, 2] (indices 0 to 2 inclusive)
    result = find_max_in_range(numbers, 0, 2)
    expected = 5  # max of [1, 5, 3]
    print(f"Test 2: Expected {expected}, Got {result}")
    assert result == expected, f"Expected {expected}, but got {result}"
    
    print("All tests passed!")

if __name__ == "__main__":
    test_find_max()
'''
            },
            validation_criteria={
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "list_processor.py"
                },
                "tests_pass": {
                    "type": "test_passes",
                    "command": "python -m pytest test_list_processor.py -v"
                },
                "manual_test_passes": {
                    "type": "test_passes",
                    "command": "python list_processor.py"
                }
            },
            timeout_seconds=180,
            tags=["logic", "off-by-one", "loops", "testing"]
        )
        register_task(task)
        
        # Incorrect condition in algorithm
        task = BenchmarkTask(
            task_id="bugfix_logic_002",
            name="Fix Binary Search Algorithm",
            description="Fix a logic error in a binary search implementation.",
            category=TaskCategory.BUGFIX,
            difficulty=DifficultyLevel.HARD,
            input_files={
                "binary_search.py": '''def binary_search(arr, target):
    """
    Perform binary search on a sorted array.
    Returns the index of target if found, -1 otherwise.
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            right = mid - 1  # Bug: should be left = mid + 1
        else:
            left = mid + 1   # Bug: should be right = mid - 1
    
    return -1

def test_binary_search():
    # Test with sorted array
    arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    
    # Test finding existing elements
    assert binary_search(arr, 1) == 0
    assert binary_search(arr, 9) == 4
    assert binary_search(arr, 19) == 9
    assert binary_search(arr, 7) == 3
    
    # Test finding non-existing elements
    assert binary_search(arr, 0) == -1
    assert binary_search(arr, 20) == -1
    assert binary_search(arr, 8) == -1
    
    # Test edge cases
    assert binary_search([], 5) == -1
    assert binary_search([5], 5) == 0
    assert binary_search([5], 3) == -1
    
    print("All binary search tests passed!")

if __name__ == "__main__":
    test_binary_search()
'''
            },
            expected_outputs={
                "binary_search.py": '''def binary_search(arr, target):
    """
    Perform binary search on a sorted array.
    Returns the index of target if found, -1 otherwise.
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1   # Fixed: move left boundary right
        else:
            right = mid - 1  # Fixed: move right boundary left
    
    return -1

def test_binary_search():
    # Test with sorted array
    arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    
    # Test finding existing elements
    assert binary_search(arr, 1) == 0
    assert binary_search(arr, 9) == 4
    assert binary_search(arr, 19) == 9
    assert binary_search(arr, 7) == 3
    
    # Test finding non-existing elements
    assert binary_search(arr, 0) == -1
    assert binary_search(arr, 20) == -1
    assert binary_search(arr, 8) == -1
    
    # Test edge cases
    assert binary_search([], 5) == -1
    assert binary_search([5], 5) == 0
    assert binary_search([5], 3) == -1
    
    print("All binary search tests passed!")

if __name__ == "__main__":
    test_binary_search()
'''
            },
            validation_criteria={
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "binary_search.py"
                },
                "tests_pass": {
                    "type": "test_passes",
                    "command": "python binary_search.py"
                }
            },
            timeout_seconds=240,
            tags=["algorithm", "binary-search", "logic", "advanced"]
        )
        register_task(task)
    
    @staticmethod
    def create_runtime_error_tasks():
        """Create runtime error fix tasks."""
        
        # Division by zero error
        task = BenchmarkTask(
            task_id="bugfix_runtime_001",
            name="Fix Division by Zero Error",
            description="Fix a function that crashes due to division by zero.",
            category=TaskCategory.BUGFIX,
            difficulty=DifficultyLevel.EASY,
            input_files={
                "statistics.py": '''def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = sum(numbers)
    count = len(numbers)
    return total / count  # Bug: crashes when numbers is empty

def calculate_statistics(data):
    """Calculate basic statistics for a dataset."""
    if not data:
        return {"error": "No data provided"}
    
    avg = calculate_average(data)
    minimum = min(data)
    maximum = max(data)
    
    return {
        "average": avg,
        "minimum": minimum,
        "maximum": maximum,
        "count": len(data)
    }

def test_statistics():
    # Test with normal data
    data1 = [1, 2, 3, 4, 5]
    result1 = calculate_statistics(data1)
    print(f"Normal data: {result1}")
    
    # Test with empty data (should not crash)
    data2 = []
    result2 = calculate_statistics(data2)
    print(f"Empty data: {result2}")
    
    # Test with single value
    data3 = [42]
    result3 = calculate_statistics(data3)
    print(f"Single value: {result3}")

if __name__ == "__main__":
    test_statistics()
'''
            },
            expected_outputs={
                "statistics.py": '''def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:  # Fixed: check for empty list
        return 0
    total = sum(numbers)
    count = len(numbers)
    return total / count

def calculate_statistics(data):
    """Calculate basic statistics for a dataset."""
    if not data:
        return {"error": "No data provided"}
    
    avg = calculate_average(data)
    minimum = min(data)
    maximum = max(data)
    
    return {
        "average": avg,
        "minimum": minimum,
        "maximum": maximum,
        "count": len(data)
    }

def test_statistics():
    # Test with normal data
    data1 = [1, 2, 3, 4, 5]
    result1 = calculate_statistics(data1)
    print(f"Normal data: {result1}")
    
    # Test with empty data (should not crash)
    data2 = []
    result2 = calculate_statistics(data2)
    print(f"Empty data: {result2}")
    
    # Test with single value
    data3 = [42]
    result3 = calculate_statistics(data3)
    print(f"Single value: {result3}")

if __name__ == "__main__":
    test_statistics()
'''
            },
            validation_criteria={
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "statistics.py"
                },
                "runs_without_crash": {
                    "type": "test_passes",
                    "command": "python statistics.py"
                }
            },
            timeout_seconds=120,
            tags=["runtime-error", "division-by-zero", "error-handling"]
        )
        register_task(task)
    
    @staticmethod
    def create_performance_bug_tasks():
        """Create performance-related bug fix tasks."""
        
        # Inefficient algorithm
        task = BenchmarkTask(
            task_id="bugfix_performance_001",
            name="Fix Inefficient Duplicate Detection",
            description="Optimize a function that has poor performance due to inefficient algorithm.",
            category=TaskCategory.BUGFIX,
            difficulty=DifficultyLevel.MEDIUM,
            input_files={
                "duplicate_finder.py": '''def find_duplicates(numbers):
    """
    Find duplicate numbers in a list.
    Current implementation: O(n²) - very slow for large lists
    """
    duplicates = []
    
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] == numbers[j] and numbers[i] not in duplicates:
                duplicates.append(numbers[i])
    
    return duplicates

def test_performance():
    import time
    
    # Small test
    small_list = [1, 2, 3, 2, 4, 5, 3, 6]
    result = find_duplicates(small_list)
    print(f"Small list duplicates: {result}")
    
    # Performance test with larger list
    large_list = list(range(1000)) + list(range(500))  # 1500 items with 500 duplicates
    
    start_time = time.time()
    duplicates = find_duplicates(large_list)
    end_time = time.time()
    
    print(f"Found {len(duplicates)} duplicates in {end_time - start_time:.4f} seconds")
    
    # Should complete in reasonable time (< 1 second for optimized version)
    if end_time - start_time > 1.0:
        print("WARNING: Performance is poor, consider optimization")
    else:
        print("Performance is acceptable")

if __name__ == "__main__":
    test_performance()
'''
            },
            expected_outputs={
                "duplicate_finder.py": '''def find_duplicates(numbers):
    """
    Find duplicate numbers in a list.
    Optimized implementation: O(n) using set for tracking
    """
    seen = set()
    duplicates = set()
    
    for num in numbers:
        if num in seen:
            duplicates.add(num)
        else:
            seen.add(num)
    
    return list(duplicates)

def test_performance():
    import time
    
    # Small test
    small_list = [1, 2, 3, 2, 4, 5, 3, 6]
    result = find_duplicates(small_list)
    print(f"Small list duplicates: {result}")
    
    # Performance test with larger list
    large_list = list(range(1000)) + list(range(500))  # 1500 items with 500 duplicates
    
    start_time = time.time()
    duplicates = find_duplicates(large_list)
    end_time = time.time()
    
    print(f"Found {len(duplicates)} duplicates in {end_time - start_time:.4f} seconds")
    
    # Should complete in reasonable time (< 1 second for optimized version)
    if end_time - start_time > 1.0:
        print("WARNING: Performance is poor, consider optimization")
    else:
        print("Performance is acceptable")

if __name__ == "__main__":
    test_performance()
'''
            },
            validation_criteria={
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "duplicate_finder.py"
                },
                "runs_successfully": {
                    "type": "test_passes",
                    "command": "python duplicate_finder.py"
                }
            },
            timeout_seconds=300,
            tags=["performance", "optimization", "algorithm", "big-o"]
        )
        register_task(task)
    
    @staticmethod
    def create_integration_bug_tasks():
        """Create integration-related bug fix tasks."""
        
        # API integration bug
        task = BenchmarkTask(
            task_id="bugfix_integration_001",
            name="Fix API Response Handling Bug",
            description="Fix a bug in API response handling that causes crashes with unexpected data.",
            category=TaskCategory.BUGFIX,
            difficulty=DifficultyLevel.HARD,
            input_files={
                "api_client.py": '''import json
from typing import Dict, Any, Optional

class APIClient:
    """Simple API client with response handling."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse API response JSON.
        Bug: Doesn't handle malformed JSON or missing fields properly.
        """
        data = json.loads(response_text)  # Bug: can crash on invalid JSON
        
        # Bug: Assumes 'status' field always exists
        if data['status'] == 'success':
            return data['result']  # Bug: assumes 'result' field exists
        else:
            raise Exception(data['error'])  # Bug: assumes 'error' field exists
    
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information from API."""
        # Simulate API responses (some malformed)
        mock_responses = {
            1: '{"status": "success", "result": {"name": "Alice", "email": "alice@example.com"}}',
            2: '{"status": "error", "error": "User not found"}',
            3: '{"status": "success"}',  # Missing 'result' field
            4: 'invalid json{',  # Malformed JSON
            5: '{"message": "Server error"}',  # Missing 'status' field
        }
        
        response_text = mock_responses.get(user_id, '{"status": "error", "error": "Unknown user"}')
        
        try:
            return self.parse_response(response_text)
        except Exception as e:
            print(f"Error processing response for user {user_id}: {e}")
            return None

def test_api_client():
    client = APIClient("https://api.example.com")
    
    # Test cases that should work
    print("Testing valid responses:")
    result1 = client.get_user_info(1)  # Should work
    print(f"User 1: {result1}")
    
    result2 = client.get_user_info(2)  # Should handle error gracefully
    print(f"User 2: {result2}")
    
    # Test cases that currently crash but should be handled gracefully
    print("\\nTesting problematic responses:")
    result3 = client.get_user_info(3)  # Missing 'result' field
    print(f"User 3: {result3}")
    
    result4 = client.get_user_info(4)  # Invalid JSON
    print(f"User 4: {result4}")
    
    result5 = client.get_user_info(5)  # Missing 'status' field
    print(f"User 5: {result5}")

if __name__ == "__main__":
    test_api_client()
'''
            },
            expected_outputs={
                "api_client.py": '''import json
from typing import Dict, Any, Optional

class APIClient:
    """Simple API client with response handling."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse API response JSON with proper error handling.
        """
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response")
        
        # Handle missing status field
        status = data.get('status', 'unknown')
        
        if status == 'success':
            # Handle missing result field
            if 'result' not in data:
                raise Exception("Success response missing result data")
            return data['result']
        elif status == 'error':
            # Handle missing error field
            error_msg = data.get('error', 'Unknown error occurred')
            raise Exception(error_msg)
        else:
            # Handle unexpected status or missing status
            raise Exception(f"Unexpected response format: {data}")
    
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information from API."""
        # Simulate API responses (some malformed)
        mock_responses = {
            1: '{"status": "success", "result": {"name": "Alice", "email": "alice@example.com"}}',
            2: '{"status": "error", "error": "User not found"}',
            3: '{"status": "success"}',  # Missing 'result' field
            4: 'invalid json{',  # Malformed JSON
            5: '{"message": "Server error"}',  # Missing 'status' field
        }
        
        response_text = mock_responses.get(user_id, '{"status": "error", "error": "Unknown user"}')
        
        try:
            return self.parse_response(response_text)
        except Exception as e:
            print(f"Error processing response for user {user_id}: {e}")
            return None

def test_api_client():
    client = APIClient("https://api.example.com")
    
    # Test cases that should work
    print("Testing valid responses:")
    result1 = client.get_user_info(1)  # Should work
    print(f"User 1: {result1}")
    
    result2 = client.get_user_info(2)  # Should handle error gracefully
    print(f"User 2: {result2}")
    
    # Test cases that currently crash but should be handled gracefully
    print("\\nTesting problematic responses:")
    result3 = client.get_user_info(3)  # Missing 'result' field
    print(f"User 3: {result3}")
    
    result4 = client.get_user_info(4)  # Invalid JSON
    print(f"User 4: {result4}")
    
    result5 = client.get_user_info(5)  # Missing 'status' field
    print(f"User 5: {result5}")

if __name__ == "__main__":
    test_api_client()
'''
            },
            validation_criteria={
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "api_client.py"
                },
                "handles_errors_gracefully": {
                    "type": "test_passes",
                    "command": "python api_client.py"
                }
            },
            timeout_seconds=180,
            tags=["integration", "api", "error-handling", "json", "robustness"]
        )
        register_task(task)