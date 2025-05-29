from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from argon2 import PasswordHasher
from database.config import UserDB
import secrets
import re

auth_bp = Blueprint('auth', __name__)

# Password hasher
ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    salt_len=16
)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Check existing user
        if UserDB.get_user_by_email(email):
            return jsonify({'error': 'Email already exists'}), 409
        
        # Hash password
        salt = secrets.token_hex(16)
        password_hash = ph.hash(f"{password}{salt}")
        
        # Create user
        user = UserDB.create_user(email, salt, password_hash)
        
        if user:
            access_token = create_access_token(identity=user['id'])
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'email': user['email']
                },
                'access_token': access_token
            }), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        # Get user
        user = UserDB.get_user_by_email(email)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        try:
            ph.verify(user['password_hash'], f"{password}{user['salt']}")
        except:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create token
        access_token = create_access_token(identity=user['id'])
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email']
            },
            'access_token': access_token
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        user = UserDB.get_user_by_id(user_id)
        
        if user:
            return jsonify({
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'created_at': user['created_at']
                }
            })
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """Get users list for sharing"""
    try:
        users = UserDB.get_all_users()
        user_list = [
            {
                'id': user['id'],
                'email': user['email']
            } for user in users
        ]
        return jsonify({'users': user_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500