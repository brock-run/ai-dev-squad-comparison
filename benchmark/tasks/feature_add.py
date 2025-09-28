#!/usr/bin/env python3
"""
Feature addition benchmark tasks.

This module contains benchmark tasks focused on adding new features to existing
codebases. Tasks range from simple method additions to complex multi-file features.
"""

from .base import BenchmarkTask, TaskCategory, DifficultyLevel, register_task


class FeatureAddTasks:
    """Collection of feature addition benchmark tasks."""
    
    @staticmethod
    def create_all_tasks():
        """Create and register all feature addition tasks."""
        FeatureAddTasks.create_simple_method_tasks()
        FeatureAddTasks.create_class_extension_tasks()
        FeatureAddTasks.create_multi_file_feature_tasks()
        FeatureAddTasks.create_api_endpoint_tasks()
    
    @staticmethod
    def create_simple_method_tasks():
        """Create simple method addition tasks."""
        
        # Add method to existing class
        task = BenchmarkTask(
            task_id="feature_add_method_001",
            name="Add Method to Calculator Class",
            description="Add a power method to an existing calculator class.",
            category=TaskCategory.FEATURE_ADD,
            difficulty=DifficultyLevel.EASY,
            input_files={
                "calculator.py": '''class Calculator:
    """Simple calculator class."""
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
'''
            },
            expected_outputs={
                "calculator.py": '''class Calculator:
    """Simple calculator class."""
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def power(self, base, exponent):
        """Calculate base raised to the power of exponent."""
        return base ** exponent
'''
            },
            validation_criteria={
                "has_power_method": {
                    "type": "file_contains",
                    "filename": "calculator.py",
                    "content": "def power(self"
                },
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "calculator.py"
                }
            },
            timeout_seconds=120,
            tags=["method-addition", "class", "simple"]
        )
        register_task(task)    
    
