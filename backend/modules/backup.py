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
    """
    Create encrypted backup of user's vault
    Theory: Client-side encrypted backup for data portability
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    backup_data = data.get('backup_data')  # Encrypted vault data from client
    backup_name = data.get('name', f"Backup {datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    if not backup_data:
        return jsonify({"error": "Backup data is required"}), 400
    
    try:
        # Generate backup ID
        backup_id = str(uuid.uuid4())
        
        # Create backup file path
        filename = f"{current_user}_{backup_id}.json"
        file_path = os.path.join(BACKUP_STORAGE_PATH, filename)
        
        # Save encrypted backup to file
        with open(file_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        # Create backup metadata
        backup_metadata = {
            'id': backup_id,
            'user_email': current_user,
            'name': backup_name,
            'filename': filename,
            'file_path': file_path,
            'size_bytes': os.path.getsize(file_path),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'completed'
        }
        
        # Save metadata to database
        BackupDB.insert_one(backup_metadata)
        
        return jsonify({
            "message": "Backup created successfully",
            "backup_id": backup_id,
            "name": backup_name,
            "created_at": backup_metadata['created_at']
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Backup creation failed: {str(e)}"}), 500

@backup_bp.route('/list', methods=['GET'])
@jwt_required()
def list_backups():
    """List all backups for current user"""
    current_user = get_jwt_identity()
    
    # Filter backups for current user
    user_backups = [
        {
            'id': backup['id'],
            'name': backup['name'],
            'size_bytes': backup['size_bytes'],
            'created_at': backup['created_at'],
            'status': backup['status']
        }
        for backup in BackupDB.find({"user_email": current_user})
    ]
    
    # Sort by creation date (newest first)
    user_backups.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({"backups": user_backups}), 200

@backup_bp.route('/latest', methods=['GET'])
@jwt_required()
def get_latest_backup():
    """Get the latest backup for current user"""
    current_user = get_jwt_identity()
    
    # Find latest backup
    user_backups = [
        backup for backup in BackupDB.find({"user_email": current_user})
    ]
    
    if not user_backups:
        return jsonify({"error": "No backups found"}), 404
    
    latest_backup = max(user_backups, key=lambda x: x['created_at'])
    
    try:
        # Read backup file
        with open(latest_backup['file_path'], 'r') as f:
            backup_data = json.load(f)
        
        return jsonify({
            "backup_id": latest_backup['id'],
            "name": latest_backup['name'],
            "created_at": latest_backup['created_at'],
            "backup_data": backup_data
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to read backup: {str(e)}"}), 500

@backup_bp.route('/<backup_id>', methods=['GET'])
@jwt_required()
def get_backup(backup_id):
    """Get specific backup by ID"""
    current_user = get_jwt_identity()
    
    # Find the backup
    backup = BackupDB.find_one({"id": backup_id})
    if not backup:
        return jsonify({"error": "Backup not found"}), 404
    
    if backup['user_email'] != current_user:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
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
        return jsonify({"error": f"Failed to read backup: {str(e)}"}), 500

@backup_bp.route('/restore', methods=['POST'])
@jwt_required()
def restore_backup():
    """
    Restore vault from backup
    Theory: Client handles decryption and merging with existing data
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    backup_id = data.get('backup_id')
    merge_strategy = data.get('merge_strategy', 'replace')  # 'replace' or 'merge'
    
    if not backup_id:
        return jsonify({"error": "Backup ID is required"}), 400
    
    # Find the backup
    backup = BackupDB.find_one({"id": backup_id})
    if not backup:
        return jsonify({"error": "Backup not found"}), 404
    
    if backup['user_email'] != current_user:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        # Read backup file
        with open(backup['file_path'], 'r') as f:
            backup_data = json.load(f)
        
        # Log restore operation
        restore_record = {
            'user_email': current_user,
            'backup_id': backup_id,
            'backup_name': backup['name'],
            'merge_strategy': merge_strategy,
            'restored_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            "message": "Backup data retrieved for restore",
            "backup_data": backup_data,
            "restore_info": restore_record
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Restore failed: {str(e)}"}), 500

@backup_bp.route('/<backup_id>', methods=['DELETE'])
@jwt_required()
def delete_backup(backup_id):
    """Delete a backup"""
    current_user = get_jwt_identity()
    
    # Find the backup
    backup = BackupDB.find_one({"id": backup_id})
    if not backup:
        return jsonify({"error": "Backup not found"}), 404
    
    if backup['user_email'] != current_user:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        # Delete backup file
        if os.path.exists(backup['file_path']):
            os.remove(backup['file_path'])
        
        # Remove from database
        BackupDB.delete_one({"id": backup_id})
        
        return jsonify({"message": "Backup deleted successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500

@backup_bp.route('/cleanup', methods=['POST'])
@jwt_required()
def cleanup_old_backups():
    """Clean up old backups (keep only latest N backups)"""
    current_user = get_jwt_identity()
    data = request.get_json()
    
    keep_count = data.get('keep_count', 5)  # Default keep 5 latest backups
    
    # Get user's backups sorted by date
    user_backups = [
        backup for backup in BackupDB.find({"user_email": current_user})
    ]
    user_backups.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Delete old backups
    deleted_count = 0
    for backup in user_backups[keep_count:]:
        try:
            if os.path.exists(backup['file_path']):
                os.remove(backup['file_path'])
            BackupDB.delete_one({"id": backup['id']})
            deleted_count += 1
        except Exception as e:
            print(f"Failed to delete backup {backup['id']}: {e}")
    
    return jsonify({
        "message": f"Cleanup completed",
        "deleted_count": deleted_count,
        "remaining_count": len(user_backups[:keep_count])
    }), 200