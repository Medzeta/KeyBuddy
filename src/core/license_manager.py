"""
License and copy protection system for KeyBuddy
Prevents unauthorized distribution and ensures legitimate usage
"""

import hashlib
import os
import platform
import uuid
import json
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import subprocess

# Optional import for process monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class LicenseManager:
    """Manages software licensing and copy protection"""
    
    def __init__(self):
        self.license_file = "data/license.dat"
        self.machine_id = self._generate_machine_id()
        self.encryption_key = self._derive_key()
        
    def _generate_machine_id(self):
        """Generate unique machine identifier based on hardware"""
        try:
            # Get multiple hardware identifiers
            identifiers = []
            
            # CPU info
            try:
                cpu_info = platform.processor()
                identifiers.append(cpu_info)
            except:
                pass
            
            # MAC address
            try:
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0,2*6,2)][::-1])
                identifiers.append(mac)
            except:
                pass
            
            # Motherboard serial (Windows)
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(['wmic', 'baseboard', 'get', 'serialnumber'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        serial = result.stdout.split('\n')[1].strip()
                        if serial and serial != "To be filled by O.E.M.":
                            identifiers.append(serial)
            except:
                pass
            
            # System UUID
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(['wmic', 'csproduct', 'get', 'uuid'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        system_uuid = result.stdout.split('\n')[1].strip()
                        if system_uuid:
                            identifiers.append(system_uuid)
            except:
                pass
            
            # Hard drive serial
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(['wmic', 'diskdrive', 'get', 'serialnumber'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines[1:]:
                            serial = line.strip()
                            if serial and len(serial) > 5:
                                identifiers.append(serial)
                                break
            except:
                pass
            
            # Fallback to basic system info
            if not identifiers:
                identifiers = [
                    platform.machine(),
                    platform.system(),
                    str(uuid.getnode())
                ]
            
            # Create hash from all identifiers
            combined = '|'.join(identifiers)
            machine_hash = hashlib.sha256(combined.encode()).hexdigest()
            
            return machine_hash[:32]  # Use first 32 characters
            
        except Exception as e:
            print(f"Error generating machine ID: {e}")
            # Fallback machine ID
            return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:32]
    
    def _derive_key(self):
        """Derive encryption key for license data"""
        # Use machine ID as part of key derivation
        salt = b'keybuddy_license_salt_2024'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.machine_id.encode()))
        return key
    
    def create_license(self, license_data):
        """Create encrypted license file"""
        try:
            # Add machine binding and timestamps
            license_data.update({
                'machine_id': self.machine_id,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=365)).isoformat(),
                'version': '1.0.0',
                'features': ['full_access'],
                'max_users': license_data.get('max_users', 5)
            })
            
            # Encrypt license data
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(json.dumps(license_data).encode())
            
            # Save to file
            os.makedirs(os.path.dirname(self.license_file), exist_ok=True)
            with open(self.license_file, 'wb') as f:
                f.write(encrypted_data)
            
            return True
            
        except Exception as e:
            print(f"Error creating license: {e}")
            return False
    
    def validate_license(self):
        """Validate current license"""
        try:
            if not os.path.exists(self.license_file):
                return False, "Ingen licens hittades"
            
            # Read and decrypt license
            with open(self.license_file, 'rb') as f:
                encrypted_data = f.read()
            
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            license_data = json.loads(decrypted_data.decode())
            
            # Validate machine binding
            if license_data.get('machine_id') != self.machine_id:
                return False, "Licensen är inte giltig för denna dator"
            
            # Check expiration
            expires_at = datetime.fromisoformat(license_data.get('expires_at'))
            if datetime.now() > expires_at:
                return False, "Licensen har gått ut"
            
            # Check if license is active
            if not license_data.get('active', True):
                return False, "Licensen är inaktiverad"
            
            return True, license_data
            
        except Exception as e:
            print(f"Error validating license: {e}")
            return False, f"Licensvalidering misslyckades: {str(e)}"
    
    def get_license_info(self):
        """Get license information"""
        is_valid, result = self.validate_license()
        
        if is_valid:
            return {
                'valid': True,
                'expires_at': result.get('expires_at'),
                'max_users': result.get('max_users', 5),
                'features': result.get('features', []),
                'company': result.get('company', ''),
                'license_type': result.get('license_type', 'Standard')
            }
        else:
            return {
                'valid': False,
                'error': result,
                'machine_id': self.machine_id
            }
    
    def check_runtime_integrity(self):
        """Check for runtime tampering and debugging"""
        try:
            # Check for common debugging tools if psutil is available
            if PSUTIL_AVAILABLE:
                suspicious_processes = [
                    'ollydbg.exe', 'x64dbg.exe', 'windbg.exe', 'ida.exe', 'ida64.exe',
                    'cheatengine.exe', 'processhacker.exe', 'procmon.exe', 'wireshark.exe'
                ]
                
                try:
                    running_processes = [p.name().lower() for p in psutil.process_iter(['name'])]
                    
                    for suspicious in suspicious_processes:
                        if suspicious in running_processes:
                            return False, f"Otillåten process upptäckt: {suspicious}"
                except:
                    pass  # Continue without process checking if it fails
            
            # Check for debugger attachment (Windows)
            if platform.system() == "Windows":
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    if kernel32.IsDebuggerPresent():
                        return False, "Debugger upptäckt"
                except:
                    pass
            
            return True, "OK"
            
        except Exception as e:
            print(f"Error checking runtime integrity: {e}")
            return True, "OK"  # Don't block on errors
    
    def log_usage(self, activity):
        """Log software usage for license compliance"""
        try:
            log_file = "data/usage.log"
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'machine_id': self.machine_id,
                'activity': activity,
                'user': os.getlogin() if hasattr(os, 'getlogin') else 'unknown'
            }
            
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            print(f"Error logging usage: {e}")
    
    def create_trial_license(self, days=30):
        """Create trial license"""
        trial_data = {
            'license_type': 'Trial',
            'company': 'Trial User',
            'max_users': 1,
            'active': True
        }
        
        # Override expiration for trial
        trial_data.update({
            'machine_id': self.machine_id,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=days)).isoformat(),
            'version': '1.0.0',
            'features': ['limited_access']
        })
        
        return self.create_license(trial_data)

