"""
User permissions and role management window
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QComboBox,
                               QPushButton, QGroupBox, QFormLayout, QCheckBox,
                               QMessageBox, QHeaderView, QAbstractItemView,
                               QScrollArea, QSizePolicy, QFrame)
from PySide6.QtCore import Qt, Signal
from ..core.permissions import PermissionManager, UserRole, Permission
from .styles import AnimatedButton
from .copyable_message_box import CopyableMessageBox

class PermissionsWindow(QWidget):
    """Window for managing user permissions and roles"""
    
    navigate_home = Signal()
    
    def __init__(self, db_manager, app_manager, translation_manager):
        super().__init__()
        self.db_manager = db_manager
        self.app_manager = app_manager
        self.translation_manager = translation_manager
        self.permission_manager = PermissionManager(db_manager)
        self.current_user = app_manager.get_current_user()
        
        self.setup_ui()
        self.load_users()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Användarhantering & Behörigheter")
        title.setProperty("class", "page-title")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Navigation buttons
        home_btn = AnimatedButton("Hem")
        home_btn.clicked.connect(self.navigate_home.emit)
        home_btn.setProperty("class", "secondary")
        header_layout.addWidget(home_btn)
        
        layout.addLayout(header_layout)
        
        # Main content with scroll area
        content_layout = QHBoxLayout()
        
        # Left side - Users table (flyttad till toppen)
        users_group = QGroupBox("Användare")
        users_group.setMaximumWidth(500)  # Begränsa bredd
        users_layout = QVBoxLayout(users_group)
        
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["Användarnamn", "E-post", "Roll", "Senast inloggad"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.users_table.itemSelectionChanged.connect(self.on_user_selected)
        self.users_table.setMinimumHeight(150)  # Minimum höjd istället för maximum
        
        users_layout.addWidget(self.users_table)
        # Lägg användartabellen överst i layout
        layout.addWidget(users_group)
        
        # Role and permissions management med bättre layout
        management_widget = QWidget()
        management_layout = QVBoxLayout(management_widget)
        
        # Role management (kompaktare med horisontell layout)
        role_group = QGroupBox("Rollhantering")
        role_group.setMaximumHeight(120)  # Mindre höjd
        role_main_layout = QVBoxLayout(role_group)
        
        # Vald användare
        self.selected_user_label = QLabel("Ingen användare vald")
        self.selected_user_label.setWordWrap(True)
        self.selected_user_label.setStyleSheet("font-weight: bold; color: #2196F3; margin: 4px;")
        role_main_layout.addWidget(self.selected_user_label)
        
        # Horisontell layout för roll och knapp
        role_controls_layout = QHBoxLayout()
        role_controls_layout.setSpacing(8)
        
        # Roll label och combo
        role_label = QLabel("Roll:")
        role_label.setMinimumWidth(35)
        role_controls_layout.addWidget(role_label)
        
        self.role_combo = QComboBox()
        self.role_combo.setMaximumWidth(150)  # Begränsa bredd
        for role in UserRole:
            display_name = self.permission_manager.get_role_display_name(role)
            self.role_combo.addItem(display_name, role)
        self.role_combo.currentIndexChanged.connect(self.on_role_changed)
        role_controls_layout.addWidget(self.role_combo)
        
        # Spara roll knapp (smal)
        self.save_role_btn = AnimatedButton("Spara")
        self.save_role_btn.setMaximumWidth(60)  # Smal knapp
        self.save_role_btn.clicked.connect(self.save_user_role)
        self.save_role_btn.setEnabled(False)
        role_controls_layout.addWidget(self.save_role_btn)
        
        role_controls_layout.addStretch()  # Push allt åt vänster
        role_main_layout.addLayout(role_controls_layout)
        
        management_layout.addWidget(role_group)
        
        # Individual permissions med scroll
        permissions_scroll = QScrollArea()
        permissions_scroll.setWidgetResizable(True)
        permissions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        permissions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        permissions_widget = QWidget()
        permissions_layout = QVBoxLayout(permissions_widget)
        
        # Create checkboxes for each permission category
        self.permission_checkboxes = {}
        
        # Customer permissions (kompaktare)
        customer_group = QGroupBox("Kunder")
        customer_group.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 6px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }")
        customer_layout = QVBoxLayout(customer_group)
        customer_layout.setSpacing(2)  # Mindre mellanrum
        customer_permissions = [
            Permission.CREATE_CUSTOMER, Permission.EDIT_CUSTOMER,
            Permission.DELETE_CUSTOMER, Permission.VIEW_CUSTOMER
        ]
        for perm in customer_permissions:
            checkbox = QCheckBox(self.permission_manager.get_permission_display_name(perm))
            checkbox.stateChanged.connect(self.on_permission_changed)
            checkbox.setStyleSheet("QCheckBox { margin: 2px; }")
            self.permission_checkboxes[perm] = checkbox
            customer_layout.addWidget(checkbox)
        permissions_layout.addWidget(customer_group)
        
        # Key system permissions (kompaktare)
        system_group = QGroupBox("Nyckelsystem")
        system_group.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 6px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }")
        system_layout = QVBoxLayout(system_group)
        system_layout.setSpacing(2)
        system_permissions = [
            Permission.CREATE_KEY_SYSTEM, Permission.EDIT_KEY_SYSTEM,
            Permission.DELETE_KEY_SYSTEM, Permission.VIEW_KEY_SYSTEM
        ]
        for perm in system_permissions:
            checkbox = QCheckBox(self.permission_manager.get_permission_display_name(perm))
            checkbox.stateChanged.connect(self.on_permission_changed)
            checkbox.setStyleSheet("QCheckBox { margin: 2px; }")
            self.permission_checkboxes[perm] = checkbox
            system_layout.addWidget(checkbox)
        permissions_layout.addWidget(system_group)
        
        # Order permissions (kompaktare)
        order_group = QGroupBox("Ordrar")
        order_group.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 6px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }")
        order_layout = QVBoxLayout(order_group)
        order_layout.setSpacing(2)
        order_permissions = [
            Permission.CREATE_ORDER, Permission.EDIT_ORDER, Permission.DELETE_ORDER,
            Permission.VIEW_ORDER, Permission.EXPORT_ORDER, Permission.PRINT_ORDER
        ]
        for perm in order_permissions:
            checkbox = QCheckBox(self.permission_manager.get_permission_display_name(perm))
            checkbox.stateChanged.connect(self.on_permission_changed)
            checkbox.setStyleSheet("QCheckBox { margin: 2px; }")
            self.permission_checkboxes[perm] = checkbox
            order_layout.addWidget(checkbox)
        permissions_layout.addWidget(order_group)
        
        # System permissions (only for admins, kompaktare)
        if self.current_user and self.permission_manager.has_permission(
            self.current_user['user_id'], Permission.MANAGE_PERMISSIONS
        ):
            admin_group = QGroupBox("Systemhantering")
            admin_group.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 6px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }")
            admin_layout = QVBoxLayout(admin_group)
            admin_layout.setSpacing(2)
            admin_permissions = [
                Permission.CREATE_USER, Permission.EDIT_USER, Permission.DELETE_USER,
                Permission.VIEW_USER, Permission.MANAGE_PERMISSIONS, Permission.MANAGE_SETTINGS,
                Permission.BACKUP_DATABASE, Permission.RESTORE_DATABASE
            ]
            for perm in admin_permissions:
                checkbox = QCheckBox(self.permission_manager.get_permission_display_name(perm))
                checkbox.stateChanged.connect(self.on_permission_changed)
                checkbox.setStyleSheet("QCheckBox { margin: 2px; }")
                self.permission_checkboxes[perm] = checkbox
                admin_layout.addWidget(checkbox)
            permissions_layout.addWidget(admin_group)
        
        # Save permissions button (smal)
        permissions_button_layout = QHBoxLayout()
        self.save_permissions_btn = AnimatedButton("Spara")
        self.save_permissions_btn.setMaximumWidth(60)  # Smal knapp som texten
        self.save_permissions_btn.clicked.connect(self.save_permissions)
        self.save_permissions_btn.setEnabled(False)
        permissions_button_layout.addWidget(self.save_permissions_btn)
        permissions_button_layout.addStretch()  # Push knappen åt vänster
        permissions_layout.addLayout(permissions_button_layout)
        
        # Sätt permissions widget i scroll area
        permissions_scroll.setWidget(permissions_widget)
        management_layout.addWidget(permissions_scroll)
        
        # Lägg till management widget i main layout
        layout.addWidget(management_widget)
        
        # Enable/disable controls based on admin permissions
        self.is_admin = (self.current_user and 
                        self.permission_manager.has_permission(
                            self.current_user['user_id'], Permission.MANAGE_PERMISSIONS
                        ))
        
        if not self.is_admin:
            self.role_combo.setEnabled(False)
            self.save_role_btn.setEnabled(False)
            for checkbox in self.permission_checkboxes.values():
                checkbox.setEnabled(False)
            self.save_permissions_btn.setEnabled(False)
        else:
            # Admin kan alltid redigera
            self.role_combo.setEnabled(True)
            for checkbox in self.permission_checkboxes.values():
                checkbox.setEnabled(True)
    
    def load_users(self):
        """Load users from database"""
        try:
            query = """
                SELECT id, username, email, role, last_login
                FROM users
                ORDER BY username
            """
            users = self.db_manager.execute_query(query)
            
            self.users_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                user_id, username, email, role, last_login = user
                
                self.users_table.setItem(row, 0, QTableWidgetItem(username))
                self.users_table.setItem(row, 1, QTableWidgetItem(email))
                
                # Display role name
                try:
                    user_role = UserRole(role) if role else UserRole.USER
                    role_display = self.permission_manager.get_role_display_name(user_role)
                except ValueError:
                    role_display = "Okänd"
                self.users_table.setItem(row, 2, QTableWidgetItem(role_display))
                
                # Format last login
                last_login_text = last_login if last_login else "Aldrig"
                self.users_table.setItem(row, 3, QTableWidgetItem(last_login_text))
                
                # Store user ID in first column for reference
                self.users_table.item(row, 0).setData(Qt.UserRole, user_id)
        
        except Exception as e:
            CopyableMessageBox.critical(
                self,
                "Fel",
                f"Kunde inte ladda användare: {str(e)}"
            )
    
    def on_user_selected(self):
        """Handle user selection"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            self.selected_user_label.setText("Ingen användare vald")
            if self.is_admin:
                self.save_role_btn.setEnabled(False)
                self.save_permissions_btn.setEnabled(False)
            return
        
        # Get selected user
        username_item = self.users_table.item(current_row, 0)
        if not username_item:
            return
        
        user_id = username_item.data(Qt.UserRole)
        username = username_item.text()
        
        self.selected_user_label.setText(f"Vald användare: {username}")
        self.selected_user_id = user_id
        
        # Load user's current role
        user_role = self.permission_manager.get_user_role(user_id)
        if user_role:
            for i in range(self.role_combo.count()):
                if self.role_combo.itemData(i) == user_role:
                    self.role_combo.setCurrentIndex(i)
                    break
        
        # Load user's permissions
        user_permissions = self.permission_manager.get_user_permissions(user_id)
        for perm, checkbox in self.permission_checkboxes.items():
            checkbox.setChecked(perm in user_permissions)
        
        # Enable controls if user is admin
        if self.is_admin:
            self.save_role_btn.setEnabled(True)
            self.save_permissions_btn.setEnabled(True)
    
    def on_role_changed(self):
        """Handle role change"""
        if hasattr(self, 'selected_user_id'):
            # Update permission checkboxes based on new role
            selected_role = self.role_combo.currentData()
            if selected_role:
                role_permissions = self.permission_manager._role_permissions.get(selected_role, [])
                for perm, checkbox in self.permission_checkboxes.items():
                    checkbox.setChecked(perm in role_permissions)
    
    def on_permission_changed(self):
        """Handle individual permission change"""
        # Enable save button when permissions change (only for admins)
        if hasattr(self, 'selected_user_id') and self.is_admin:
            self.save_permissions_btn.setEnabled(True)
    
    def save_user_role(self):
        """Save user's role"""
        if not hasattr(self, 'selected_user_id'):
            return
        
        selected_role = self.role_combo.currentData()
        if not selected_role:
            return
        
        success = self.permission_manager.set_user_role(
            self.selected_user_id, 
            selected_role, 
            self.current_user['user_id']
        )
        
        if success:
            CopyableMessageBox.information(
                self,
                "Framgång",
                "Användarens roll har uppdaterats."
            )
            self.load_users()  # Refresh the table
        else:
            CopyableMessageBox.critical(
                self,
                "Fel",
                "Kunde inte uppdatera användarens roll."
            )
    
    def save_permissions(self):
        """Save individual permissions"""
        if not hasattr(self, 'selected_user_id'):
            return
        
        # Get current permissions from checkboxes
        new_permissions = set()
        for perm, checkbox in self.permission_checkboxes.items():
            if checkbox.isChecked():
                new_permissions.add(perm)
        
        # Get current permissions from database
        current_permissions = set(self.permission_manager.get_user_permissions(self.selected_user_id))
        
        # Calculate permissions to grant and revoke
        to_grant = new_permissions - current_permissions
        to_revoke = current_permissions - new_permissions
        
        success = True
        
        # Grant new permissions
        for perm in to_grant:
            if not self.permission_manager.grant_permission(
                self.selected_user_id, perm, self.current_user['user_id']
            ):
                success = False
        
        # Revoke removed permissions
        for perm in to_revoke:
            if not self.permission_manager.revoke_permission(self.selected_user_id, perm):
                success = False
        
        if success:
            CopyableMessageBox.information(
                self,
                "Framgång",
                "Användarens behörigheter har uppdaterats."
            )
        else:
            CopyableMessageBox.warning(
                self,
                "Varning",
                "Vissa behörigheter kunde inte uppdateras."
            )
