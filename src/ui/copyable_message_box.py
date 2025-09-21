"""
Copyable message box for error messages and other dialogs
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QTextEdit, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

class CopyableMessageBox(QDialog):
    """Custom message box with copy functionality"""
    
    # Message box types
    Information = 0
    Warning = 1
    Critical = 2
    Question = 3
    
    # Standard buttons
    Ok = 1
    Cancel = 2
    Yes = 4
    No = 8
    
    def __init__(self, parent=None, title="", text="", detailed_text="", icon=Information):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.result_value = 0
        # Read debug mode from parent if available
        self.debug_mode = False
        try:
            if parent is not None and hasattr(parent, 'app_manager'):
                self.debug_mode = bool(parent.app_manager.get_setting('debug_mode', False))
            else:
                # Fallback: read settings file directly
                import json, os
                settings_path = os.path.join('data', 'app_settings.json')
                if os.path.exists(settings_path):
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.debug_mode = bool(data.get('debug_mode', False))
        except Exception:
            self.debug_mode = False
        self.setup_ui(text, detailed_text, icon)
    
    def setup_ui(self, text, detailed_text, icon):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Main content layout
        content_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignTop)
        
        if icon == self.Information:
            icon_label.setText("ℹ️")
        elif icon == self.Warning:
            icon_label.setText("⚠️")
        elif icon == self.Critical:
            icon_label.setText("❌")
        elif icon == self.Question:
            icon_label.setText("❓")
        
        icon_label.setStyleSheet("font-size: 24px;")
        content_layout.addWidget(icon_label)
        
        # Text content
        text_layout = QVBoxLayout()
        
        # Main text
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        # Always allow selecting text; enable click-to-copy only in debug mode
        self.text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if self.debug_mode:
            # Clicking text copies content
            self.text_label.mousePressEvent = lambda e: self.copy_to_clipboard()
        text_layout.addWidget(self.text_label)
        
        # Detailed text (if provided)
        if detailed_text:
            self.detailed_text = QTextEdit()
            self.detailed_text.setPlainText(detailed_text)
            self.detailed_text.setReadOnly(True)
            self.detailed_text.setMaximumHeight(100)
            if self.debug_mode:
                # Clicking details also copies content
                self.detailed_text.mousePressEvent = lambda e: self.copy_to_clipboard()
            text_layout.addWidget(self.detailed_text)
        
        content_layout.addLayout(text_layout)
        layout.addLayout(content_layout)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Copy button (shown only in debug mode)
        self.copy_btn = QPushButton("Kopiera")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.apply_button_style(self.copy_btn)
        if not self.debug_mode:
            self.copy_btn.hide()
        button_layout.addWidget(self.copy_btn)
        
        # OK button
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setDefault(True)
        self.apply_button_style(self.ok_btn)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def apply_button_style(self, button):
        """Apply logout button matching style to button"""
        button_style = """
            QPushButton {
                font-size: 10px; 
                padding: 2px 6px;
                min-width: 60px;
                max-width: 60px;
                min-height: 20px;
                max-height: 20px;
                border-radius: 6px;
            }
        """
        button.setStyleSheet(button_style)
        button.setFixedSize(60, 20)
    
    def copy_to_clipboard(self):
        """Copy message content to clipboard"""
        clipboard = QApplication.clipboard()
        
        # Get all text content
        content = self.text_label.text()
        
        # Add detailed text if available
        if hasattr(self, 'detailed_text'):
            content += "\n\nDetaljer:\n" + self.detailed_text.toPlainText()
        
        clipboard.setText(content)
        
        # Temporarily change button text to show feedback
        original_text = self.copy_btn.text()
        self.copy_btn.setText("Kopierat!")
        self.copy_btn.setEnabled(False)
        
        # Reset button after 1 second
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: (
            self.copy_btn.setText(original_text),
            self.copy_btn.setEnabled(True)
        ))
    
    def add_button(self, text, role):
        """Add custom button"""
        btn = QPushButton(text)
        if role == self.Yes:
            btn.clicked.connect(lambda: self.done(self.Yes))
        elif role == self.No:
            btn.clicked.connect(lambda: self.done(self.No))
        elif role == self.Cancel:
            btn.clicked.connect(lambda: self.done(self.Cancel))
        
        # Apply logout button matching style
        self.apply_button_style(btn)
        
        # Insert before OK button
        layout = self.layout().itemAt(1).layout()  # Button layout
        layout.insertWidget(layout.count() - 1, btn)
        return btn
    
    @staticmethod
    def information(parent, title, text, detailed_text=""):
        """Show information message"""
        msg = CopyableMessageBox(parent, title, text, detailed_text, CopyableMessageBox.Information)
        return msg.exec()
    
    @staticmethod
    def warning(parent, title, text, detailed_text=""):
        """Show warning message"""
        msg = CopyableMessageBox(parent, title, text, detailed_text, CopyableMessageBox.Warning)
        return msg.exec()
    
    @staticmethod
    def critical(parent, title, text, detailed_text=""):
        """Show critical error message"""
        msg = CopyableMessageBox(parent, title, text, detailed_text, CopyableMessageBox.Critical)
        return msg.exec()
    
    @staticmethod
    def question(parent, title, text, buttons=None):
        """Show question dialog"""
        msg = CopyableMessageBox(parent, title, text, "", CopyableMessageBox.Question)
        
        # Remove default OK button
        msg.ok_btn.hide()
        
        if buttons is None:
            buttons = CopyableMessageBox.Yes | CopyableMessageBox.No
        
        if buttons & CopyableMessageBox.Yes:
            msg.add_button("Ja", CopyableMessageBox.Yes)
        if buttons & CopyableMessageBox.No:
            msg.add_button("Nej", CopyableMessageBox.No)
        if buttons & CopyableMessageBox.Cancel:
            msg.add_button("Avbryt", CopyableMessageBox.Cancel)
        
        return msg.exec()
