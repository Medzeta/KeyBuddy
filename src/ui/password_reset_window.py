from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QPushButton, QFrame, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
import os

class PasswordResetWindow(QDialog):
    """Window for resetting password with token"""
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.setWindowTitle("Återställ lösenord - KeyBuddy")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        # Styling handled by global CSS system
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Header with logo
        header_layout = QHBoxLayout()
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join("assets", "Kaybuddy_ikon.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("🔑")
            # Logo styling handled by global CSS
        
        # Title
        title_label = QLabel("Återställ lösenord")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setProperty("kb_label_type", "title")
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Instructions
        instructions = QLabel(
            "Ange återställningskoden som skickades till din e-post och välj ett nytt lösenord."
        )
        instructions.setWordWrap(True)
        instructions.setProperty("kb_label_type", "caption")
        layout.addWidget(instructions)
        
        # Token input
        token_label = QLabel("Återställningskod:")
        token_label.setProperty("kb_label_type", "subtitle")
        layout.addWidget(token_label)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Ange koden från e-postmeddelandet")
        layout.addWidget(self.token_input)
        
        # New password input
        password_label = QLabel("Nytt lösenord:")
        password_label.setProperty("kb_label_type", "subtitle")
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Ange ditt nya lösenord")
        layout.addWidget(self.password_input)
        
        # Confirm password input
        confirm_label = QLabel("Bekräfta lösenord:")
        confirm_label.setProperty("kb_label_type", "subtitle")
        layout.addWidget(confirm_label)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText("Bekräfta ditt nya lösenord")
        layout.addWidget(self.confirm_input)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        # Separator styling handled by global CSS
        layout.addWidget(separator)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Avbryt")
        self.cancel_button.setProperty("kb_button_type", "secondary")
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton("Återställ lösenord")
        self.reset_button.clicked.connect(self.reset_password)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        
        layout.addLayout(button_layout)
        
        # Connect Enter key to reset
        self.confirm_input.returnPressed.connect(self.reset_password)
        
    def reset_password(self):
        """Reset password with token"""
        token = self.token_input.text().strip()
        new_password = self.password_input.text()
        confirm_password = self.confirm_input.text()
        
        # Validation
        if not token:
            self.show_error("Ange återställningskoden")
            return
            
        if not new_password:
            self.show_error("Ange ett nytt lösenord")
            return
            
        if len(new_password) < 8:
            self.show_error("Lösenordet måste vara minst 8 tecken långt")
            return
            
        if new_password != confirm_password:
            self.show_error("Lösenorden matchar inte")
            return
        
        # Attempt password reset
        success, message = self.auth_manager.reset_password(token, new_password)
        
        if success:
            QMessageBox.information(self, "Framgång", message)
            self.accept()
        else:
            self.show_error(message)
    
    def show_error(self, message):
        """Show error message"""
        QMessageBox.warning(self, "Fel", message)
        
    def set_token(self, token):
        """Pre-fill token if provided"""
        self.token_input.setText(token)
