from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from argon2 import PasswordHasher, exceptions
from database.helpers import UserDB
import secrets
import re
import traceback

auth_bp = Blueprint('auth', __name__)

# Initialize password hasher with consistent settings
ph = PasswordHasher(
    time_cost=2,      # Number of iterations
    memory_cost=65536, # Memory usage in KB
    parallelism=1,    # Number of parallel threads
    hash_len=32,      # Length of hash
    salt_len=16       # Length of salt
)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        print("🔧 Starting registration process...")
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract data
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        public_key = data.get('public_key', '')
        
        print(f"📧 Email: {email}")
        print(f"🔑 Password length: {len(password)}")
        
        # Validation
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Check if user exists
        existing_user = UserDB.get_user_by_email(email)
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 409
        
        # Generate salt and hash password
        print("🔐 Generating salt and hashing password...")
        salt = secrets.token_hex(16)  # 16 bytes = 32 hex chars
        
        # Combine password and salt consistently
        password_with_salt = f"{password}{salt}"
        password_hash = ph.hash(password_with_salt)
        
        print(f"📋 Salt: {salt}")
        print(f"📋 Combined length: {len(password_with_salt)}")
        print(f"📋 Hash: {password_hash[:50]}...")
        
        # Create user
        user = UserDB.create_user(
            email=email,
            salt=salt,
            password_hash=password_hash,
            public_key=public_key
        )
        
        if user:
            print(f"✅ User created: {user['id']}")
            
            # Create tokens
            access_token = create_access_token(identity=user['id'])
            refresh_token = create_refresh_token(identity=user['id'])
            
            return jsonify({
                'message': 'User created successfully',
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'created_at': user['created_at']
                },
                'access_token': access_token,
                'refresh_token': refresh_token
            }), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        print("🔧 Starting login process...")
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        print(f"📧 Login attempt: {email}")
        print(f"🔑 Password length: {len(password)}")
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Get user
        user = UserDB.get_user_by_email(email)
        if not user:
            print(f"❌ User not found: {email}")
            return jsonify({'error': 'Invalid email or password'}), 401
        
        print(f"✅ User found: {user['id']}")
        print(f"📋 Stored salt: {user['salt']}")
        
        # Verify password using same method as registration
        try:
            password_with_salt = f"{password}{user['salt']}"
            print(f"📋 Combined for verification: {len(password_with_salt)} chars")
            
            ph.verify(user['password_hash'], password_with_salt)
            print("✅ Password verified successfully")
            
        except exceptions.VerifyMismatchError as e:
            print(f"❌ Password verification failed: {e}")
            print(f"   Stored hash: {user['password_hash'][:50]}...")
            print(f"   Input combined: {password_with_salt[:30]}...")
            return jsonify({'error': 'Invalid email or password'}), 401
        except Exception as e:
            print(f"❌ Password verification error: {e}")
            return jsonify({'error': 'Authentication error'}), 500
        
        # Create tokens
        access_token = create_access_token(identity=user['id'])
        refresh_token = create_refresh_token(identity=user['id'])
        
        print("✅ Login successful")
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'public_key': user.get('public_key', '')
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        })
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

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
                    'created_at': user['created_at'],
                    'public_key': user.get('public_key', '')
                }
            })
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        print(f"❌ Profile error: {e}")
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

# Debug endpoint (remove in production)
@auth_bp.route('/debug/user/<email>', methods=['GET'])
def debug_user(email):
    """Debug endpoint to check user data"""
    try:
        user = UserDB.get_user_by_email(email.lower())
        if user:
            return jsonify({
                'found': True,
                'id': user['id'],
                'email': user['email'],
                'salt': user['salt'][:10] + "...",
                'hash': user['password_hash'][:30] + "...",
                'created_at': user['created_at']
            })
        else:
            return jsonify({'found': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500