class LicenseDialog:
    """License activation dialog"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.license_manager = LicenseManager()
    
    def show_activation_dialog(self):
        """Show license activation dialog"""
        from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                      QLineEdit, QPushButton, QTextEdit, QTabWidget,
                                      QWidget, QMessageBox)
        
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("KeyBuddy - Licensaktivering")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Info text
        info_label = QLabel("""
        <h3>Välkommen till KeyBuddy!</h3>
        <p>För att använda KeyBuddy behöver du en giltig licens.</p>
        <p>Kontakta din leverantör för att få en licensnyckel.</p>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Tabs
        tab_widget = QTabWidget()
        
        # License activation tab
        activation_tab = QWidget()
        activation_layout = QVBoxLayout(activation_tab)
        
        activation_layout.addWidget(QLabel("Licensnyckel:"))
        license_key_edit = QLineEdit()
        license_key_edit.setPlaceholderText("Ange din licensnyckel här...")
        activation_layout.addWidget(license_key_edit)
        
        activation_layout.addWidget(QLabel("Företagsnamn:"))
        company_edit = QLineEdit()
        company_edit.setPlaceholderText("Ditt företagsnamn")
        activation_layout.addWidget(company_edit)
        
        activate_btn = QPushButton("Aktivera licens")
        activation_layout.addWidget(activate_btn)
        
        tab_widget.addTab(activation_tab, "Aktivera licens")
        
        # Trial tab
        trial_tab = QWidget()
        trial_layout = QVBoxLayout(trial_tab)
        
        trial_info = QLabel("""
        <p>Starta en 30-dagars testperiod för att prova KeyBuddy.</p>
        <p><b>Begränsningar under testperioden:</b></p>
        <ul>
        <li>Endast en användare</li>
        <li>Begränsad funktionalitet</li>
        <li>30 dagars tidsgräns</li>
        </ul>
        """)
        trial_info.setWordWrap(True)
        trial_layout.addWidget(trial_info)
        
        trial_btn = QPushButton("Starta testperiod")
        trial_layout.addWidget(trial_btn)
        
        tab_widget.addTab(trial_tab, "Testperiod")
        
        # Machine info tab
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        
        machine_info = QTextEdit()
        machine_info.setReadOnly(True)
        machine_info.setPlainText(f"""
Maskin-ID: {self.license_manager.machine_id}
System: {platform.system()} {platform.release()}
Processor: {platform.processor()}
Dator: {platform.node()}

Denna information behövs för licensaktivering.
        """)
        info_layout.addWidget(machine_info)
        
        tab_widget.addTab(info_tab, "Maskininfo")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        exit_btn = QPushButton("Avsluta")
        exit_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(exit_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect buttons
        def activate_license():
            license_key = license_key_edit.text().strip()
            company = company_edit.text().strip()
            
            if not license_key or not company:
                QMessageBox.warning(dialog, "Fel", "Fyll i alla fält.")
                return
            
            # Validate license key format and authenticity
            if not _validate_license_key_standalone(license_key, company):
                QMessageBox.warning(dialog, "Fel", "Ogiltig licensnyckel eller företagsnamn.")
                return
            
            # Create license data
            license_data = {
                'license_key': license_key,
                'company': company,
                'license_type': 'Full',
                'max_users': 10,
                'active': True
            }
            
            if self.license_manager.create_license(license_data):
                QMessageBox.information(dialog, "Licens aktiverad", 
                                      "Licensen har aktiverats framgångsrikt!")
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "Fel", "Kunde inte aktivera licensen.")
        
        def start_trial():
            if self.license_manager.create_trial_license():
                QMessageBox.information(dialog, "Testperiod startad", 
                                      "30-dagars testperiod har startats!")
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "Fel", "Kunde inte starta testperiod.")
        
        activate_btn.clicked.connect(activate_license)
        trial_btn.clicked.connect(start_trial)
        
        return dialog.exec()
    
    def _validate_license_key(self, license_key, company):
        """Validate license key authenticity with cryptographic verification"""
        try:
            # Known valid licenses (hardcoded for security)
            valid_licenses = {
                'KEYBUDDY-MEDZETA-DESIGN-2024': 'Medzeta Design',
                'KEYBUDDY-UNLIMITED-2024-MEDZETA': 'Medzeta Design'
            }
            
            # Check if license key exists and matches company
            if license_key in valid_licenses:
                return valid_licenses[license_key].lower() == company.lower()
            
            # For generated keys, validate cryptographically
            if len(license_key) >= 15 and license_key.count('-') == 3:
                return self._verify_generated_license_key(license_key, company)
            
            return False
            
        except Exception as e:
            print(f"License validation error: {e}")
            return False
    
    def _verify_generated_license_key(self, license_key, company):
        """Verify generated license key using cryptographic hash"""
        try:
            # Remove dashes and get the key parts
            key_clean = license_key.replace('-', '')
            
            # Remove KEYBUDDY prefix if present
            if key_clean.startswith('KEYBUDDY'):
                key_clean = key_clean[7:]  # Remove 'KEYBUDDY'
            
            # The key should be generated from company name + machine ID + secret
            # We'll verify by regenerating the expected key
            master_secret = "KEYBUDDY_MASTER_SECRET_2024_MEDZETA_DESIGN"
            
            # Create verification data (same as generator)
            verification_data = f"{company}|{self.machine_id}|{master_secret}"
            hash_obj = hashlib.sha256(verification_data.encode())
            expected_hash = hash_obj.hexdigest()[:15].upper()  # 15 chars after KEYBUDDY-
            
            # Debug output
            print(f"DEBUG: License validation")
            print(f"DEBUG: Company: '{company}'")
            print(f"DEBUG: Machine ID: '{self.machine_id}'")
            print(f"DEBUG: Key clean: '{key_clean}'")
            print(f"DEBUG: Expected: '{expected_hash}'")
            print(f"DEBUG: Match: {key_clean == expected_hash}")
            
            # Check if the provided key matches the expected hash
            if key_clean == expected_hash:
                return True
            
            return False
            
        except Exception as e:
            print(f"License key verification error: {e}")
            return False

