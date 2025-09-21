"""
Database backup management system with scheduling
"""

import os
import shutil
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal, QTimer
import zipfile
import threading

class BackupManager(QObject):
    """Manages database backups and scheduling"""
    
    backup_started = Signal()
    backup_progress = Signal(int)
    backup_completed = Signal(str)
    backup_auto_completed = Signal(str)
    backup_error = Signal(str)
    
    def __init__(self, db_manager, delay_startup_backup=False):
        super().__init__()
        self.db_manager = db_manager
        self.config_file = "data/backup_config.json"
        self.backup_config = self.load_backup_config()
        self.delay_startup_backup = delay_startup_backup
        
        # Setup automatic backup timer (24h interval checks)
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.perform_scheduled_backup)
        
        self.setup_automatic_backup()
        
        # Perform an immediate check on startup only if not delayed
        if not delay_startup_backup:
            try:
                self.perform_scheduled_backup()
            except Exception:
                pass
    
    def load_backup_config(self) -> Dict:
        """Load backup configuration"""
        default_config = {
            "enabled": True,
            "frequency": "daily",  # daily, weekly, monthly
            "backup_path": "backups",
            "max_backups": 10,
            "last_backup": None,
            "include_logs": True,
            "compress": True
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"Error loading backup config: {e}")
        
        return default_config
    
    def save_backup_config(self):
        """Save backup configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.backup_config, f, indent=2)
        except Exception as e:
            print(f"Error saving backup config: {e}")
    
    def setup_automatic_backup(self):
        """Setup automatic backup based on configuration"""
        print(f"Setting up automatic backup. Enabled: {self.backup_config.get('enabled', False)}")
        
        # Always reset timers when (re)configuring
        try:
            self.backup_timer.stop()
        except Exception:
            pass
        
        if not self.backup_config.get("enabled", False):
            print("Automatic backup disabled, timers stopped")
            return
        
        # Start the regular schedule (24 hours between checks)
        self.start_regular_backup_schedule()
        
        # Immediately evaluate once after (re)configuring, but only if not delayed
        if not getattr(self, 'delay_startup_backup', False):
            try:
                self.perform_scheduled_backup()
            except Exception:
                pass
        else:
            print("Startup backup delayed until user login")
    
    def start_regular_backup_schedule(self):
        """Start the regular backup schedule"""
        frequency = self.backup_config.get("frequency", "daily")
        print(f"Starting regular backup schedule (24h checks). Frequency: {frequency}")
        
        # Check once every 24 hours
        interval = 24 * 60 * 60 * 1000
        print(f"Starting backup timer with interval: {interval}ms (24.0 hours)")
        self.backup_timer.start(interval)
    
    def perform_scheduled_backup(self):
        """Perform scheduled automatic backup"""
        print(f"Backup timer triggered at {datetime.now()}")
        print(f"Backup enabled: {self.backup_config.get('enabled', False)}")
        print(f"Should perform backup: {self.should_perform_backup()}")
        
        if self.should_perform_backup():
            print("Creating automatic backup...")
            self.create_backup(auto=True)
        else:
            print("Backup not needed yet")
    
    def perform_startup_backup_check(self):
        """Perform startup backup check after user login"""
        print(f"Performing startup backup check after user login at {datetime.now()}")
        try:
            self.perform_scheduled_backup()
        except Exception as e:
            print(f"Error during startup backup check: {e}")
    
    def should_perform_backup(self) -> bool:
        """Check if backup should be performed based on schedule and last backup date."""
        if not self.backup_config.get("enabled", False):
            return False

        frequency = self.backup_config.get("frequency", "daily")
        now = datetime.now()

        # Determine latest backup based on existing files (source of truth)
        latest_backup_dt = None
        try:
            backups = self.get_backup_list(self.backup_config.get("backup_path", "backups"))
            if backups:
                latest_backup_dt = max((b.get('created') for b in backups if b.get('created')), default=None)
        except Exception as e:
            print(f"Error reading backup list: {e}")
            latest_backup_dt = None

        if frequency == "daily":
            # Create a backup if there is no backup from today
            return not (latest_backup_dt and latest_backup_dt.date() == now.date())
        elif frequency == "weekly":
            # Create if none exist or last one is >= 7 days old
            return (latest_backup_dt is None) or ((now - latest_backup_dt) >= timedelta(days=7))
        elif frequency == "monthly":
            # Create if none exist or last one is at least 1 calendar month old
            if latest_backup_dt is None:
                return True
            months_now = now.year * 12 + now.month
            months_last = latest_backup_dt.year * 12 + latest_backup_dt.month
            return (months_now - months_last) >= 1
        else:
            # Default to daily behavior
            return not (latest_backup_dt and latest_backup_dt.date() == now.date())
    
    def create_backup(self, custom_path: str = None, auto: bool = False) -> str:
        """Create database backup"""
        try:
            self.backup_started.emit()
            
            # Determine backup path
            if custom_path:
                backup_dir = custom_path
            else:
                backup_dir = self.backup_config.get("backup_path", "backups")
                # If it's a relative path, make it relative to the application root
                if not os.path.isabs(backup_dir):
                    import sys
                    if hasattr(sys, '_MEIPASS'):
                        # Running as PyInstaller bundle
                        app_root = os.path.dirname(sys.executable)
                    else:
                        # Running as script
                        app_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    backup_dir = os.path.join(app_root, backup_dir)
            
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_type = "auto" if auto else "manual"
            backup_name = f"nyckelhanteraren_backup_{backup_type}_{timestamp}"
            
            if self.backup_config.get("compress", True):
                backup_file = os.path.join(backup_dir, f"{backup_name}.zip")
                self.create_compressed_backup(backup_file, backup_name)
            else:
                backup_file = os.path.join(backup_dir, backup_name)
                os.makedirs(backup_file, exist_ok=True)
                self.create_folder_backup(backup_file)
            
            # Update last backup time
            self.backup_config["last_backup"] = datetime.now().isoformat()
            self.save_backup_config()
            
            # Emit different signals for manual vs automatic backups
            if auto:
                print(f"DEBUG: Emitting backup_auto_completed signal for: {backup_file}")
                self.backup_auto_completed.emit(backup_file)
            else:
                print(f"DEBUG: Emitting backup_completed signal for: {backup_file}")
                self.backup_completed.emit(backup_file)
            print(f"Backup completed: {backup_file}")
            return backup_file
            
        except Exception as e:
            self.backup_error.emit(str(e))
            return ""
    
    def create_compressed_backup(self, backup_file: str, backup_name: str):
        """Create compressed backup"""
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add database file
            db_path = self.db_manager.db_path
            if os.path.exists(db_path):
                zipf.write(db_path, f"{backup_name}/database.db")
                self.backup_progress.emit(30)
            
            # Add salt file
            salt_file = db_path + ".salt"
            if os.path.exists(salt_file):
                zipf.write(salt_file, f"{backup_name}/database.db.salt")
                self.backup_progress.emit(50)
            
            # Add settings
            settings_file = "data/app_settings.json"
            if os.path.exists(settings_file):
                zipf.write(settings_file, f"{backup_name}/app_settings.json")
                self.backup_progress.emit(70)
            
            # Add backup config
            if os.path.exists(self.config_file):
                zipf.write(self.config_file, f"{backup_name}/backup_config.json")
                self.backup_progress.emit(80)
            
            # Add version info
            version_file = "version.json"
            if os.path.exists(version_file):
                zipf.write(version_file, f"{backup_name}/version.json")
                self.backup_progress.emit(90)
            
            # Add company logo if exists
            logo_path = "assets/company_logo.png"
            if os.path.exists(logo_path):
                zipf.write(logo_path, f"{backup_name}/company_logo.png")
            
            self.backup_progress.emit(100)
    
    def create_folder_backup(self, backup_dir: str):
        """Create folder-based backup"""
        # Copy database
        db_path = self.db_manager.db_path
        if os.path.exists(db_path):
            shutil.copy2(db_path, os.path.join(backup_dir, "database.db"))
            self.backup_progress.emit(30)
        
        # Copy salt file
        salt_file = db_path + ".salt"
        if os.path.exists(salt_file):
            shutil.copy2(salt_file, os.path.join(backup_dir, "database.db.salt"))
            self.backup_progress.emit(50)
        
        # Copy settings
        settings_file = "data/app_settings.json"
        if os.path.exists(settings_file):
            shutil.copy2(settings_file, os.path.join(backup_dir, "app_settings.json"))
            self.backup_progress.emit(70)
        
        # Copy backup config
        if os.path.exists(self.config_file):
            shutil.copy2(self.config_file, os.path.join(backup_dir, "backup_config.json"))
            self.backup_progress.emit(80)
        
        # Copy version info
        version_file = "version.json"
        if os.path.exists(version_file):
            shutil.copy2(version_file, os.path.join(backup_dir, "version.json"))
            self.backup_progress.emit(90)
        
        # Copy company logo
        logo_path = "assets/company_logo.png"
        if os.path.exists(logo_path):
            shutil.copy2(logo_path, os.path.join(backup_dir, "company_logo.png"))
        
        self.backup_progress.emit(100)
    
    def cleanup_old_backups(self, backup_dir: str):
        """Remove old backups based on max_backups setting"""
        try:
            max_backups = self.backup_config.get("max_backups", 10)
            
            # Get all backup files/folders
            backups = []
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                if item.startswith("nyckelhanteraren_backup_"):
                    backups.append((item_path, os.path.getctime(item_path)))
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups
            for backup_path, _ in backups[max_backups:]:
                if os.path.isfile(backup_path):
                    os.remove(backup_path)
                elif os.path.isdir(backup_path):
                    shutil.rmtree(backup_path)
                    
        except Exception as e:
            print(f"Error cleaning up old backups: {e}")
    
    def restore_backup(self, backup_file: str) -> bool:
        """Restore from backup file"""
        try:
            if not os.path.exists(backup_file):
                self.backup_error.emit("Backupfil hittades inte")
                return False
            
            # Create restore point
            restore_point = f"restore_point_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_backup(f"backups/{restore_point}")
            
            if backup_file.endswith('.zip'):
                return self.restore_from_zip(backup_file)
            else:
                return self.restore_from_folder(backup_file)
                
        except Exception as e:
            self.backup_error.emit(f"Återställning misslyckades: {str(e)}")
            return False
    
    def restore_from_zip(self, backup_file: str) -> bool:
        """Restore from compressed backup"""
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            # Extract to temporary directory
            temp_dir = "temp_restore"
            zipf.extractall(temp_dir)
            
            # Find backup folder inside
            backup_folders = [d for d in os.listdir(temp_dir) 
                            if d.startswith("nyckelhanteraren_backup_")]
            
            if not backup_folders:
                shutil.rmtree(temp_dir)
                return False
            
            backup_folder = os.path.join(temp_dir, backup_folders[0])
            result = self.restore_files(backup_folder)
            
            # Cleanup
            shutil.rmtree(temp_dir)
            return result
    
    def restore_from_folder(self, backup_dir: str) -> bool:
        """Restore from folder backup"""
        return self.restore_files(backup_dir)
    
    def restore_files(self, backup_dir: str) -> bool:
        """Restore individual files from backup"""
        try:
            # Close database connection
            self.db_manager.close()
            
            # Restore database
            backup_db = os.path.join(backup_dir, "database.db")
            if os.path.exists(backup_db):
                shutil.copy2(backup_db, self.db_manager.db_path)
            
            # Restore salt file
            backup_salt = os.path.join(backup_dir, "database.db.salt")
            salt_file = self.db_manager.db_path + ".salt"
            if os.path.exists(backup_salt):
                shutil.copy2(backup_salt, salt_file)
            
            # Restore settings
            backup_settings = os.path.join(backup_dir, "app_settings.json")
            if os.path.exists(backup_settings):
                os.makedirs("data", exist_ok=True)
                shutil.copy2(backup_settings, "data/app_settings.json")
            
            # Restore logo
            backup_logo = os.path.join(backup_dir, "company_logo.png")
            if os.path.exists(backup_logo):
                os.makedirs("assets", exist_ok=True)
                shutil.copy2(backup_logo, "assets/company_logo.png")
            
            return True
            
        except Exception as e:
            print(f"Error restoring files: {e}")
            return False
    
    def get_backup_list(self, backup_dir: str = None) -> List[Dict]:
        """Get list of available backups"""
        if not backup_dir:
            backup_dir = self.backup_config.get("backup_path", "backups")
            # If it's a relative path, make it relative to the application root
            if not os.path.isabs(backup_dir):
                import sys
                if hasattr(sys, '_MEIPASS'):
                    # Running as PyInstaller bundle
                    app_root = os.path.dirname(sys.executable)
                else:
                    # Running as script
                    app_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                backup_dir = os.path.join(app_root, backup_dir)
        
        backups = []
        
        if not os.path.exists(backup_dir):
            return backups
        
        try:
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                if item.startswith("nyckelhanteraren_backup_"):
                    stat = os.stat(item_path)
                    backups.append({
                        'name': item,
                        'path': item_path,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'type': 'auto' if 'auto' in item else 'manual'
                    })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            print(f"Error listing backups: {e}")
        
        return backups
    
    def update_config(self, config: Dict):
        """Update backup configuration"""
        self.backup_config.update(config)
        self.save_backup_config()
        self.setup_automatic_backup()
    
    def get_config(self) -> Dict:
        """Get current backup configuration"""
        return self.backup_config.copy()
    
    def cleanup(self):
        """Clean up timers and resources before shutdown"""
        print("Cleaning up BackupManager timers...")
        if hasattr(self, 'backup_timer') and self.backup_timer:
            self.backup_timer.stop()
            self.backup_timer.deleteLater()
        
        if hasattr(self, 'initial_backup_timer') and self.initial_backup_timer:
            self.initial_backup_timer.stop()
            self.initial_backup_timer.deleteLater()
        
        print("BackupManager cleanup completed")
