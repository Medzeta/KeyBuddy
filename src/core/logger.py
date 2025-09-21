"""
User activity logging system
"""
from datetime import datetime
from typing import Optional

class UserLogger:
    """Handles user activity logging"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def log_activity(self, user_id: int, activity_type: str, details: str = None, ip_address: str = None):
        """Log user activity to database"""
        try:
            self.db_manager.execute_update(
                """INSERT INTO user_logs (user_id, activity_type, details, ip_address, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, activity_type, details, ip_address, datetime.now().isoformat())
            )
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    def log_login(self, user_id: int, username: str, ip_address: str = None):
        """Log user login"""
        self.log_activity(user_id, "LOGIN", f"Användare {username} loggade in", ip_address)
    
    def log_logout(self, user_id: int, username: str, ip_address: str = None):
        """Log user logout"""
        self.log_activity(user_id, "LOGOUT", f"Användare {username} loggade ut", ip_address)
    
    def log_user_created(self, admin_user_id: int, new_username: str, ip_address: str = None):
        """Log user creation"""
        self.log_activity(admin_user_id, "USER_CREATED", f"Skapade ny användare: {new_username}", ip_address)
    
    def log_user_updated(self, admin_user_id: int, updated_username: str, ip_address: str = None):
        """Log user update"""
        self.log_activity(admin_user_id, "USER_UPDATED", f"Uppdaterade användare: {updated_username}", ip_address)
    
    def log_user_deleted(self, admin_user_id: int, deleted_username: str, ip_address: str = None):
        """Log user deletion"""
        self.log_activity(admin_user_id, "USER_DELETED", f"Raderade användare: {deleted_username}", ip_address)
    
    def log_system_access(self, user_id: int, system_name: str, ip_address: str = None):
        """Log system access"""
        self.log_activity(user_id, "SYSTEM_ACCESS", f"Åtkomst till system: {system_name}", ip_address)
    
    def log_order_created(self, user_id: int, order_details: str, ip_address: str = None):
        """Log order creation"""
        self.log_activity(user_id, "ORDER_CREATED", f"Skapade beställning: {order_details}", ip_address)
    
    def log_backup_created(self, user_id: int, backup_name: str, ip_address: str = None):
        """Log backup creation"""
        self.log_activity(user_id, "BACKUP_CREATED", f"Skapade backup: {backup_name}", ip_address)
    
    def log_settings_changed(self, user_id: int, setting_name: str, ip_address: str = None):
        """Log settings change"""
        self.log_activity(user_id, "SETTINGS_CHANGED", f"Ändrade inställning: {setting_name}", ip_address)
