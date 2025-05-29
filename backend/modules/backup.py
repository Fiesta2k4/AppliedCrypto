from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from database.helpers import UserDB, BackupDB

backup_bp = Blueprint('backup', __name__)

# Configuration
BACKUP_STORAGE_PATH = os.getenv('BACKUP_STORAGE_PATH', './backups')
Path(BACKUP_STORAGE_PATH).mkdir(exist_ok=True)

@backup_bp.route('/create', methods=['POST'])
@jwt_required()
def create_backup():
    """Create encrypted backup of user's vault"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        print(f"🔐 Creating backup for user: {current_user_id}")
        print(f"🔍 Request data: {data}")
        
        backup_data = data.get('backup_data')
        backup_name = data.get('name', f"Backup {datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        if not backup_data:
            return jsonify({"error": "Backup data is required"}), 400
        
        # Generate backup ID
        backup_id = str(uuid.uuid4())
        
        # Create backup file path
        filename = f"{current_user_id}_{backup_id}.json"
        file_path = os.path.join(BACKUP_STORAGE_PATH, filename)
        
        print(f"🔍 Backup file path: {file_path}")
        
        # Save encrypted backup to file
        with open(file_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        file_size = os.path.getsize(file_path)
        print(f"🔍 Backup file size: {file_size} bytes")
        
        # Debug: Check if BackupDB methods exist
        print(f"🔍 BackupDB methods: {dir(BackupDB)}")
        
        # Create backup record in database using SQL
        print(f"🔍 Calling BackupDB.create_backup with:")
        print(f"   user_id: {current_user_id}")
        print(f"   name: {backup_name}")
        print(f"   filename: {filename}")
        print(f"   file_path: {file_path}")
        print(f"   size_bytes: {file_size}")
        
        backup_record = BackupDB.create_backup(
            user_id=current_user_id,
            name=backup_name,
            filename=filename,
            file_path=file_path,
            size_bytes=file_size,
            checksum=""
        )
        
        print(f"🔍 BackupDB.create_backup returned: {backup_record}")
        
        if backup_record:
            print(f"✅ Backup created successfully: {backup_record.get('id', 'unknown')}")
            return jsonify({
                "message": "Backup created successfully",
                "backup_id": backup_record.get('id'),
                "name": backup_name,
                "created_at": backup_record.get('created_at'),
                "size_bytes": file_size
            }), 201
        else:
            print("❌ BackupDB.create_backup returned None")
            return jsonify({"error": "Failed to create backup record in database"}), 500
        
    except Exception as e:
        print(f"❌ Create backup error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Backup creation failed: {str(e)}"}), 500

@backup_bp.route('/list', methods=['GET'])
@jwt_required()
def list_backups():
    """List all backups for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        print(f"🔍 Getting backups for user: {current_user_id}")
        
        # Debug: Check user exists
        user = UserDB.get_user_by_id(current_user_id)
        print(f"🔍 User found: {user is not None}")
        if user:
            print(f"🔍 User email: {user.get('email', 'unknown')}")
        
        # Get backups using SQL
        user_backups = BackupDB.get_user_backups(current_user_id)
        
        print(f"🔍 Raw backups from DB: {user_backups}")
        
        # Format response
        backups_response = []
        for backup in user_backups:
            print(f"🔍 Processing backup: {backup}")
            backups_response.append({
                'id': backup['id'],
                'name': backup['name'],
                'size_bytes': backup['size_bytes'],
                'created_at': backup['created_at'],
                'status': backup.get('status', 'completed')
            })
        
        print(f"✅ Found {len(backups_response)} backups")
        print(f"🔍 Formatted response: {backups_response}")
        
        return jsonify({"backups": backups_response}), 200
        
    except Exception as e:
        print(f"❌ List backups error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to list backups: {str(e)}"}), 500

@backup_bp.route('/<backup_id>', methods=['GET'])
@jwt_required()
def get_backup(backup_id):
    """Get specific backup by ID"""
    try:
        current_user_id = get_jwt_identity()
        
        # Find the backup
        backup = BackupDB.get_backup_by_id(backup_id, current_user_id)
        if not backup:
            return jsonify({"error": "Backup not found"}), 404
        
        # Read backup file
        with open(backup['file_path'], 'r') as f:
            backup_data = json.load(f)
        
        return jsonify({
            "backup_id": backup['id'],
            "name": backup['name'],
            "created_at": backup['created_at'],
            "backup_data": backup_data
        }), 200
        
    except Exception as e:
        print(f"❌ Get backup error: {e}")
        return jsonify({"error": f"Failed to read backup: {str(e)}"}), 500

@backup_bp.route('/restore', methods=['POST'])
@jwt_required()
def restore_backup():
    """Restore vault from backup"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        backup_id = data.get('backup_id')
        merge_strategy = data.get('merge_strategy', 'replace')
        
        if not backup_id:
            return jsonify({"error": "Backup ID is required"}), 400
        
        # Find the backup
        backup = BackupDB.get_backup_by_id(backup_id, current_user_id)
        if not backup:
            return jsonify({"error": "Backup not found"}), 404
        
        # Read backup file
        with open(backup['file_path'], 'r') as f:
            backup_data = json.load(f)
        
        return jsonify({
            "message": "Backup data retrieved for restore",
            "backup_data": backup_data,
            "restore_info": {
                'backup_id': backup_id,
                'backup_name': backup['name'],
                'merge_strategy': merge_strategy,
                'restored_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Restore backup error: {e}")
        return jsonify({"error": f"Restore failed: {str(e)}"}), 500

@backup_bp.route('/<backup_id>', methods=['DELETE'])
@jwt_required()
def delete_backup(backup_id):
    """Delete a backup"""
    try:
        current_user_id = get_jwt_identity()
        
        # Find the backup
        backup = BackupDB.get_backup_by_id(backup_id, current_user_id)
        if not backup:
            return jsonify({"error": "Backup not found"}), 404
        
        # Delete backup file
        if os.path.exists(backup['file_path']):
            os.remove(backup['file_path'])
        
        # Remove from database
        success = BackupDB.delete_backup(backup_id, current_user_id)
        
        if success:
            return jsonify({"message": "Backup deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete backup from database"}), 500
        
    except Exception as e:
        print(f"❌ Delete backup error: {e}")
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500

# Add this debug endpoint
@backup_bp.route('/debug', methods=['GET'])
@jwt_required()
def debug_backups():
    """Debug endpoint to check backup table and data"""
    try:
        current_user_id = get_jwt_identity()
        
        # Debug table info
        BackupDB.debug_table_info()
        
        # Get user info
        user = UserDB.get_user_by_id(current_user_id)
        
        debug_info = {
            'current_user_id': current_user_id,
            'user_found': user is not None,
            'user_email': user.get('email') if user else None,
            'backup_table_methods': [method for method in dir(BackupDB) if not method.startswith('_')]
        }
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        return jsonify({"error": str(e)}), 500