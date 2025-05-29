from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from database.config import UserDB, BackupDB, VaultDB

backup_bp = Blueprint('backup', __name__)

# Ensure backup directory exists
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
        print(f"🔍 Request data keys: {list(data.keys()) if data else 'None'}")
        
        backup_data = data.get('backup_data')
        
        # ✅ FIX: Handle None name and provide proper default
        backup_name = data.get('name')
        if not backup_name or backup_name.strip() == "":
            backup_name = f"Backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"🔍 Backup name (fixed): '{backup_name}'")
        
        if not backup_data:
            print("❌ No backup data provided")
            return jsonify({"error": "Backup data is required"}), 400
        
        print(f"🔍 Backup data type: {type(backup_data)}")
        
        # Generate backup ID and filename
        backup_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{current_user_id}_{timestamp}_{backup_id[:8]}.json"
        
        # ✅ FIX: Use proper path separator
        file_path = os.path.normpath(os.path.join(BACKUP_STORAGE_PATH, filename))
        
        print(f"🔍 Backup file path: {file_path}")
        
        # Ensure backup directory exists
        os.makedirs(BACKUP_STORAGE_PATH, exist_ok=True)
        
        # Save backup data to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Backup file written successfully")
        except Exception as write_error:
            print(f"❌ Failed to write backup file: {write_error}")
            return jsonify({"error": f"Failed to write backup file: {str(write_error)}"}), 500
        
        # Get file size
        try:
            file_size = os.path.getsize(file_path)
            print(f"🔍 Backup file size: {file_size} bytes")
        except Exception as size_error:
            print(f"⚠️ Could not get file size: {size_error}")
            file_size = 0
        
        # ✅ FIX: Validate all parameters before database insert
        print(f"🔍 Creating backup record with validated data:")
        print(f"   user_id: '{current_user_id}' (length: {len(current_user_id)})")
        print(f"   name: '{backup_name}' (length: {len(backup_name)})")
        print(f"   filename: '{filename}' (length: {len(filename)})")
        print(f"   file_path: '{file_path}' (length: {len(file_path)})")
        print(f"   size_bytes: {file_size}")
        
        # Validate required fields
        if not current_user_id or len(current_user_id.strip()) == 0:
            raise ValueError("Invalid user_id")
        if not backup_name or len(backup_name.strip()) == 0:
            raise ValueError("Invalid backup name")
        if not filename or len(filename.strip()) == 0:
            raise ValueError("Invalid filename")
        if not file_path or len(file_path.strip()) == 0:
            raise ValueError("Invalid file_path")
        
        # Create backup record in database
        backup_record = BackupDB.create_backup(
            user_id=current_user_id.strip(),
            name=backup_name.strip(),
            filename=filename.strip(), 
            file_path=file_path.strip(),
            size_bytes=file_size
        )
        
        if backup_record:
            print(f"✅ Backup created successfully: {backup_record['id']}")
            return jsonify({
                "success": True,
                "message": "Backup created successfully",
                "backup_id": backup_record['id'],
                "name": backup_name,
                "filename": filename,
                "created_at": backup_record.get('created_at'),
                "size_bytes": file_size
            }), 201
        else:
            print("❌ Failed to create backup record in database")
            # Clean up file if database insert failed
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🔧 Cleaned up backup file: {file_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to cleanup backup file: {cleanup_error}")
            
            return jsonify({"error": "Failed to create backup record in database"}), 500
        
    except ValueError as ve:
        print(f"❌ Validation error: {ve}")
        return jsonify({"error": f"Validation error: {str(ve)}"}), 400
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
        
        print(f"🔍 Listing backups for user: {current_user_id}")
        
        # Verify user exists
        user = UserDB.get_user_by_id(current_user_id)
        if not user:
            print(f"❌ User not found: {current_user_id}")
            return jsonify({"error": "User not found"}), 404
        
        print(f"✅ User found: {user['email']}")
        
        # Get user backups
        user_backups = BackupDB.get_user_backups(current_user_id)
        print(f"🔍 Raw backups from DB: {len(user_backups)} items")
        
        # Format response with file verification
        backups_response = []
        for backup in user_backups:
            print(f"🔍 Processing backup: {backup['name']}")
            
            # Check if backup file still exists
            file_exists = os.path.exists(backup['file_path'])
            actual_size = 0
            
            if file_exists:
                try:
                    actual_size = os.path.getsize(backup['file_path'])
                except:
                    file_exists = False
            
            backup_info = {
                'id': backup['id'],
                'name': backup['name'],
                'filename': backup['filename'],
                'size_bytes': backup['size_bytes'],
                'actual_size': actual_size,
                'file_exists': file_exists,
                'created_at': backup['created_at'],
                'status': backup.get('status', 'completed')
            }
            
            backups_response.append(backup_info)
            print(f"   ✅ Added to response: {backup['name']}")
        
        print(f"✅ Returning {len(backups_response)} backups")
        
        return jsonify({
            "success": True,
            "backups": backups_response,
            "count": len(backups_response)
        }), 200
        
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
        
        print(f"🔍 Getting backup {backup_id} for user {current_user_id}")
        
        # Find the backup
        backup = BackupDB.get_backup_by_id(backup_id, current_user_id)
        if not backup:
            print(f"❌ Backup not found: {backup_id}")
            return jsonify({"error": "Backup not found"}), 404
        
        print(f"✅ Backup found: {backup['name']}")
        
        # Check if file exists
        if not os.path.exists(backup['file_path']):
            print(f"❌ Backup file not found: {backup['file_path']}")
            return jsonify({"error": "Backup file not found"}), 404
        
        # Read backup file
        try:
            with open(backup['file_path'], 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            print(f"✅ Backup file loaded successfully")
        except Exception as read_error:
            print(f"❌ Failed to read backup file: {read_error}")
            return jsonify({"error": f"Failed to read backup file: {str(read_error)}"}), 500
        
        return jsonify({
            "success": True,
            "backup_id": backup['id'],
            "name": backup['name'],
            "filename": backup['filename'],
            "created_at": backup['created_at'],
            "size_bytes": backup['size_bytes'],
            "backup_data": backup_data
        }), 200
        
    except Exception as e:
        print(f"❌ Get backup error: {e}")
        import traceback
        traceback.print_exc()
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
        
        print(f"🔍 Restoring backup {backup_id} with strategy: {merge_strategy}")
        
        if not backup_id:
            return jsonify({"error": "Backup ID is required"}), 400
        
        # Get backup
        backup_response = get_backup(backup_id)
        if backup_response[1] != 200:
            return backup_response
        
        backup_data = backup_response[0].get_json()['backup_data']
        
        # Return backup data for client-side restore
        return jsonify({
            "success": True,
            "message": "Backup data retrieved for restore",
            "backup_data": backup_data,
            "restore_info": {
                'backup_id': backup_id,
                'merge_strategy': merge_strategy,
                'restored_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Restore backup error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Restore failed: {str(e)}"}), 500

@backup_bp.route('/<backup_id>/download', methods=['GET'])
@jwt_required()
def download_backup(backup_id):
    """Download backup file"""
    try:
        current_user_id = get_jwt_identity()
        
        # Find the backup
        backup = BackupDB.get_backup_by_id(backup_id, current_user_id)
        if not backup:
            return jsonify({"error": "Backup not found"}), 404
        
        # Check if file exists
        if not os.path.exists(backup['file_path']):
            return jsonify({"error": "Backup file not found"}), 404
        
        # Send file
        return send_file(
            backup['file_path'],
            as_attachment=True,
            download_name=backup['filename'],
            mimetype='application/json'
        )
        
    except Exception as e:
        print(f"❌ Download backup error: {e}")
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

@backup_bp.route('/<backup_id>', methods=['DELETE'])
@jwt_required()
def delete_backup(backup_id):
    """Delete a backup"""
    try:
        current_user_id = get_jwt_identity()
        
        print(f"🔍 Deleting backup {backup_id} for user {current_user_id}")
        
        # Find the backup
        backup = BackupDB.get_backup_by_id(backup_id, current_user_id)
        if not backup:
            print(f"❌ Backup not found: {backup_id}")
            return jsonify({"error": "Backup not found"}), 404
        
        print(f"✅ Backup found: {backup['name']}")
        
        # Delete backup file
        if os.path.exists(backup['file_path']):
            try:
                os.remove(backup['file_path'])
                print(f"✅ Backup file deleted: {backup['file_path']}")
            except Exception as file_error:
                print(f"⚠️ Failed to delete backup file: {file_error}")
        
        # Remove from database
        success = BackupDB.delete_backup(backup_id, current_user_id)
        
        if success:
            print(f"✅ Backup record deleted from database")
            return jsonify({
                "success": True,
                "message": "Backup deleted successfully"
            }), 200
        else:
            print(f"❌ Failed to delete backup record from database")
            return jsonify({"error": "Failed to delete backup"}), 500
        
    except Exception as e:
        print(f"❌ Delete backup error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500

@backup_bp.route('/stats', methods=['GET'])
@jwt_required()
def backup_stats():
    """Get backup statistics"""
    try:
        current_user_id = get_jwt_identity()
        
        backups = BackupDB.get_user_backups(current_user_id)
        
        total_size = sum(backup['size_bytes'] for backup in backups)
        
        return jsonify({
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_backup": backups[-1]['created_at'] if backups else None,
            "newest_backup": backups[0]['created_at'] if backups else None
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500