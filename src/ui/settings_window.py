"""
Settings window with theme, language, logo upload, and permissions
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QComboBox, QPushButton, QGroupBox, QFormLayout,
                              QFileDialog, QMessageBox, QScrollArea, QFrame,
                              QListWidget, QListWidgetItem, QCheckBox, QSpinBox,
                              QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
                              QLineEdit, QGridLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
import os
import shutil
from PIL import Image

from .styles import KeyBuddyButton, KeyBuddyLabel, KeyBuddyLineEdit, ButtonType, LabelType, FieldType, ThemeManager
from ..core.backup_manager import BackupManager
from ..core.license_manager import LicenseManager
from .copyable_message_box import CopyableMessageBox
from ..core.auth import AuthManager

class SettingsWindow(QWidget):
    """Settings window for app configuration"""
    
    navigate_home = Signal()
    
    def __init__(self, app_manager, db_manager, translation_manager):
        super().__init__()
        self.app_manager = app_manager
        self.db_manager = db_manager
        self.translation_manager = translation_manager
        # Use global backup manager from app_manager
        if hasattr(app_manager, 'backup_manager') and app_manager.backup_manager:
            self.backup_manager = app_manager.backup_manager
        else:
            # Fallback: create local backup manager
            self.backup_manager = BackupManager(db_manager)
        self.license_manager = LicenseManager()
        self.auth_manager = AuthManager(db_manager)
        self.theme_manager = ThemeManager()
        
        self.setup_ui()
        self.setup_backup_connections()
        self.load_current_settings()

    def showEvent(self, event):
        """Ensure profile picture preview is refreshed every time settings opens."""
        try:
            self.load_profile_picture()
        except Exception:
            pass
        super().showEvent(event)
    
    def setup_ui(self):
        """Setup settings UI"""
        # Create scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Main widget inside scroll area
        main_widget = QWidget()
        scroll.setWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        
        # Title
        title = QLabel(self.translation_manager.get_text("settings"))
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Appearance settings
        appearance_group = self.create_appearance_group()
        layout.addWidget(appearance_group)
        
        # Language settings
        language_group = self.create_language_group()
        layout.addWidget(language_group)
        
        # Profile settings
        profile_group = self.create_profile_group()
        layout.addWidget(profile_group)
        
        # Company branding
        branding_group = self.create_branding_group()
        layout.addWidget(branding_group)
        
        # Pricing settings
        pricing_group = self.create_pricing_group()
        layout.addWidget(pricing_group)
        
        # Backup settings
        backup_group = self.create_backup_group()
        layout.addWidget(backup_group)
        
        # Security settings
        security_group = self.create_security_group()
        layout.addWidget(security_group)
        
        # License information
        license_group = self.create_license_group()
        layout.addWidget(license_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        home_btn = KeyBuddyButton(self.translation_manager.get_text("home"), ButtonType.SECONDARY)
        home_btn.clicked.connect(self.navigate_home.emit)
        
        save_btn = KeyBuddyButton(self.translation_manager.get_text("save"), ButtonType.PRIMARY)
        save_btn.clicked.connect(self.save_settings)
        
        button_layout.addWidget(home_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Set main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
    
    def apply_logout_button_style(self, button):
        """Apply small button style - DEPRECATED, use ButtonType.SMALL instead"""
        button.setProperty("kb_button_type", "small")
    
    def apply_theme(self):
        """Apply current theme to settings window"""
        theme_name = self.app_manager.get_setting("theme", "light")
        stylesheet = self.theme_manager.get_stylesheet(theme_name)
        
        # Add rounded corners for settings window
        rounded_corners_style = """
        SettingsWindow {
            border-radius: 12px;
        }
        """
        
        # Combine global stylesheet with rounded corners
        combined_stylesheet = stylesheet + rounded_corners_style
        self.setStyleSheet(combined_stylesheet)
    
    def create_appearance_group(self):
        """Create appearance settings group"""
        group = QGroupBox("Utseende")
        layout = QFormLayout(group)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.setMaximumWidth(150)  # Limit width to prevent accidental scrolling
        themes = self.app_manager.get_available_themes()
        for theme_key, theme_name in themes.items():
            self.theme_combo.addItem(theme_name, theme_key)
        
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        layout.addRow(self.translation_manager.get_text("theme") + ":", self.theme_combo)
        
        return group
    
    def create_language_group(self):
        """Create language settings group"""
        group = QGroupBox("Språk")
        layout = QFormLayout(group)
        
        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.setMaximumWidth(150)  # Limit width to prevent accidental scrolling
        languages = self.app_manager.get_available_languages()
        for lang_key, lang_name in languages.items():
            self.language_combo.addItem(lang_name, lang_key)
        
        # Disable until feature is ready
        self.language_combo.setEnabled(False)
        layout.addRow(self.translation_manager.get_text("language") + ":", self.language_combo)
        # Info note
        info = KeyBuddyLabel("Språkbyte kommer snart.", LabelType.CAPTION)
        layout.addRow("", info)
        
        return group
    
    def create_branding_group(self):
        """Create company branding group"""
        group = QGroupBox("Företagsidentitet")
        layout = QVBoxLayout(group)
        
        # Logo section
        logo_layout = QHBoxLayout()
        
        # Logo preview
        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(100, 100)
        # Logo preview styling handled by global CSS
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setText("Ingen logga")
        
        # Logo buttons
        logo_buttons_layout = QVBoxLayout()
        
        upload_logo_btn = KeyBuddyButton(self.translation_manager.get_text("upload_logo"), ButtonType.PRIMARY)
        upload_logo_btn.clicked.connect(self.upload_logo)
        
        remove_logo_btn = KeyBuddyButton("Ta bort logga", ButtonType.SECONDARY)
        remove_logo_btn.clicked.connect(self.remove_logo)
        
        logo_buttons_layout.addWidget(upload_logo_btn)
        logo_buttons_layout.addWidget(remove_logo_btn)
        logo_buttons_layout.addStretch()
        
        logo_layout.addWidget(self.logo_preview)
        logo_layout.addLayout(logo_buttons_layout)
        logo_layout.addStretch()
        
        layout.addLayout(logo_layout)
        
        # Logo info
        logo_info = QLabel(
            "Ladda upp företagets logga i PNG-format. "
            "Loggan kommer att skalas automatiskt och visas i alla fönster."
        )
        logo_info.setWordWrap(True)
        logo_info.setProperty("class", "subtitle")
        layout.addWidget(logo_info)
        
        return group
    
    def create_pricing_group(self):
        """Create pricing settings group"""
        group = QGroupBox("Nyckelpriser")
        layout = QVBoxLayout(group)
        
        # Pricing label
        pricing_label = KeyBuddyLabel("Konfigurera priser för olika nyckelkoncept", LabelType.SUBTITLE)
        layout.addWidget(pricing_label)
        
        # New pricing selection section
        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(15)
        
        # Fabrikat dropdown
        fabrikat_label = QLabel("Fabrikat:")
        fabrikat_label.setMinimumWidth(60)
        self.pricing_fabrikat_combo = QComboBox()
        self.pricing_fabrikat_combo.setMaximumWidth(120)
        self.pricing_fabrikat_combo.currentTextChanged.connect(self.on_pricing_fabrikat_changed)
        self.populate_pricing_fabrikat_combo()
        
        # Koncept dropdown
        koncept_label = QLabel("Koncept:")
        koncept_label.setMinimumWidth(60)
        self.pricing_koncept_combo = QComboBox()
        self.pricing_koncept_combo.addItems(["Välj koncept..."])
        self.pricing_koncept_combo.setMaximumWidth(120)
        self.pricing_koncept_combo.setEnabled(False)
        self.pricing_koncept_combo.currentTextChanged.connect(self.on_pricing_koncept_changed)
        
        # Price input
        price_label = QLabel("Pris (SEK):")
        price_label.setMinimumWidth(70)
        self.pricing_price_input = KeyBuddyLineEdit(FieldType.STANDARD, "0.00")
        self.pricing_price_input.setMaximumWidth(120)  # Slightly wider for better appearance
        self.pricing_price_input.setEnabled(False)
        self.pricing_price_input.textChanged.connect(self.on_pricing_price_changed)
        
        # Add/Update button
        self.pricing_add_btn = QPushButton("OK")
        self.pricing_add_btn.setMinimumWidth(50)
        self.pricing_add_btn.setMaximumWidth(80)
        self.pricing_add_btn.setEnabled(False)
        self.pricing_add_btn.clicked.connect(self.add_pricing_entry)
        # Set primary style after creation
        self.pricing_add_btn.setProperty("class", "primary")
        # Style handled by global CSS
        
        selection_layout.addWidget(fabrikat_label)
        selection_layout.addWidget(self.pricing_fabrikat_combo)
        selection_layout.addWidget(koncept_label)
        selection_layout.addWidget(self.pricing_koncept_combo)
        selection_layout.addWidget(price_label)
        selection_layout.addWidget(self.pricing_price_input)
        selection_layout.addWidget(self.pricing_add_btn)
        selection_layout.addStretch()
        
        layout.addLayout(selection_layout)
        
        # Current pricing list
        self.pricing_list = QListWidget()
        self.pricing_list.setMaximumHeight(150)
        self.pricing_list.itemDoubleClicked.connect(self.edit_pricing_entry)
        # Selection styling handled by global CSS
        layout.addWidget(self.pricing_list)
        
        # Pricing list buttons
        list_buttons_layout = QHBoxLayout()
        
        self.pricing_edit_btn = QPushButton("Redigera")
        self.pricing_edit_btn.setProperty("class", "secondary")
        self.pricing_edit_btn.setEnabled(False)
        self.pricing_edit_btn.clicked.connect(self.edit_pricing_entry)
        
        self.pricing_remove_btn = QPushButton("Ta bort")
        self.pricing_remove_btn.setProperty("class", "secondary")
        self.pricing_remove_btn.setEnabled(False)
        self.pricing_remove_btn.clicked.connect(self.remove_pricing_entry)
        
        list_buttons_layout.addWidget(self.pricing_edit_btn)
        list_buttons_layout.addWidget(self.pricing_remove_btn)
        list_buttons_layout.addStretch()
        
        layout.addLayout(list_buttons_layout)
        
        # Connect list selection change
        self.pricing_list.itemSelectionChanged.connect(self.on_pricing_selection_changed)
        
        # Store pricing data
        self.pricing_data = {}
        
        # Load existing pricing data
        self.load_pricing_data()
        
        # Pricing info
        pricing_info = QLabel(
            "Ange priser för olika nyckelkoncept. Dessa används för att beräkna "
            "intäkter i statistiken på hemsidan."
        )
        pricing_info.setWordWrap(True)
        pricing_info.setProperty("class", "subtitle")
        layout.addWidget(pricing_info)
        
        return group
    
    def on_pricing_fabrikat_changed(self, fabrikat):
        """Handle fabrikat selection change in pricing - load koncept from database"""
        # Safety check - make sure all components exist
        if not hasattr(self, 'pricing_koncept_combo'):
            return
            
        self.pricing_koncept_combo.clear()
        self.pricing_koncept_combo.setEnabled(False)
        self.pricing_price_input.setEnabled(False)
        self.pricing_price_input.clear()
        self.pricing_add_btn.setEnabled(False)
        
        if not fabrikat or fabrikat == "Välj fabrikat...":
            return
            
        try:
            # Load koncept options from database for selected fabrikat
            rows = self.db_manager.execute_query(
                "SELECT koncept FROM key_catalog WHERE fabrikat = ? ORDER BY koncept", 
                (fabrikat,)
            )
            
            self.pricing_koncept_combo.addItem("Välj koncept...")
            
            for row in rows:
                koncept = row[0] if isinstance(row, (list, tuple)) else row['koncept']
                if koncept:
                    self.pricing_koncept_combo.addItem(koncept)
            
            # Enable koncept dropdown if we have options
            if self.pricing_koncept_combo.count() > 1:
                self.pricing_koncept_combo.setEnabled(True)
                
        except Exception as e:
            print(f"Error loading koncept for fabrikat {fabrikat}: {e}")
            # Fallback - just enable the dropdown
            self.pricing_koncept_combo.addItem("Välj koncept...")
            self.pricing_koncept_combo.setEnabled(True)
        
        # Update button state after changes
        self.update_pricing_ok_button()
    
    def on_pricing_koncept_changed(self, koncept):
        """Handle koncept selection change in pricing"""
        if koncept and koncept != "Välj koncept...":
            self.pricing_price_input.setEnabled(True)
            
            # Load existing price if available
            fabrikat = self.pricing_fabrikat_combo.currentText()
            key = f"{fabrikat}_{koncept}"
            if key in self.pricing_data:
                self.pricing_price_input.setText(str(self.pricing_data[key]))
            
            # Enable OK button if price is entered
            self.update_pricing_ok_button()
        else:
            self.pricing_price_input.setEnabled(False)
            self.pricing_price_input.clear()
            self.pricing_add_btn.setEnabled(False)
    
    def on_pricing_price_changed(self, text):
        """Handle price input change"""
        self.update_pricing_ok_button()
    
    def update_pricing_ok_button(self):
        """Update OK button state based on form completion"""
        fabrikat = self.pricing_fabrikat_combo.currentText()
        koncept = self.pricing_koncept_combo.currentText()
        price = self.pricing_price_input.text().strip()
        
        # Debug output
        print(f"Pricing button check - Fabrikat: '{fabrikat}', Koncept: '{koncept}', Price: '{price}'")
        
        # Enable OK button only if all fields are filled
        enabled = bool(fabrikat and fabrikat != "Välj fabrikat..." and
                      koncept and koncept != "Välj koncept..." and
                      price and len(price) > 0)
        
        print(f"OK button enabled: {enabled}")
        
        self.pricing_add_btn.setEnabled(enabled)
        
        # Force style refresh to ensure primary styling shows when enabled
        self.pricing_add_btn.setProperty("class", "primary")
        self.pricing_add_btn.style().unpolish(self.pricing_add_btn)
        self.pricing_add_btn.style().polish(self.pricing_add_btn)
    
    def add_pricing_entry(self):
        """Add or update pricing entry"""
        fabrikat = self.pricing_fabrikat_combo.currentText()
        koncept = self.pricing_koncept_combo.currentText()
        price_text = self.pricing_price_input.text().strip()
        
        if not price_text:
            return
        
        try:
            price = float(price_text)
            if price < 0:
                raise ValueError("Price cannot be negative")
        except ValueError:
            from .copyable_message_box import CopyableMessageBox
            CopyableMessageBox.warning(
                self, 
                "Ogiltigt pris", 
                "Ange ett giltigt pris (endast siffror)."
            )
            return
        
        key = f"{fabrikat}_{koncept}"
        self.pricing_data[key] = price
        
        # Save immediately to ensure persistence
        self.save_pricing_settings()
        
        # Update the list
        self.update_pricing_list()
        
        # Clear selections
        self.pricing_fabrikat_combo.setCurrentIndex(0)
        self.pricing_koncept_combo.clear()
        self.pricing_koncept_combo.addItems(["Välj koncept..."])
        self.pricing_koncept_combo.setEnabled(False)
        self.pricing_price_input.clear()
        self.pricing_price_input.setEnabled(False)
        self.pricing_add_btn.setEnabled(False)
    
    def edit_pricing_entry(self):
        """Edit selected pricing entry"""
        current_item = self.pricing_list.currentItem()
        if not current_item:
            return
        
        # Parse the item text to get fabrikat and koncept
        item_text = current_item.text()
        # Format: "Fabrikat - Koncept: Price SEK"
        parts = item_text.split(": ")
        if len(parts) != 2:
            return
        
        fabrikat_koncept = parts[0]
        price_text = parts[1].replace(" SEK", "")
        
        # Split fabrikat and koncept
        fab_kon_parts = fabrikat_koncept.split(" - ")
        if len(fab_kon_parts) != 2:
            return
        
        fabrikat, koncept = fab_kon_parts
        
        # Set the dropdowns
        fabrikat_index = self.pricing_fabrikat_combo.findText(fabrikat)
        if fabrikat_index >= 0:
            self.pricing_fabrikat_combo.setCurrentIndex(fabrikat_index)
            # This will trigger the koncept population
            
            koncept_index = self.pricing_koncept_combo.findText(koncept)
            if koncept_index >= 0:
                self.pricing_koncept_combo.setCurrentIndex(koncept_index)
                self.pricing_price_input.setText(price_text)
    
    def remove_pricing_entry(self):
        """Remove selected pricing entry"""
        current_item = self.pricing_list.currentItem()
        if not current_item:
            return
        
        # Parse the item text to get the key
        item_text = current_item.text()
        parts = item_text.split(": ")
        if len(parts) != 2:
            return
        
        fabrikat_koncept = parts[0]
        fab_kon_parts = fabrikat_koncept.split(" - ")
        if len(fab_kon_parts) != 2:
            return
        
        fabrikat, koncept = fab_kon_parts
        key = f"{fabrikat}_{koncept}"
        
        if key in self.pricing_data:
            del self.pricing_data[key]
            # Save immediately to ensure persistence
            self.save_pricing_settings()
            self.update_pricing_list()
    
    def on_pricing_selection_changed(self):
        """Handle pricing list selection change"""
        has_selection = bool(self.pricing_list.currentItem())
        self.pricing_edit_btn.setEnabled(has_selection)
        self.pricing_remove_btn.setEnabled(has_selection)
    
    def update_pricing_list(self):
        """Update the pricing list display - only show items with price > 0"""
        self.pricing_list.clear()
        
        for key, price in sorted(self.pricing_data.items()):
            # Only show items that have a price set (> 0)
            if price > 0:
                fabrikat, koncept = key.split("_", 1)
                item_text = f"{fabrikat} - {koncept}: {price:.2f} SEK"
                self.pricing_list.addItem(item_text)
    
    def load_pricing_data(self):
        """Load pricing data from key_catalog database table"""
        try:
            # Get all fabrikat-koncept combinations from key_catalog
            rows = self.db_manager.execute_query(
                "SELECT fabrikat, koncept FROM key_catalog ORDER BY fabrikat, koncept"
            )
            
            # Get existing pricing from settings (for backwards compatibility)
            existing_pricing = self.app_manager.get_setting("key_pricing", {})
            
            self.pricing_data = {}
            
            for row in rows:
                fabrikat = row[0] if isinstance(row, (list, tuple)) else row['fabrikat']
                koncept = row[1] if isinstance(row, (list, tuple)) else row['koncept']
                
                if fabrikat and koncept:
                    key = f"{fabrikat}_{koncept}"
                    # Use existing price if available, otherwise default to 0.00
                    self.pricing_data[key] = existing_pricing.get(key, 0.00)
            
            self.update_pricing_list()
            print(f"DEBUG: Loaded pricing data from key_catalog: {self.pricing_data}")
        except Exception as e:
            print(f"Error loading pricing data from database: {e}")
            # Fallback to old method
            pricing_data = self.app_manager.get_setting("key_pricing", {})
            self.pricing_data = pricing_data.copy()
            self.update_pricing_list()
    
    def save_pricing_settings(self):
        """Save pricing data to app settings"""
        try:
            # Use the same key as home_window for consistency
            self.app_manager.set_setting("key_pricing", self.pricing_data)
            print(f"DEBUG: Saved pricing data: {self.pricing_data}")
        except Exception as e:
            print(f"Error saving pricing settings: {e}")
    
    def populate_pricing_fabrikat_combo(self):
        """Load fabrikat options from key_catalog database"""
        try:
            self.pricing_fabrikat_combo.clear()
            self.pricing_fabrikat_combo.addItem("Välj fabrikat...")
            
            rows = self.db_manager.execute_query(
                "SELECT DISTINCT fabrikat FROM key_catalog ORDER BY fabrikat"
            )
            
            for row in rows:
                fabrikat = row[0] if isinstance(row, (list, tuple)) else row['fabrikat']
                if fabrikat:
                    self.pricing_fabrikat_combo.addItem(fabrikat)
                    
        except Exception as e:
            print(f"Error loading fabrikat for pricing: {e}")
            # Fallback to hardcoded values
            self.pricing_fabrikat_combo.addItems(["Assa", "Dorma", "Kaba", "Alfa", "Evva", "Dom"])
    
    def create_backup_group(self):
        """Create backup settings group"""
        group = QGroupBox("Databasbackup")
        layout = QVBoxLayout(group)
        
        # Manual backup section
        manual_layout = QHBoxLayout()
        
        create_backup_btn = KeyBuddyButton("Skapa backup", ButtonType.PRIMARY)
        create_backup_btn.clicked.connect(self.create_manual_backup)
        
        restore_backup_btn = KeyBuddyButton("Återställ backup", ButtonType.SECONDARY)
        restore_backup_btn.clicked.connect(self.restore_backup)
        
        manual_layout.addWidget(create_backup_btn)
        manual_layout.addWidget(restore_backup_btn)
        manual_layout.addStretch()
        
        layout.addLayout(manual_layout)
        
        # Progress bar (hidden initially)
        self.backup_progress = QProgressBar()
        self.backup_progress.hide()
        layout.addWidget(self.backup_progress)
        
        # Automatic backup settings
        auto_group = QGroupBox("Automatisk backup")
        auto_layout = QFormLayout(auto_group)
        
        self.backup_enabled_cb = QCheckBox("Aktivera automatisk backup")
        auto_layout.addRow("", self.backup_enabled_cb)
        
        # Email confirmation checkbox
        self.backup_email_cb = QCheckBox("Skicka e-postbekräftelse när backup skapas")
        auto_layout.addRow("", self.backup_email_cb)
        
        self.backup_frequency_combo = QComboBox()
        self.backup_frequency_combo.setMaximumWidth(120)  # Limit width to prevent accidental scrolling
        self.backup_frequency_combo.addItems(["Dagligen", "Veckovis", "Månadsvis"])
        auto_layout.addRow("Frekvens:", self.backup_frequency_combo)
        
        # Add info label about backup intervals
        info_label = QLabel(
            "ℹ️ Kontrollintervall:\n"
            "• Daglig backup: varje timme\n"
            "• Veckovis backup: var 6:e timme\n"
            "• Månadsvis backup: var 12:e timme\n"
            "• Max backups: max antal olika backupfiler innan den äldsta skrivs över"
        )
        info_label.setWordWrap(True)
        auto_layout.addRow("", info_label)
        
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setMinimum(1)
        self.max_backups_spin.setMaximum(100)
        self.max_backups_spin.setValue(10)
        self.max_backups_spin.setMaximumWidth(150)  # Wider for better appearance
        auto_layout.addRow("Max backups:", self.max_backups_spin)
        
        backup_path_layout = QHBoxLayout()
        self.backup_path_edit = KeyBuddyLineEdit(FieldType.STANDARD, "backups")
        self.backup_path_edit.setMaximumWidth(200)  # Wider for better appearance
        browse_path_btn = KeyBuddyButton("Bläddra...", ButtonType.SECONDARY)
        browse_path_btn.setMaximumWidth(120)
        browse_path_btn.clicked.connect(self.browse_backup_path)
        backup_path_layout.addWidget(self.backup_path_edit)
        backup_path_layout.addWidget(browse_path_btn)
        backup_path_layout.addStretch()
        auto_layout.addRow("Backup-mapp:", backup_path_layout)

        # Last automatic/manual backup info (discreet label)
        if not hasattr(self, 'last_auto_backup_label'):
            self.last_auto_backup_label = QLabel("Senaste automatisk backup: -")
            self.last_auto_backup_label.setProperty("kb_label_type", "caption")
        auto_layout.addRow("", self.last_auto_backup_label)

        layout.addWidget(auto_group)
        
        # Backup list
        list_group = QGroupBox("Befintliga backups")
        list_layout = QVBoxLayout(list_group)
        
        self.backup_table = QTableWidget()
        self.setup_backup_table()
        list_layout.addWidget(self.backup_table)
        # Summary label for count and total size
        if not hasattr(self, 'backup_summary_label'):
            self.backup_summary_label = QLabel("Totalt: 0 backups | 0 B")
            self.backup_summary_label.setProperty("kb_label_type", "caption")
        list_layout.addWidget(self.backup_summary_label)
        
        
        layout.addWidget(list_group)
        
        return group
    
    def create_profile_group(self):
        """Create profile settings group"""
        group = QGroupBox("Profil")
        layout = QVBoxLayout(group)
        
        # Profile picture section
        profile_layout = QHBoxLayout()
        
        # Profile picture preview
        self.profile_picture_label = QLabel()
        self.profile_picture_label.setFixedSize(80, 80)
        self.profile_picture_label.setObjectName("profilePicture")  # Use global styling
        self.profile_picture_label.setScaledContents(True)
        
        # Upload buttons
        button_layout = QVBoxLayout()
        
        upload_btn = QPushButton("Välj profilbild")
        upload_btn.clicked.connect(self.upload_profile_picture)
        upload_btn.setProperty("class", "secondary")
        
        remove_btn = QPushButton("Ta bort bild")
        remove_btn.clicked.connect(self.remove_profile_picture)
        remove_btn.setProperty("class", "secondary")
        
        button_layout.addWidget(upload_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        
        profile_layout.addWidget(self.profile_picture_label)
        profile_layout.addLayout(button_layout)
        profile_layout.addStretch()
        
        layout.addLayout(profile_layout)
        
        # Load current profile picture
        self.load_profile_picture()
        
        return group
    
    def upload_profile_picture(self):
        """Upload new profile picture"""
        from PySide6.QtWidgets import QFileDialog
        from PySide6.QtGui import QPixmap
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Välj profilbild",
            "",
            "Bildfiler (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if file_path:
            try:
                # Load and resize image
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # Scale to fit profile picture size
                    scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # Create circular mask
                    circular_pixmap = self.create_circular_pixmap(scaled_pixmap)
                    self.profile_picture_label.setPixmap(circular_pixmap)
                    
                    # Save profile picture path
                    user_data = self.app_manager.get_current_user()
                    if user_data:
                        # Copy file to data directory
                        import shutil
                        os.makedirs("data/profiles", exist_ok=True)
                        profile_filename = f"profile_{user_data['user_id']}.png"
                        profile_path = os.path.join("data/profiles", profile_filename)
                        
                        # Save the circular pixmap
                        circular_pixmap.save(profile_path, "PNG")
                        
                        # Update user profile in database
                        self.db_manager.execute_update(
                            "UPDATE users SET profile_picture = ? WHERE id = ?",
                            (profile_path, user_data['user_id'])
                        )
                        
                        # Update main window user display immediately
                        self.update_main_window_user_display()
                        
                        print(f"DEBUG: Profile picture saved to {profile_path}")
                        print(f"DEBUG: Database updated with profile picture path")
                        
            except Exception as e:
                CopyableMessageBox.warning(self, "Fel", f"Kunde inte ladda upp profilbild: {str(e)}")
    
    def remove_profile_picture(self):
        """Remove profile picture"""
        try:
            user_data = self.app_manager.get_current_user()
            if user_data:
                # Remove from database
                self.db_manager.execute_update(
                    "UPDATE users SET profile_picture = NULL WHERE id = ?",
                    (user_data['user_id'],)
                )
                
                # Remove file if exists
                profile_path = f"data/profiles/profile_{user_data['user_id']}.png"
                if os.path.exists(profile_path):
                    os.remove(profile_path)
                
                # Reset label
                self.profile_picture_label.clear()
                self.profile_picture_label.setText("Ingen bild")
                
                # Update main window user display immediately
                self.update_main_window_user_display()
                
        except Exception as e:
            CopyableMessageBox.warning(self, "Fel", f"Kunde inte ta bort profilbild: {str(e)}")
    
    def create_circular_pixmap(self, pixmap):
        """Create circular version of pixmap"""
        from PySide6.QtGui import QPainter, QBrush, QPen
        from PySide6.QtCore import Qt
        
        size = min(pixmap.width(), pixmap.height())
        circular_pixmap = QPixmap(size, size)
        circular_pixmap.fill(Qt.transparent)
        
        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create circular path
        painter.setBrush(QBrush(pixmap))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawEllipse(0, 0, size, size)
        
        painter.end()
        return circular_pixmap
    
    def load_profile_picture(self):
        """Load current user's profile picture"""
        try:
            user_data = self.app_manager.get_current_user()
            if user_data:
                # Get profile picture from database
                result = self.db_manager.execute_query(
                    "SELECT profile_picture FROM users WHERE id = ?",
                    (user_data['user_id'],)
                )
                
                print(f"DEBUG: Loading profile picture for user {user_data['user_id']}")
                print(f"DEBUG: Database result: {result}")
                
                # Support both tuple and dict row formats
                profile_picture_path = None
                if result:
                    row0 = result[0]
                    try:
                        # dict-like
                        profile_picture_path = row0.get('profile_picture') if hasattr(row0, 'get') else None
                    except Exception:
                        profile_picture_path = None
                    if not profile_picture_path:
                        try:
                            # tuple-like at index 0
                            profile_picture_path = row0[0]
                        except Exception:
                            profile_picture_path = None
                if profile_picture_path:
                    # Normalize and resolve to absolute if needed
                    path_norm = os.path.normpath(profile_picture_path)
                    if not os.path.isabs(path_norm):
                        try:
                            app_dir = os.getcwd()
                            path_norm = os.path.normpath(os.path.join(app_dir, path_norm))
                        except Exception:
                            pass
                    if os.path.exists(path_norm):
                        from PySide6.QtGui import QPixmap
                        pixmap = QPixmap(path_norm)
                        if not pixmap.isNull():
                            scaled = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            self.profile_picture_label.setPixmap(scaled)
                            self.profile_picture_label.setText("")
                            print(f"DEBUG: Profile picture loaded successfully")
                            return
                    else:
                        print(f"DEBUG: Profile picture file does not exist: {path_norm}")
                
                # No profile picture found
                self.profile_picture_label.clear()
                self.profile_picture_label.setText("Ingen bild")
                print(f"DEBUG: No profile picture found, showing placeholder")
                
        except Exception as e:
            print(f"Error loading profile picture: {e}")
    
    def setup_backup_table(self):
        """Setup backup list table"""
        headers = ["Namn", "Typ", "Storlek", "Skapad"]
        self.backup_table.setColumnCount(len(headers))
        self.backup_table.setHorizontalHeaderLabels(headers)
        
        header = self.backup_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.backup_table.setMaximumHeight(150)
    
    def load_current_settings(self):
        """Load current settings into UI"""
        # Load theme
        current_theme = self.app_manager.get_setting("theme", "light")
        theme_index = self.theme_combo.findData(current_theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        
        # Load language
        current_language = self.app_manager.get_setting("language", "sv")
        lang_index = self.language_combo.findData(current_language)
        if lang_index >= 0:
            self.language_combo.setCurrentIndex(lang_index)
        
        # Load security settings
        try:
            self.load_security_settings()
        except AttributeError:
            pass
        
        # Load pricing settings
        try:
            self.load_pricing_settings()
        except AttributeError:
            pass
        
        # Load backup settings
        try:
            self.load_backup_settings()
        except AttributeError:
            pass
        
        # Load profile picture
        try:
            self.load_profile_picture()
        except AttributeError:
            pass

        # Ensure company logo preview loads on start
        try:
            self.update_logo_preview()
        except Exception:
            pass

    def update_main_window_user_display(self):
        """Update the MainWindow user display (profile picture/name) immediately."""
        try:
            current_user = self.app_manager.get_current_user()
            if hasattr(self.app_manager, 'main_window') and self.app_manager.main_window and current_user:
                mw = self.app_manager.main_window
                if hasattr(mw, 'update_user_display'):
                    mw.update_user_display(current_user)
        except Exception:
            pass

    # Backwards compatibility alias for older builds which called a misspelled method name
    def upsate_window_user_display(self):
        self.update_main_window_user_display()
    
    def update_logo_preview(self):
        """Update logo preview"""
        logo_path = self.app_manager.get_setting("company_logo", "")
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(
                self.logo_preview.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.logo_preview.setPixmap(scaled_pixmap)
        else:
            self.logo_preview.clear()
            self.logo_preview.setText("Ingen logga")
    
    def on_theme_changed(self):
        """Handle theme change"""
        theme_data = self.theme_combo.currentData()
        if theme_data:
            self.app_manager.set_setting("theme", theme_data)
    
    def on_language_changed(self):
        """Handle language change"""
        lang_data = self.language_combo.currentData()
        if lang_data:
            self.app_manager.set_setting("language", lang_data)
    
    def upload_logo(self):
        """Upload company logo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Välj företagslogga",
            "",
            "PNG-filer (*.png);;Alla filer (*)"
        )
        
        if file_path:
            try:
                # Create assets directory if it doesn't exist
                assets_dir = "assets"
                os.makedirs(assets_dir, exist_ok=True)
                
                # Process and save logo
                logo_filename = "company_logo.png"
                logo_path = os.path.join(assets_dir, logo_filename)
                
                # Resize image to reasonable size
                with Image.open(file_path) as img:
                    # Convert to RGBA if not already
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # Resize maintaining aspect ratio
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    img.save(logo_path, 'PNG')
                
                # Update setting
                self.app_manager.set_setting("company_logo", logo_path)
                self.update_logo_preview()
                
                CopyableMessageBox.information(
                    self, 
                    "Logga uppladdad", 
                    "Företagsloggan har laddats upp och kommer att visas i alla fönster."
                )
                
            except Exception as e:
                CopyableMessageBox.critical(
                    self, 
                    "Fel", 
                    f"Kunde inte ladda upp loggan: {str(e)}"
                )
    
    def remove_logo(self):
        """Remove company logo"""
        reply = CopyableMessageBox.question(
            self,
            "Ta bort logga",
            "Är du säker på att du vill ta bort företagsloggan?",
            CopyableMessageBox.Yes | CopyableMessageBox.No
        )
        
        if reply == CopyableMessageBox.Yes:
            self.app_manager.set_setting("company_logo", "")
            self.update_logo_preview()
    
    
    
    
    
    def save_settings(self):
        """Save all settings"""
        # Save backup settings first
        self.save_backup_settings()
        
        # Save pricing settings
        self.save_pricing_settings()
        
        # Save security settings
        self.save_security_settings()
        
        # Save other app settings
        self.app_manager.save_settings()
        
        CopyableMessageBox.information(
            self, 
            "Inställningar sparade",
            "Alla inställningar har sparats framgångsrikt."
        )
    
    def save_backup_settings(self):
        """Save backup settings from UI to config"""
        try:
            if hasattr(self, 'backup_manager') and hasattr(self, 'backup_enabled_cb'):
                config = {
                    "enabled": self.backup_enabled_cb.isChecked(),
                    "frequency": ["daily", "weekly", "monthly"][self.backup_frequency_combo.currentIndex()],
                    "max_backups": self.max_backups_spin.value(),
                    "backup_path": self.backup_path_edit.text() or "backups",
                    "compress": True,
                    "include_logs": True
                }
                print(f"DEBUG: Saving backup config: {config}")
                self.backup_manager.update_config(config)
                print(f"DEBUG: Backup config saved successfully")
            # Save email confirmation setting via AppManager
            if hasattr(self, 'backup_email_cb'):
                self.app_manager.set_setting("backup_email_confirmation", self.backup_email_cb.isChecked())
        except Exception as e:
            print(f"Error saving backup settings: {e}")
    
    def save_pricing_settings(self):
        """Save pricing data to app settings"""
        try:
            # Use the same key as home_window for consistency
            self.app_manager.set_setting("key_pricing", self.pricing_data)
            print(f"DEBUG: Saved pricing data: {self.pricing_data}")
        except Exception as e:
            print(f"Error saving pricing settings: {e}")
    
    def load_pricing_settings(self):
        """Load pricing settings from app settings"""
        try:
            # Load pricing data using the same method as load_pricing_data
            self.load_pricing_data()
        except Exception as e:
            print(f"Error loading pricing settings: {e}")
    
    def create_manual_backup(self):
        """Create manual backup"""
        backup_dir = QFileDialog.getExistingDirectory(
            self, "Välj backup-mapp", self.backup_path_edit.text()
        )
        
        if backup_dir:
            self.backup_manager.create_backup(backup_dir)
    
    def restore_backup(self):
        """Restore from backup"""
        backup_file = None
        # Prefer the selected row in the table if available
        try:
            current_row = self.backup_table.currentRow()
            if current_row is not None and current_row >= 0:
                # Ensure we have a cached list
                if not hasattr(self, '_backup_items'):
                    self.refresh_backup_list()
                if hasattr(self, '_backup_items') and 0 <= current_row < len(self._backup_items):
                    backup_file = self._backup_items[current_row]['path']
        except Exception:
            pass
        
        # Fallback: let the user pick a file if nothing was selected
        if not backup_file:
            backup_file, _ = QFileDialog.getOpenFileName(
                self, "Välj backup-fil", "", 
                "Backup-filer (*.zip);;Alla filer (*)"
            )
        
        if backup_file:
            reply = CopyableMessageBox.question(
                self,
                "Återställ backup",
                "Är du säker på att du vill återställa från backup?\nDetta kommer att ersätta nuvarande data!",
                CopyableMessageBox.Yes | CopyableMessageBox.No
            )
            
            if reply == CopyableMessageBox.Yes:
                if self.backup_manager.restore_backup(backup_file):
                    CopyableMessageBox.information(
                        self, "Återställning klar",
                        "Backup har återställts. Starta om applikationen."
                    )
                else:
                    CopyableMessageBox.critical(
                        self, "Fel", "Återställning misslyckades"
                    )
    
    def browse_backup_path(self):
        """Browse for backup directory"""
        backup_dir = QFileDialog.getExistingDirectory(
            self, "Välj backup-mapp", self.backup_path_edit.text()
        )
        
        if backup_dir:
            self.backup_path_edit.setText(backup_dir)
    
    def refresh_backup_list(self):
        """Refresh backup list"""
        try:
            backups = self.backup_manager.get_backup_list(self.backup_path_edit.text())
            # Cache list for restore lookup
            self._backup_items = backups
            
            self.backup_table.setRowCount(len(backups))
            
            for row, backup in enumerate(backups):
                self.backup_table.setItem(row, 0, QTableWidgetItem(backup['name']))
                self.backup_table.setItem(row, 1, QTableWidgetItem(backup['type']))
                
                # Format size
                size_mb = backup['size'] / (1024 * 1024)
                size_text = f"{size_mb:.1f} MB" if size_mb > 1 else f"{backup['size']} B"
                self.backup_table.setItem(row, 2, QTableWidgetItem(size_text))
                
                # Format date
                date_text = backup['created'].strftime("%Y-%m-%d %H:%M")
                self.backup_table.setItem(row, 3, QTableWidgetItem(date_text))
            # Update summary label
            try:
                total_bytes = sum(b.get('size', 0) for b in backups)
                count = len(backups)
                # Human readable total
                if total_bytes >= 1024**3:
                    total_text = f"{total_bytes / (1024**3):.2f} GB"
                elif total_bytes >= 1024**2:
                    total_text = f"{total_bytes / (1024**2):.1f} MB"
                elif total_bytes >= 1024:
                    total_text = f"{total_bytes / 1024:.0f} KB"
                else:
                    total_text = f"{total_bytes} B"
                if hasattr(self, 'backup_summary_label') and self.backup_summary_label:
                    self.backup_summary_label.setText(f"Totalt: {count} backups | {total_text}")
            except Exception:
                pass
        except Exception as e:
            pass  # Silently handle error
    
    def setup_backup_connections(self):
        """Setup backup signal connections"""
        try:
            self.backup_manager.backup_started.connect(self.on_backup_started)
            self.backup_manager.backup_progress.connect(self.on_backup_progress)
            self.backup_manager.backup_completed.connect(self.on_backup_completed)
            # Auto backups should refresh list silently
            if hasattr(self.backup_manager, 'backup_auto_completed'):
                self.backup_manager.backup_auto_completed.connect(self.on_backup_auto_completed)
            self.backup_manager.backup_error.connect(self.on_backup_error)
        except AttributeError:
            # BackupManager might not have signals implemented yet
            pass

    def on_backup_auto_completed(self, backup_file: str):
        """Handle automatic backup completion: refresh the list without popup"""
        try:
            self.refresh_backup_list()
            # Update discreet status label
            from datetime import datetime
            now_iso = datetime.now().isoformat()
            ts = datetime.fromisoformat(now_iso).strftime('%Y-%m-%d %H:%M')
            if hasattr(self, 'last_auto_backup_label') and self.last_auto_backup_label:
                self.last_auto_backup_label.setText(f"Senaste automatisk backup: {ts}  (\u2192 {backup_file})")
            # Persist last auto-backup info
            try:
                self.app_manager.set_setting("last_auto_backup_info", {"timestamp": now_iso, "path": backup_file})
            except Exception:
                pass
            # Notify main window to update status bar immediately
            try:
                self._update_mainwindow_backup_status(now_iso, 'automatisk', backup_file)
            except Exception:
                pass
        except Exception:
            pass
        
        # Email is now handled globally by app_manager, no need to send here

    def _update_mainwindow_backup_status(self, timestamp_iso: str, source: str, path: str = ""):
        """Helper to update MainWindow's backup status label if available."""
        try:
            # Preferred path: use AppManager reference set in MainWindow
            if hasattr(self.app_manager, 'main_window') and self.app_manager.main_window:
                mw = self.app_manager.main_window
                if hasattr(mw, 'update_backup_status'):
                    mw.update_backup_status(timestamp_iso, source, path)
                    return
            # Fallback: walk parent chain to find a widget with update_backup_status
            parent = self.parent()
            # Safely traverse parent hierarchy
            guard = 0
            while parent is not None and guard < 10:
                if hasattr(parent, 'update_backup_status'):
                    parent.update_backup_status(timestamp_iso, source, path)
                    return
                parent = parent.parent() if hasattr(parent, 'parent') else None
                guard += 1
        except Exception:
            pass

    
    def on_backup_started(self):
        """Handle backup started"""
        self.backup_progress.show()
        self.backup_progress.setValue(0)
    
    def on_backup_progress(self, progress):
        """Handle backup progress"""
        self.backup_progress.setValue(progress)
    
    def on_manual_backup_completed(self, backup_path):
        """Handle manual backup completion"""
        from .copyable_message_box import CopyableMessageBox
        CopyableMessageBox.information(
            self, 
            "Backup skapad", 
            f"Backup har skapats framgångsrikt:\n{backup_path}"
        )
        self.refresh_backup_list()
    
    def on_backup_completed(self, backup_file):
        """Handle backup completed"""
        self.backup_progress.hide()
        self.refresh_backup_list()
        CopyableMessageBox.information(
            self, "Backup klar",
            f"Backup har skapats:\n{backup_file}"
        )
        # Update discreet status label for manual backups
        try:
            from datetime import datetime
            now_iso = datetime.now().isoformat()
            ts = datetime.fromisoformat(now_iso).strftime('%Y-%m-%d %H:%M')
            if hasattr(self, 'last_auto_backup_label') and self.last_auto_backup_label:
                self.last_auto_backup_label.setText(f"Senaste manuella backup: {ts}  (\u2192 {backup_file})")
            # Persist last manual-backup info
            try:
                self.app_manager.set_setting("last_manual_backup_info", {"timestamp": now_iso, "path": backup_file})
            except Exception:
                pass
            # Notify main window to update status bar immediately
            try:
                self._update_mainwindow_backup_status(now_iso, 'manuell', backup_file)
            except Exception:
                pass
        except Exception:
            pass
        
        # Email is now handled globally by app_manager, no need to send here
    
    def on_backup_error(self, error_msg):
        """Handle backup error"""
        self.backup_progress.hide()
        CopyableMessageBox.critical(self, "Backup-fel", error_msg)
    def load_backup_settings(self):
        """Load backup settings into UI"""
        try:
            config = self.backup_manager.get_config()
            
            if hasattr(self, 'backup_enabled_cb'):
                self.backup_enabled_cb.setChecked(config.get("enabled", False))
            
            if hasattr(self, 'backup_frequency_combo'):
                frequency = config.get("frequency", "daily")
                frequency_map = {"daily": 0, "weekly": 1, "monthly": 2}
                self.backup_frequency_combo.setCurrentIndex(frequency_map.get(frequency, 0))
            
            # Load email confirmation setting
            if hasattr(self, 'backup_email_cb'):
                email_enabled = self.app_manager.get_setting("backup_email_confirmation", False)
                self.backup_email_cb.setChecked(email_enabled)
            
            # Load backup path and refresh list immediately on startup
            try:
                if hasattr(self, 'backup_path_edit'):
                    self.backup_path_edit.setText(config.get("backup_path", "backups"))
                # Refresh list from current path regardless of auto/manual events
                self.refresh_backup_list()
            except Exception:
                pass
            # Show last backup status label from persisted settings
            try:
                from datetime import datetime
                info_auto = self.app_manager.get_setting("last_auto_backup_info", {}) or {}
                info_manual = self.app_manager.get_setting("last_manual_backup_info", {}) or {}
                ts_auto = info_auto.get("timestamp")
                ts_manual = info_manual.get("timestamp")
                latest_label = None
                if ts_auto and ts_manual:
                    dt_a = datetime.fromisoformat(ts_auto)
                    dt_m = datetime.fromisoformat(ts_manual)
                    if dt_m > dt_a:
                        latest_label = f"Senaste manuella backup: {dt_m.strftime('%Y-%m-%d %H:%M')}  (\u2192 {info_manual.get('path','')})"
                    else:
                        latest_label = f"Senaste automatisk backup: {dt_a.strftime('%Y-%m-%d %H:%M')}  (\u2192 {info_auto.get('path','')})"
                elif ts_manual:
                    dt_m = datetime.fromisoformat(ts_manual)
                    latest_label = f"Senaste manuella backup: {dt_m.strftime('%Y-%m-%d %H:%M')}  (\u2192 {info_manual.get('path','')})"
                elif ts_auto:
                    dt_a = datetime.fromisoformat(ts_auto)
                    latest_label = f"Senaste automatisk backup: {dt_a.strftime('%Y-%m-%d %H:%M')}  (\u2192 {info_auto.get('path','')})"
                if latest_label and hasattr(self, 'last_auto_backup_label') and self.last_auto_backup_label:
                    self.last_auto_backup_label.setText(latest_label)
            except Exception:
                pass
        except Exception as e:
            print(f"Error updating main window user display: {e}")
    
    def closeEvent(self, event):
        """Handle window close event - cleanup resources"""
        try:
            if hasattr(self, 'backup_manager') and self.backup_manager:
                self.backup_manager.cleanup()
        except Exception as e:
            print(f"Error during settings window cleanup: {e}")
        
        super().closeEvent(event)
    
    def create_security_group(self):
        """Create security settings group"""
        group = QGroupBox("Säkerhetsinställningar")
        layout = QFormLayout(group)
        
        # Auto-logout setting
        self.auto_logout_checkbox = QCheckBox()
        self.auto_logout_checkbox.setText("Automatisk utloggning efter 5 minuters inaktivitet")
        layout.addRow(self.auto_logout_checkbox)

        # Debug mode setting
        self.debug_mode_checkbox = QCheckBox()
        self.debug_mode_checkbox.setText("Debugläge (visa 'Kopiera' i popuper och klicka för att kopiera)")
        layout.addRow(self.debug_mode_checkbox)
        
        return group
    
    def load_security_settings(self):
        """Load security settings from app manager"""
        auto_logout = self.app_manager.get_setting("auto_logout_enabled", True)
        self.auto_logout_checkbox.setChecked(auto_logout)
        debug_mode = self.app_manager.get_setting("debug_mode", False)
        self.debug_mode_checkbox.setChecked(debug_mode)
    
    def save_security_settings(self):
        """Save security settings to app manager"""
        auto_logout_value = self.auto_logout_checkbox.isChecked()
        print(f"DEBUG: Saving auto_logout_enabled = {auto_logout_value}")
        self.app_manager.set_setting("auto_logout_enabled", auto_logout_value)
        # Save debug mode
        debug_value = self.debug_mode_checkbox.isChecked()
        print(f"DEBUG: Saving debug_mode = {debug_value}")
        self.app_manager.set_setting("debug_mode", debug_value)
        print(f"DEBUG: Security settings saved successfully")
    
    def create_license_group(self):
        """Create license information group"""
        group = QGroupBox("Licensinformation")
        layout = QVBoxLayout(group)
        
        # Get license info
        license_info = self.license_manager.get_license_info()
        
        if license_info['valid']:
            # Valid license display
            info_layout = QFormLayout()
            
            # License type
            license_type = QLabel(license_info.get('license_type', 'Standard'))
            license_type.setProperty("kb_label_type", "success")
            info_layout.addRow("Licenstyp:", license_type)
            
            # Company
            company = QLabel(license_info.get('company', 'Okänd'))
            info_layout.addRow("Företag:", company)
            
            # Expiration date
            expires_at = license_info.get('expires_at', '')
            if expires_at:
                from datetime import datetime
                try:
                    exp_date = datetime.fromisoformat(expires_at)
                    exp_str = exp_date.strftime("%Y-%m-%d")
                    expires_label = QLabel(exp_str)
                    
                    # Color code based on time remaining
                    days_left = (exp_date - datetime.now()).days
                    if days_left < 30:
                        expires_label.setProperty("kb_label_type", "error")
                    elif days_left < 90:
                        expires_label.setProperty("kb_label_type", "warning")
                    else:
                        expires_label.setProperty("kb_label_type", "success")
                        
                    info_layout.addRow("Giltig till:", expires_label)
                except:
                    info_layout.addRow("Giltig till:", QLabel("Okänt"))
            
            # Max users
            max_users = QLabel(str(license_info.get('max_users', 'Obegränsat')))
            info_layout.addRow("Max användare:", max_users)
            
            layout.addLayout(info_layout)
            
            # Status
            status_label = QLabel("✓ Licens giltig")
            status_label.setProperty("kb_label_type", "success")
            layout.addWidget(status_label)
            
        else:
            # Invalid license display
            error_label = QLabel(f"❌ {license_info.get('error', 'Licensfel')}")
            error_label.setProperty("kb_label_type", "error")
            layout.addWidget(error_label)
            
            # Machine ID for support
            machine_id_layout = QFormLayout()
            machine_id_label = QLabel(license_info.get('machine_id', 'Okänd'))
            machine_id_label.setProperty("kb_label_type", "caption")
            machine_id_layout.addRow("Maskin-ID:", machine_id_label)
            layout.addLayout(machine_id_layout)
            
            # Activation button
            activate_btn = QPushButton("Aktivera licens")
            activate_btn.clicked.connect(self.show_license_activation)
            layout.addWidget(activate_btn)
        
        return group
    
    def show_license_activation(self):
        """Show license activation dialog"""
        from ..core.license_manager import LicenseDialog
        dialog = LicenseDialog(self)
        if dialog.show_activation_dialog() == 1:  # Accepted
            # Refresh license display
            self.load_current_settings()
            CopyableMessageBox.information(self, "Licens", "Licensinformation uppdaterad!")
    
    def update_ui_text(self):
        """Update UI text for current language"""
        pass# This would update all text elements with current language
        pass
