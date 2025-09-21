from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QPushButton, QMessageBox, QTextEdit)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

class EmailVerificationWindow(QDialog):
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.setWindowTitle("E-postverifiering")
        self.setFixedSize(500, 400)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the email verification window UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("E-postverifiering")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Instructions
        instructions = QLabel(
            "Ett verifieringsmail har skickats till din e-postadress.\n"
            "Kontrollera din inkorg och klicka på verifieringslänken.\n\n"
            "Alternativt kan du ange verifieringskoden nedan:"
        )
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        # Token input
        token_layout = QHBoxLayout()
        token_label = QLabel("Verifieringskod:")
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Ange verifieringskod här...")
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        layout.addLayout(token_layout)
        
        # Verify button
        self.verify_btn = QPushButton("Verifiera")
        self.verify_btn.clicked.connect(self.verify_email)
        layout.addWidget(self.verify_btn)
        
        # Resend button
        self.resend_btn = QPushButton("Skicka nytt mail")
        self.resend_btn.clicked.connect(self.resend_email)
        layout.addWidget(self.resend_btn)
        
        # Manual verification section
        layout.addWidget(QLabel(""))  # Spacer
        manual_label = QLabel("För utveckling - manuell verifiering:")
        manual_font = QFont()
        manual_font.setBold(True)
        manual_label.setFont(manual_font)
        layout.addWidget(manual_label)
        
        self.manual_text = QTextEdit()
        self.manual_text.setMaximumHeight(100)
        self.manual_text.setReadOnly(True)
        layout.addWidget(self.manual_text)
        
        # Close button
        close_btn = QPushButton("Stäng")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
    def set_manual_token(self, email: str, token: str):
        """Set manual verification token for development"""
        self.manual_text.setText(f"E-post: {email}\nEtt verifieringsmail har skickats till din e-postadress.\nKontrollera din inkorg för verifieringskoden.")
        
    def verify_email(self):
        """Verify email with token"""
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Fel", "Ange verifieringskod")
            return
            
        success, message = self.auth_manager.verify_email(token)
        
        if success:
            QMessageBox.information(self, "Verifiering lyckades", message)
            self.accept()  # Close dialog with success
        else:
            QMessageBox.critical(self, "Verifiering misslyckades", message)
            
    def resend_email(self):
        """Resend verification email (placeholder)"""
        QMessageBox.information(
            self, 
            "Mail skickat", 
            "Ett nytt verifieringsmail har skickats till din e-postadress."
        )