def _validate_license_key_standalone(license_key, company):
    """Standalone license key validation function"""
    try:
        # Known valid licenses (hardcoded for security)
        valid_licenses = {
            'KEYBUDDY-MEDZETA-DESIGN-2024': 'Medzeta Design',
            'KEYBUDDY-UNLIMITED-2024-MEDZETA': 'Medzeta Design'
        }
        
        # Check if license key exists and matches company
        if license_key in valid_licenses:
            return valid_licenses[license_key].lower() == company.lower()
        
        # For generated keys, validate cryptographically
        if len(license_key) >= 15 and license_key.count('-') == 3:
            return _verify_generated_license_key_standalone(license_key, company)
        
        return False
        
    except Exception as e:
        print(f"License validation error: {e}")
        return False

def _verify_generated_license_key_standalone(license_key, company):
    """Standalone verification of generated license key"""
    try:
        # Get machine ID
        license_manager = LicenseManager()
        machine_id = license_manager.machine_id
        
        # Remove dashes and get the key parts
        key_clean = license_key.replace('-', '')
        
        # Remove KEYBUDDY prefix if present
        if key_clean.startswith('KEYBUDDY'):
            key_clean = key_clean[8:]  # Remove 'KEYBUDDY' (8 characters)
        
        # The key should be generated from company name + machine ID + secret
        master_secret = "KEYBUDDY_MASTER_SECRET_2024_MEDZETA_DESIGN"
        
        # Create verification data (same as generator)
        verification_data = f"{company}|{machine_id}|{master_secret}"
        hash_obj = hashlib.sha256(verification_data.encode())
        expected_hash = hash_obj.hexdigest()[:15].upper()  # 15 chars after KEYBUDDY-
        
        # Debug output
        print(f"DEBUG: License validation")
        print(f"DEBUG: Company: '{company}'")
        print(f"DEBUG: Machine ID: '{machine_id}'")
        print(f"DEBUG: Key clean: '{key_clean}'")
        print(f"DEBUG: Expected: '{expected_hash}'")
        print(f"DEBUG: Match: {key_clean == expected_hash}")
        
        # Check if the provided key matches the expected hash
        if key_clean == expected_hash:
            return True
        
        return False
        
    except Exception as e:
        print(f"License key verification error: {e}")
        return False

def check_license_on_startup():
    """Check license when application starts"""
    license_manager = LicenseManager()
    
    # Log startup
    license_manager.log_usage("application_start")
    
    # Check runtime integrity
    integrity_ok, integrity_msg = license_manager.check_runtime_integrity()
    if not integrity_ok:
        return False, integrity_msg
    
    # Validate license
    is_valid, result = license_manager.validate_license()
    
    if not is_valid:
        # Show activation dialog
        dialog = LicenseDialog()
        if dialog.show_activation_dialog() != 1:  # Dialog was rejected
            return False, "Licens krävs för att använda KeyBuddy"
        
        # Re-validate after activation
        is_valid, result = license_manager.validate_license()
    
    if is_valid:
        license_manager.log_usage("license_validated")
        return True, result
    else:
        return False, result
