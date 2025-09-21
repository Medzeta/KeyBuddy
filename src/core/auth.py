"""
Authentication system with 2FA support
Handles user registration, login, email verification, and TOTP
"""

import bcrypt
import pyotp
import qrcode
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .database import DatabaseManager
from .logger import UserLogger
import hashlib
import pyotp
import qrcode
from io import BytesIO
import base64
from typing import Optional, Dict, Tuple, Dict
from datetime import datetime, timedelta
import io
import base64
from PIL import Image
import secrets

class AuthManager:
    """Manages user authentication and 2FA"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.current_user = None
        self.logger = UserLogger(db_manager)
        
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_totp_secret(self) -> str:
        """Generate TOTP secret for 2FA"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, email: str, secret: str) -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name="Keybuddy"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 string
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def generate_verification_token(self) -> str:
        """Generate email verification token"""
        return secrets.token_urlsafe(32)
    
    def register_user(self, username: str, email: str, password: str, company_name: str = "", org_number: str = "") -> Tuple[bool, str]:
        """Register new user"""
        try:
            # Check if user already exists
            existing_user = self.db_manager.execute_query(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email)
            )
            
            if existing_user:
                return False, "Användare eller e-post finns redan"
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Generate TOTP secret and verification token
            totp_secret = self.generate_totp_secret()
            verification_token = self.generate_verification_token()
            
            # Insert user with company info
            user_id = self.db_manager.execute_update(
                """INSERT INTO users (username, email, password_hash, totp_secret, 
                   verification_token, company_name, org_number) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (username, email, password_hash, totp_secret, verification_token, company_name, org_number)
            )
            
            # Send verification email
            self.send_verification_email(email, verification_token)
            
            return True, "Användare registrerad. Kontrollera din e-post för verifiering."
            
        except Exception as e:
            return False, f"Registrering misslyckades: {str(e)}"
    
    def verify_email(self, token: str) -> Tuple[bool, str]:
        """Verify email with token"""
        try:
            user = self.db_manager.execute_query(
                "SELECT id FROM users WHERE verification_token = ?",
                (token,)
            )
            
            if not user:
                return False, "Ogiltig verifieringstoken"
            
            self.db_manager.execute_update(
                "UPDATE users SET is_verified = TRUE, verification_token = NULL WHERE verification_token = ?",
                (token,)
            )
            
            return True, "E-post verifierad framgångsrikt"
            
        except Exception as e:
            return False, f"Verifiering misslyckades: {str(e)}"
    
    def login(self, username: str, password: str, totp_token: str = None) -> Tuple[bool, str, Dict]:
        """Login user with optional 2FA"""
        try:
            user = self.db_manager.execute_query(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (username, username)
            )
            
            if not user:
                return False, "Ogiltig användare eller lösenord", {}
            
            user = user[0]
            
            # Verify password with bcrypt, with legacy SHA-256 fallback + migration
            try:
                bcrypt_ok = self.verify_password(password, user['password_hash'])
            except Exception:
                # If stored hash is not bcrypt, treat as not ok to try legacy
                bcrypt_ok = False
            if not bcrypt_ok:
                import hashlib, re
                stored = user['password_hash']
                # Detect legacy sha256 hex hash
                if isinstance(stored, str) and re.fullmatch(r"[0-9a-fA-F]{64}", stored or ""):
                    legacy_ok = hashlib.sha256(password.encode('utf-8')).hexdigest() == stored
                    if not legacy_ok:
                        return False, "Ogiltig användare eller lösenord", {}
                    # Migrate to bcrypt
                    import bcrypt as _bcrypt
                    new_hash = _bcrypt.hashpw(password.encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')
                    try:
                        self.db_manager.execute_update(
                            "UPDATE users SET password_hash = ? WHERE id = ?",
                            (new_hash, user['id'])
                        )
                        user['password_hash'] = new_hash
                    except Exception:
                        pass
                else:
                    return False, "Ogiltig användare eller lösenord", {}
            
            # Check if email is verified (skip for admin)
            if not user['is_verified'] and user['username'] != 'admin':
                return False, "E-post inte verifierad. Kontrollera din inkorg.", {}
            
            # Disallow login for inactivated users
            if 'is_active' in user.keys() and not user['is_active']:
                return False, "Användare inaktiverad av systemadmin", {}
            
            # Check if 2FA is enabled for this user
            two_factor_enabled = user['two_factor_enabled'] if 'two_factor_enabled' in user.keys() else True
            if two_factor_enabled and user['username'] != 'admin':
                # Verify TOTP if provided
                if totp_token:
                    if not self.verify_totp(user['totp_secret'], totp_token):
                        return False, "Ogiltig 2FA-kod", {}
                else:
                    # Return user data for 2FA setup if no token provided
                    return True, "2FA krävs", {
                        'user_id': user['id'],
                    'requires_2fa': True,
                    'totp_secret': user['totp_secret']
                }
            
            # Update last login
            self.db_manager.execute_update(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user['id'],)
            )
            
            self.current_user = dict(user)
            
            # Log successful login
            self.logger.log_login(user['id'], user['username'])
            
            return True, "Inloggning lyckades", {
                'user_id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'company_name': user['company_name'],
                'org_number': user['org_number'],
                'role': user['role'] if 'role' in user.keys() else 'user',
                'is_admin': user['is_admin'] if 'is_admin' in user.keys() else False
            }
            
        except Exception as e:
            return False, f"Inloggning misslyckades: {str(e)}", {}
    
    def logout(self):
        """Logout current user"""
        if self.current_user:
            # Log logout before clearing user
            self.logger.log_logout(self.current_user['id'], self.current_user['username'])
        self.current_user = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.current_user is not None
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user"""
        return self.current_user
    
    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """Request password reset"""
        try:
            user = self.db_manager.execute_query(
                "SELECT id FROM users WHERE email = ?",
                (email,)
            )
            
            if not user:
                return False, "E-post hittades inte"
            
            reset_token = self.generate_verification_token()
            
            self.db_manager.execute_update(
                "UPDATE users SET reset_token = ? WHERE email = ?",
                (reset_token, email)
            )
            
            self.send_reset_email(email, reset_token)
            
            return True, "Återställningslänk skickad till din e-post"
            
        except Exception as e:
            return False, f"Återställning misslyckades: {str(e)}"
    
    def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """Reset password with token"""
        try:
            user = self.db_manager.execute_query(
                "SELECT id FROM users WHERE reset_token = ?",
                (token,)
            )
            
            if not user:
                return False, "Ogiltig återställningstoken"
            
            password_hash = self.hash_password(new_password)
            
            self.db_manager.execute_update(
                "UPDATE users SET password_hash = ?, reset_token = NULL WHERE reset_token = ?",
                (password_hash, token)
            )
            
            return True, "Lösenord återställt framgångsrikt"
            
        except Exception as e:
            return False, f"Återställning misslyckades: {str(e)}"
    
    def get_smtp_config(self):
        """Get SMTP configuration from settings or use defaults"""
        try:
            import json
            import os
            
            # Try to load SMTP config from app_settings.json
            settings_path = os.path.join("data", "app_settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    smtp_config = settings.get('smtp', {})
                    if smtp_config.get('enabled', False):
                        return smtp_config
            
            # Default configuration (requires App Password)
            return {
                'enabled': True,
                'server': 'smtp.gmail.com',
                'port': 587,
                'email': 'keybuddyreg@gmail.com',
                'password': 'dyxu kgjb hxrj okky',  # Gmail App Password
                'use_tls': True
            }
        except Exception:
            # Fallback configuration
            return {
                'enabled': True,
                'server': 'smtp.gmail.com',
                'port': 587,
                'email': 'keybuddyreg@gmail.com',
                'password': 'dyxu kgjb hxrj okky',  # Gmail App Password
                'use_tls': True
            }

    def send_verification_email(self, email: str, token: str):
        """Send verification email with token"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Get SMTP configuration
            smtp_config = self.get_smtp_config()
            
            if not smtp_config.get('enabled', False):
                print("SMTP is disabled in configuration")
                print(f"Manual verification token for {email}: {token}")
                return
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "KeyBuddy - Verifiera din e-postadress"
            message["From"] = smtp_config['email']
            message["To"] = email
            
            # Create HTML content
            html = f"""
            <html>
              <body>
                <h2>Välkommen till KeyBuddy!</h2>
                <p>Tack för att du registrerat dig. Använd följande verifieringskod i KeyBuddy-applikationen:</p>
                <h3 style="background-color: #f0f0f0; padding: 10px; text-align: center; font-family: monospace;">{token}</h3>
                <p>Öppna KeyBuddy-applikationen och ange denna kod i verifieringsfönstret för att slutföra din registrering.</p>
                <br>
                <p>Med vänliga hälsningar,<br>KeyBuddy Team</p>
              </body>
            </html>
            """
            
            # Convert to MIMEText
            html_part = MIMEText(html, "html")
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                if smtp_config.get('use_tls', True):
                    server.starttls()
                server.login(smtp_config['email'], smtp_config['password'])
                server.sendmail(smtp_config['email'], email, message.as_string())
                
            print(f"Verification email sent successfully to {email}")
            print(f"SMTP server: {smtp_config['server']}:{smtp_config['port']}")
            print(f"From: {smtp_config['email']}")
            
        except Exception as e:
            print(f"SMTP ERROR: Failed to send verification email to {email}")
            print(f"Error details: {e}")
            print(f"SMTP Config - Server: {smtp_config.get('server', 'N/A')}")
            print(f"SMTP Config - Port: {smtp_config.get('port', 'N/A')}")
            print(f"SMTP Config - Email: {smtp_config.get('email', 'N/A')}")
            print(f"SMTP Config - Password length: {len(smtp_config.get('password', ''))}")
            print(f"Manual verification token for {email}: {token}")
            print(f"Copy this token to verify the account manually.")
    
    def send_reset_email(self, email: str, token: str):
        """Send password reset email"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Get SMTP configuration
            smtp_config = self.get_smtp_config()
            
            if not smtp_config.get('enabled', False):
                print("SMTP is disabled in configuration")
                print(f"Manual reset token for {email}: {token}")
                return
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "KeyBuddy - Återställ lösenord"
            message["From"] = smtp_config['email']
            message["To"] = email
            
            # Create HTML content
            html = f"""
            <html>
              <body>
                <h2>Återställ ditt KeyBuddy-lösenord</h2>
                <p>Du har begärt att återställa ditt lösenord. Använd följande kod i KeyBuddy-applikationen:</p>
                <h3 style="background-color: #f0f0f0; padding: 10px; text-align: center; font-family: monospace;">{token}</h3>
                <p>Öppna KeyBuddy-applikationen och ange denna kod för att återställa ditt lösenord.</p>
                <p>Om du inte begärt denna återställning kan du ignorera detta mail.</p>
                <br>
                <p>Med vänliga hälsningar,<br>KeyBuddy Team</p>
              </body>
            </html>
            """
            
            # Convert to MIMEText
            html_part = MIMEText(html, "html")
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                if smtp_config.get('use_tls', True):
                    server.starttls()
                server.login(smtp_config['email'], smtp_config['password'])
                server.sendmail(smtp_config['email'], email, message.as_string())
                
            print(f"Password reset email sent to {email}")
            
        except Exception as e:
            print(f"Failed to send reset email: {e}")
            print(f"Gmail requires App Password instead of regular password.")
            print(f"Manual reset token for {email}: {token}")
