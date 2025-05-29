import os
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("🔐 Personal Vault API Server")
print("=" * 40)

# Create Flask app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-this-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

# Enable CORS
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

# Initialize database
try:
    from database.config import db
    print(f"✅ Database: {db.db_path}")
except Exception as e:
    print(f"❌ Database error: {e}")

# Register modules
modules = []

# Auth module
try:
    from modules.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    modules.append('auth')
    print("✅ Auth module")
except Exception as e:
    print(f"❌ Auth module: {e}")

# Vault module
try:
    from modules.vault import vault_bp
    app.register_blueprint(vault_bp, url_prefix='/api/vault')
    modules.append('vault')
    print("✅ Vault module")
except Exception as e:
    print(f"❌ Vault module: {e}")

# OTP module
try:
    from modules.otp import otp_bp
    app.register_blueprint(otp_bp, url_prefix='/api/otp')
    modules.append('otp')
    print("✅ OTP module")
except Exception as e:
    print(f"❌ OTP module: {e}")

# Backup module
try:
    from modules.backup import backup_bp
    app.register_blueprint(backup_bp, url_prefix='/api/backup')
    modules.append('backup')
    print("✅ Backup module")
except Exception as e:
    print(f"❌ Backup module: {e}")

# Share module
try:
    from modules.share import share_bp
    app.register_blueprint(share_bp, url_prefix='/api/share')
    modules.append('share')
    print("✅ Share module")
except Exception as e:
    print(f"❌ Share module: {e}")

# Health check
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "modules": modules
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Starting server on http://{host}:{port}")
    print("=" * 40)
    
    try:
        app.run(debug=debug, host=host, port=port, threaded=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")