@staticmethod
    def create_class_extension_tasks():
        """Create class extension tasks."""
        
        # Add new class with inheritance
        task = BenchmarkTask(
            task_id="feature_add_class_001",
            name="Create User Authentication System",
            description="Add a user authentication system with login/logout functionality.",
            category=TaskCategory.FEATURE_ADD,
            difficulty=DifficultyLevel.MEDIUM,
            input_files={
                "user.py": '''class User:
    """Basic user class."""
    
    def __init__(self, username, email):
        self.username = username
        self.email = email
        self.created_at = None
    
    def get_info(self):
        return f"User: {self.username} ({self.email})"
'''
            },
            expected_outputs={
                "user.py": '''from datetime import datetime
import hashlib

class User:
    """Basic user class."""
    
    def __init__(self, username, email):
        self.username = username
        self.email = email
        self.created_at = datetime.now()
    
    def get_info(self):
        return f"User: {self.username} ({self.email})"

class AuthenticatedUser(User):
    """User with authentication capabilities."""
    
    def __init__(self, username, email, password):
        super().__init__(username, email)
        self.password_hash = self._hash_password(password)
        self.is_logged_in = False
        self.last_login = None
    
    def _hash_password(self, password):
        """Hash password for secure storage."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self, password):
        """Authenticate user with password."""
        if self._hash_password(password) == self.password_hash:
            self.is_logged_in = True
            self.last_login = datetime.now()
            return True
        return False
    
    def logout(self):
        """Log out the user."""
        self.is_logged_in = False
    
    def change_password(self, old_password, new_password):
        """Change user password."""
        if self.login(old_password):
            self.password_hash = self._hash_password(new_password)
            return True
        return False
'''
            },
            validation_criteria={
                "has_authenticated_user_class": {
                    "type": "file_contains",
                    "filename": "user.py",
                    "content": "class AuthenticatedUser"
                },
                "has_login_method": {
                    "type": "file_contains",
                    "filename": "user.py",
                    "content": "def login("
                },
                "has_logout_method": {
                    "type": "file_contains",
                    "filename": "user.py",
                    "content": "def logout("
                },
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "user.py"
                }
            },
            timeout_seconds=300,
            tags=["class-extension", "inheritance", "authentication", "security"]
        )
        register_task(task)
    
    @staticmethod
    def create_multi_file_feature_tasks():
        """Create multi-file feature tasks."""
        
        # Add REST API endpoints
        task = BenchmarkTask(
            task_id="feature_add_multifile_001",
            name="Add REST API Endpoints",
            description="Add REST API endpoints for user management to an existing Flask application.",
            category=TaskCategory.FEATURE_ADD,
            difficulty=DifficultyLevel.HARD,
            input_files={
                "app.py": '''from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(debug=True)
''',
                "requirements.txt": '''Flask==2.3.3
'''
            },
            expected_outputs={
                "app.py": '''from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory user storage (for demo purposes)
users = {}
next_user_id = 1

@app.route('/')
def hello():
    return "Hello, World!"

@app.route('/users', methods=['GET'])
def get_users():
    """Get all users."""
    return jsonify(list(users.values()))

@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user."""
    global next_user_id
    data = request.get_json()
    
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({'error': 'Name and email are required'}), 400
    
    user = {
        'id': next_user_id,
        'name': data['name'],
        'email': data['email']
    }
    
    users[next_user_id] = user
    next_user_id += 1
    
    return jsonify(user), 201

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user."""
    user = users.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user)

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update a user."""
    user = users.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    user.update(data)
    return jsonify(user)

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user."""
    if user_id not in users:
        return jsonify({'error': 'User not found'}), 404
    
    del users[user_id]
    return jsonify({'message': 'User deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)
'''
            },
            validation_criteria={
                "has_get_users_endpoint": {
                    "type": "file_contains",
                    "filename": "app.py",
                    "content": "@app.route('/users', methods=['GET'])"
                },
                "has_create_user_endpoint": {
                    "type": "file_contains",
                    "filename": "app.py",
                    "content": "@app.route('/users', methods=['POST'])"
                },
                "has_crud_operations": {
                    "type": "file_contains",
                    "filename": "app.py",
                    "content": "methods=['DELETE']"
                },
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "app.py"
                }
            },
            timeout_seconds=600,
            tags=["rest-api", "flask", "crud", "multi-endpoint"]
        )
        register_task(task)
    
    @staticmethod
    def create_api_endpoint_tasks():
        """Create API endpoint addition tasks."""
        
        # Add authentication middleware
        task = BenchmarkTask(
            task_id="feature_add_api_001",
            name="Add Authentication Middleware",
            description="Add JWT authentication middleware to protect API endpoints.",
            category=TaskCategory.FEATURE_ADD,
            difficulty=DifficultyLevel.EXPERT,
            input_files={
                "api.py": '''from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/public')
def public_endpoint():
    return jsonify({"message": "This is a public endpoint"})

@app.route('/protected')
def protected_endpoint():
    # This should be protected but currently isn't
    return jsonify({"message": "This should be protected", "user": "anonymous"})

@app.route('/admin')
def admin_endpoint():
    # This should require admin privileges
    return jsonify({"message": "Admin only content"})

if __name__ == '__main__':
    app.run(debug=True)
''',
                "requirements.txt": '''Flask==2.3.3
PyJWT==2.8.0
'''
            },
            expected_outputs={
                "api.py": '''from flask import Flask, request, jsonify
import jwt
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

def token_required(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['user']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.get('is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint to get JWT token."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Simple authentication (in production, check against database)
    if username == 'admin' and password == 'admin123':
        token = jwt.encode({
            'user': {'username': username, 'is_admin': True},
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({'token': token})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/public')
def public_endpoint():
    return jsonify({"message": "This is a public endpoint"})

@app.route('/protected')
@token_required
def protected_endpoint(current_user):
    return jsonify({
        "message": "This is a protected endpoint", 
        "user": current_user['username']
    })

@app.route('/admin')
@token_required
@admin_required
def admin_endpoint(current_user):
    return jsonify({
        "message": "Admin only content",
        "admin": current_user['username']
    })

if __name__ == '__main__':
    app.run(debug=True)
'''
            },
            validation_criteria={
                "has_token_required_decorator": {
                    "type": "file_contains",
                    "filename": "api.py",
                    "content": "def token_required"
                },
                "has_login_endpoint": {
                    "type": "file_contains",
                    "filename": "api.py",
                    "content": "@app.route('/login'"
                },
                "protected_endpoint_secured": {
                    "type": "file_contains",
                    "filename": "api.py",
                    "content": "@token_required"
                },
                "no_syntax_errors": {
                    "type": "no_syntax_errors",
                    "filename": "api.py"
                }
            },
            timeout_seconds=600,
            tags=["authentication", "jwt", "middleware", "security", "flask"]
        )
        register_task(task)