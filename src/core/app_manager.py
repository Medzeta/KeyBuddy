"""
Application manager - handles global app state and settings
"""

import json
import os
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal

class AppManager(QObject):
    """Manages application state, settings, and global functionality"""
    
    # Signals for UI updates
    language_changed = Signal(str)
    theme_changed = Signal(str)
    logo_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.settings_file = "data/app_settings.json"
        self.settings = self._load_settings()
        self.current_user = None
        self.main_window = None
        self.backup_manager = None
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load application settings"""
        default_settings = {
            "language": "sv",  # Swedish default
            "theme": "light",
            "company_logo": "",
            "smtp_server": "",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "app_version": "1.0.0",
            "debug_mode": False
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        return default_settings
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_setting(self, key: str, default=None) -> Any:
        """Get setting value"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set setting value"""
        print(f"DEBUG: Setting {key} = {value}")
        self.settings[key] = value
        print(f"DEBUG: Current settings after update: {self.settings}")
        self.save_settings()
        print(f"DEBUG: Settings saved to file")
        
        # Emit signals for UI updates
        if key == "language":
            self.language_changed.emit(value)
        elif key == "theme":
            self.theme_changed.emit(value)
        elif key == "company_logo":
            self.logo_changed.emit(value)
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages"""
        return {
            "sv": "Svenska",
            "en": "English", 
            "no": "Norsk",
            "da": "Dansk",
            "fi": "Suomi",
            "ar": "العربية",
            "zh": "中文",
            "es": "Español"
        }
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get available themes"""
        return {
            "light": "Crystal Clear",
            "smokey": "Smokey Glass",
            "ocean": "Ocean Breeze",
            "purple": "Purple Dream",
            "sunset": "Sunset Glow",
            "neon_cyber": "Neon Cyberpunk",
            "volcanic_rage": "Volcanic Rage",
            "arctic_storm": "Arctic Storm",
            "toxic_waste": "Toxic Waste",
            "galaxy_dream": "Galaxy Dream",
            "desert_mirage": "Desert Mirage",
            "electric_blue": "Electric Blue",
            "cherry_bomb": "Cherry Bomb",
            "matrix_code": "Matrix Code",
            "royal_gold": "Royal Gold"
        }
    
    def set_current_user(self, user_data: Dict):
        """Set current user data"""
        self.current_user = user_data
        print(f"DEBUG: User logged in: {user_data.get('username', 'Unknown')}")
        
        # Trigger startup backup check after user login
        if self.backup_manager and hasattr(self.backup_manager, 'perform_startup_backup_check'):
            print("DEBUG: Triggering startup backup check after login")
            self.backup_manager.perform_startup_backup_check()
        else:
            print("DEBUG: No backup manager available for startup check")
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current user"""
        return self.current_user
    
    def clear_current_user(self):
        """Clear current user (logout)"""
        self.current_user = None

    def logout(self):
        """Public logout method for UI callers.
        Keeps backward compatibility with code expecting AppManager.logout().
        """
        self.clear_current_user()
    
    def initialize_backup_manager(self, db_manager):
        """Initialize global backup manager"""
        if self.backup_manager is None:
            from .backup_manager import BackupManager
            self.backup_manager = BackupManager(db_manager, delay_startup_backup=True)  # Delay startup backup
            self.db_manager = db_manager  # Store for email functionality
            # Connect to email notification handler
            self.backup_manager.backup_auto_completed.connect(self._handle_auto_backup_email)
    
    def _handle_auto_backup_email(self, backup_file: str):
        """Handle automatic backup email notifications"""
        try:
            backup_email_enabled = self.get_setting("backup_email_confirmation", False)
            print(f"DEBUG: Backup email confirmation enabled: {backup_email_enabled}")
            print(f"DEBUG: Backup file: {backup_file}")
            if backup_email_enabled:
                # Use the same email logic as settings_window for consistency
                self._send_backup_email_like_settings(backup_file, auto=True)
            else:
                print("DEBUG: Backup email confirmation is disabled")
        except Exception as e:
            print(f"Error sending backup email (auto): {e}")
    
    def _send_backup_email_like_settings(self, backup_file: str, auto: bool):
        """Send backup email using same logic as settings_window.py"""
        try:
            user = self.get_current_user() or {}
            print(f"DEBUG: Current user for backup email: {user}")
            recipient = user.get('email')
            print(f"DEBUG: Recipient email: {recipient}")
            if not recipient:
                print("No recipient email for backup confirmation")
                return
            
            # Use AuthManager SMTP configuration
            from .auth import AuthManager
            auth = AuthManager(self.db_manager)
            smtp_config = auth.get_smtp_config()
            if not smtp_config.get('enabled', False):
                print("SMTP disabled; skipping backup email")
                return
                
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from datetime import datetime
            
            subject = "KeyBuddy - Backup bekräftelse"
            when = datetime.now().strftime('%Y-%m-%d %H:%M')
            backup_type = "Automatisk" if auto else "Manuell"
            
            html = f"""
            <html>
              <body style='font-family:Segoe UI,Arial,sans-serif; color:#2c3e50;'>
                <div style='border:1px solid #e1e8ed; border-radius:8px; padding:16px;'>
                  <h2 style='margin:0 0 10px 0; color:#0078d4;'>KeyBuddy – Backup bekräftad</h2>
                  <p>En <b>{backup_type.lower()}</b> backup har skapats.</p>
                  <table style='border-collapse:collapse;'>
                    <tr><td style='padding:4px 8px; color:#555;'>Datum:</td><td style='padding:4px 8px;'>{when}</td></tr>
                    <tr><td style='padding:4px 8px; color:#555;'>Plats:</td><td style='padding:4px 8px;'>{backup_file}</td></tr>
                  </table>
                  <p style='margin-top:12px;'>Tack för att du använder <b>KeyBuddy</b>.</p>
                </div>
              </body>
            </html>
            """
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = smtp_config['email']
            message["To"] = recipient
            message.attach(MIMEText(html, "html"))
            
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                if smtp_config.get('use_tls', True):
                    server.starttls()
                server.login(smtp_config['email'], smtp_config['password'])
                server.sendmail(smtp_config['email'], recipient, message.as_string())
            print(f"Backup confirmation email sent to {recipient}")
            
        except Exception as e:
            print(f"Failed to send backup confirmation email: {e}")
