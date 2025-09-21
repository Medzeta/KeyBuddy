"""
Users management window with role-based permissions
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QTableWidget, QTableWidgetItem, QPushButton,
                              QGroupBox, QFormLayout, QLineEdit, QComboBox,
                              QCheckBox, QTextEdit, QTabWidget, QHeaderView,
                              QDialog, QDialogButtonBox,
                              QScrollArea, QFrame, QAbstractItemView, QSplitter)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import bcrypt
from datetime import datetime

from .styles import AnimatedButton
from .copyable_message_box import CopyableMessageBox
from ..core.auth import AuthManager
from ..core.permissions import PermissionManager, UserRole, Permission

class UserDialog(QDialog):
    """Dialog for adding/editing users"""
    
    def __init__(self, parent=None, user_data=None, is_edit=False):
        super().__init__(parent)
        self.user_data = user_data
        self.is_edit = is_edit
        self.setup_ui()
        
        if user_data and is_edit:
            self.load_user_data()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Redigera användare" if self.is_edit else "Ny användare")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        
        # User info group
        user_group = QGroupBox("Användarinformation")
        user_layout = QFormLayout(user_group)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Användarnamn")
        user_layout.addRow("Användarnamn *:", self.username_edit)
        
        self.company_edit = QLineEdit()
        self.company_edit.setPlaceholderText("Företagsnamn")
        user_layout.addRow("Företag *:", self.company_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("E-postadress")
        user_layout.addRow("E-post *:", self.email_edit)
        
        self.org_number_edit = QLineEdit()
        self.org_number_edit.setPlaceholderText("Organisationsnummer")
        user_layout.addRow("Org.nummer:", self.org_number_edit)
        
        # Role selection
        self.role_combo = QComboBox()
        self.role_combo.addItems(["User", "Nyckelansvarig", "Förvaltare", "Låssmed", "Admin"])
        user_layout.addRow("Behörighet *:", self.role_combo)
        
        # Password section (only for new users or when changing)
        password_group = QGroupBox("Lösenord")
        password_layout = QFormLayout(password_group)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Nytt lösenord")
        password_layout.addRow("Lösenord:", self.password_edit)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText("Bekräfta lösenord")
        password_layout.addRow("Bekräfta:", self.confirm_password_edit)
        
        # Security settings
        security_group = QGroupBox("Säkerhetsinställningar")
        security_layout = QFormLayout(security_group)
        
        self.is_active_cb = QCheckBox()
        self.is_active_cb.setChecked(False)
        # Label changed: when checked => user is inactive
        security_layout.addRow("Inaktivera användare:", self.is_active_cb)
        
        self.two_factor_cb = QCheckBox()
        security_layout.addRow("Tvåfaktorsautentisering:", self.two_factor_cb)
        
        # Add groups to layout
        layout.addWidget(user_group)
        layout.addWidget(password_group)
        layout.addWidget(security_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Hide password section for edit mode initially
        if self.is_edit:
            password_group.hide()
            change_password_btn = QPushButton("Ändra lösenord")
            change_password_btn.clicked.connect(lambda: password_group.show())
            layout.insertWidget(2, change_password_btn)
    
    def load_user_data(self):
        """Load existing user data into form"""
        if self.user_data:
            self.username_edit.setText(self.user_data.get('username', ''))
            self.company_edit.setText(self.user_data.get('company_name', ''))
            self.email_edit.setText(self.user_data.get('email', ''))
            self.org_number_edit.setText(self.user_data.get('org_number', ''))
            
            # Set role
            role = self.user_data.get('role', 'User')
            # Ensure role is a string
            role = str(role) if role is not None else 'User'
            index = self.role_combo.findText(role)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
            
            # Convert to boolean for checkboxes
            is_active = self.user_data.get('is_active', True)
            if isinstance(is_active, str):
                is_active = is_active.lower() in ('true', '1', 'yes', 'on')
            # Invert: checkbox shows 'inactivate user' so checked means not active
            self.is_active_cb.setChecked(not bool(is_active))
            
            two_factor = self.user_data.get('two_factor_enabled', False)
            if isinstance(two_factor, str):
                two_factor = two_factor.lower() in ('true', '1', 'yes', 'on')
            self.two_factor_cb.setChecked(bool(two_factor))
    
    def get_user_data(self):
        """Get user data from form"""
        return {
            'username': self.username_edit.text().strip(),
            'company_name': self.company_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'org_number': self.org_number_edit.text().strip(),
            'role': self.role_combo.currentText(),
            'password': self.password_edit.text() if self.password_edit.text() else None,
            # Invert: if checkbox is checked (inactivate), then is_active should be False
            'is_active': not self.is_active_cb.isChecked(),
            'two_factor_enabled': self.two_factor_cb.isChecked()
        }
    
    def validate_form(self):
        """Validate form data"""
        errors = []
        
        if not self.username_edit.text().strip():
            errors.append("Användarnamn är obligatoriskt")
        
        if not self.company_edit.text().strip():
            errors.append("Företagsnamn är obligatoriskt")
        
        if not self.email_edit.text().strip():
            errors.append("E-postadress är obligatorisk")
        
        # Password validation for new users
        if not self.is_edit or self.password_edit.text():
            if not self.password_edit.text():
                errors.append("Lösenord är obligatoriskt")
            elif len(self.password_edit.text()) < 6:
                errors.append("Lösenord måste vara minst 6 tecken")
            elif self.password_edit.text() != self.confirm_password_edit.text():
                errors.append("Lösenorden matchar inte")
        
        return errors

class UserLogsDialog(QDialog):
    """Dialog for viewing user activity logs"""
    
    def __init__(self, parent=None, user_id=None, db_manager=None):
        super().__init__(parent)
        self.user_id = user_id
        self.db_manager = db_manager
        self.setup_ui()
        self.load_logs()
    
    def setup_ui(self):
        """Setup logs dialog UI"""
        self.setWindowTitle("Användarloggar")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(4)
        self.logs_table.setHorizontalHeaderLabels(["Datum", "Aktivitet", "Detaljer", "IP-adress"])
        
        # Set column widths
        header = self.logs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.logs_table)
        
        # Close button
        close_btn = QPushButton("Stäng")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def load_logs(self):
        """Load user activity logs"""
        if not self.user_id or not self.db_manager:
            return
        
        try:
            # Get user logs from database
            logs = self.db_manager.execute_query(
                """SELECT timestamp, activity_type, details, ip_address 
                   FROM user_logs 
                   WHERE user_id = ? 
                   ORDER BY timestamp DESC LIMIT 1000""",
                (self.user_id,)
            )
            
            self.logs_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                self.logs_table.setItem(row, 0, QTableWidgetItem(log['timestamp']))
                self.logs_table.setItem(row, 1, QTableWidgetItem(log['activity_type']))
                self.logs_table.setItem(row, 2, QTableWidgetItem(log['details']))
                self.logs_table.setItem(row, 3, QTableWidgetItem(log['ip_address'] or ''))
                
        except Exception as e:
            print(f"Error loading user logs: {e}")

class UsersWindow(QWidget):
    """Users management window"""
    
    navigate_home = Signal()
    
    def __init__(self, app_manager, db_manager, translation_manager):
        super().__init__()
        self.app_manager = app_manager
        self.db_manager = db_manager
        self.translation_manager = translation_manager
        self.permission_manager = PermissionManager(db_manager)
        self.current_user = app_manager.get_current_user()
        
        self.setup_ui()
        self.load_users()
        
        # Load role users table when roles tab is created
        if hasattr(self, 'role_users_table'):
            self.load_role_users()
    
    def setup_ui(self):
        """Setup users management UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Systemanvändarhantering")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        # Remove dotted focus rectangle on tabs
        try:
            self.tab_widget.tabBar().setFocusPolicy(Qt.NoFocus)
        except Exception:
            pass
        
        # Users tab
        users_tab = self.create_users_tab()
        self.tab_widget.addTab(users_tab, "Användare")
        
        # Roles tab
        roles_tab = self.create_roles_tab()
        self.tab_widget.addTab(roles_tab, "Behörigheter")
        
        # Logs tab
        logs_tab = self.create_logs_tab()
        self.tab_widget.addTab(logs_tab, "Systemloggar")
        
        layout.addWidget(self.tab_widget)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        home_btn = AnimatedButton("Hem")
        home_btn.clicked.connect(self.navigate_home.emit)
        home_btn.setProperty("class", "secondary")
        
        button_layout.addWidget(home_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def create_users_tab(self):
        """Create users management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_user_btn = AnimatedButton("Lägg till användare")
        add_user_btn.clicked.connect(self.add_user)
        
        edit_user_btn = QPushButton("Redigera")
        edit_user_btn.setProperty("class", "secondary")
        edit_user_btn.clicked.connect(self.edit_user)
        
        delete_user_btn = QPushButton("Ta bort")
        delete_user_btn.setProperty("class", "danger")
        delete_user_btn.clicked.connect(self.delete_user)
        
        view_logs_btn = QPushButton("Visa loggar")
        view_logs_btn.setProperty("class", "secondary")
        view_logs_btn.clicked.connect(self.view_user_logs)
        
        toolbar_layout.addWidget(add_user_btn)
        toolbar_layout.addWidget(edit_user_btn)
        toolbar_layout.addWidget(delete_user_btn)
        toolbar_layout.addWidget(view_logs_btn)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "Användarnamn", "Företag", "E-post", "Behörighet", 
            "Aktiv", "2FA", "Senast inloggad"
        ])
        
        # Set column widths
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        # Disable in-table editing (including double-click)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.users_table)
        
        return widget
    
    def create_roles_tab(self):
        """Create roles and permissions management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create splitter for better layout
        splitter = QSplitter(Qt.Vertical)
        
        # Top section - Users table (smaller)
        users_section = QWidget()
        users_layout = QVBoxLayout(users_section)
        users_layout.setContentsMargins(0, 0, 0, 0)
        
        users_label = QLabel("Välj användare för rollhantering:")
        users_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        users_layout.addWidget(users_label)
        
        # Compact users table for role management
        self.role_users_table = QTableWidget()
        self.role_users_table.setColumnCount(4)
        self.role_users_table.setHorizontalHeaderLabels(["Användarnamn", "E-post", "Roll", "Senast inloggad"])
        self.role_users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.role_users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.role_users_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.role_users_table.itemSelectionChanged.connect(self.on_role_user_selected)
        self.role_users_table.setMaximumHeight(200)
        users_layout.addWidget(self.role_users_table)
        
        splitter.addWidget(users_section)
        
        # Bottom section - Role and permissions management
        management_section = QWidget()
        management_layout = QVBoxLayout(management_section)
        management_layout.setContentsMargins(0, 0, 0, 0)
        
        # Role management group
        role_group = QGroupBox("Rollhantering")
        role_group.setMaximumHeight(120)
        role_main_layout = QVBoxLayout(role_group)
        
        # Selected user label
        self.selected_user_label = QLabel("Ingen användare vald")
        self.selected_user_label.setWordWrap(True)
        self.selected_user_label.setStyleSheet("font-weight: bold; color: #2196F3; margin: 4px;")
        role_main_layout.addWidget(self.selected_user_label)
        
        # Role controls layout
        role_controls_layout = QHBoxLayout()
        role_controls_layout.setSpacing(8)
        
        role_label = QLabel("Roll:")
        role_label.setMinimumWidth(35)
        role_controls_layout.addWidget(role_label)
        
        self.role_combo = QComboBox()
        self.role_combo.setMaximumWidth(150)
        for role in UserRole:
            display_name = self.permission_manager.get_role_display_name(role)
            self.role_combo.addItem(display_name, role)
        self.role_combo.currentIndexChanged.connect(self.on_role_changed)
        role_controls_layout.addWidget(self.role_combo)
        
        self.save_role_btn = AnimatedButton("Spara")
        self.save_role_btn.setMaximumWidth(60)
        self.save_role_btn.clicked.connect(self.save_user_role)
        self.save_role_btn.setEnabled(False)
        role_controls_layout.addWidget(self.save_role_btn)
        
        role_controls_layout.addStretch()
        role_main_layout.addLayout(role_controls_layout)
        
        management_layout.addWidget(role_group)
        
        # Permissions scroll area
        permissions_scroll = QScrollArea()
        permissions_scroll.setWidgetResizable(True)
        permissions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        permissions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        permissions_widget = QWidget()
        permissions_layout = QVBoxLayout(permissions_widget)
        
        # Create permission checkboxes
        self.permission_checkboxes = {}
        
        # Customer permissions
        customer_group = QGroupBox("Kunder")
        customer_group.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 6px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }")
        customer_layout = QVBoxLayout(customer_group)
        customer_layout.setSpacing(2)
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
        
        # Key system permissions
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
        
        # Order permissions
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
        
        # Admin permissions (only for admins)
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
        
        # Save permissions button
        permissions_button_layout = QHBoxLayout()
        self.save_permissions_btn = AnimatedButton("Spara")
        self.save_permissions_btn.setMaximumWidth(60)
        self.save_permissions_btn.clicked.connect(self.save_permissions)
        self.save_permissions_btn.setEnabled(False)
        permissions_button_layout.addWidget(self.save_permissions_btn)
        permissions_button_layout.addStretch()
        permissions_layout.addLayout(permissions_button_layout)
        
        permissions_scroll.setWidget(permissions_widget)
        management_layout.addWidget(permissions_scroll)
        
        splitter.addWidget(management_section)
        
        # Set splitter proportions
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
        
        # Check admin permissions
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
            self.role_combo.setEnabled(True)
            for checkbox in self.permission_checkboxes.values():
                checkbox.setEnabled(True)
        
        # Load role users table
        self.load_role_users()
        
        return widget
    
    def create_logs_tab(self):
        """Create system logs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # System logs table
        self.system_logs_table = QTableWidget()
        self.system_logs_table.setColumnCount(5)
        self.system_logs_table.setHorizontalHeaderLabels([
            "Datum", "Användare", "Aktivitet", "Detaljer", "IP-adress"
        ])
        
        # Set column widths
        header = self.system_logs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.system_logs_table)
        
        # Load system logs
        self.load_system_logs()
        
        return widget
    
    def load_users(self):
        """Load users from database"""
        try:
            users = self.db_manager.execute_query(
                """SELECT id, username, company_name, email, role, is_active, 
                          two_factor_enabled, last_login 
                   FROM users ORDER BY username"""
            )
            
            self.users_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.users_table.setItem(row, 0, QTableWidgetItem(user['username']))
                self.users_table.setItem(row, 1, QTableWidgetItem(user['company_name'] or ''))
                self.users_table.setItem(row, 2, QTableWidgetItem(user['email'] or ''))
                self.users_table.setItem(row, 3, QTableWidgetItem(user['role'] or 'User'))
                self.users_table.setItem(row, 4, QTableWidgetItem("Ja" if user['is_active'] else "Nej"))
                self.users_table.setItem(row, 5, QTableWidgetItem("Ja" if user['two_factor_enabled'] else "Nej"))
                self.users_table.setItem(row, 6, QTableWidgetItem(user['last_login'] or 'Aldrig'))
                
                # Store user ID in first column
                self.users_table.item(row, 0).setData(Qt.UserRole, user['id'])
                
        except Exception as e:
            print(f"Error loading users: {e}")
    
    def load_role_users(self):
        """Load users into role management table"""
        try:
            users = self.db_manager.execute_query(
                """SELECT id, username, email, role, last_login 
                   FROM users ORDER BY username"""
            )
            
            self.role_users_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.role_users_table.setItem(row, 0, QTableWidgetItem(user['username']))
                self.role_users_table.setItem(row, 1, QTableWidgetItem(user['email'] or ''))
                
                # Display role name
                try:
                    user_role = UserRole(user['role']) if user['role'] else UserRole.USER
                    role_display = self.permission_manager.get_role_display_name(user_role)
                except ValueError:
                    role_display = "Okänd"
                self.role_users_table.setItem(row, 2, QTableWidgetItem(role_display))
                
                # Format last login
                last_login_text = user['last_login'] if user['last_login'] else "Aldrig"
                self.role_users_table.setItem(row, 3, QTableWidgetItem(last_login_text))
                
                # Store user ID in first column for reference
                self.role_users_table.item(row, 0).setData(Qt.UserRole, user['id'])
                
        except Exception as e:
            print(f"Error loading role users: {e}")
    
    def on_role_user_selected(self):
        """Handle user selection in role management"""
        current_row = self.role_users_table.currentRow()
        if current_row < 0:
            self.selected_user_label.setText("Ingen användare vald")
            if self.is_admin:
                self.save_role_btn.setEnabled(False)
                self.save_permissions_btn.setEnabled(False)
            return
        
        # Get selected user
        username_item = self.role_users_table.item(current_row, 0)
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
            self.load_users()  # Refresh main users table
            self.load_role_users()  # Refresh role users table
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
    
    def load_system_logs(self):
        """Load system logs"""
        try:
            logs = self.db_manager.execute_query(
                """SELECT ul.timestamp, u.username, ul.activity_type, 
                          ul.details, ul.ip_address
                   FROM user_logs ul
                   LEFT JOIN users u ON ul.user_id = u.id
                   ORDER BY ul.timestamp DESC LIMIT 1000"""
            )
            
            self.system_logs_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                self.system_logs_table.setItem(row, 0, QTableWidgetItem(log['timestamp']))
                self.system_logs_table.setItem(row, 1, QTableWidgetItem(log['username'] or 'System'))
                self.system_logs_table.setItem(row, 2, QTableWidgetItem(log['activity_type']))
                self.system_logs_table.setItem(row, 3, QTableWidgetItem(log['details']))
                self.system_logs_table.setItem(row, 4, QTableWidgetItem(log['ip_address'] or ''))
                
        except Exception as e:
            print(f"Error loading system logs: {e}")
    
    def add_user(self):
        """Add new user"""
        dialog = UserDialog(self)
        if dialog.exec() == QDialog.Accepted:
            errors = dialog.validate_form()
            if errors:
                CopyableMessageBox.warning(self, "Valideringsfel", "\n".join(errors))
                return
            
            user_data = dialog.get_user_data()
            self.save_user(user_data)
            
            # Log user creation activity
            if hasattr(self, 'app_manager') and self.app_manager.get_current_user():
                current_user = self.app_manager.get_current_user()
                from ..core.logger import UserLogger
                logger = UserLogger(self.db_manager)
                logger.log_user_created(current_user['user_id'], user_data['username'])
    
    def edit_user(self):
        """Edit selected user"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            CopyableMessageBox.information(self, "Ingen användare vald", "Välj en användare att redigera.")
            return
        
        user_id = self.users_table.item(current_row, 0).data(Qt.UserRole)
        
        # Fetch user with explicit columns so we can map reliably
        rows = self.db_manager.execute_query(
            """
            SELECT 
                id, username, company_name, email, org_number, role,
                is_active, two_factor_enabled, profile_picture, totp_secret,
                last_login, created_at, is_verified, password_hash
            FROM users WHERE id = ?
            """,
            (user_id,)
        )
        
        if rows:
            row = rows[0]
            def get(field, idx, default=None):
                try:
                    return row[field] if isinstance(row, dict) else row[idx]
                except Exception:
                    return default
            user_dict = {
                'id': get('id', 0),
                'username': get('username', 1, ''),
                'company_name': get('company_name', 2, ''),
                'email': get('email', 3, ''),
                'org_number': get('org_number', 4, ''),
                'role': get('role', 5, 'User'),
                'is_active': bool(get('is_active', 6, True)),
                'two_factor_enabled': bool(get('two_factor_enabled', 7, False)),
                'profile_picture': get('profile_picture', 8, None),
                'totp_secret': get('totp_secret', 9, None),
                'last_login': get('last_login', 10, None),
                'created_at': get('created_at', 11, None),
                'is_verified': get('is_verified', 12, False),
                'password_hash': get('password_hash', 13, None)
            }
            
            dialog = UserDialog(self, user_dict, is_edit=True)
            if dialog.exec() == QDialog.Accepted:
                errors = dialog.validate_form()
                if errors:
                    CopyableMessageBox.warning(self, "Valideringsfel", "\n".join(errors))
                    return
                updated_data = dialog.get_user_data()
                updated_data['id'] = user_id
                self.save_user(updated_data, is_edit=True)
                # If user was inactivated, inform admin
                if not updated_data.get('is_active', True):
                    CopyableMessageBox.information(self, "Användare inaktiverad", "Användare inaktiverad av systemadmin")
                
                # Log user update activity
                if hasattr(self, 'app_manager') and self.app_manager.get_current_user():
                    current_user = self.app_manager.get_current_user()
                    from ..core.logger import UserLogger
                    logger = UserLogger(self.db_manager)
                    logger.log_user_updated(current_user['user_id'], updated_data['username'])
    
    def delete_user(self):
        """Delete selected user"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            CopyableMessageBox.information(self, "Ingen användare vald", "Välj en användare att ta bort.")
            return
        
        username = self.users_table.item(current_row, 0).text()
        user_id = self.users_table.item(current_row, 0).data(Qt.UserRole)
        
        reply = CopyableMessageBox.question(
            self, "Ta bort användare",
            f"Är du säker på att du vill ta bort användaren '{username}'?",
            CopyableMessageBox.Yes | CopyableMessageBox.No
        )
        
        if reply == CopyableMessageBox.Yes:
            try:
                self.db_manager.execute_update("DELETE FROM users WHERE id = ?", (user_id,))
                self.load_users()
                
                # Log user deletion activity
                if hasattr(self, 'app_manager') and self.app_manager.get_current_user():
                    current_user = self.app_manager.get_current_user()
                    from ..core.logger import UserLogger
                    logger = UserLogger(self.db_manager)
                    logger.log_user_deleted(current_user['user_id'], username)
                
                CopyableMessageBox.information(self, "Användare borttagen", f"Användaren '{username}' har tagits bort.")
            except Exception as e:
                CopyableMessageBox.critical(self, "Fel", f"Kunde inte ta bort användaren: {str(e)}")
    
    def view_user_logs(self):
        """View logs for selected user"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            CopyableMessageBox.information(self, "Ingen användare vald", "Välj en användare för att visa loggar.")
            return
        
        user_id = self.users_table.item(current_row, 0).data(Qt.UserRole)
        username = self.users_table.item(current_row, 0).text()
        
        dialog = UserLogsDialog(self, user_id, self.db_manager)
        dialog.setWindowTitle(f"Loggar för {username}")
        dialog.exec()
    
    def save_user(self, user_data, is_edit=False):
        """Save user to database"""
        try:
            if is_edit:
                # Update existing user
                if user_data['password']:
                    # Hash password with bcrypt if provided
                    password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    self.db_manager.execute_update(
                        """UPDATE users SET username=?, company_name=?, email=?, 
                           org_number=?, role=?, password_hash=?, is_active=?, 
                           two_factor_enabled=? WHERE id=?""",
                        (user_data['username'], user_data['company_name'], user_data['email'],
                         user_data['org_number'], user_data['role'], password_hash,
                         user_data['is_active'], user_data['two_factor_enabled'], user_data['id'])
                    )
                else:
                    # Update without password change
                    self.db_manager.execute_update(
                        """UPDATE users SET username=?, company_name=?, email=?, 
                           org_number=?, role=?, is_active=?, two_factor_enabled=? 
                           WHERE id=?""",
                        (user_data['username'], user_data['company_name'], user_data['email'],
                         user_data['org_number'], user_data['role'], user_data['is_active'],
                         user_data['two_factor_enabled'], user_data['id'])
                    )
            else:
                # Create new user (manual) with email verification
                password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                auth_manager = AuthManager(self.db_manager)
                verification_token = auth_manager.generate_verification_token()
                totp_secret = auth_manager.generate_totp_secret()
                # Insert including verification and totp fields
                self.db_manager.execute_update(
                    """INSERT INTO users (username, company_name, email, org_number,
                       role, password_hash, is_active, two_factor_enabled, created_at,
                       is_verified, verification_token, totp_secret)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user_data['username'],
                        user_data['company_name'],
                        user_data['email'],
                        user_data['org_number'],
                        user_data['role'],
                        password_hash,
                        user_data['is_active'],
                        user_data['two_factor_enabled'],
                        datetime.now().isoformat(),
                        False,
                        verification_token,
                        totp_secret
                    )
                )
                # Send verification email
                try:
                    auth_manager.send_verification_email(user_data['email'], verification_token)
                except Exception as e:
                    print(f"Error sending verification email: {e}")
            
            self.load_users()
            action = "uppdaterad" if is_edit else "skapad"
            CopyableMessageBox.information(self, "Användare sparad", f"Användaren har {action} framgångsrikt.")
            
        except Exception as e:
            CopyableMessageBox.critical(self, "Fel", f"Kunde inte spara användaren: {str(e)}")
