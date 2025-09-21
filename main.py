#!/usr/bin/env python3
"""
Keybuddy - Key Management System
Main application entry point
"""

import sys
import os
from PySide6.QtCore import Qt, QSharedMemory, QSystemSemaphore
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QGuiApplication

# Set high DPI policy before creating any GUI application instance
try:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
except Exception:
    pass
try:
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
except Exception:
    pass

# Add src directory to path
def setup_paths():
    """Setup paths for both script and executable environments"""
    if getattr(sys, 'frozen', False):
        # Running as executable - src is bundled
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(__file__)
    
    src_path = os.path.join(base_path, 'src')
    if os.path.exists(src_path):
        sys.path.insert(0, src_path)

setup_paths()

try:
    from src.ui.main_window import MainWindow
    from src.core.app_manager import AppManager
    from src.core.database import DatabaseManager
    from src.core.version_manager import VersionManager
    from src.core.license_manager import check_license_on_startup
    from src.ui.copyable_message_box import CopyableMessageBox
except ImportError as e:
    # Write import error to file
    error_file = os.path.join(os.path.dirname(__file__), "import_error.log")
    with open(error_file, "w", encoding="utf-8") as f:
        f.write(f"Import error: {str(e)}\n")
        f.write(f"Python path: {sys.path}\n")
        f.write(f"Working directory: {os.getcwd()}\n")
        f.write(f"Frozen: {getattr(sys, 'frozen', False)}\n")
        if getattr(sys, 'frozen', False):
            f.write(f"MEIPASS: {getattr(sys, '_MEIPASS', 'Not available')}\n")
        import traceback
        f.write(traceback.format_exc())
    raise

def get_application_path():
    """Get the application directory path, works for both script and executable"""
    if getattr(sys, 'frozen', False):
        # Running as executable
        application_path = os.path.dirname(sys.executable)
    else:
        # Running as script
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

def main():
    """Main application entry point"""
    try:
        app = QApplication(sys.argv)
    except Exception as e:
        # Write error to file since we can't show it in console
        error_file = os.path.join(os.path.dirname(__file__), "startup_error.log")
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(f"Failed to create QApplication: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())
        return 1
    
    # Enforce single-instance (also when minimized to tray)
    SINGLETON_KEY = "KeyBuddy_SingleInstance_Key"
    SEMAPHORE_KEY = SINGLETON_KEY + "_sem"
    semaphore = QSystemSemaphore(SEMAPHORE_KEY, 1)
    semaphore.acquire()
    shared_mem = QSharedMemory(SINGLETON_KEY)
    if shared_mem.attach():
        # Another instance is already running
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("KeyBuddy")
        msg.setIcon(QMessageBox.Information)
        msg.setText("KeyBuddy kör redan på denna dator.\nEndast en session kan vara aktiv åt gången.")
        msg.exec()
        semaphore.release()
        return 0
    # Create shared memory segment to mark this instance as running
    shared_mem.create(1)
    semaphore.release()
    
    # Set application properties
    app.setApplicationName("Keybuddy - Säker Nyckelhantering")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Medzeta Design")
    
    # Get application path
    app_path = get_application_path()
    
    # Check license before proceeding
    try:
        license_valid, license_result = check_license_on_startup()
        if not license_valid:
            CopyableMessageBox.critical(
                None,
                "KeyBuddy - Licensfel",
                "Licensvalidering misslyckades",
                detailed_text=str(license_result)
            )
            return 1
    except Exception as e:
        CopyableMessageBox.critical(
            None,
            "KeyBuddy - Systemfel",
            "Ett fel uppstod vid licensvalidering",
            detailed_text=str(e)
        )
        return 1
    
    # Ensure backups folder exists
    backups_path = os.path.join(app_path, "backups")
    os.makedirs(backups_path, exist_ok=True)
    
    # Set application icon
    icon_path = os.path.join(app_path, "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Initialize core managers with database path
    db_path = os.path.join(app_path, "data", "keybuddy.db")
    db_manager = DatabaseManager(db_path)
    
    # Initialize database
    if not db_manager.initialize():
        print("Failed to initialize database")
        return 1
    
    # Initialize app manager
    app_manager = AppManager()
    
    # Initialize version manager
    version_manager = VersionManager()
    
    # Create and show main window
    main_window = MainWindow(app_manager, db_manager, version_manager)
    app_manager.main_window = main_window  # Set reference for settings updates
    main_window.show()
    
    # Check for updates on startup
    version_manager.check_for_updates()
    
    return app.exec()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Write comprehensive error to file
        app_path = get_application_path()
        error_file = os.path.join(app_path, "critical_error.log")
        try:
            with open(error_file, "w", encoding="utf-8") as f:
                f.write(f"CRITICAL ERROR in KeyBuddy startup:\n")
                f.write(f"Error: {str(e)}\n")
                f.write(f"Python version: {sys.version}\n")
                f.write(f"Frozen: {getattr(sys, 'frozen', False)}\n")
                f.write(f"Executable path: {sys.executable}\n")
                f.write(f"Application path: {app_path}\n")
                f.write(f"Working directory: {os.getcwd()}\n")
                f.write(f"Python path: {sys.path}\n\n")
                import traceback
                f.write("Full traceback:\n")
                f.write(traceback.format_exc())
        except:
            pass  # If we can't even write to file, we're in deep trouble
        sys.exit(1)
