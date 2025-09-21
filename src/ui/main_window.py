"""
Main application window with modern UI and navigation
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QStackedWidget, QStatusBar, QLabel,
                              QApplication, QSystemTrayIcon, QMenu, QStyle, QPushButton)
from PySide6.QtCore import Qt, QTimer, Signal, QEvent, QObject
from PySide6.QtGui import QPixmap, QIcon, QAction, QPainter, QPainterPath, QColor, QRegion
import os
from datetime import datetime

from .styles import ThemeManager, AnimatedButton
from .login_window import LoginWindow
from .home_window import HomeWindow
from .settings_window import SettingsWindow
from .add_system_window import AddSystemWindow
from .my_systems_window import MySystemsWindow
from .orders_window import OrdersWindow
from .permissions_window import PermissionsWindow
from .users_window import UsersWindow
from ..core.translations import TranslationManager
from .copyable_message_box import CopyableMessageBox

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, app_manager, db_manager, version_manager):
        super().__init__()
        self.app_manager = app_manager
        self.db_manager = db_manager
        
        # Set reference to this main window in app_manager for backup status updates
        self.app_manager.main_window = self
        
        # Initialize global backup manager for email notifications
        self.app_manager.initialize_backup_manager(db_manager)
        
        # Initialize logger
        from ..core.logger import UserLogger
        self.logger = UserLogger(db_manager)
        self.version_manager = version_manager
        self.theme_manager = ThemeManager()
        self.translation_manager = TranslationManager()
        
        # Set initial language from settings
        lang = self.app_manager.get_setting("language", "sv")
        self.translation_manager.set_language(lang)
        
        # Auto-logout timer setup
        self.auto_logout_timer = QTimer()
        self.auto_logout_timer.setSingleShot(True)
        self.auto_logout_timer.timeout.connect(self.auto_logout)
        self.last_activity_time = None
        
        # Backup monitoring timer (60 seconds)
        self.backup_monitor_timer = QTimer()
        self.backup_monitor_timer.timeout.connect(self.check_latest_backup)
        self.backup_monitor_timer.start(60000)  # 60 seconds = 60000 ms
        self.last_backup_check = None
        
        # Perform initial backup check after UI is set up
        QTimer.singleShot(1000, self.check_latest_backup)  # Check after 1 second
        
        self.setup_ui()
        self.setup_connections()
        
        # Apply theme AFTER all windows are created
        self.apply_theme()
        
        # Setup version manager connections
        self.setup_version_connections()
        
        # Setup system tray
        self.setup_system_tray()
        
        # Show login window first
        self.show_login()
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for window dragging"""
        self.dragging = False
    
    def apply_rounded_corners_mask(self):
        """Apply rounded corners using a mask with smooth antialiasing"""
        try:
            # Create rounded rectangle path with 20px radius for better consistency
            path = QPainterPath()
            rect = self.rect()
            path.addRoundedRect(rect, 20, 20)
            
            # Create a high-resolution pixmap for smooth edges
            pixmap = QPixmap(rect.size())
            pixmap.fill(Qt.transparent)
            
            # Paint the rounded rectangle with antialiasing
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.fillPath(path, Qt.white)
            painter.end()
            
            # Convert pixmap to region and set as mask
            region = QRegion(pixmap.mask())
            self.setMask(region)
            self.rounded_corners_applied = True
            print(f"DEBUG: Applied smooth rounded corners mask to window: {rect}")
        except Exception as e:
            print(f"ERROR: Failed to apply smooth rounded corners mask: {e}")
            self.rounded_corners_applied = True
    
    def resizeEvent(self, event):
        """Handle window resize and reapply mask"""
        super().resizeEvent(event)
        # Reapply mask when window is resized
        self.rounded_corners_applied = False
        self.apply_rounded_corners_mask()
    
    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        # Apply rounded corners when window is shown
        QTimer.singleShot(100, self.apply_rounded_corners_mask)
    
    def create_title_bar(self):
        """Create custom title bar with integrated menu and window controls"""
        self.title_bar = QWidget()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(45)  # Single row height
        
        # Main vertical layout for title bar
        main_layout = QVBoxLayout(self.title_bar)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Single row: Menu buttons, stretch, Mac buttons, KeyBuddy text
        single_row = QWidget()
        single_layout = QHBoxLayout(single_row)
        single_layout.setContentsMargins(15, 8, 15, 8)
        single_layout.setSpacing(8)
        
        # DESTROY ALL OLD MENU BUTTONS AND CREATE COMPLETELY NEW ONES
        print("DEBUG: *** DESTROYING ALL OLD MENUS AND CREATING RADICAL NEW SYSTEM ***")
        
        # Clear any existing menu buttons
        for i in reversed(range(single_layout.count())):
            child = single_layout.itemAt(i)
            if child and child.widget():
                widget = child.widget()
                if isinstance(widget, QPushButton):
                    print(f"DEBUG: DESTROYING old button: {widget.text()} with objectName: {widget.objectName()}")
                    widget.deleteLater()
                    single_layout.removeWidget(widget)
        
        # Create COMPLETELY NEW menu system
        try:
            self.create_radical_new_menu_system(single_layout)
            print("DEBUG: *** FINISHED CREATING RADICAL NEW MENU SYSTEM ***")
        except Exception as e:
            print(f"DEBUG: *** ERROR in create_radical_new_menu_system: {e} ***")
            import traceback
            traceback.print_exc()
        
        single_layout.addStretch()
        
        # Modern window control buttons with icons matching menu button style
        self.minimize_btn = QPushButton("🗕")  # Modern minimize icon
        self.minimize_btn.setObjectName("modernWindowControlButton")
        self.minimize_btn.clicked.connect(self.showMinimized)
        
        self.maximize_btn = QPushButton("🗖")  # Modern maximize icon
        self.maximize_btn.setObjectName("modernWindowControlButton")
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        
        self.close_btn = QPushButton("🗙")  # Modern close icon
        self.close_btn.setObjectName("modernWindowControlCloseButton")  # Special styling for close
        self.close_btn.clicked.connect(self.close)
        
        single_layout.addWidget(self.maximize_btn)
        single_layout.addWidget(self.minimize_btn)
        single_layout.addWidget(self.close_btn)
        
        main_layout.addWidget(single_row)
        
        # Make title bar draggable
        self.title_bar.mousePressEvent = self.title_bar_mouse_press
        self.title_bar.mouseMoveEvent = self.title_bar_mouse_move
        self.title_bar.mouseReleaseEvent = self.title_bar_mouse_release
    
    def create_radical_new_menu_system(self, layout):
        """COMPLETELY NEW menu system - DESTROY AND REBUILD"""
        
        print("DEBUG: *** CREATING RADICAL NEW MENU SYSTEM FROM SCRATCH ***")
        
        # Define menu structure
        self.menu_data = {
            "Hem": [
                ("Hem", self.show_home),
                ("separator", None),
                ("Avsluta", self.quit_application)
            ],
            "System": [
                ("Lägg till system", self.show_add_system),
                ("Mina system", self.show_my_systems),
                ("Beställningar", self.show_orders)
            ],
            "Användare": [
                ("Hantera användare", self.show_users),
                ("Logga ut", self.logout)
            ],
            "Inställningar": [
                ("Inställningar", self.show_settings)
            ],
            "Hjälp": [
                ("GDPR", self.show_gdpr),
                ("Sök efter uppdateringar", self.version_manager.check_for_updates)
            ]
        }
        
        # Create CLEAN modern buttons that match the right-click menu design
        for menu_name in self.menu_data.keys():
            # Create clean modern button - NO INLINE STYLING
            button = QPushButton(menu_name)
            button.setObjectName("modernTopMenuButton")  # Uses global stylesheet styling
            
            
            # DEBUG: Print what we're creating
            print(f"DEBUG: Creating clean modern menu button '{menu_name}' with objectName: {button.objectName()}")
            
            # Connect to manual popup function - FIX lambda closure problem
            button.clicked.connect(lambda checked, name=menu_name, btn=button: self.show_extreme_popup(name, btn))
            
            # Add to layout
            layout.addWidget(button)
            
            # Store references for backward compatibility
            if menu_name == "Hem":
                self.home_menu_btn = button
            elif menu_name == "System":
                self.system_menu_btn = button
            elif menu_name == "Användare":
                self.users_menu_btn = button
            elif menu_name == "Inställningar":
                self.settings_menu_btn = button
            elif menu_name == "Hjälp":
                self.help_menu_btn = button
    
    def show_extreme_popup(self, menu_name, button):
        """Show popup menu EXACTLY like right-click context menu"""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        # Create menu EXACTLY like right-click context menu
        popup = QMenu(self)
        popup.setObjectName("newDropdownMenu")  # SAME as right-click menu
        
        # Make menu frameless/translucent EXACTLY like right-click menu
        try:
            popup.setWindowFlags(popup.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            popup.setAttribute(Qt.WA_TranslucentBackground, True)
        except Exception:
            pass
        
        # DEBUG: Print what we're creating
        print(f"DEBUG: Creating popup menu EXACTLY like right-click for '{menu_name}' with objectName: {popup.objectName()}")
        
        # Get menu items for this menu
        menu_items = self.menu_data.get(menu_name, [])
        
        # Add items to popup EXACTLY like right-click menu
        for item_name, callback in menu_items:
            if item_name == "separator":
                popup.addSeparator()
            else:
                action = QAction(item_name, self)  # NO emojis, clean like right-click
                if callback:
                    action.triggered.connect(callback)
                popup.addAction(action)
        
        # Show popup at button position
        button_pos = button.mapToGlobal(button.rect().bottomLeft())
        popup.exec(button_pos)
    
    def refresh_menu_styling(self):
        """Force refresh menu styling after theme changes - EXTREME NEW SYSTEM"""
        print("DEBUG: REFRESHING EXTREME menu styling...")
        
        # Re-apply object names for the EXTREME system
        if hasattr(self, 'home_menu_btn') and self.home_menu_btn:
            self.home_menu_btn.setObjectName("EXTREME_NEW_MENU_BUTTON")
            print(f"DEBUG: Set home_menu_btn objectName to: {self.home_menu_btn.objectName()}")
        
        if hasattr(self, 'system_menu_btn') and self.system_menu_btn:
            self.system_menu_btn.setObjectName("EXTREME_NEW_MENU_BUTTON")
            print(f"DEBUG: Set system_menu_btn objectName to: {self.system_menu_btn.objectName()}")
        
        if hasattr(self, 'users_menu_btn') and self.users_menu_btn:
            self.users_menu_btn.setObjectName("EXTREME_NEW_MENU_BUTTON")
            print(f"DEBUG: Set users_menu_btn objectName to: {self.users_menu_btn.objectName()}")
        
        if hasattr(self, 'settings_menu_btn') and self.settings_menu_btn:
            self.settings_menu_btn.setObjectName("EXTREME_NEW_MENU_BUTTON")
            print(f"DEBUG: Set settings_menu_btn objectName to: {self.settings_menu_btn.objectName()}")
        
        if hasattr(self, 'help_menu_btn') and self.help_menu_btn:
            self.help_menu_btn.setObjectName("EXTREME_NEW_MENU_BUTTON")
            print(f"DEBUG: Set help_menu_btn objectName to: {self.help_menu_btn.objectName()}")
        
        # Force style refresh
        print("DEBUG: Forcing Qt style refresh...")
        self.style().unpolish(self)
        self.style().polish(self)
    
    def toggle_maximize(self):
        """Toggle between maximized and normal window state"""
        if self.isMaximized():
            self.showNormal()
            # Reset fixed size when returning to normal
            self.setMinimumSize(1250, 1000)
            self.setMaximumSize(1250, 1000)
            self.resize(1250, 1000)
            self.maximize_btn.setText("🗖")  # Restore icon
        else:
            # Remove size constraints for maximizing
            self.setMaximumSize(16777215, 16777215)  # Qt's maximum size
            self.showMaximized()
            self.maximize_btn.setText("🗗")  # Restore down icon
    
    def title_bar_mouse_press(self, event):
        """Handle title bar mouse press"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def title_bar_mouse_move(self, event):
        """Handle title bar mouse move"""
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
    
    def title_bar_mouse_release(self, event):
        """Handle title bar mouse release"""
        self.dragging = False
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle(self.translation_manager.get_text("app_title"))
        self.setMinimumSize(1250, 1000)
        self.setMaximumSize(1250, 1000)
        
        # Make window borderless and set background color - SAME as dropdown menus
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        # Enable translucent background for rounded corners
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Force rounded corners by setting a mask after window is shown
        self.rounded_corners_applied = False
        
        # Enable window dragging
        self.dragging = False
        self.drag_position = None
        
        # Create custom title bar
        self.create_title_bar()
        
        # Set window size to fixed dimensions
        self.resize(1250, 1000)
        
        # Center the window on screen
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - 1250) // 2
        y = (screen_geometry.height() - 1000) // 2
        self.move(x, y)
        
        # Create central widget and stacked layout
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add custom title bar
        self.main_layout.addWidget(self.title_bar)
        
        # Create header with logo and user info
        self.create_header()
        
        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("stacked_widget")
        self.main_layout.addWidget(self.stacked_widget)
        
        # Create different windows
        self.login_window = LoginWindow(self.app_manager, self.db_manager, self.translation_manager)
        self.home_window = HomeWindow(self.app_manager, self.db_manager, self.translation_manager)
        self.settings_window = SettingsWindow(self.app_manager, self.db_manager, self.translation_manager)
        self.add_system_window = AddSystemWindow(self.app_manager, self.db_manager, self.translation_manager)
        self.my_systems_window = MySystemsWindow(self.app_manager, self.db_manager, self.translation_manager)
        self.orders_window = OrdersWindow(self.app_manager, self.db_manager, self.translation_manager)
        self.permissions_window = PermissionsWindow(self.db_manager, self.app_manager, self.translation_manager)
        self.users_window = UsersWindow(self.app_manager, self.db_manager, self.translation_manager)
        
        # Add windows to stack
        self.stacked_widget.addWidget(self.login_window)
        self.stacked_widget.addWidget(self.home_window)
        self.stacked_widget.addWidget(self.settings_window)
        self.stacked_widget.addWidget(self.add_system_window)
        self.stacked_widget.addWidget(self.my_systems_window)
        self.stacked_widget.addWidget(self.orders_window)
        self.stacked_widget.addWidget(self.permissions_window)
        self.stacked_widget.addWidget(self.users_window)
        
        # Create status bar
        self.status_bar = QStatusBar()
        # Status bar styling handled by global CSS
        self.setStatusBar(self.status_bar)
        
        # Add KeyBuddy name, backup status and version info to status bar
        # KeyBuddy name (will be placed after backup status)
        self.keybuddy_name_label = QLabel("KeyBuddy")
        self.keybuddy_name_label.setObjectName("statusKeyBuddyName")
        
        # Backup status (left of version)
        self.backup_status_label = QLabel("")
        self.backup_status_label.setProperty("kb_label_type", "caption")
        # Initialize backup status from saved settings
        try:
            info_manual = self.app_manager.get_setting("last_manual_backup_info", {}) or {}
            info_auto = self.app_manager.get_setting("last_auto_backup_info", {}) or {}
            latest_ts = None
            latest_src = None
            latest_path = None
            if isinstance(info_manual, dict) and info_manual.get("timestamp"):
                latest_ts = info_manual.get("timestamp")
                latest_src = "manuell"
                latest_path = info_manual.get("path", "")
            if isinstance(info_auto, dict) and info_auto.get("timestamp"):
                # Prefer newer timestamp
                ts_m = info_manual.get("timestamp") if isinstance(info_manual, dict) else None
                if (not ts_m) or (info_auto.get("timestamp") > ts_m):
                    latest_ts = info_auto.get("timestamp")
                    latest_src = "automatisk"
                    latest_path = info_auto.get("path", "")
            if latest_ts:
                from datetime import datetime
                dt = datetime.fromisoformat(latest_ts)
                self.backup_status_label.setText(f"Backup: {dt.strftime('%Y-%m-%d')}, {dt.strftime('%H:%M')}, {latest_src}")
            else:
                self.backup_status_label.setText("Backup: -")
        except Exception:
            self.backup_status_label.setText("Backup: -")

        try:
            # Just show the version number without build number
            current_version = self.version_manager.get_current_version()
            version_text = f"v{current_version}"
        except:
            version_text = "v1.05"
        self.version_label = QLabel(version_text)
        self.version_label.setProperty("kb_label_type", "caption")
        # Order: backup status, KeyBuddy name, then version
        # Add a transparent spacer to the far right to avoid style bleed in corner
        spacer = QLabel("")
        spacer.setFixedWidth(8)
        # Spacer styling handled by global CSS
        self.status_bar.addPermanentWidget(self.backup_status_label)
        self.status_bar.addPermanentWidget(self.keybuddy_name_label)
        self.status_bar.addPermanentWidget(self.version_label)
        self.status_bar.addPermanentWidget(spacer)
        
        # Status messages hidden by user request
        # self.status_bar.showMessage(self.translation_manager.get_text("app_title") + " - " + 
        #                            self.translation_manager.get_text("login"))

    def update_backup_status(self, timestamp_iso: str, source: str, path: str = ""):
        """Update backup status label in the status bar.
        source: 'manuell' or 'automatisk'
        """
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp_iso)
            self.backup_status_label.setText(
                f"Backup: {dt.strftime('%Y-%m-%d')}, {dt.strftime('%H:%M')}, {source}"
            )
        except Exception:
            self.backup_status_label.setText("Backup: -")
    
    def update_version_display(self):
        """Update version display in status bar"""
        try:
            current_version = self.version_manager.get_current_version()
            version_text = f"v{current_version}"
            self.version_label.setText(version_text)
            print(f"Version display updated to: {version_text}")
        except Exception as e:
            print(f"Error updating version display: {e}")
            self.version_label.setText("v1.05")
    
    def check_latest_backup(self):
        """Check for the latest backup file and update status bar every 60 seconds"""
        print(f"Checking latest backup at {datetime.now().strftime('%H:%M:%S')}")
        try:
            # Get backup directory path
            backup_dir = "backups"
            if not os.path.isabs(backup_dir):
                import sys
                if hasattr(sys, '_MEIPASS'):
                    # Running as PyInstaller bundle
                    app_root = os.path.dirname(sys.executable)
                else:
                    # Running as script
                    app_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                backup_dir = os.path.join(app_root, backup_dir)
            
            if not os.path.exists(backup_dir):
                self.backup_status_label.setText("Backup: -")
                return
            
            # Get all backup files
            backup_files = []
            for item in os.listdir(backup_dir):
                if item.startswith("nyckelhanteraren_backup_") and item.endswith(".zip"):
                    item_path = os.path.join(backup_dir, item)
                    stat = os.stat(item_path)
                    backup_files.append({
                        'name': item,
                        'path': item_path,
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'type': 'automatisk' if 'auto' in item else 'manuell'
                    })
            
            if not backup_files:
                self.backup_status_label.setText("Backup: -")
                return
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x['created'], reverse=True)
            latest_backup = backup_files[0]
            
            # Update status bar with latest backup info
            dt = latest_backup['created']
            backup_type = latest_backup['type']
            self.backup_status_label.setText(
                f"Backup: {dt.strftime('%Y-%m-%d')}, {dt.strftime('%H:%M')}, {backup_type}"
            )
            
        except Exception as e:
            print(f"Error checking latest backup: {e}")
            self.backup_status_label.setText("Backup: -")
    
    def create_header(self):
        """Create header with logo and user info"""
        self.header_widget = QWidget()
        self.header_widget.setMaximumHeight(320)
        self.header_layout = QHBoxLayout(self.header_widget)
        
        # Company logo (5x larger)
        self.logo_label = QLabel()
        self.logo_label.setMaximumSize(300, 300)
        self.logo_label.setScaledContents(True)
        self.update_logo()
        
        # User info (hidden initially)
        self.user_info_widget = QWidget()
        self.user_info_layout = QHBoxLayout(self.user_info_widget)
        
        self.user_label = QLabel()
        self.user_label.setProperty("kb_label_type", "caption")
        
        # Create vertical layout for user area (no logout button)
        self.user_vertical_layout = QVBoxLayout()
        self.user_vertical_layout.addWidget(self.user_label)
        self.user_vertical_layout.setSpacing(5)
        self.user_vertical_layout.setAlignment(Qt.AlignCenter)
        
        # Add vertical layout to horizontal layout
        self.user_info_layout.addLayout(self.user_vertical_layout)
        self.user_info_widget.hide()
        
        # Add to header layout
        self.header_layout.addWidget(self.logo_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.user_info_widget)
        
        print(f"DEBUG: Header created, user_info_widget visibility: {self.user_info_widget.isVisible()}")
        
        self.main_layout.addWidget(self.header_widget)
    
        
    def show_gdpr(self):
        """Show GDPR window"""
        from .gdpr_window import GDPRWindow
        gdpr_window = GDPRWindow(self.app_manager, self)
        gdpr_window.exec()
    
    def setup_connections(self):
        """Setup signal connections"""
        # App manager signals
        self.app_manager.language_changed.connect(self.on_language_changed)
        self.app_manager.theme_changed.connect(self.on_theme_changed)
        self.app_manager.logo_changed.connect(self.update_logo)
        
        # Login window signals
        self.login_window.login_successful.connect(self.on_login_successful)
        
        # Home window signals
        self.home_window.navigate_to_add_system.connect(self.show_add_system)
        self.home_window.navigate_to_my_systems.connect(self.show_my_systems)
        self.home_window.navigate_to_settings.connect(self.show_settings)
        
        # Window navigation signals
        self.add_system_window.navigate_home.connect(self.show_home)
        self.my_systems_window.navigate_home.connect(self.show_home)
        self.my_systems_window.navigate_to_home.connect(self.show_home)
        self.my_systems_window.navigate_to_orders.connect(self.show_orders)
        self.my_systems_window.order_created.connect(self.orders_window.refresh_data)
        self.orders_window.navigate_home.connect(self.show_home)
        self.settings_window.navigate_home.connect(self.show_home)
        self.users_window.navigate_home.connect(self.show_home)
    
    def setup_version_connections(self):
        """Setup version manager signal connections"""
        try:
            self.version_manager.update_available.connect(self.on_update_available)
            self.version_manager.update_progress.connect(self.on_update_progress)
            self.version_manager.update_completed.connect(self.on_update_completed)
            self.version_manager.update_error.connect(self.on_update_error)
        except AttributeError:
            # Version manager signals not implemented yet
            pass
    
    def setup_system_tray(self):
        """Setup system tray functionality"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Set tray icon (use app icon or default)
        icon_path = "assets/Kaybuddy_ikon.ico"
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Use default icon if custom icon not found
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show/Hide action
        show_action = QAction("Visa KeyBuddy", self)
        show_action.triggered.connect(self.show_from_tray)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Avsluta", self)
        exit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Connect double-click to show window
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # Show tray icon
        self.tray_icon.show()
        
        # Show notification on first minimize
        self.first_minimize = True
    
    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_from_tray()
    
    def show_from_tray(self):
        """Show window from system tray"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def quit_application(self):
        """Quit application completely"""
        # Close database connection
        self.db_manager.close()
        QApplication.quit()
    
    def apply_theme(self):
        """Apply current theme"""
        theme_name = self.app_manager.get_setting("theme", "light")
        stylesheet = self.theme_manager.get_stylesheet(theme_name)
        
        # Apply the global stylesheet (which now includes rounded corners)
        self.setStyleSheet(stylesheet)
        
        # DEBUG: Print stylesheet size and radical menu styling presence
        print(f"DEBUG: Applied stylesheet with {len(stylesheet)} characters")
        if "radicalNewMenuButton" in stylesheet:
            print("DEBUG: RADICAL menu button styling FOUND in stylesheet")
        else:
            print("DEBUG: RADICAL menu button styling NOT FOUND in stylesheet")
        
        # FORCE REFRESH MENU STYLING AFTER THEME APPLICATION
        self.refresh_menu_styling()
        
        # Apply theme to all child windows
        if hasattr(self, 'login_window') and hasattr(self.login_window, 'apply_theme'):
            self.login_window.apply_theme()
        if hasattr(self, 'settings_window') and hasattr(self.settings_window, 'apply_theme'):
            self.settings_window.apply_theme()
        # Add more windows as needed
    
    def update_logo(self):
        """Update company logo"""
        logo_path = self.app_manager.get_setting("company_logo", "")
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(pixmap)
        else:
            # Default logo placeholder
            self.logo_label.setText("LOGO")
            self.logo_label.setAlignment(Qt.AlignCenter)
            self.logo_label.setObjectName("logoPlaceholder")  # Use global styling
    
    def on_language_changed(self, language_code):
        """Handle language change"""
        self.translation_manager.set_language(language_code)
        self.update_ui_text()
    
    def on_theme_changed(self, theme_name):
        """Handle theme change"""
        print(f"DEBUG: on_theme_changed called with theme: {theme_name}")
        self.apply_theme()
        print("DEBUG: Global stylesheet applied - dashboard cards should update automatically")
    
    def on_update_available(self, version_info):
        """Handle update available notification"""
        reply = CopyableMessageBox.question(
            self, self.translation_manager.get_text("update_available"),
            f"En ny version ({version_info['version']}) är tillgänglig.\n"
            f"Vill du ladda ner och installera den nu?",
            CopyableMessageBox.Yes | CopyableMessageBox.No
        )
        
        if reply == CopyableMessageBox.Yes:
            self.version_manager.download_update(version_info['download_url'])
    
    def on_update_progress(self, progress):
        """Handle update download progress"""
        # self.status_bar.showMessage(f"Laddar ner uppdatering... {progress}%")
    
    def on_update_completed(self, update_file):
        """Handle update download completed"""
        # self.status_bar.showMessage("Uppdatering nedladdad")
        
        reply = CopyableMessageBox.question(
            self, self.translation_manager.get_text("install_update"),
            "Uppdateringen har laddats ner.\n"
            "Vill du installera den nu? (Applikationen kommer att starta om)",
            CopyableMessageBox.Yes | CopyableMessageBox.No
        )
        
        if reply == CopyableMessageBox.Yes:
            self.version_manager.install_update(update_file)
            QApplication.quit()
    
    def on_update_error(self, error_msg):
        """Handle update error"""
        # self.status_bar.showMessage("Uppdateringsfel")
        CopyableMessageBox.critical(
            self, self.translation_manager.get_text("update_error"),
            f"Ett fel uppstod vid uppdatering:\n{error_msg}"
        )
    
    def eventFilter(self, obj, event):
        """Filter events to detect user activity for auto-logout"""
        # Simple check without isinstance to avoid import issues
        if not hasattr(obj, 'metaObject'):
            return False
            
        if self.app_manager.get_current_user() and self.app_manager.get_setting("auto_logout_enabled", True):
            # Track mouse and keyboard activity
            if event.type() in [QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.KeyPress]:
                self.reset_auto_logout_timer()
        
        try:
            return super().eventFilter(obj, event)
        except (TypeError, AttributeError):
            # Handle cases where obj is not a proper QObject
            return False
    
    def reset_auto_logout_timer(self):
        """Reset the auto-logout timer"""
        if self.app_manager.get_setting("auto_logout_enabled", True):
            self.auto_logout_timer.stop()
            self.auto_logout_timer.start(5 * 60 * 1000)  # 5 minutes in milliseconds
            self.last_activity_time = datetime.now()
    
    def start_auto_logout_timer(self):
        """Start auto-logout timer when user logs in"""
        if self.app_manager.get_setting("auto_logout_enabled", True):
            # Install event filter to track activity
            QApplication.instance().installEventFilter(self)
            self.reset_auto_logout_timer()
    
    def stop_auto_logout_timer(self):
        """Stop auto-logout timer when user logs out"""
        self.auto_logout_timer.stop()
        QApplication.instance().removeEventFilter(self)
    
    def auto_logout(self):
        """Perform automatic logout due to inactivity"""
        if self.app_manager.get_current_user():
            self.logout()
    
    def update_ui_text(self):
        """Update UI text for current language"""
        self.setWindowTitle(self.translation_manager.get_text("app_title"))
        
        # Custom menu buttons are already created and don't need updating
        
        # Update all windows
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if hasattr(widget, 'update_ui_text'):
                widget.update_ui_text()
    
    def show_login(self):
        """Show login window"""
        self.stacked_widget.setCurrentWidget(self.login_window)
        # Hide custom menu buttons during login
        if hasattr(self, 'home_menu_btn'):
            self.home_menu_btn.hide()
            self.system_menu_btn.hide()
            self.users_menu_btn.hide()
            self.settings_menu_btn.hide()
            self.help_menu_btn.hide()
        self.user_info_widget.hide()
        # self.status_bar.showMessage(self.translation_manager.get_text("login"))
    
    def show_home(self):
        """Show home window"""
        if self.app_manager.get_current_user():
            self.stacked_widget.setCurrentWidget(self.home_window)
            # self.status_bar.showMessage(self.translation_manager.get_text("home"))
            # Show custom menu buttons when logged in
            if hasattr(self, 'home_menu_btn'):
                self.home_menu_btn.show()
                self.system_menu_btn.show()
                self.users_menu_btn.show()
                self.settings_menu_btn.show()
                self.help_menu_btn.show()
        else:
            self.show_login()
    
    def show_settings(self):
        """Show settings window"""
        if self.app_manager.get_current_user():
            self.stacked_widget.setCurrentWidget(self.settings_window)
            # self.status_bar.showMessage(self.translation_manager.get_text("settings"))
        else:
            self.show_login()
    
    def show_add_system(self):
        """Show add system window"""
        if self.app_manager.get_current_user():
            self.stacked_widget.setCurrentWidget(self.add_system_window)
            # self.status_bar.showMessage(self.translation_manager.get_text("add_system"))
        else:
            self.show_login()
    
    def show_my_systems(self):
        """Show my systems window"""
        if self.app_manager.get_current_user():
            self.stacked_widget.setCurrentWidget(self.my_systems_window)
            self.my_systems_window.refresh_data()
            # self.status_bar.showMessage(self.translation_manager.get_text("my_systems"))
        else:
            self.show_login()
    
    def show_orders(self):
        """Show orders window"""
        if self.app_manager.get_current_user():
            self.stacked_widget.setCurrentWidget(self.orders_window)
            self.orders_window.refresh_data()
            # self.status_bar.showMessage(self.translation_manager.get_text("orders"))
        else:
            self.show_login()
    
    def show_users(self):
        """Show users management window (Admin only)"""
        current_user = self.app_manager.get_current_user()
        if current_user:
            # Check if user has admin role
            if current_user.get('role') == 'admin' or current_user.get('is_admin', False):
                # Log access to user management
                self.logger.log_system_access(current_user['user_id'], "User Management")
                # Always refresh users list before showing
                try:
                    if hasattr(self, 'users_window') and hasattr(self.users_window, 'load_users'):
                        self.users_window.load_users()
                except Exception:
                    pass
                self.stacked_widget.setCurrentWidget(self.users_window)
                # self.status_bar.showMessage("Systemanvändarhantering")
            else:
                CopyableMessageBox.warning(self, "Åtkomst nekad", "Du har inte behörighet att komma åt användarhantering.")
        else:
            self.show_login()
    
    def show_permissions(self):
        """Show permissions window"""
        if self.app_manager.get_current_user():
            self.stacked_widget.setCurrentWidget(self.permissions_window)
            # self.status_bar.showMessage("Behörigheter")
        else:
            self.show_login()
    
    def on_login_successful(self, user_data):
        """Handle successful login"""
        print(f"DEBUG: Login successful, emitting signal")
        self.app_manager.set_current_user(user_data)
        self.show_home()
        self.update_user_display(user_data)
        # Show custom menu buttons after login
        if hasattr(self, 'home_menu_btn'):
            self.home_menu_btn.show()
            self.system_menu_btn.show()
            self.users_menu_btn.show()
            self.settings_menu_btn.show()
            self.help_menu_btn.show()
        
        # Start auto-logout timer if enabled
        self.start_auto_logout_timer()
        
        # Update home window stats
        if hasattr(self.home_window, 'update_stats'):
            self.home_window.update_stats()
    
    def update_user_display(self, user_data):
        """Update user display with profile picture and username"""
        print(f"DEBUG: Updating user display for {user_data['username']}")
        
        # Show user info widget
        self.user_info_widget.show()
        print(f"DEBUG: User info widget shown, visibility: {self.user_info_widget.isVisible()}")
        
        # Get profile picture from database
        try:
            result = self.db_manager.execute_query(
                "SELECT profile_picture FROM users WHERE id = ?",
                (user_data['user_id'],)
            )
            
            profile_picture_path = None
            if result and result[0] and result[0]['profile_picture']:
                profile_picture_path = result[0]['profile_picture']
            
            print(f"DEBUG: Profile picture path: {profile_picture_path}")
            
            # Create layout for user info if not exists
            if not hasattr(self, 'user_display_layout'):
                print(f"DEBUG: Creating new user display layout")
                self.user_display_layout = QHBoxLayout()
                
                
                # Profile picture label
                self.profile_pic_label = QLabel()
                self.profile_pic_label.setFixedSize(64, 64)
                self.profile_pic_label.setObjectName("profilePicture")  # Use global styling
                self.profile_pic_label.setAlignment(Qt.AlignCenter)
                self.profile_pic_label.setScaledContents(True)
                
                # Create vertical layout for username only
                self.user_text_layout = QVBoxLayout()
                self.user_text_layout.addWidget(self.user_label)
                self.user_text_layout.setSpacing(5)
                self.user_text_layout.setAlignment(Qt.AlignCenter)
                
                self.user_display_layout.addWidget(self.profile_pic_label)
                self.user_display_layout.addSpacing(10)  # Add spacing between picture and name
                self.user_display_layout.addLayout(self.user_text_layout)
                
                # Replace user_vertical_layout in user_info_layout
                self.user_info_layout.removeItem(self.user_vertical_layout)
                self.user_info_layout.insertLayout(0, self.user_display_layout)
                
                print(f"DEBUG: User display layout created and added")
            
            # Update profile picture
            if profile_picture_path and os.path.exists(profile_picture_path):
                from PySide6.QtGui import QPixmap
                pixmap = QPixmap(profile_picture_path)
                if not pixmap.isNull():
                    # Scale pixmap to fit label
                    scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.profile_pic_label.setPixmap(scaled_pixmap)
                    print(f"DEBUG: Profile picture loaded and set")
                else:
                    self.profile_pic_label.setText("👤")
                    print(f"DEBUG: Invalid pixmap, using emoji")
            else:
                self.profile_pic_label.setText("👤")
                print(f"DEBUG: No profile picture file, using emoji")
            
            # Update username
            self.user_label.setText(user_data['username'])
            print(f"DEBUG: Username set to: {user_data['username']}")
            
        except Exception as e:
            print(f"Error updating user display: {e}")
            self.user_label.setText(user_data['username'])
    
    def logout(self):
        """Handle logout"""
        # Stop auto-logout timer
        self.stop_auto_logout_timer()
        
        # Log logout before clearing user session
        current_user = self.app_manager.get_current_user()
        if current_user:
            self.logger.log_logout(current_user['user_id'], current_user['username'])
        
        self.app_manager.logout()
        self.show_login()
        # Status message hidden by user request
        # self.status_bar.showMessage("Utloggad")
        
        # Clear sensitive data from windows
        self.home_window.clear_data()
        self.my_systems_window.clear_data()
        self.orders_window.clear_data()
    
    def closeEvent(self, event):
        """Handle application close - minimize to tray instead"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            # Show notification on first minimize
            if hasattr(self, 'first_minimize') and self.first_minimize:
                self.tray_icon.showMessage(
                    "KeyBuddy",
                    "Applikationen minimerades till systemfältet. Dubbelklicka på ikonen för att visa den igen.",
                    QSystemTrayIcon.Information,
                    3000
                )
                self.first_minimize = False
            
            # Hide window instead of closing
            self.hide()
            event.ignore()
        else:
            # Fallback to normal close behavior if tray not available
            reply = CopyableMessageBox.question(
                self,
                self.translation_manager.get_text("app_title"),
                "Är du säker på att du vill avsluta?",
                CopyableMessageBox.Yes | CopyableMessageBox.No
            )
            if reply == CopyableMessageBox.Yes:
                # Stop backup monitoring timer
                if hasattr(self, 'backup_monitor_timer'):
                    self.backup_monitor_timer.stop()
                # Close database connection
                self.db_manager.close()
                event.accept()
            else:
                event.ignore()
