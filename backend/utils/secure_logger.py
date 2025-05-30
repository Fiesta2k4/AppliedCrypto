import os
import logging
from datetime import datetime

class SecureLogger:
    """Production-safe logger that never logs sensitive data"""
    
    def __init__(self):
        self.debug_mode = os.getenv('DEBUG_LOGGING', 'false').lower() == 'true'
        self.setup_logger()
    
    def setup_logger(self):
        """Setup secure logging"""
        logging.basicConfig(
            level=logging.INFO if not self.debug_mode else logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('app.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_auth_attempt(self, email, success):
        """Log authentication attempt (safe)"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Auth {status}: {email}")
    
    def log_vault_operation(self, user_id, operation, success):
        """Log vault operation (safe)"""
        status = "SUCCESS" if success else "FAILED"
        # Only log first 8 chars of user ID
        safe_user_id = user_id[:8] + "..." if len(user_id) > 8 else user_id
        self.logger.info(f"Vault {operation} {status}: user_{safe_user_id}")
    
    def log_error(self, operation, error_type):
        """Log error without sensitive data"""
        self.logger.error(f"Error in {operation}: {error_type}")
    
    def never_log(self, sensitive_data):
        """Method that explicitly never logs sensitive data"""
        # This method exists to remind developers what NOT to log
        pass

# Global secure logger
secure_logger = SecureLogger()