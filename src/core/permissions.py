"""
System permissions and user role management
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from .database import DatabaseManager

class UserRole(Enum):
    """User roles with different permission levels"""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"

class Permission(Enum):
    """System permissions"""
    # Customer management
    CREATE_CUSTOMER = "create_customer"
    EDIT_CUSTOMER = "edit_customer"
    DELETE_CUSTOMER = "delete_customer"
    VIEW_CUSTOMER = "view_customer"
    
    # Key system management
    CREATE_KEY_SYSTEM = "create_key_system"
    EDIT_KEY_SYSTEM = "edit_key_system"
    DELETE_KEY_SYSTEM = "delete_key_system"
    VIEW_KEY_SYSTEM = "view_key_system"
    
    # Order management
    CREATE_ORDER = "create_order"
    EDIT_ORDER = "edit_order"
    DELETE_ORDER = "delete_order"
    VIEW_ORDER = "view_order"
    EXPORT_ORDER = "export_order"
    PRINT_ORDER = "print_order"
    
    # User management
    CREATE_USER = "create_user"
    EDIT_USER = "edit_user"
    DELETE_USER = "delete_user"
    VIEW_USER = "view_user"
    MANAGE_PERMISSIONS = "manage_permissions"
    
    # System settings
    MANAGE_SETTINGS = "manage_settings"
    BACKUP_DATABASE = "backup_database"
    RESTORE_DATABASE = "restore_database"

class PermissionManager:
    """Manages user permissions and role-based access control"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._role_permissions = self._initialize_role_permissions()
    
    def _initialize_role_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Initialize default permissions for each role"""
        return {
            UserRole.ADMIN: [
                # Full access to everything
                Permission.CREATE_CUSTOMER, Permission.EDIT_CUSTOMER, 
                Permission.DELETE_CUSTOMER, Permission.VIEW_CUSTOMER,
                Permission.CREATE_KEY_SYSTEM, Permission.EDIT_KEY_SYSTEM,
                Permission.DELETE_KEY_SYSTEM, Permission.VIEW_KEY_SYSTEM,
                Permission.CREATE_ORDER, Permission.EDIT_ORDER,
                Permission.DELETE_ORDER, Permission.VIEW_ORDER,
                Permission.EXPORT_ORDER, Permission.PRINT_ORDER,
                Permission.CREATE_USER, Permission.EDIT_USER,
                Permission.DELETE_USER, Permission.VIEW_USER,
                Permission.MANAGE_PERMISSIONS, Permission.MANAGE_SETTINGS,
                Permission.BACKUP_DATABASE, Permission.RESTORE_DATABASE
            ],
            UserRole.MANAGER: [
                # Customer and system management
                Permission.CREATE_CUSTOMER, Permission.EDIT_CUSTOMER, Permission.VIEW_CUSTOMER,
                Permission.CREATE_KEY_SYSTEM, Permission.EDIT_KEY_SYSTEM, Permission.VIEW_KEY_SYSTEM,
                Permission.CREATE_ORDER, Permission.EDIT_ORDER, Permission.VIEW_ORDER,
                Permission.EXPORT_ORDER, Permission.PRINT_ORDER,
                Permission.VIEW_USER, Permission.BACKUP_DATABASE
            ],
            UserRole.USER: [
                # Basic operations
                Permission.VIEW_CUSTOMER, Permission.VIEW_KEY_SYSTEM,
                Permission.CREATE_ORDER, Permission.VIEW_ORDER,
                Permission.EXPORT_ORDER, Permission.PRINT_ORDER
            ],
            UserRole.VIEWER: [
                # Read-only access
                Permission.VIEW_CUSTOMER, Permission.VIEW_KEY_SYSTEM,
                Permission.VIEW_ORDER
            ]
        }
    
    def get_user_role(self, user_id: int) -> Optional[UserRole]:
        """Get user's role from database"""
        try:
            query = "SELECT role FROM users WHERE id = ?"
            result = self.db_manager.execute_query(query, (user_id,))
            if result:
                role_str = result[0][0]
                return UserRole(role_str) if role_str else UserRole.USER
            return None
        except Exception:
            return None
    
    def set_user_role(self, user_id: int, role: UserRole, granted_by: int) -> bool:
        """Set user's role in database"""
        try:
            # Update user role
            update_query = "UPDATE users SET role = ? WHERE id = ?"
            self.db_manager.execute_update(update_query, (role.value, user_id))
            
            # Log permission change
            log_query = """
                INSERT INTO permissions (user_id, permission_type, granted_by)
                VALUES (?, ?, ?)
            """
            self.db_manager.execute_update(log_query, (user_id, f"role_change_{role.value}", granted_by))
            return True
        except Exception:
            return False
    
    def has_permission(self, user_id: int, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user_role = self.get_user_role(user_id)
        if not user_role:
            return False
        
        # Check role-based permissions
        role_permissions = self._role_permissions.get(user_role, [])
        if permission in role_permissions:
            return True
        
        # Check individual permissions from database
        try:
            query = """
                SELECT COUNT(*) FROM permissions 
                WHERE user_id = ? AND permission_type = ?
            """
            result = self.db_manager.execute_query(query, (user_id, permission.value))
            return result and result[0][0] > 0
        except Exception:
            return False
    
    def grant_permission(self, user_id: int, permission: Permission, granted_by: int) -> bool:
        """Grant specific permission to user"""
        try:
            query = """
                INSERT OR IGNORE INTO permissions (user_id, permission_type, granted_by)
                VALUES (?, ?, ?)
            """
            self.db_manager.execute_update(query, (user_id, permission.value, granted_by))
            return True
        except Exception:
            return False
    
    def revoke_permission(self, user_id: int, permission: Permission) -> bool:
        """Revoke specific permission from user"""
        try:
            query = "DELETE FROM permissions WHERE user_id = ? AND permission_type = ?"
            self.db_manager.execute_update(query, (user_id, permission.value))
            return True
        except Exception:
            return False
    
    def get_user_permissions(self, user_id: int) -> List[Permission]:
        """Get all permissions for a user (role-based + individual)"""
        permissions = set()
        
        # Add role-based permissions
        user_role = self.get_user_role(user_id)
        if user_role:
            role_permissions = self._role_permissions.get(user_role, [])
            permissions.update(role_permissions)
        
        # Add individual permissions
        try:
            query = "SELECT permission_type FROM permissions WHERE user_id = ?"
            results = self.db_manager.execute_query(query, (user_id,))
            for result in results:
                try:
                    perm = Permission(result[0])
                    permissions.add(perm)
                except ValueError:
                    # Skip invalid permissions
                    continue
        except Exception:
            pass
        
        return list(permissions)
    
    def can_access_feature(self, user_id: int, feature: str) -> bool:
        """Check if user can access a specific feature"""
        feature_permissions = {
            'customers': [Permission.VIEW_CUSTOMER],
            'key_systems': [Permission.VIEW_KEY_SYSTEM],
            'orders': [Permission.VIEW_ORDER],
            'users': [Permission.VIEW_USER],
            'settings': [Permission.MANAGE_SETTINGS],
            'create_customer': [Permission.CREATE_CUSTOMER],
            'edit_customer': [Permission.EDIT_CUSTOMER],
            'delete_customer': [Permission.DELETE_CUSTOMER],
            'create_key_system': [Permission.CREATE_KEY_SYSTEM],
            'edit_key_system': [Permission.EDIT_KEY_SYSTEM],
            'delete_key_system': [Permission.DELETE_KEY_SYSTEM],
            'create_order': [Permission.CREATE_ORDER],
            'edit_order': [Permission.EDIT_ORDER],
            'delete_order': [Permission.DELETE_ORDER],
            'export_order': [Permission.EXPORT_ORDER],
            'print_order': [Permission.PRINT_ORDER],
        }
        
        required_permissions = feature_permissions.get(feature, [])
        return any(self.has_permission(user_id, perm) for perm in required_permissions)
    
    def get_role_display_name(self, role: UserRole) -> str:
        """Get display name for role"""
        role_names = {
            UserRole.ADMIN: "Administratör",
            UserRole.MANAGER: "Chef",
            UserRole.USER: "Användare",
            UserRole.VIEWER: "Läsare"
        }
        return role_names.get(role, "Okänd")
    
    def get_permission_display_name(self, permission: Permission) -> str:
        """Get display name for permission"""
        permission_names = {
            Permission.CREATE_CUSTOMER: "Skapa kunder",
            Permission.EDIT_CUSTOMER: "Redigera kunder",
            Permission.DELETE_CUSTOMER: "Ta bort kunder",
            Permission.VIEW_CUSTOMER: "Visa kunder",
            Permission.CREATE_KEY_SYSTEM: "Skapa nyckelsystem",
            Permission.EDIT_KEY_SYSTEM: "Redigera nyckelsystem",
            Permission.DELETE_KEY_SYSTEM: "Ta bort nyckelsystem",
            Permission.VIEW_KEY_SYSTEM: "Visa nyckelsystem",
            Permission.CREATE_ORDER: "Skapa ordrar",
            Permission.EDIT_ORDER: "Redigera ordrar",
            Permission.DELETE_ORDER: "Ta bort ordrar",
            Permission.VIEW_ORDER: "Visa ordrar",
            Permission.EXPORT_ORDER: "Exportera ordrar",
            Permission.PRINT_ORDER: "Skriva ut ordrar",
            Permission.CREATE_USER: "Skapa användare",
            Permission.EDIT_USER: "Redigera användare",
            Permission.DELETE_USER: "Ta bort användare",
            Permission.VIEW_USER: "Visa användare",
            Permission.MANAGE_PERMISSIONS: "Hantera behörigheter",
            Permission.MANAGE_SETTINGS: "Hantera inställningar",
            Permission.BACKUP_DATABASE: "Säkerhetskopiera databas",
            Permission.RESTORE_DATABASE: "Återställa databas"
        }
        return permission_names.get(permission, permission.value)
