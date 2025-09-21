"""
Add System window for creating new customer systems
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QTextEdit, QGroupBox, QFormLayout,
                              QScrollArea, QPushButton, QMessageBox, QComboBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .styles import KeyBuddyButton, KeyBuddyLineEdit, ButtonType, FieldType

class AddSystemWindow(QWidget):
    """Window for adding new customer systems"""
    
    navigate_home = Signal()
    
    def __init__(self, app_manager, db_manager, translation_manager):
        super().__init__()
        self.app_manager = app_manager
        self.db_manager = db_manager
        self.translation_manager = translation_manager
        
        # Mode tracking for mutual exclusion
        self.current_mode = None  # 'nyckelkort' or 'standard' or None
        
        self.setup_ui()
        self.setup_mode_logic()
    
    def setup_ui(self):
        """Setup add system UI"""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Main widget inside scroll area
        main_widget = QWidget()
        main_widget.setMaximumWidth(1400)  # Increased overall width for wider fields
        scroll.setWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Nytt System")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Create horizontal layout for customer and system groups
        groups_layout = QHBoxLayout()
        
        # Customer information group
        customer_group = self.create_customer_group()
        groups_layout.addWidget(customer_group)
        
        # Key system information group
        system_group = self.create_system_group()
        groups_layout.addWidget(system_group)

        # Standard & System-nycklar group on the right
        standard_group = self.create_standard_group()
        groups_layout.addWidget(standard_group)
        
        # Add stretch to push groups to the left
        groups_layout.addStretch()
        
        layout.addLayout(groups_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        home_btn = KeyBuddyButton(self.translation_manager.get_text("home"), ButtonType.SECONDARY)
        home_btn.clicked.connect(self.navigate_home.emit)
        
        clear_btn = KeyBuddyButton("Rensa", ButtonType.SECONDARY)
        clear_btn.clicked.connect(self.clear_form)
        
        save_btn = KeyBuddyButton(self.translation_manager.get_text("save"), ButtonType.PRIMARY)
        save_btn.clicked.connect(self.save_system)
        
        button_layout.addWidget(home_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Set main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
    
    def create_customer_group(self):
        """Create customer information group"""
        group = QGroupBox(self.translation_manager.get_text("customer"))
        group.setMaximumWidth(650)  # Increased width for longer company names
        layout = QFormLayout(group)
        
        # Customer fields
        self.company_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Företagsnamn")
        self.company_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("company") + " *:", self.company_edit)
        
        self.project_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Projektnamn")
        self.project_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("project") + ":", self.project_edit)
        
        self.customer_number_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Kundnummer")
        self.customer_number_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("customer_number") + ":", self.customer_number_edit)
        
        self.org_number_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Organisationsnummer")
        self.org_number_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("org_number") + ":", self.org_number_edit)
        
        self.address_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Gatuadress")
        self.address_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("address") + ":", self.address_edit)
        
        self.postal_code_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Postnummer")
        self.postal_code_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("postal_code") + ":", self.postal_code_edit)
        
        self.postal_address_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Postort")
        self.postal_address_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("postal_address") + ":", self.postal_address_edit)
        
        self.phone_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Telefonnummer")
        self.phone_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("phone") + ":", self.phone_edit)
        
        self.mobile_phone_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Mobilnummer")
        self.mobile_phone_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("mobile_phone") + ":", self.mobile_phone_edit)
        
        self.email_edit = KeyBuddyLineEdit(FieldType.STANDARD, "E-postadress")
        self.email_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("email") + ":", self.email_edit)
        
        self.website_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Hemsida")
        self.website_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("website") + ":", self.website_edit)
        
        self.key_responsible_1_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Namn på nyckelansvarig")
        self.key_responsible_1_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("key_responsible_1") + ":", self.key_responsible_1_edit)
        
        self.key_responsible_2_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Namn på nyckelansvarig")
        self.key_responsible_2_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("key_responsible_2") + ":", self.key_responsible_2_edit)
        
        self.key_responsible_3_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Namn på nyckelansvarig")
        self.key_responsible_3_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("key_responsible_3") + ":", self.key_responsible_3_edit)
        
        return group
    
    def create_system_group(self):
        """Create key system information group"""
        # Create group with icon in title
        self.nyckelkort_group = QGroupBox("🔑 Nyckelkort")
        self.nyckelkort_group.setMaximumWidth(650)  # Same width as customer group
        layout = QFormLayout(self.nyckelkort_group)
        group = self.nyckelkort_group
        
        # System fields
        self.key_code_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Nyckelkod")
        self.key_code_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("key_code") + ":", self.key_code_edit)
        
        self.series_id_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Serie-ID")
        self.series_id_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("series_id") + ":", self.series_id_edit)
        
        self.key_profile_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Nyckelprofil")
        self.key_profile_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("key_profile") + ":", self.key_profile_edit)
        
        # Nyckelplats (moved from customer group)
        self.key_location_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Plats för nycklar")
        self.key_location_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("key_location") + ":", self.key_location_edit)
        
        # Fabrikat dropdown (from DB key_catalog)
        self.fabrikat_combo = QComboBox()
        self.fabrikat_combo.setMinimumWidth(500)
        self.fabrikat_combo.setMaximumWidth(500)
        self.populate_fabrikat_combo()
        self.fabrikat_combo.currentTextChanged.connect(self.on_fabrikat_changed)
        layout.addRow("Fabrikat:", self.fabrikat_combo)
        
        # Koncept dropdown (filtered by Fabrikat)
        self.koncept_combo = QComboBox()
        self.koncept_combo.addItems(["Välj koncept..."])
        self.koncept_combo.setMinimumWidth(500)
        self.koncept_combo.setMaximumWidth(500)
        self.koncept_combo.setEnabled(False)
        layout.addRow("Koncept:", self.koncept_combo)
        
        # Billing options framed and placed near Koncept
        billing_group = QGroupBox("Debitering för nyckelkort")
        billing_form = QFormLayout(billing_group)
        billing_form.setVerticalSpacing(6)  # Match spacing with other groups
        billing_form.setLabelAlignment(Qt.AlignLeft)
        billing_group.setStyleSheet("QGroupBox { font-weight: bold; }")

        self.billing_plan_combo = QComboBox()
        self.billing_plan_combo.addItems([
            "Välj plan...",
            "Engångskostnad",
            "Månadskostnad",
            "Halvårskostnad",
            "Helårskostnad"
        ])
        self.billing_plan_combo.setMinimumWidth(500)
        self.billing_plan_combo.setMaximumWidth(500)
        billing_form.addRow("Betalningsplan:", self.billing_plan_combo)

        # Single price input - simplified from 4 separate fields to 1
        self.price_edit = KeyBuddyLineEdit(FieldType.STANDARD, "0.00")
        self.price_edit.setMaximumWidth(500)
        billing_form.addRow("Pris:", self.price_edit)

        layout.addRow(billing_group)
        
        # Notes / Övrigt as separate field with consistent spacing
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Skriv en kort text som följer med till tillverkningsordern")
        self.notes_edit.setFixedHeight(60)
        self.notes_edit.setMaximumWidth(500)
        layout.addRow("Övrigt:", self.notes_edit)
        
        return group

    def create_standard_group(self):
        """Create 'Standard & System-nycklar' group with separate catalog"""
        # Create group with icon in title
        self.standard_group = QGroupBox("⚙️ Standard & System-nycklar")
        self.standard_group.setMaximumWidth(650)
        layout = QFormLayout(self.standard_group)
        group = self.standard_group

        self.key_code2_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Nyckelkod 2")
        self.key_code2_edit.setMaximumWidth(500)
        layout.addRow("Nyckelkod 2:", self.key_code2_edit)

        self.system_number_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Systemnummer")
        self.system_number_edit.setMaximumWidth(500)
        layout.addRow("Systemnummer:", self.system_number_edit)

        self.profile2_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Profil")
        self.profile2_edit.setMaximumWidth(500)
        layout.addRow("Profil:", self.profile2_edit)

        self.delning_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Delning")
        self.delning_edit.setMaximumWidth(500)
        layout.addRow("Delning:", self.delning_edit)

        self.key_location2_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Nyckelplats 2")
        self.key_location2_edit.setMaximumWidth(500)
        layout.addRow("Nyckelplats 2:", self.key_location2_edit)

        self.fabrikat2_combo = QComboBox(); self.fabrikat2_combo.setMinimumWidth(500); self.fabrikat2_combo.setMaximumWidth(500)
        self.populate_fabrikat2_combo()
        self.fabrikat2_combo.currentTextChanged.connect(self.on_fabrikat2_changed)
        layout.addRow("Fabrikat 2:", self.fabrikat2_combo)

        self.koncept2_combo = QComboBox(); self.koncept2_combo.addItems(["Välj koncept..."]); self.koncept2_combo.setMinimumWidth(500); self.koncept2_combo.setMaximumWidth(500); self.koncept2_combo.setEnabled(False)
        layout.addRow("Koncept 2:", self.koncept2_combo)

        self.flex1_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Flex 1")
        self.flex1_edit.setMaximumWidth(500)
        self.flex2_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Flex 2")
        self.flex2_edit.setMaximumWidth(500)
        self.flex3_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Flex 3")
        self.flex3_edit.setMaximumWidth(500)
        layout.addRow("Flex1:", self.flex1_edit)
        layout.addRow("Flex2:", self.flex2_edit)
        layout.addRow("Flex3:", self.flex3_edit)

        return group
    
    def setup_mode_logic(self):
        """Setup mutual exclusion logic between Nyckelkort and Standard groups"""
        # Connect all Nyckelkort fields to mode detection
        nyckelkort_fields = [
            self.key_code_edit,
            self.series_id_edit, 
            self.key_profile_edit,
            self.key_location_edit,
            self.fabrikat_combo,
            self.koncept_combo
        ]
        
        # Connect all Standard fields to mode detection  
        standard_fields = [
            self.key_code2_edit,
            self.system_number_edit,
            self.profile2_edit,
            self.delning_edit,
            self.key_location2_edit,
            self.fabrikat2_combo,
            self.koncept2_combo,
            self.flex1_edit,
            self.flex2_edit,
            self.flex3_edit
        ]
        
        # Connect text change signals for line edits
        for field in nyckelkort_fields:
            if hasattr(field, 'textChanged'):
                field.textChanged.connect(lambda: self.check_mode_change('nyckelkort'))
            elif hasattr(field, 'currentTextChanged'):
                field.currentTextChanged.connect(lambda: self.check_mode_change('nyckelkort'))
        
        for field in standard_fields:
            if hasattr(field, 'textChanged'):
                field.textChanged.connect(lambda: self.check_mode_change('standard'))
            elif hasattr(field, 'currentTextChanged'):
                field.currentTextChanged.connect(lambda: self.check_mode_change('standard'))
        
        # Initial state - both groups enabled
        self.update_group_states()
    
    def check_mode_change(self, attempted_mode):
        """Check if mode should change based on field input"""
        # Check if any nyckelkort fields have content
        nyckelkort_has_content = (
            self.key_code_edit.text().strip() or
            self.series_id_edit.text().strip() or
            self.key_profile_edit.text().strip() or
            self.key_location_edit.text().strip() or
            (self.fabrikat_combo.currentText() and self.fabrikat_combo.currentText() != "Välj fabrikat...") or
            (self.koncept_combo.currentText() and self.koncept_combo.currentText() != "Välj koncept...")
        )
        
        # Check if any standard fields have content
        standard_has_content = (
            self.key_code2_edit.text().strip() or
            self.system_number_edit.text().strip() or
            self.profile2_edit.text().strip() or
            self.delning_edit.text().strip() or
            self.key_location2_edit.text().strip() or
            (self.fabrikat2_combo.currentText() and self.fabrikat2_combo.currentText() != "Välj fabrikat...") or
            (self.koncept2_combo.currentText() and self.koncept2_combo.currentText() != "Välj koncept...") or
            self.flex1_edit.text().strip() or
            self.flex2_edit.text().strip() or
            self.flex3_edit.text().strip()
        )
        
        # Determine new mode
        if nyckelkort_has_content and not standard_has_content:
            self.current_mode = 'nyckelkort'
        elif standard_has_content and not nyckelkort_has_content:
            self.current_mode = 'standard'
        elif not nyckelkort_has_content and not standard_has_content:
            self.current_mode = None
        # If both have content, keep current mode (shouldn't happen in normal flow)
        
        self.update_group_states()
    
    def update_group_states(self):
        """Update visual state of groups based on current mode"""
        if self.current_mode == 'nyckelkort':
            # Nyckelkort active, Standard disabled
            self.nyckelkort_group.setTitle("🔑 Nyckelkort ✅")
            self.standard_group.setTitle("⚙️ Standard & System-nycklar ❌")
            self.set_group_enabled(self.standard_group, False)
            self.set_group_enabled(self.nyckelkort_group, True)
            
        elif self.current_mode == 'standard':
            # Standard active, Nyckelkort disabled
            self.nyckelkort_group.setTitle("🔑 Nyckelkort ❌")
            self.standard_group.setTitle("⚙️ Standard & System-nycklar ✅")
            self.set_group_enabled(self.nyckelkort_group, False)
            self.set_group_enabled(self.standard_group, True)
            
        else:
            # Both available
            self.nyckelkort_group.setTitle("🔑 Nyckelkort")
            self.standard_group.setTitle("⚙️ Standard & System-nycklar")
            self.set_group_enabled(self.nyckelkort_group, True)
            self.set_group_enabled(self.standard_group, True)
    
    def set_group_enabled(self, group, enabled):
        """Enable/disable all input fields in a group"""
        for child in group.findChildren(KeyBuddyLineEdit):
            child.setEnabled(enabled)
        for child in group.findChildren(QComboBox):
            child.setEnabled(enabled)
        # Note: Billing and Notes should always remain enabled
        # They are in nyckelkort group but should be accessible regardless
        if hasattr(self, 'billing_plan_combo'):
            self.billing_plan_combo.setEnabled(True)
        if hasattr(self, 'price_edit'):
            self.price_edit.setEnabled(True)
        if hasattr(self, 'notes_edit'):
            self.notes_edit.setEnabled(True)
    
    def populate_fabrikat_combo(self):
        """Load unik Fabrikat from key_catalog table"""
        try:
            self.fabrikat_combo.clear()
            self.fabrikat_combo.addItem("Välj fabrikat...")
            rows = self.db_manager.execute_query("SELECT DISTINCT fabrikat FROM key_catalog ORDER BY fabrikat")
            for r in rows:
                val = r[0] if isinstance(r, (list, tuple)) else r['fabrikat']
                if val:
                    self.fabrikat_combo.addItem(str(val))
        except Exception:
            # Fallback: keep only the placeholder
            pass

    def on_fabrikat_changed(self, fabrikat):
        """When Fabrikat changes, load matching Koncept from key_catalog"""
        try:
            self.koncept_combo.clear()
            self.koncept_combo.addItem("Välj koncept...")
            self.koncept_combo.setEnabled(False)
            if not fabrikat or fabrikat == "Välj fabrikat...":
                return
            rows = self.db_manager.execute_query(
                "SELECT koncept FROM key_catalog WHERE fabrikat = ? ORDER BY koncept", (fabrikat,)
            )
            for r in rows:
                val = r[0] if isinstance(r, (list, tuple)) else r['koncept']
                if val:
                    self.koncept_combo.addItem(str(val))
            # Enable only if there are real items beyond placeholder
            self.koncept_combo.setEnabled(self.koncept_combo.count() > 1)
        except Exception:
            pass

    def populate_fabrikat2_combo(self):
        """Load Fabrikat 2 from key_catalog2"""
        try:
            self.fabrikat2_combo.clear()
            self.fabrikat2_combo.addItem("Välj fabrikat...")
            rows = self.db_manager.execute_query("SELECT DISTINCT fabrikat FROM key_catalog2 ORDER BY fabrikat")
            for r in rows:
                val = r[0] if isinstance(r, (list, tuple)) else r['fabrikat']
                if val:
                    self.fabrikat2_combo.addItem(str(val))
        except Exception:
            pass

    def on_fabrikat2_changed(self, fabrikat):
        """When Fabrikat 2 changes, load Koncept 2 from key_catalog2"""
        try:
            self.koncept2_combo.clear()
            self.koncept2_combo.addItem("Välj koncept...")
            self.koncept2_combo.setEnabled(False)
            if not fabrikat or fabrikat == "Välj fabrikat...":
                return
            rows = self.db_manager.execute_query("SELECT koncept FROM key_catalog2 WHERE fabrikat = ? ORDER BY koncept", (fabrikat,))
            for r in rows:
                val = r[0] if isinstance(r, (list, tuple)) else r['koncept']
                if val:
                    self.koncept2_combo.addItem(str(val))
            self.koncept2_combo.setEnabled(self.koncept2_combo.count() > 1)
        except Exception:
            pass
    
    def clear_form(self):
        """Clear all form fields"""
        reply = QMessageBox.question(
            self,
            "Rensa formulär",
            "Är du säker på att du vill rensa alla fält?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear customer fields
            self.company_edit.clear()
            self.project_edit.clear()
            self.customer_number_edit.clear()
            self.org_number_edit.clear()
            self.address_edit.clear()
            self.postal_code_edit.clear()
            self.postal_address_edit.clear()
            self.phone_edit.clear()
            self.mobile_phone_edit.clear()
            self.email_edit.clear()
            self.website_edit.clear()
            self.key_responsible_1_edit.clear()
            self.key_responsible_2_edit.clear()
            self.key_responsible_3_edit.clear()
            self.key_location_edit.clear()
            
            # Clear system fields
            self.key_code_edit.clear()
            self.series_id_edit.clear()
            self.key_profile_edit.clear()
            self.fabrikat_combo.setCurrentIndex(0)
            self.koncept_combo.clear()
            self.koncept_combo.setEnabled(False)
            
            # Clear billing fields for nyckelkort
            try:
                if hasattr(self, 'billing_plan_combo'):
                    self.billing_plan_combo.setCurrentIndex(0)
                if hasattr(self, 'price_edit'):
                    self.price_edit.clear()
                if hasattr(self, 'notes_edit'):
                    self.notes_edit.clear()
                # Clear Standard & System-nycklar
                for attr in ['key_code2_edit','system_number_edit','profile2_edit','delning_edit','key_location2_edit','flex1_edit','flex2_edit','flex3_edit']:
                    if hasattr(self, attr):
                        getattr(self, attr).clear()
                if hasattr(self, 'fabrikat2_combo'):
                    self.fabrikat2_combo.setCurrentIndex(0)
                if hasattr(self, 'koncept2_combo'):
                    self.koncept2_combo.clear(); self.koncept2_combo.addItem("Välj koncept..."); self.koncept2_combo.setEnabled(False)
            except Exception:
                pass
            
            # Reset mode logic
            self.current_mode = None
            self.update_group_states()
    
    def validate_form(self):
        """Validate form data with strict field requirements"""
        errors = []
        
        # Required fields
        if not self.company_edit.text().strip():
            errors.append("Företag är obligatoriskt")
        
        if not self.mobile_phone_edit.text().strip():
            errors.append("Mobiltelefon är obligatoriskt")
        
        if not self.email_edit.text().strip():
            errors.append("E-post är obligatoriskt")
        
        if not self.key_responsible_1_edit.text().strip():
            errors.append("Nyckelansvarig 1 är obligatoriskt")
        
        # Nyckelkod optional; if provided validate exactly 7 digits
        key_code = self.key_code_edit.text().strip()
        if key_code:
            if not key_code.isdigit():
                errors.append("Nyckelkod får endast innehålla siffror")
            elif len(key_code) != 7:
                errors.append("Nyckelkod måste vara exakt 7 siffror")
        
        # Nyckelprofil optional; if provided 1-3 digits
        key_profile = self.key_profile_edit.text().strip()
        if key_profile:
            if not key_profile.isdigit():
                errors.append("Nyckelprofil får endast innehålla siffror")
            elif len(key_profile) < 1 or len(key_profile) > 3:
                errors.append("Nyckelprofil måste vara 1-3 siffror")
        
        # Serie-ID validation - optional but if provided must be exactly 3 digits
        series_id = self.series_id_edit.text().strip()
        if series_id:  # Only validate if provided
            if not series_id.isdigit():
                errors.append("Serie-ID får endast innehålla siffror")
            elif len(series_id) != 3:
                errors.append("Serie-ID måste vara exakt 3 siffror")
        
        # Email validation - more thorough
        email = self.email_edit.text().strip()
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                errors.append("Ogiltig e-postadress")
        
        return errors
    
    def save_system(self):
        """Save new system to database"""
        # Validate form
        errors = self.validate_form()
        if errors:
            QMessageBox.warning(
                self,
                "Valideringsfel",
                "\n".join(errors)
            )
            return
        
        try:
            # Get current user
            current_user = self.app_manager.get_current_user()
            if not current_user:
                QMessageBox.critical(self, "Fel", "Ingen användare inloggad")
                return
            
            # Insert customer
            customer_id = self.db_manager.execute_update(
                """INSERT INTO customers (
                    company, project, customer_number, org_number, address,
                    postal_code, postal_address, phone, mobile_phone, email,
                    website, key_responsible_1, key_responsible_2, key_responsible_3,
                    key_location, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.company_edit.text().strip(),
                    self.project_edit.text().strip(),
                    self.customer_number_edit.text().strip(),
                    self.org_number_edit.text().strip(),
                    self.address_edit.text().strip(),
                    self.postal_code_edit.text().strip(),
                    self.postal_address_edit.text().strip(),
                    self.phone_edit.text().strip(),
                    self.mobile_phone_edit.text().strip(),
                    self.email_edit.text().strip(),
                    self.website_edit.text().strip(),
                    self.key_responsible_1_edit.text().strip(),
                    self.key_responsible_2_edit.text().strip(),
                    self.key_responsible_3_edit.text().strip(),
                    self.key_location_edit.text().strip(),
                    current_user['user_id']
                )
            )
            
            # Parse prices safely
            def _p(txt):
                try:
                    t = txt.strip()
                    return float(t) if t else None
                except Exception:
                    return None
            billing_plan = self.billing_plan_combo.currentText()
            if billing_plan == "Välj plan...":
                billing_plan = None
            # Single price field - used for all billing plans
            price = _p(self.price_edit.text())

            # Insert key system including Standard & System-nycklar
            self.db_manager.execute_update(
                """INSERT INTO key_systems (
                    customer_id, key_code, series_id, key_profile, fabrikat, koncept, notes,
                    billing_plan, price_one_time, price_monthly, price_half_year, price_yearly,
                    key_code2, system_number, profile2, delning, key_location2, fabrikat2, koncept2,
                    flex1, flex2, flex3
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    customer_id,
                    self.key_code_edit.text().strip(),
                    self.series_id_edit.text().strip(),
                    self.key_profile_edit.text().strip(),
                    self.fabrikat_combo.currentText().strip() if self.fabrikat_combo.currentText() != "Välj fabrikat..." else "",
                    self.koncept_combo.currentText().strip() if self.koncept_combo.currentText() != "Välj koncept..." else "",
                    (self.notes_edit.toPlainText().strip() if hasattr(self, 'notes_edit') else ""),
                    billing_plan,
                    price, None, None, None,  # Store price in price_one_time, others as None
                    self.key_code2_edit.text().strip() if hasattr(self, 'key_code2_edit') else "",
                    self.system_number_edit.text().strip() if hasattr(self, 'system_number_edit') else "",
                    self.profile2_edit.text().strip() if hasattr(self, 'profile2_edit') else "",
                    self.delning_edit.text().strip() if hasattr(self, 'delning_edit') else "",
                    self.key_location2_edit.text().strip() if hasattr(self, 'key_location2_edit') else "",
                    (self.fabrikat2_combo.currentText().strip() if hasattr(self, 'fabrikat2_combo') and self.fabrikat2_combo.currentText() != "Välj fabrikat..." else ""),
                    (self.koncept2_combo.currentText().strip() if hasattr(self, 'koncept2_combo') and self.koncept2_combo.currentText() != "Välj koncept..." else ""),
                    self.flex1_edit.text().strip() if hasattr(self, 'flex1_edit') else "",
                    self.flex2_edit.text().strip() if hasattr(self, 'flex2_edit') else "",
                    self.flex3_edit.text().strip() if hasattr(self, 'flex3_edit') else "",
                )
            )
            
            QMessageBox.information(
                self,
                "System sparat",
                f"Nytt system för {self.company_edit.text()} har sparats framgångsrikt."
            )
            
            # Clear form after successful save
            self.clear_form()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Databasfel",
                f"Kunde inte spara systemet: {str(e)}"
            )
    
    def update_ui_text(self):
        """Update UI text for current language"""
        pass
