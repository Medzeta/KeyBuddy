"""
Login window with 2FA support and modern UI
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QPushButton, QTabWidget, QFrame,
                                QProgressBar, QDialog, QMessageBox, QCheckBox,
                                QInputDialog, QDialogButtonBox, QTextEdit, QGroupBox,
                                QFormLayout)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QPixmap, QFont
import os
import sys
import base64
from io import BytesIO

from .styles import KeyBuddyButton, KeyBuddyLineEdit, ButtonType, FieldType, ThemeManager
from ..core.auth import AuthManager

class TwoFactorDialog(QDialog):
    """Dialog for 2FA setup and verification"""
    
    def __init__(self, parent=None, qr_code_data=None, translation_manager=None):
        super().__init__(parent)
        self.translation_manager = translation_manager
        self.qr_code_data = qr_code_data
        self.setup_ui()
    
    def setup_ui(self):
        """Setup 2FA dialog UI"""
        self.setWindowTitle("2FA Verifiering")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Skanna QR-koden med Google Authenticator eller liknande app, "
            "och ange sedan den 6-siffriga koden nedan:"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # QR Code display
        if self.qr_code_data:
            qr_label = QLabel()
            qr_label.setAlignment(Qt.AlignCenter)
            
            # Convert base64 to QPixmap
            qr_data = base64.b64decode(self.qr_code_data)
            pixmap = QPixmap()
            pixmap.loadFromData(qr_data)
            qr_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            layout.addWidget(qr_label)
        
        # Code input
        self.code_input = KeyBuddyLineEdit(FieldType.STANDARD, "Ange 6-siffrig kod")
        self.code_input.setMaxLength(6)
        layout.addWidget(self.code_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_code(self):
        """Get entered 2FA code"""
        return self.code_input.text()

class LoginWorker(QThread):
    """Worker thread for login operations"""
    
    login_result = Signal(bool, str, dict)
    
    def __init__(self, auth_manager, username, password, totp_code=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.username = username
        self.password = password
        self.totp_code = totp_code
    
    def run(self):
        """Perform login in background thread"""
        success, message, data = self.auth_manager.login(
            self.username, self.password, self.totp_code
        )
        self.login_result.emit(success, message, data)

class LoginWindow(QWidget):
    """Login window with registration and 2FA support"""
    
    login_successful = Signal(dict)
    
    def __init__(self, app_manager, db_manager, translation_manager):
        super().__init__()
        self.app_manager = app_manager
        self.db_manager = db_manager
        self.translation_manager = translation_manager
        self.auth_manager = AuthManager(db_manager)
        self.login_worker = None
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        self.setup_ui()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup login UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(50, 150, 50, 50)  # Force more top margin to center better
        
        # Removed title and subtitle as requested
        
        # Tab widget for login/register
        self.tab_widget = QTabWidget()
        self.tab_widget.setMaximumWidth(500)  # Slightly wider for better tab styling
        self.tab_widget.setMinimumWidth(450)  # Ensure consistent width
        
        # Login tab
        self.login_tab = self.create_login_tab()
        self.tab_widget.addTab(self.login_tab, self.translation_manager.get_text("login"))
        
        # Register tab
        self.register_tab = self.create_register_tab()
        self.tab_widget.addTab(self.register_tab, self.translation_manager.get_text("register"))
        
        # Just add the widget without stretch - let margins handle positioning
        layout.addWidget(self.tab_widget)
        
        # Text fields will use global styling automatically - no manual styling needed
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        # Make it match the login form width and look compact
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("")
        self.progress_bar.setFixedHeight(14)
        # Match the tab widget max width (login form width)
        self.progress_bar.setMaximumWidth(self.tab_widget.maximumWidth())
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar, 0, Qt.AlignCenter)
        
        # Set focus to username field when window is shown
        self.login_username.setFocus()
    
    def create_login_tab(self):
        """Create login tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Login form
        form_group = QGroupBox("Logga in")
        form_layout = QFormLayout(form_group)
        
        self.login_username = KeyBuddyLineEdit(FieldType.STANDARD, "Användarnamn eller e-post")
        self.login_username.setObjectName("login_username")
        form_layout.addRow(self.translation_manager.get_text("username") + ":", self.login_username)
        
        self.login_password = KeyBuddyLineEdit(FieldType.STANDARD, "Lösenord")
        self.login_password.setObjectName("login_password")
        self.login_password.setEchoMode(QLineEdit.Password)
        form_layout.addRow(self.translation_manager.get_text("password") + ":", self.login_password)
        
        layout.addWidget(form_group)
        
        # Keybuddy logo
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        
        # Load and scale the KeyBuddy logo (works in script and PyInstaller exe)
        try:
            # Determine base path depending on runtime
            if getattr(sys, 'frozen', False):
                base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            else:
                # Project root: ../../../ from this file
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            logo_path = os.path.join(base_path, 'assets', 'KeyBuddy_Logo.png')
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                # Scale the logo to twice the original size (400x200 instead of 200x100)
                scaled_pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
            else:
                # Fallback if logo file doesn't exist
                logo_label.setText("KEYBUDDY")
                logo_label.setProperty("class", "logo-text")
        except Exception:
            # Fallback text if there's any error loading the image
            logo_label.setText("KEYBUDDY")
            logo_label.setProperty("class", "logo-text")
        
        layout.addWidget(logo_label)
        
        # Login button
        self.login_btn = KeyBuddyButton(self.translation_manager.get_text("login"), ButtonType.PRIMARY)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        # Forgot password link
        forgot_btn = KeyBuddyButton("Glömt lösenord?", ButtonType.SECONDARY)
        forgot_btn.clicked.connect(self.forgot_password)
        layout.addWidget(forgot_btn)
        
        # Enable enter key for login
        self.login_password.returnPressed.connect(self.handle_login)
        self.login_username.returnPressed.connect(self.handle_login)
        
        return widget
    
    def create_register_tab(self):
        """Create registration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Registration form
        form_group = QGroupBox("Skapa konto")
        form_layout = QFormLayout(form_group)
        
        self.reg_username = KeyBuddyLineEdit(FieldType.STANDARD, "Användarnamn")
        form_layout.addRow(self.translation_manager.get_text("username") + ":", self.reg_username)
        
        self.reg_email = KeyBuddyLineEdit(FieldType.STANDARD, "E-postadress")
        form_layout.addRow(self.translation_manager.get_text("email") + ":", self.reg_email)
        
        self.reg_password = KeyBuddyLineEdit(FieldType.STANDARD, "Lösenord")
        self.reg_password.setEchoMode(QLineEdit.Password)
        form_layout.addRow(self.translation_manager.get_text("password") + ":", self.reg_password)
        
        self.reg_confirm_password = KeyBuddyLineEdit(FieldType.STANDARD, "Bekräfta lösenord")
        self.reg_confirm_password.setEchoMode(QLineEdit.Password)
        form_layout.addRow(self.translation_manager.get_text("confirm_password") + ":", self.reg_confirm_password)
        
        # Company information (required fields)
        self.reg_company_name = KeyBuddyLineEdit(FieldType.STANDARD, "Bolagsnamn (obligatoriskt)")
        form_layout.addRow("Bolagsnamn *:", self.reg_company_name)
        
        self.reg_org_number = KeyBuddyLineEdit(FieldType.STANDARD, "Organisationsnummer (obligatoriskt)")
        form_layout.addRow("Org-nummer *:", self.reg_org_number)
        
        layout.addWidget(form_group)
        
        # Register button
        self.register_btn = KeyBuddyButton(self.translation_manager.get_text("register"), ButtonType.PRIMARY)
        self.register_btn.clicked.connect(self.handle_register)
        layout.addWidget(self.register_btn)
        
        # Info text
        info_text = QLabel(
            "Efter registrering kommer du att få ett e-postmeddelande "
            "för att verifiera ditt konto."
        )
        info_text.setWordWrap(True)
        info_text.setProperty("class", "subtitle")
        layout.addWidget(info_text)
        
        return widget
    
    def apply_theme(self):
        """Apply current theme to login window"""
        print("=== APPLY_THEME CALLED ===")
        theme_name = self.app_manager.get_setting("theme", "light")
        stylesheet = self.theme_manager.get_stylesheet(theme_name)
        
        # Add rounded corners for login window
        rounded_corners_style = """
        LoginWindow {
            border-radius: 12px;
        }
        """
        
        # Combine global stylesheet with rounded corners
        combined_stylesheet = stylesheet + rounded_corners_style
        print(f"Setting main stylesheet with {len(combined_stylesheet)} characters")
        self.setStyleSheet(combined_stylesheet)
        
        # All text fields now use global styling automatically - no manual styling needed
        print("All text fields will use global QLineEdit styling from theme system")
    
    def handle_login(self):
        """Handle login attempt"""
        username = self.login_username.text().strip()
        password = self.login_password.text()
        
        if not username or not password:
            self.show_message("Fel", "Fyll i både användarnamn och lösenord", "error")
            return
        
        # Show progress
        self.set_loading(True, "Loggar in...")
        
        # Start login worker
        self.login_worker = LoginWorker(self.auth_manager, username, password)
        self.login_worker.login_result.connect(self.on_login_result)
        self.login_worker.start()
    
    def on_login_result(self, success, message, data):
        """Handle login result"""
        print(f"DEBUG LOGIN: success={success}, message={message}, data={data}")
        self.set_loading(False)
        
        if success:
            if data.get('requires_2fa'):
                print("DEBUG: 2FA required, showing dialog")
                # Show 2FA dialog
                self.show_2fa_dialog(data)
            else:
                print("DEBUG: Login successful, emitting signal")
                # Login successful
                self.login_successful.emit(data)
                self.clear_login_form()
        else:
            print(f"DEBUG: Login failed: {message}")
            # If the email is not verified, show verification dialog to enter code
            if isinstance(message, str) and "E-post inte verifierad" in message:
                try:
                    from .email_verification_window import EmailVerificationWindow
                    dialog = EmailVerificationWindow(self.auth_manager, self)
                    # Optionally show hint text; we don't require token here
                    dialog.set_manual_token(self.login_username.text().strip(), "")
                    if dialog.exec() == QDialog.Accepted:
                        # Retry login automatically after successful verification
                        username = self.login_username.text().strip()
                        password = self.login_password.text()
                        self.set_loading(True, "Verifierar och loggar in...")
                        self.login_worker = LoginWorker(self.auth_manager, username, password)
                        self.login_worker.login_result.connect(self.on_login_result)
                        self.login_worker.start()
                        return
                except Exception as e:
                    print(f"DEBUG: Could not open EmailVerificationWindow: {e}")
            
            # Fallback: show the error
            self.show_message("Inloggningsfel", message, "error")
    
    def show_2fa_dialog(self, user_data):
        """Show 2FA verification dialog"""
        # Generate QR code for first-time setup
        qr_code = self.auth_manager.generate_qr_code(
            user_data.get('email', ''), 
            user_data.get('totp_secret', '')
        )
        
        dialog = TwoFactorDialog(self, qr_code, self.translation_manager)
        
        if dialog.exec() == QDialog.Accepted:
            totp_code = dialog.get_code()
            if totp_code and len(totp_code) == 6:
                # Verify 2FA code
                self.set_loading(True, "Verifierar 2FA...")
                username = self.login_username.text().strip()
                password = self.login_password.text()
                
                self.login_worker = LoginWorker(self.auth_manager, username, password, totp_code)
                self.login_worker.login_result.connect(self.on_login_result)
                self.login_worker.start()
            else:
                self.show_message("Fel", "Ange en giltig 6-siffrig kod", "error")
    
    def handle_register(self):
        """Handle registration attempt"""
        username = self.reg_username.text().strip()
        email = self.reg_email.text().strip()
        password = self.reg_password.text()
        confirm_password = self.reg_confirm_password.text()
        company_name = self.reg_company_name.text().strip()
        org_number = self.reg_org_number.text().strip()
        
        # Validation
        if not all([username, email, password, confirm_password, company_name, org_number]):
            self.show_message("Fel", "Fyll i alla fält inklusive bolagsnamn och org-nummer", "error")
            return
        
        if password != confirm_password:
            self.show_message("Fel", "Lösenorden matchar inte", "error")
            return
        
        if len(password) < 8:
            self.show_message("Fel", "Lösenordet måste vara minst 8 tecken", "error")
            return
        
        if "@" not in email:
            self.show_message("Fel", "Ange en giltig e-postadress", "error")
            return
        
        # Show progress with message
        self.set_loading(True, "Registrerar konto...")
        
        # Register user with company info
        success, message = self.auth_manager.register_user(username, email, password, company_name, org_number)
        
        self.set_loading(False)
        
        if success:
            # Show email verification window
            from .email_verification_window import EmailVerificationWindow
            verification_window = EmailVerificationWindow(self.auth_manager, self)
            verification_window.set_manual_token(email, "")
            verification_window.exec()
            
            self.show_message("Registrering lyckades", message, "success")
            self.clear_register_form()
            self.tab_widget.setCurrentIndex(0)  # Switch to login tab
        else:
            self.show_message("Registreringsfel", message, "error")
    
    def forgot_password(self):
        """Handle forgot password"""
        # Custom dialog to allow a wider email input field
        dlg = QDialog(self)
        dlg.setWindowTitle("Glömt lösenord")
        dlg.setModal(True)
        v = QVBoxLayout(dlg)
        lbl = QLabel("Ange din e-postadress:")
        v.addWidget(lbl)
        email_edit = QLineEdit()
        email_edit.setPlaceholderText("namn@foretag.se")
        # Make the input wide enough to see long addresses fully
        email_edit.setMinimumWidth(380)
        v.addWidget(email_edit)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        v.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec() == QDialog.Accepted:
            email = email_edit.text().strip()
            if not email:
                self.show_message("Fel", "Ange en e-postadress", "error")
                return
            success, message = self.auth_manager.request_password_reset(email)
            if success:
                self.show_message("Återställning av lösenord", message, "success")
                # Open password reset window
                from .password_reset_window import PasswordResetWindow
                reset_window = PasswordResetWindow(self.auth_manager, self)
                reset_window.exec()
            else:
                self.show_message("Återställning av lösenord", message, "error")

    def set_loading(self, loading, message: str = ""):
        """Set loading state with optional message shown inside the progress bar"""
        self.login_btn.setEnabled(not loading)
        self.register_btn.setEnabled(not loading)
        
        if loading:
            # Keep width aligned with the login form container
            self.progress_bar.setMaximumWidth(self.tab_widget.maximumWidth())
            self.progress_bar.setFormat(message if message else "Laddar...")
            self.progress_bar.show()
        else:
            self.progress_bar.setFormat("")
            self.progress_bar.hide()
    
    def show_message(self, title, message, msg_type="info"):
        """Show message dialog"""
        if msg_type == "error":
            QMessageBox.critical(self, title, message)
        elif msg_type == "success":
            QMessageBox.information(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def clear_login_form(self):
        """Clear login form fields"""
        try:
            self.login_username.clear()
            self.login_password.clear()
        except Exception:
            pass
    
    def clear_register_form(self):
        """Clear registration form"""
        self.reg_username.clear()
        self.reg_email.clear()
        self.reg_password.clear()
        self.reg_confirm_password.clear()
        self.reg_company_name.clear()
        self.reg_org_number.clear()
    
    def showEvent(self, event):
        """Handle show event to set focus"""
        super().showEvent(event)
        # Set focus to username field when window is shown
        self.login_username.setFocus()
    
    def update_ui_text(self):
        """Update UI text for current language"""
        # Update tab titles
        self.tab_widget.setTabText(0, self.translation_manager.get_text("login"))
        self.tab_widget.setTabText(1, self.translation_manager.get_text("register"))
        
        # Update button text
        self.login_btn.setText(self.translation_manager.get_text("login"))
        self.register_btn.setText(self.translation_manager.get_text("register"))
