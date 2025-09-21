"""
Modern Edit System Dialog - Complete redesign with all fields
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QTextEdit, QGroupBox, QFormLayout,
                              QScrollArea, QPushButton, QMessageBox, QComboBox, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .styles import KeyBuddyButton, KeyBuddyLineEdit, ButtonType, FieldType
from .copyable_message_box import CopyableMessageBox

class ModernEditSystemDialog(QDialog):
    """Modern dialog for editing all system data with smart field pairing"""
    
    system_updated = Signal()
    
    def __init__(self, system_data, db_manager, translation_manager, parent=None):
        super().__init__(parent)
        self.system_data = system_data
        self.db_manager = db_manager
        self.translation_manager = translation_manager
        
        # Mode tracking for mutual exclusion
        self.current_mode = None  # 'nyckelkort' or 'standard' or None
        
        self.setWindowTitle("Redigera System - Modern Design")
        self.setModal(True)
        self.resize(1400, 800)
        self.setup_ui()
        self.setup_mode_logic()
        self.load_data()
    
    def setup_ui(self):
        """Setup modern edit dialog UI"""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Main widget inside scroll area
        main_widget = QWidget()
        main_widget.setMaximumWidth(1400)
        scroll.setWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Redigera System")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Create horizontal layout for groups
        groups_layout = QHBoxLayout()
        
        # Customer information group
        customer_group = self.create_customer_group()
        groups_layout.addWidget(customer_group)
        
        # Key system information group (Nyckelkort)
        system_group = self.create_system_group()
        groups_layout.addWidget(system_group)

        # Standard & System-nycklar group
        standard_group = self.create_standard_group()
        groups_layout.addWidget(standard_group)
        
        # Add stretch to push groups to the left
        groups_layout.addStretch()
        
        layout.addLayout(groups_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = KeyBuddyButton("Avbryt", ButtonType.SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        
        clear_btn = KeyBuddyButton("Rensa", ButtonType.SECONDARY)
        clear_btn.clicked.connect(self.clear_form)
        
        save_btn = KeyBuddyButton("Spara Ändringar", ButtonType.PRIMARY)
        save_btn.clicked.connect(self.save_changes)
        
        button_layout.addWidget(cancel_btn)
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
        group.setMaximumWidth(650)
        layout = QFormLayout(group)
        
        # Customer fields
        self.company_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Företagsnamn")
        self.company_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("company") + ":", self.company_edit)
        
        self.project_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Projektnamn")
        self.project_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("project") + ":", self.project_edit)
        
        self.customer_number_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Kundnummer")
        self.customer_number_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("customer_number") + ":", self.customer_number_edit)
        
        self.org_number_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Organisationsnummer")
        self.org_number_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("org_number") + ":", self.org_number_edit)
        
        self.street_address_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Gatuadress")
        self.street_address_edit.setMaximumWidth(500)
        layout.addRow(self.translation_manager.get_text("street_address") + ":", self.street_address_edit)
        
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
        """Create key system information group (Nyckelkort)"""
        # Create group with icon in title
        self.nyckelkort_group = QGroupBox("🔑 Nyckelkort")
        self.nyckelkort_group.setMaximumWidth(650)
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
        billing_form.setVerticalSpacing(2)
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

        # Single price input
        self.price_edit = KeyBuddyLineEdit(FieldType.STANDARD, "0.00")
        self.price_edit.setMaximumWidth(500)
        billing_form.addRow("Pris:", self.price_edit)

        layout.addRow(billing_group)
        
        # Notes / Övrigt
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Skriv en kort text som följer med till tillverkningsordern")
        self.notes_edit.setFixedHeight(60)
        self.notes_edit.setMaximumWidth(500)
        layout.addRow("Övrigt:", self.notes_edit)
        
        return group

    def create_standard_group(self):
        """Create 'Standard & System-nycklar' group"""
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

        self.fabrikat2_combo = QComboBox()
        self.fabrikat2_combo.setMinimumWidth(500)
        self.fabrikat2_combo.setMaximumWidth(500)
        self.populate_fabrikat2_combo()
        self.fabrikat2_combo.currentTextChanged.connect(self.on_fabrikat2_changed)
        layout.addRow("Fabrikat 2:", self.fabrikat2_combo)

        self.koncept2_combo = QComboBox()
        self.koncept2_combo.addItems(["Välj koncept..."])
        self.koncept2_combo.setMinimumWidth(500)
        self.koncept2_combo.setMaximumWidth(500)
        self.koncept2_combo.setEnabled(False)
        layout.addRow("Koncept 2:", self.koncept2_combo)

        # Flex fields
        self.flex1_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Flex 1")
        self.flex1_edit.setMaximumWidth(500)
        layout.addRow("Flex 1:", self.flex1_edit)

        self.flex2_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Flex 2")
        self.flex2_edit.setMaximumWidth(500)
        layout.addRow("Flex 2:", self.flex2_edit)

        self.flex3_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Flex 3")
        self.flex3_edit.setMaximumWidth(500)
        layout.addRow("Flex 3:", self.flex3_edit)

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
        else:
            self.current_mode = None  # Both empty or both have content
        
        self.update_group_states()
    
    def update_group_states(self):
        """Update visual state and enable/disable groups based on current mode"""
        if self.current_mode == 'nyckelkort':
            # Nyckelkort active, Standard disabled
            self.nyckelkort_group.setTitle("🔑 Nyckelkort ✅")
            self.standard_group.setTitle("⚙️ Standard & System-nycklar ❌")
            self.set_group_enabled(self.nyckelkort_group, True)
            self.set_group_enabled(self.standard_group, False)
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
        """Enable or disable all fields in a group"""
        # Find KeyBuddyLineEdit widgets
        line_edits = group.findChildren(KeyBuddyLineEdit)
        # Find QComboBox widgets
        combo_boxes = group.findChildren(QComboBox)
        
        # Combine both lists
        all_widgets = line_edits + combo_boxes
        
        for child in all_widgets:
            child.setEnabled(enabled)
            if not enabled:
                child.setStyleSheet("color: #888888;")  # Gray out disabled fields
            else:
                child.setStyleSheet("")  # Reset to normal styling
    
    def show_message(self, message_type, title, message):
        """Show message with copyable option if debug mode is enabled"""
        try:
            # Check if debug mode is enabled via app_manager (since we don't have direct access to it, use fallback)
            debug_mode = False
            try:
                # Try to get debug mode from parent's app_manager if available
                if hasattr(self.parent(), 'app_manager'):
                    debug_mode = self.parent().app_manager.get_setting('debug_mode', False)
            except:
                pass
            
            if debug_mode:
                # Use copyable message box in debug mode
                if message_type == 'warning':
                    CopyableMessageBox.warning(self, title, message)
                elif message_type == 'critical':
                    CopyableMessageBox.critical(self, title, message)
                elif message_type == 'information':
                    CopyableMessageBox.information(self, title, message)
            else:
                # Use standard message box in normal mode
                if message_type == 'warning':
                    QMessageBox.warning(self, title, message)
                elif message_type == 'critical':
                    QMessageBox.critical(self, title, message)
                elif message_type == 'information':
                    QMessageBox.information(self, title, message)
        except Exception:
            # Fallback to standard message box if settings can't be read
            if message_type == 'warning':
                QMessageBox.warning(self, title, message)
            elif message_type == 'critical':
                QMessageBox.critical(self, title, message)
            elif message_type == 'information':
                QMessageBox.information(self, title, message)
    
    def populate_fabrikat_combo(self):
        """Populate fabrikat combo with data from key_catalog"""
        try:
            # Query database directly since get_fabrikats doesn't exist
            rows = self.db_manager.execute_query("SELECT DISTINCT fabrikat FROM key_catalog ORDER BY fabrikat")
            self.fabrikat_combo.clear()
            self.fabrikat_combo.addItem("Välj fabrikat...")
            for row in rows:
                fabrikat = row[0] if isinstance(row, (list, tuple)) else row['fabrikat']
                if fabrikat:
                    self.fabrikat_combo.addItem(fabrikat)
        except Exception as e:
            print(f"Error loading fabrikats: {e}")
    
    def populate_fabrikat2_combo(self):
        """Populate fabrikat2 combo with data from key_catalog"""
        try:
            # Query database directly since get_fabrikats doesn't exist
            rows = self.db_manager.execute_query("SELECT DISTINCT fabrikat FROM key_catalog ORDER BY fabrikat")
            self.fabrikat2_combo.clear()
            self.fabrikat2_combo.addItem("Välj fabrikat...")
            for row in rows:
                fabrikat = row[0] if isinstance(row, (list, tuple)) else row['fabrikat']
                if fabrikat:
                    self.fabrikat2_combo.addItem(fabrikat)
        except Exception as e:
            print(f"Error loading fabrikats: {e}")
    
    def on_fabrikat_changed(self, fabrikat):
        """Handle fabrikat selection change"""
        if fabrikat and fabrikat != "Välj fabrikat...":
            try:
                # Query database directly since get_koncepts_by_fabrikat doesn't exist
                rows = self.db_manager.execute_query(
                    "SELECT DISTINCT koncept FROM key_catalog WHERE fabrikat = ? ORDER BY koncept",
                    (fabrikat,)
                )
                self.koncept_combo.clear()
                self.koncept_combo.addItem("Välj koncept...")
                for row in rows:
                    koncept = row[0] if isinstance(row, (list, tuple)) else row['koncept']
                    if koncept:
                        self.koncept_combo.addItem(koncept)
                self.koncept_combo.setEnabled(True)
            except Exception as e:
                print(f"Error loading koncepts: {e}")
        else:
            self.koncept_combo.clear()
            self.koncept_combo.addItem("Välj koncept...")
            self.koncept_combo.setEnabled(False)
    
    def on_fabrikat2_changed(self, fabrikat):
        """Handle fabrikat2 selection change"""
        if fabrikat and fabrikat != "Välj fabrikat...":
            try:
                # Query database directly since get_koncepts_by_fabrikat doesn't exist
                rows = self.db_manager.execute_query(
                    "SELECT DISTINCT koncept FROM key_catalog WHERE fabrikat = ? ORDER BY koncept",
                    (fabrikat,)
                )
                self.koncept2_combo.clear()
                self.koncept2_combo.addItem("Välj koncept...")
                for row in rows:
                    koncept = row[0] if isinstance(row, (list, tuple)) else row['koncept']
                    if koncept:
                        self.koncept2_combo.addItem(koncept)
                self.koncept2_combo.setEnabled(True)
            except Exception as e:
                print(f"Error loading koncepts: {e}")
        else:
            self.koncept2_combo.clear()
            self.koncept2_combo.addItem("Välj koncept...")
            self.koncept2_combo.setEnabled(False)
    
    def load_data(self):
        """Load existing system data into form fields"""
        # Customer data
        self.company_edit.setText(self.system_data.get('company', ''))
        self.project_edit.setText(self.system_data.get('project', ''))
        self.customer_number_edit.setText(self.system_data.get('customer_number', ''))
        self.org_number_edit.setText(self.system_data.get('org_number', ''))
        self.street_address_edit.setText(self.system_data.get('street_address', ''))
        self.postal_code_edit.setText(self.system_data.get('postal_code', ''))
        self.postal_address_edit.setText(self.system_data.get('postal_address', ''))
        self.phone_edit.setText(self.system_data.get('phone', ''))
        self.mobile_phone_edit.setText(self.system_data.get('mobile_phone', ''))
        self.email_edit.setText(self.system_data.get('email', ''))
        self.website_edit.setText(self.system_data.get('website', ''))
        self.key_responsible_1_edit.setText(self.system_data.get('key_responsible_1', ''))
        self.key_responsible_2_edit.setText(self.system_data.get('key_responsible_2', ''))
        self.key_responsible_3_edit.setText(self.system_data.get('key_responsible_3', ''))
        
        # Nyckelkort data
        self.key_code_edit.setText(self.system_data.get('key_code', ''))
        self.series_id_edit.setText(self.system_data.get('series_id', ''))
        self.key_profile_edit.setText(self.system_data.get('key_profile', ''))
        self.key_location_edit.setText(self.system_data.get('key_location', ''))
        
        # Set fabrikat and koncept
        fabrikat = self.system_data.get('fabrikat', '')
        if fabrikat:
            index = self.fabrikat_combo.findText(fabrikat)
            if index >= 0:
                self.fabrikat_combo.setCurrentIndex(index)
                self.on_fabrikat_changed(fabrikat)
                
                koncept = self.system_data.get('koncept', '')
                if koncept:
                    koncept_index = self.koncept_combo.findText(koncept)
                    if koncept_index >= 0:
                        self.koncept_combo.setCurrentIndex(koncept_index)
        
        # Billing data
        billing_plan = self.system_data.get('billing_plan', '')
        if billing_plan:
            index = self.billing_plan_combo.findText(billing_plan)
            if index >= 0:
                self.billing_plan_combo.setCurrentIndex(index)
        
        self.price_edit.setText(str(self.system_data.get('price_one_time', 0.0)))
        self.notes_edit.setPlainText(self.system_data.get('notes', ''))
        
        # Standard & System-nycklar data
        self.key_code2_edit.setText(self.system_data.get('key_code2', ''))
        self.system_number_edit.setText(self.system_data.get('system_number', ''))
        self.profile2_edit.setText(self.system_data.get('profile2', ''))
        self.delning_edit.setText(self.system_data.get('delning', ''))
        self.key_location2_edit.setText(self.system_data.get('key_location2', ''))
        
        # Set fabrikat2 and koncept2
        fabrikat2 = self.system_data.get('fabrikat2', '')
        if fabrikat2:
            index = self.fabrikat2_combo.findText(fabrikat2)
            if index >= 0:
                self.fabrikat2_combo.setCurrentIndex(index)
                self.on_fabrikat2_changed(fabrikat2)
                
                koncept2 = self.system_data.get('koncept2', '')
                if koncept2:
                    koncept_index = self.koncept2_combo.findText(koncept2)
                    if koncept_index >= 0:
                        self.koncept2_combo.setCurrentIndex(koncept_index)
        
        # Flex fields
        self.flex1_edit.setText(self.system_data.get('flex1', ''))
        self.flex2_edit.setText(self.system_data.get('flex2', ''))
        self.flex3_edit.setText(self.system_data.get('flex3', ''))
        
        # Trigger mode detection after loading data
        self.check_mode_change(None)
    
    def clear_form(self):
        """Clear all form fields"""
        # Customer fields
        for field in [self.company_edit, self.project_edit, self.customer_number_edit,
                     self.org_number_edit, self.street_address_edit, self.postal_code_edit,
                     self.postal_address_edit, self.phone_edit, self.mobile_phone_edit,
                     self.email_edit, self.website_edit, self.key_responsible_1_edit,
                     self.key_responsible_2_edit, self.key_responsible_3_edit]:
            field.clear()
        
        # Nyckelkort fields
        for field in [self.key_code_edit, self.series_id_edit, self.key_profile_edit,
                     self.key_location_edit, self.price_edit]:
            field.clear()
        
        # Standard fields
        for field in [self.key_code2_edit, self.system_number_edit, self.profile2_edit,
                     self.delning_edit, self.key_location2_edit, self.flex1_edit,
                     self.flex2_edit, self.flex3_edit]:
            field.clear()
        
        # Combos
        self.fabrikat_combo.setCurrentIndex(0)
        self.koncept_combo.setCurrentIndex(0)
        self.fabrikat2_combo.setCurrentIndex(0)
        self.koncept2_combo.setCurrentIndex(0)
        self.billing_plan_combo.setCurrentIndex(0)
        
        # Text areas
        self.notes_edit.clear()
        
        # Reset mode
        self.current_mode = None
        self.update_group_states()
    
    def save_changes(self):
        """Save changes to database"""
        try:
            # Collect all data
            updated_data = {
                # Customer data
                'company': self.company_edit.text().strip(),
                'project': self.project_edit.text().strip(),
                'customer_number': self.customer_number_edit.text().strip(),
                'org_number': self.org_number_edit.text().strip(),
                'street_address': self.street_address_edit.text().strip(),
                'postal_code': self.postal_code_edit.text().strip(),
                'postal_address': self.postal_address_edit.text().strip(),
                'phone': self.phone_edit.text().strip(),
                'mobile_phone': self.mobile_phone_edit.text().strip(),
                'email': self.email_edit.text().strip(),
                'website': self.website_edit.text().strip(),
                'key_responsible_1': self.key_responsible_1_edit.text().strip(),
                'key_responsible_2': self.key_responsible_2_edit.text().strip(),
                'key_responsible_3': self.key_responsible_3_edit.text().strip(),
                
                # Nyckelkort data
                'key_code': self.key_code_edit.text().strip(),
                'series_id': self.series_id_edit.text().strip(),
                'key_profile': self.key_profile_edit.text().strip(),
                'key_location': self.key_location_edit.text().strip(),
                'fabrikat': self.fabrikat_combo.currentText() if self.fabrikat_combo.currentText() != "Välj fabrikat..." else '',
                'koncept': self.koncept_combo.currentText() if self.koncept_combo.currentText() != "Välj koncept..." else '',
                'billing_plan': self.billing_plan_combo.currentText() if self.billing_plan_combo.currentText() != "Välj plan..." else '',
                'price_one_time': float(self.price_edit.text() or 0),
                'notes': self.notes_edit.toPlainText().strip(),
                
                # Standard & System-nycklar data
                'key_code2': self.key_code2_edit.text().strip(),
                'system_number': self.system_number_edit.text().strip(),
                'profile2': self.profile2_edit.text().strip(),
                'delning': self.delning_edit.text().strip(),
                'key_location2': self.key_location2_edit.text().strip(),
                'fabrikat2': self.fabrikat2_combo.currentText() if self.fabrikat2_combo.currentText() != "Välj fabrikat..." else '',
                'koncept2': self.koncept2_combo.currentText() if self.koncept2_combo.currentText() != "Välj koncept..." else '',
                'flex1': self.flex1_edit.text().strip(),
                'flex2': self.flex2_edit.text().strip(),
                'flex3': self.flex3_edit.text().strip(),
            }
            
            # Validate required fields
            if not updated_data['company']:
                self.show_message('warning', "Valideringsfel", "Företagsnamn är obligatoriskt.")
                return
            
            # Update system in database using execute_update
            system_id = self.system_data['id']
            customer_id = self.system_data['customer_id']
            
            # Update customers table (customer information)
            customer_update_query = """
                UPDATE customers SET 
                    company = ?, project = ?, customer_number = ?, org_number = ?,
                    address = ?, postal_code = ?, postal_address = ?,
                    phone = ?, mobile_phone = ?, email = ?, website = ?,
                    key_responsible_1 = ?, key_responsible_2 = ?, key_responsible_3 = ?, key_location = ?
                WHERE id = ?
            """
            
            customer_params = (
                updated_data['company'], updated_data['project'], updated_data['customer_number'], updated_data['org_number'],
                updated_data['street_address'], updated_data['postal_code'], updated_data['postal_address'],
                updated_data['phone'], updated_data['mobile_phone'], updated_data['email'], updated_data['website'],
                updated_data['key_responsible_1'], updated_data['key_responsible_2'], updated_data['key_responsible_3'], updated_data['key_location'],
                customer_id
            )
            
            # Update key_systems table (system information)
            system_update_query = """
                UPDATE key_systems SET 
                    key_code = ?, series_id = ?, key_profile = ?,
                    fabrikat = ?, koncept = ?, billing_plan = ?, price_one_time = ?, notes = ?,
                    key_code2 = ?, system_number = ?, profile2 = ?, delning = ?, key_location2 = ?,
                    fabrikat2 = ?, koncept2 = ?, flex1 = ?, flex2 = ?, flex3 = ?
                WHERE id = ?
            """
            
            system_params = (
                updated_data['key_code'], updated_data['series_id'], updated_data['key_profile'],
                updated_data['fabrikat'], updated_data['koncept'], updated_data['billing_plan'], updated_data['price_one_time'], updated_data['notes'],
                updated_data['key_code2'], updated_data['system_number'], updated_data['profile2'], updated_data['delning'], updated_data['key_location2'],
                updated_data['fabrikat2'], updated_data['koncept2'], updated_data['flex1'], updated_data['flex2'], updated_data['flex3'],
                system_id
            )
            
            # Execute both updates
            customer_rows = self.db_manager.execute_update(customer_update_query, customer_params)
            system_rows = self.db_manager.execute_update(system_update_query, system_params)
            
            rows_affected = customer_rows + system_rows
            
            if rows_affected > 0:
                self.show_message('information', "Framgång", "Systemet har uppdaterats framgångsrikt.")
                self.system_updated.emit()
                self.accept()
            else:
                self.show_message('critical', "Fel", "Kunde inte uppdatera systemet. Inga rader påverkades.")
                
        except ValueError:
            self.show_message('warning', "Valideringsfel", "Priset måste vara ett giltigt nummer.")
        except Exception as e:
            self.show_message('critical', "Fel", f"Ett fel uppstod: {str(e)}")
