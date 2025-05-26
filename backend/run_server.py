import os
import sys
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🔐 Personal Vault API Server")
print("=" * 60)

# Import database first
try:
    from database.config import db
    database_available = True
    print(f"✅ Database connected: {db.db_path}")
    print(f"📈 Database stats: {db.get_stats()}")
except ImportError as e:
    print(f"❌ Database import failed: {e}")
    database_available = False

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

# Enable CORS for frontend communication
CORS(app)

# Initialize extensions
jwt = JWTManager(app)

# Redis for rate limiting (optional)
redis_available = False
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_client.ping()
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        storage_uri="redis://localhost:6379"
    )
    redis_available = True
    print("✅ Redis connected")
except Exception as e:
    print(f"⚠️  Redis not available: {str(e)}")
    print("   Using memory storage for rate limiting")
    limiter = Limiter(
        key_func=get_remote_address,
        app=app
    )

# Import and register modules
modules_loaded = []

# Auth module
try:
    from modules.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    modules_loaded.append('auth')
    print("✅ Auth module loaded")
except ImportError as e:
    print(f"❌ Auth module failed: {e}")

# Vault module
try:
    from modules.vault import vault_bp
    app.register_blueprint(vault_bp, url_prefix='/api/vault')
    modules_loaded.append('vault')
    print("✅ Vault module loaded")
except ImportError as e:
    print(f"❌ Vault module failed: {e}")

# Share module (optional)
try:
    from modules.share import share_bp
    app.register_blueprint(share_bp, url_prefix='/api/share')
    modules_loaded.append('share')
    print("✅ Share module loaded")
except ImportError as e:
    print(f"⚠️  Share module failed: {e}")

# Backup module (optional)
try:
    from modules.backup import backup_bp
    app.register_blueprint(backup_bp, url_prefix='/api/backup')
    modules_loaded.append('backup')
    print("✅ Backup module loaded")
except ImportError as e:
    print(f"⚠️  Backup module failed: {e}")

# Rate limiting for auth endpoints
@limiter.limit("10 per minute")
def rate_limited_auth():
    pass

# Global error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "Rate limit exceeded", 
        "message": "Too many requests. Please try again later."
    }), 429

# Health check endpoint
@app.route('/api/health')
def health_check():
    health_data = {
        "status": "healthy", 
        "version": "1.0.0",
        "database_available": database_available,
        "redis_available": redis_available,
        "modules_loaded": modules_loaded,
        "rate_limiting": "memory" if not redis_available else "redis"
    }
    
    if database_available:
        health_data["database_stats"] = db.get_stats()
    
    return jsonify(health_data)

# API info endpoint
@app.route('/api/info')
def api_info():
    return jsonify({
        "name": "Personal Vault API",
        "version": "1.0.0",
        "database": "SQLite" if database_available else "None",
        "modules_loaded": modules_loaded,
        "rate_limiting": "memory" if not redis_available else "redis",
        "endpoints": {
            "health": "/api/health",
            "info": "/api/info",
            "auth": "/api/auth" if "auth" in modules_loaded else None,
            "vault": "/api/vault" if "vault" in modules_loaded else None,
            "share": "/api/share" if "share" in modules_loaded else None,
            "backup": "/api/backup" if "backup" in modules_loaded else None
        }
    })

# Main server runner
if __name__ == '__main__':
    # Server configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Server starting on http://{host}:{port}")
    print(f"🐛 Debug mode: {debug}")
    print(f"⚡ Rate limiting: {'Redis' if redis_available else 'In-memory'}")
    print("=" * 60)
    print("Available endpoints:")
    print("  GET  /api/health          - Health check")
    print("  GET  /api/info            - API information")
    
    if "auth" in modules_loaded:
        print("  POST /api/auth/register   - User registration")
        print("  POST /api/auth/login      - User login")
        print("  GET  /api/auth/profile    - User profile")
    
    if "vault" in modules_loaded:
        print("  POST /api/vault/          - Create vault entry")
        print("  GET  /api/vault/          - Get vault entries")
        print("  GET  /api/vault/stats     - Vault statistics")
    
    if "share" in modules_loaded:
        print("  POST /api/share/send      - Send encrypted share")
        print("  GET  /api/share/incoming  - Get incoming shares")
    
    if "backup" in modules_loaded:
        print("  POST /api/backup/create   - Create backup")
        print("  GET  /api/backup/latest   - Get latest backup")
    
    print("=" * 60)
    print("🔧 To test the API, run in another terminal:")
    print("   python test_register.py")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        app.run(debug=debug, host=host, port=port, threaded=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped gracefully")
    except Exception as e:
        print(f"❌ Server error: {e}")