"""
Version management system with automatic update check
"""

import os
import sys
import json
import requests
import zipfile
import shutil
from datetime import datetime
from typing import Dict
from PySide6.QtCore import QObject, Signal, QThread
import zipfile
import shutil
from datetime import datetime

class UpdateChecker(QThread):
    """Background thread for checking updates"""
    
    update_available = Signal(dict)
    update_error = Signal(str)
    
    def __init__(self, current_version, update_url):
        super().__init__()
        self.current_version = current_version
        self.update_url = update_url
    
    def run(self):
        """Check for updates in background"""
        try:
            response = requests.get(self.update_url, timeout=10)
            if response.status_code == 200:
                update_info = response.json()
                latest_version = update_info.get('version', '0.0')
                
                if self.is_newer_version(latest_version, self.current_version):
                    self.update_available.emit(update_info)
                    
        except Exception as e:
            self.update_error.emit(str(e))
    
    def is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return False

class VersionManager(QObject):
    """Manages application versioning and updates"""
    
    update_available = Signal(dict)
    update_progress = Signal(int)
    update_complete = Signal()
    update_error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.version_file = "version.json"
        self.current_version = self.load_version()
        self.update_url = "https://api.github.com/repos/your-repo/nyckelhanteraren/releases/latest"  # Placeholder
        
    def load_version(self) -> str:
        """Load current version from file"""
        version_file_path = self.get_version_file_path()
        
        if os.path.exists(version_file_path):
            try:
                with open(version_file_path, 'r') as f:
                    version_data = json.load(f)
                    return version_data.get('version', '1.0')
            except:
                pass
        
        # Create initial version file
        self.save_version('1.05')
        return '1.05'
    
    def get_version_file_path(self):
        """Get the correct path to version.json, handling PyInstaller bundled apps"""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle - version.json is bundled inside
            bundle_dir = sys._MEIPASS
            return os.path.join(bundle_dir, 'version.json')
        else:
            # Running as script - use version.json in project root
            return self.version_file
    
    def save_version(self, version: str):
        """Save version to file"""
        version_data = {
            'version': version,
            'build_date': datetime.now().isoformat(),
            'build_number': self.get_build_number(version)
        }
        
        try:
            with open(self.version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
            self.current_version = version
        except Exception as e:
            print(f"Could not save version: {e}")
    
    def get_build_number(self, version: str) -> int:
        """Generate build number from version"""
        try:
            # Handle decimal versions like 1.05, 1.06 etc
            version_float = float(version)
            return int(version_float * 100)
        except:
            return 105
    
    def increment_version(self, increment_type: str = 'minor') -> str:
        """Increment version number by 0.01 for each publication"""
        try:
            current_float = float(self.current_version)
            
            if increment_type == 'major':
                # Increment to next major version (1.05 -> 2.00)
                new_version = f"{int(current_float) + 1}.00"
            elif increment_type == 'minor':
                # Increment by 0.01 (1.05 -> 1.06)
                new_version = f"{current_float + 0.01:.2f}"
                # Remove trailing zeros and decimal point if not needed
                if new_version.endswith('.00'):
                    new_version = str(int(float(new_version)))
                elif new_version.endswith('0'):
                    new_version = new_version[:-1]
            
            self.save_version(new_version)
            return new_version
            
        except Exception as e:
            print(f"Could not increment version: {e}")
            return self.current_version
    
    def get_current_version(self) -> str:
        """Get current version string"""
        return self.current_version
    
    def get_version_info(self) -> Dict:
        """Get detailed version information"""
        version_file_path = self.get_version_file_path()
        
        if os.path.exists(version_file_path):
            try:
                with open(version_file_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'version': self.current_version,
            'build_date': datetime.now().isoformat(),
            'build_number': self.get_build_number(self.current_version)
        }
    
    def check_for_updates(self):
        """Check for available updates"""
        self.update_checker = UpdateChecker(self.current_version, self.update_url)
        self.update_checker.update_available.connect(self.update_available.emit)
        self.update_checker.update_error.connect(self.update_error.emit)
        self.update_checker.start()
    
    def download_and_install_update(self, update_info: Dict):
        """Download and install update"""
        try:
            download_url = update_info.get('download_url')
            if not download_url:
                self.update_error.emit("Ingen nedladdningslänk hittades")
                return
            
            # Download update
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            update_file = "update.zip"
            downloaded = 0
            
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.update_progress.emit(progress)
            
            # Extract and install
            self.install_update(update_file, update_info.get('version'))
            
        except Exception as e:
            self.update_error.emit(f"Uppdatering misslyckades: {str(e)}")
    
    def install_update(self, update_file: str, new_version: str):
        """Install downloaded update"""
        try:
            # Create backup of current installation
            backup_dir = f"backup_{self.current_version}"
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            
            # Backup current files
            for item in ['src', 'main.py', 'requirements.txt']:
                if os.path.exists(item):
                    if os.path.isdir(item):
                        shutil.copytree(item, os.path.join(backup_dir, item))
                    else:
                        os.makedirs(backup_dir, exist_ok=True)
                        shutil.copy2(item, backup_dir)
            
            # Extract update
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall('.')
            
            # Update version
            self.save_version(new_version)
            
            # Cleanup
            os.remove(update_file)
            
            self.update_complete.emit()
            
        except Exception as e:
            self.update_error.emit(f"Installation misslyckades: {str(e)}")
    
    def set_update_url(self, url: str):
        """Set custom update URL"""
        self.update_url = url
