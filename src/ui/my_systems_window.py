"""
My Systems window for searching and managing existing systems
"""

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
                              QHeaderView, QPushButton, QMessageBox, QFormLayout,
                              QGroupBox, QSpinBox, QCheckBox, QProgressBar, QDialog, QComboBox,
                               QMessageBox, QAbstractItemView, QScrollArea, QDialogButtonBox, QToolButton, QMenu)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from .copyable_message_box import CopyableMessageBox
from ..core.pdf_generator import OrderPDFGenerator
from ..core.auth import AuthManager
from .key_fob_return_dialog import KeyFobReturnDialog
from .edit_system_dialog import ModernEditSystemDialog

from .styles import KeyBuddyButton, ButtonType
from .copyable_message_box import CopyableMessageBox

# Old EditSystemDialog removed - using ModernEditSystemDialog instead

class CreateKeyDialog(QDialog):
    """Dialog for creating key manufacturing order"""
    
    def __init__(self, parent, system_data, translation_manager):
        super().__init__(parent)
        self.system_data = system_data
        self.translation_manager = translation_manager
        self.setWindowTitle("Tillverka Nyckel")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup create key dialog UI"""
        layout = QVBoxLayout(self)
        
        # System info group
        info_group = QGroupBox("Systeminformation")
        info_layout = QFormLayout(info_group)
        
        # Use smart data logic to get display values (same as table and PDF)
        smart_data = self.get_smart_display_data(self.system_data)
        
        info_layout.addRow("Företag:", QLabel(self.system_data.get('company', '')))
        info_layout.addRow("Nyckelkod:", QLabel(smart_data.get('key_code', '')))
        info_layout.addRow("Profil:", QLabel(smart_data.get('key_profile', '')))
        
        layout.addWidget(info_group)
        
        # Order details group
        order_group = QGroupBox("Orderdetaljer")
        order_layout = QFormLayout(order_group)
        
        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(9999)
        self.quantity_spin.setValue(1)
        order_layout.addRow("Antal nycklar:", self.quantity_spin)
        
        # Sequence start
        self.sequence_start_spin = QSpinBox()
        self.sequence_start_spin.setMinimum(1)
        self.sequence_start_spin.setMaximum(9999)
        self.sequence_start_spin.setValue(1)
        order_layout.addRow("Löpnummer start:", self.sequence_start_spin)
        
        # Key responsible
        self.responsible_combo = QComboBox()
        self.responsible_combo.setEditable(True)
        # Add existing responsible persons
        responsibles = []
        for i in range(1, 4):
            resp = self.system_data.get(f'key_responsible_{i}', '').strip()
            if resp:
                responsibles.append(resp)
        
        if responsibles:
            self.responsible_combo.addItems(responsibles)
        else:
            self.responsible_combo.addItem("Ej angiven")
        
        order_layout.addRow("Nyckelansvarig:", self.responsible_combo)
        
        # Create receipt checkbox
        self.create_receipt_cb = QCheckBox("Skapa nyckelkvittens")
        self.create_receipt_cb.setChecked(True)
        order_layout.addRow(self.create_receipt_cb)
        
        layout.addWidget(order_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Avbryt")
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = QPushButton("Skapa Order")
        create_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
    
    def get_smart_display_data(self, system_data):
        """Smart logic to choose between Nyckelkort and Standard & System-nycklar data for display"""
        # Check if Nyckelkort data exists
        nyckelkort_has_data = (
            system_data.get('key_code', '').strip() or
            system_data.get('series_id', '').strip() or
            system_data.get('key_profile', '').strip() or
            system_data.get('key_location', '').strip() or
            system_data.get('fabrikat', '').strip() or
            system_data.get('koncept', '').strip()
        )
        
        # Check if Standard & System-nycklar data exists
        standard_has_data = (
            system_data.get('key_code2', '').strip() or
            system_data.get('system_number', '').strip() or
            system_data.get('profile2', '').strip() or
            system_data.get('delning', '').strip() or
            system_data.get('key_location2', '').strip() or
            system_data.get('fabrikat2', '').strip() or
            system_data.get('koncept2', '').strip()
        )
        
        # Smart key_location logic: prioritize nyckelplats, fallback to nyckelplats 2
        smart_key_location = system_data.get('key_location', '').strip()
        if not smart_key_location:
            smart_key_location = system_data.get('key_location2', '').strip()
        
        # Return the appropriate data set for display
        if nyckelkort_has_data:
            return {
                'key_code': system_data.get('key_code', ''),
                'series_id': system_data.get('series_id', ''),
                'key_profile': system_data.get('key_profile', ''),
                'key_location': smart_key_location,  # Use smart key_location
                'fabrikat': system_data.get('fabrikat', ''),
                'koncept': system_data.get('koncept', ''),
                'data_source': 'nyckelkort'
            }
        elif standard_has_data:
            return {
                'key_code': system_data.get('key_code2', ''),  # Map key_code2 -> key_code
                'series_id': system_data.get('system_number', ''),  # Map system_number -> series_id
                'key_profile': system_data.get('profile2', ''),  # Map profile2 -> key_profile
                'key_location': smart_key_location,  # Use smart key_location
                'fabrikat': system_data.get('fabrikat2', ''),  # Map fabrikat2 -> fabrikat
                'koncept': system_data.get('koncept2', ''),  # Map koncept2 -> koncept
                'data_source': 'standard'
            }
        else:
            # No data in either, return empty
            return {
                'key_code': '',
                'series_id': '',
                'key_profile': '',
                'key_location': smart_key_location,  # Use smart key_location
                'fabrikat': '',
                'koncept': '',
                'data_source': 'none'
            }
    
    def get_order_data(self):
        """Get order data from dialog"""
        return {
            'quantity': self.quantity_spin.value(),
            'sequence_start': self.sequence_start_spin.value(),
            'key_responsible': self.responsible_combo.currentText(),
            'create_receipt': self.create_receipt_cb.isChecked()
        }

class MySystemsWindow(QWidget):
    """Window for viewing and managing existing systems"""
    
    navigate_home = Signal()
    navigate_to_home = Signal()
    navigate_to_orders = Signal()
    order_created = Signal()
    
    def __init__(self, app_manager, db_manager, translation_manager):
        super().__init__()
        self.app_manager = app_manager
        self.db_manager = db_manager
        self.translation_manager = translation_manager
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Setup my systems UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel(self.translation_manager.get_text("my_systems"))
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Search section - styled to match orders window dropdowns
        search_group = QGroupBox("Filter")
        search_group.setMaximumWidth(700)  # Wider to hold extra filters
        search_layout = QHBoxLayout(search_group)
        search_layout.setSpacing(15)
        search_layout.setContentsMargins(15, 15, 15, 15)  # Add margins to center content
        search_layout.setAlignment(Qt.AlignVCenter)  # Center vertically
        
        # Use global styling - no local overrides
        
        search_label = QLabel("Sök:")
        search_label.setProperty("kb_label_type", "caption")
        from .styles import KeyBuddyLineEdit, FieldType
        
        cancel_btn = QPushButton("Avbryt")
        cancel_btn.clicked.connect(self.reject)
        self.apply_logout_button_style(cancel_btn)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def populate_fabrikat_combo(self):
        try:
            self.fabrikat_combo.clear()
            self.fabrikat_combo.addItem("Välj fabrikat...")
            rows = self.db_manager.execute_query("SELECT DISTINCT fabrikat FROM key_catalog ORDER BY fabrikat")
            for r in rows:
                val = r[0] if isinstance(r, (list, tuple)) else r['fabrikat']
                if val:
                    self.fabrikat_combo.addItem(str(val))
        except Exception:
            pass

    def on_fabrikat_changed(self, fabrikat):
        """Load concepts for selected Fabrikat"""
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
            self.koncept_combo.setEnabled(self.koncept_combo.count() > 1)
        except Exception:
            pass
    
    def apply_logout_button_style(self, button):
        """Apply small button style - DEPRECATED, use ButtonType.SMALL instead"""
        button.setProperty("kb_button_type", "small")
    
    def load_data(self):
        """Load system data into form"""
        # Get complete customer data
        customer_query = """SELECT company, project, customer_number, org_number, address,
                           postal_code, postal_address, phone, mobile_phone, email, website,
                           key_responsible_1, key_responsible_2, key_responsible_3, key_location
                           FROM customers WHERE id = ?"""
        customer_result = self.db_manager.execute_query(customer_query, (self.system_data['customer_id'],))
        
        if customer_result:
            customer_data = customer_result[0]
            self.company_edit.setText(customer_data[0] or '')
            self.project_edit.setText(customer_data[1] or '')
            self.customer_number_edit.setText(customer_data[2] or '')
            self.org_number_edit.setText(customer_data[3] or '')
            self.address_edit.setText(customer_data[4] or '')
            self.postal_code_edit.setText(customer_data[5] or '')
            self.postal_address_edit.setText(customer_data[6] or '')
            self.phone_edit.setText(customer_data[7] or '')
            self.mobile_phone_edit.setText(customer_data[8] or '')
            self.email_edit.setText(customer_data[9] or '')
            self.website_edit.setText(customer_data[10] or '')
            self.key_responsible_1_edit.setText(customer_data[11] or '')
            self.key_responsible_2_edit.setText(customer_data[12] or '')
            self.key_responsible_3_edit.setText(customer_data[13] or '')
            self.key_location_edit.setText(customer_data[14] or '')
        
        # Load system data
        self.key_code_edit.setText(self.system_data.get('key_code', '') or '')
        self.key_profile_edit.setText(self.system_data.get('key_profile', '') or '')
        self.series_id_edit.setText(self.system_data.get('series_id', '') or '')
        
        # Load fabrikat/koncept from existing system
        try:
            fab = self.system_data.get('fabrikat', '') or ""
            self.fabrikat_combo.setCurrentText(fab if fab else "Välj fabrikat...")
            # Populate koncept for selected fabrikat
            self.on_fabrikat_changed(self.fabrikat_combo.currentText())
            ktxt = self.system_data.get('koncept', '') or ""
            if ktxt:
                idx = self.koncept_combo.findText(ktxt)
                if idx >= 0:
                    self.koncept_combo.setCurrentIndex(idx)
        except Exception:
            pass
        
        # Load billing fields from DB
        try:
            ks = self.db_manager.execute_query(
                """
                SELECT billing_plan, price_one_time, price_monthly, price_half_year, price_yearly
                FROM key_systems WHERE id = ?
                """,
                (self.system_data['id'],)
            )
            if ks:
                billing_plan = ks[0][0]
                # Set plan
                if billing_plan:
                    idx = self.billing_plan_combo.findText(billing_plan)
                    if idx >= 0:
                        self.billing_plan_combo.setCurrentIndex(idx)
                # Prices
                def _fmt(v):
                    try:
                        return ("%g" % float(v)) if v is not None else ""
                    except Exception:
                        return ""
                self.price_one_time_edit.setText(_fmt(ks[0][1]))
                self.price_monthly_edit.setText(_fmt(ks[0][2]))
                self.price_half_year_edit.setText(_fmt(ks[0][3]))
                self.price_yearly_edit.setText(_fmt(ks[0][4]))
        except Exception:
            pass
        
        # Load notes
        try:
            notes = self.system_data.get('notes', '') or ''
            self.notes_edit.setText(notes)
        except Exception:
            pass
        
        # Always refresh from DB to ensure all dependent fields (like next due date) are recalculated
        try:
            current_id = None
            row = self.systems_table.currentRow()
            if row >= 0:
                id_item = self.systems_table.item(row, 0)
                if id_item:
                    current_id = id_item.text()
            self.refresh_data()
            # Reselect the same system if possible
            if current_id:
                for r in range(self.systems_table.rowCount()):
                    it = self.systems_table.item(r, 0)
                    if it and it.text() == current_id:
                        self.systems_table.selectRow(r)
                        break
        except Exception:
            pass
    
    def save_changes(self):
        """Save changes to database with comprehensive validation"""
        try:
            # Validate all fields with strict requirements
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
            
            # Nyckelkod validation - must be exactly 7 digits
            key_code = self.key_code_edit.text().strip()
            if not key_code:
                errors.append("Nyckelkod är obligatoriskt")
            elif not key_code.isdigit():
                errors.append("Nyckelkod får endast innehålla siffror")
            elif len(key_code) != 7:
                errors.append("Nyckelkod måste vara exakt 7 siffror")
            
            # Nyckelprofil validation - must be 1-3 digits
            key_profile = self.key_profile_edit.text().strip()
            if not key_profile:
                errors.append("Nyckelprofil är obligatoriskt")
            elif not key_profile.isdigit():
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
            
            # Show all errors at once
            if errors:
                CopyableMessageBox.warning(
                    self, 
                    "Valideringsfel", 
                    "\n".join(errors)
                )
                return
            
            # Update customer data with all fields
            self.db_manager.execute_update(
                """UPDATE customers SET 
                   company = ?, project = ?, customer_number = ?, org_number = ?, 
                   address = ?, postal_code = ?, postal_address = ?, phone = ?, 
                   mobile_phone = ?, email = ?, website = ?, key_responsible_1 = ?, 
                   key_responsible_2 = ?, key_responsible_3 = ?, key_location = ?
                   WHERE id = ?""",
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
                    self.system_data['customer_id']
                )
            )
            
            # Parse billing values
            billing_plan = self.billing_plan_combo.currentText()
            if billing_plan == "Välj plan...":
                billing_plan = None
            def _p(txt):
                try:
                    t = txt.strip()
                    return float(t) if t else None
                except Exception:
                    return None
            p_one = _p(self.price_one_time_edit.text())
            p_month = _p(self.price_monthly_edit.text())
            p_half = _p(self.price_half_year_edit.text())
            p_year = _p(self.price_yearly_edit.text())

            # Update key system data including billing and notes
            self.db_manager.execute_update(
                """UPDATE key_systems SET 
                   key_code = ?, key_profile = ?, series_id = ?, fabrikat = ?, koncept = ?, last_sequence_number = ?,
                   billing_plan = ?, price_one_time = ?, price_monthly = ?, price_half_year = ?, price_yearly = ?, notes = ?
                   WHERE id = ?""",
                (
                    self.key_code_edit.text().strip(),
                    self.key_profile_edit.text().strip(), 
                    self.series_id_edit.text().strip(),
                    self.fabrikat_combo.currentText().strip() if self.fabrikat_combo.currentText() != "Välj fabrikat..." else "",
                    self.koncept_combo.currentText().strip() if self.koncept_combo.currentText() != "Välj koncept..." else "",
                    self.last_seq_spin.value(),
                    billing_plan, p_one, p_month, p_half, p_year,
                    (self.notes_edit.toPlainText().strip() if hasattr(self, 'notes_edit') else ""),
                    self.system_data['id']
                )
            )
            
            self.accept()
            
        except Exception as e:
            CopyableMessageBox.critical(
                self,
                "Databasfel",
                f"Kunde inte spara ändringar: {str(e)}"
            )

class MySystemsWindow(QWidget):
    """Window for viewing and managing existing systems"""
    
    navigate_home = Signal()
    navigate_to_home = Signal()
    navigate_to_orders = Signal()
    order_created = Signal()
    
    def __init__(self, app_manager, db_manager, translation_manager):
        super().__init__()
        self.app_manager = app_manager
        self.db_manager = db_manager
        self.translation_manager = translation_manager
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Setup my systems UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel(self.translation_manager.get_text("my_systems"))
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Search section - styled to match orders window dropdowns
        search_group = QGroupBox("Filter")
        search_group.setMaximumWidth(700)  # Wider to hold extra filters
        search_layout = QHBoxLayout(search_group)
        search_layout.setSpacing(15)
        search_layout.setContentsMargins(15, 15, 15, 15)  # Add margins to center content
        search_layout.setAlignment(Qt.AlignVCenter)  # Center vertically
        
        # Use global styling - no local overrides
        
        search_label = QLabel("Sök:")
        search_label.setProperty("kb_label_type", "caption")
        from .styles import KeyBuddyLineEdit, FieldType
        self.search_edit = KeyBuddyLineEdit(FieldType.STANDARD, "Sök företag, projekt, nyckelkod, profil, ansvarig...")
        # Now uses EXACT same class and styling as all other input fields
        # Search field styling handled by global CSS
        self.search_edit.textChanged.connect(self.filter_systems)

        # Invoice status filter (Alla/Betald/Obetald)
        status_label = QLabel("Faktura:")
        status_label.setProperty("kb_label_type", "caption")
        self.invoice_status_combo = QComboBox()
        self.invoice_status_combo.addItems(["Alla", "Betald", "Obetald"]) 
        self.invoice_status_combo.setMinimumWidth(120)
        # Combo styling handled by global CSS
        self.invoice_status_combo.currentTextChanged.connect(self.filter_systems)

        # Add widgets to horizontal layout - no filter button needed
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(status_label)
        search_layout.addWidget(self.invoice_status_combo)
        search_layout.addStretch()
        
        layout.addWidget(search_group)
        
        # Systems table
        self.systems_table = QTableWidget()
        self.systems_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Disable editing
        self.setup_table()
        layout.addWidget(self.systems_table)
        
        # Info label
        self.info_label = QLabel()
        layout.addWidget(self.info_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        home_btn = KeyBuddyButton(self.translation_manager.get_text("home"), ButtonType.SECONDARY)
        home_btn.clicked.connect(self.navigate_to_home.emit)
        
        create_key_btn = KeyBuddyButton("Tillverka Nyckel", ButtonType.PRIMARY)
        create_key_btn.clicked.connect(self.create_key_order)
        
        view_orders_btn = KeyBuddyButton("Visa Ordrar", ButtonType.PRIMARY)
        view_orders_btn.clicked.connect(self.navigate_to_orders.emit)
        
        
        self.edit_system_btn = KeyBuddyButton("Redigera", ButtonType.SECONDARY)
        self.edit_system_btn.clicked.connect(self.edit_selected_system)
        self.edit_system_btn.setEnabled(False)  # Disabled until system is selected
        
        self.return_key_fob_btn = KeyBuddyButton("Återlämna Nyckelbricka", ButtonType.DANGER)
        self.return_key_fob_btn.clicked.connect(self.return_key_fob)
        self.return_key_fob_btn.setEnabled(False)  # Disabled until system is selected
        
        # Invoice actions button removed/hidden as requested
        self.invoice_btn = QToolButton()
        self.invoice_btn.hide()
        
        button_layout.addWidget(home_btn)
        button_layout.addWidget(self.edit_system_btn)
        button_layout.addWidget(self.return_key_fob_btn)
        button_layout.addStretch()
        button_layout.addWidget(view_orders_btn)
        button_layout.addWidget(create_key_btn)
        # Removed invoice button from toolbar per request
        
        layout.addLayout(button_layout)
    
    def setup_table(self):
        """Setup systems table"""
        headers = [
            "ID", "Företag", "Projekt", "Nyckelkod", "Profil", 
            "Serie-ID", "Löpnr", "Nyckelansvarig", "Faktura", "Nästa förfallodatum", "Skapad"
        ]
        
        self.systems_table.setColumnCount(len(headers))
        self.systems_table.setHorizontalHeaderLabels(headers)
        
        # Set column widths
        header = self.systems_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Company (wider)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Project
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Key Code
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Profile
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Series ID
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Last Sequence (narrow)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Responsible
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Faktura
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # Nästa förfallodatum
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents)  # Skapad
        # Make Löpnr narrow to ~5 digits
        try:
            self.systems_table.setColumnWidth(6, 60)
        except Exception:
            pass
        # Avoid horizontal scroll
        try:
            self.systems_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        except Exception:
            pass
        
        # Enable sorting and selection (single selection only)
        try:
            self.systems_table.setSortingEnabled(True)
        except Exception:
            pass
        
        # Enable selection (single selection only)
        self.systems_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.systems_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Connect table selection change to enable/disable buttons
        self.systems_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Connect selection change to enable edit button
        self.systems_table.itemSelectionChanged.connect(self.update_edit_button_state)

        # Do not use double-click behavior; rely on context menu only
        # Right-click context menu for Faktura column
        try:
            self.systems_table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.systems_table.customContextMenuRequested.connect(self.on_systems_context_menu)
        except Exception:
            pass

    def on_systems_context_menu(self, point):
        try:
            index = self.systems_table.indexAt(point)
            if not index.isValid():
                return
            row = index.row(); col = index.column()
            menu = QMenu(self)
            menu.setObjectName("newDropdownMenu")  # Use new styling
            # Make menu frameless/translucent so rounded corners render on Windows
            try:
                menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                menu.setAttribute(Qt.WA_TranslucentBackground, True)
            except Exception:
                pass
            # Use global menu styling instead of inline styles
            if col == 8:
                # Faktura menu
                act_view = menu.addAction("Visa faktura")
                act_email = menu.addAction("Maila faktura")
                act_create = menu.addAction("Skapa faktura")
                act_print = menu.addAction("Skriv ut faktura")
                act_hist = menu.addAction("Fakturahistorik")
                menu.addSeparator()
                act_paid = menu.addAction("Sätt betald")
                act_unpaid = menu.addAction("Sätt obetald")
                chosen = menu.exec(self.systems_table.viewport().mapToGlobal(point))
                if chosen == act_view:
                    self.view_invoice_stub()
                elif chosen == act_email:
                    self.email_invoice_stub()
                elif chosen == act_create:
                    self.create_invoice_stub()
                elif chosen == act_hist:
                    id_item = self.systems_table.item(row, 0)
                    if id_item:
                        self.show_invoice_history(int(id_item.text()))
                elif chosen == act_paid:
                    self.set_selected_invoice_status(True)
                elif chosen == act_unpaid:
                    self.set_selected_invoice_status(False)
            elif col == 1:
                # Company column menu
                act_edit = menu.addAction("Redigera")
                act_return = menu.addAction("Återlämna Nyckelbricka")
                act_make = menu.addAction("Tillverka nyckel")
                chosen = menu.exec(self.systems_table.viewport().mapToGlobal(point))
                if chosen == act_edit:
                    self.edit_selected_system()
                elif chosen == act_return:
                    self.return_key_fob()
                elif chosen == act_make:
                    self.create_key_order()
        except Exception:
            pass
    
    def refresh_data(self):
        """Refresh systems data from database"""
        try:
            # Get systems with customer data including all fields for smart data selection
            systems = self.db_manager.execute_query("""
                SELECT 
                    ks.id,
                    ks.customer_id,
                    c.company,
                    c.project,
                    ks.key_code,
                    ks.key_profile,
                    ks.series_id,
                    ks.fabrikat,
                    ks.koncept,
                    ks.last_sequence_number,
                    ks.is_paid,
                    ks.billing_plan,
                    ks.paid_at,
                    ks.invoice_count,
                    ks.last_invoice_date,
                    c.key_responsible_1,
                    date(ks.created_at) as created_date,
                    ks.key_code2,
                    ks.system_number,
                    ks.profile2,
                    ks.delning,
                    ks.key_location2,
                    ks.fabrikat2,
                    ks.koncept2,
                    ks.flex1,
                    ks.flex2,
                    ks.flex3,
                    c.key_location,
                    c.customer_number,
                    c.org_number,
                    c.address,
                    c.postal_code,
                    c.postal_address,
                    c.phone,
                    c.mobile_phone,
                    c.email,
                    c.website,
                    c.key_responsible_2,
                    c.key_responsible_3,
                    ks.notes,
                    ks.price_one_time
                FROM key_systems ks
                JOIN customers c ON ks.customer_id = c.id
                ORDER BY ks.created_at DESC
            """)
            
            self.populate_table(systems)
            
        except Exception as e:
            self.show_message('critical', "Databasfel", f"Kunde inte ladda system: {str(e)}")
    
    def show_message(self, message_type, title, message):
        """Show message with copyable option if debug mode is enabled"""
        try:
            # Check if debug mode is enabled via app_manager
            debug_mode = self.app_manager.get_setting('debug_mode', False)
            
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
    
    def get_smart_display_data(self, system_data):
        """Smart logic to choose between Nyckelkort and Standard & System-nycklar data for display"""
        # Check if Nyckelkort data exists
        nyckelkort_has_data = (
            system_data.get('key_code', '').strip() or
            system_data.get('series_id', '').strip() or
            system_data.get('key_profile', '').strip() or
            system_data.get('key_location', '').strip() or
            system_data.get('fabrikat', '').strip() or
            system_data.get('koncept', '').strip()
        )
        
        # Check if Standard & System-nycklar data exists
        standard_has_data = (
            system_data.get('key_code2', '').strip() or
            system_data.get('system_number', '').strip() or
            system_data.get('profile2', '').strip() or
            system_data.get('delning', '').strip() or
            system_data.get('key_location2', '').strip() or
            system_data.get('fabrikat2', '').strip() or
            system_data.get('koncept2', '').strip()
        )
        
        # Smart key_location logic: prioritize nyckelplats, fallback to nyckelplats 2
        smart_key_location = system_data.get('key_location', '').strip()
        if not smart_key_location:
            smart_key_location = system_data.get('key_location2', '').strip()
        
        # Return the appropriate data set for display
        if nyckelkort_has_data:
            return {
                'key_code': system_data.get('key_code', ''),
                'series_id': system_data.get('series_id', ''),
                'key_profile': system_data.get('key_profile', ''),
                'key_location': smart_key_location,  # Use smart key_location
                'fabrikat': system_data.get('fabrikat', ''),
                'koncept': system_data.get('koncept', ''),
                'data_source': 'nyckelkort'
            }
        elif standard_has_data:
            return {
                'key_code': system_data.get('key_code2', ''),  # Map key_code2 -> key_code
                'series_id': system_data.get('system_number', ''),  # Map system_number -> series_id
                'key_profile': system_data.get('profile2', ''),  # Map profile2 -> key_profile
                'key_location': smart_key_location,  # Use smart key_location
                'fabrikat': system_data.get('fabrikat2', ''),  # Map fabrikat2 -> fabrikat
                'koncept': system_data.get('koncept2', ''),  # Map koncept2 -> koncept
                'data_source': 'standard'
            }
        else:
            # No data in either, return empty
            return {
                'key_code': '',
                'series_id': '',
                'key_profile': '',
                'key_location': smart_key_location,  # Use smart key_location
                'fabrikat': '',
                'koncept': '',
                'data_source': 'none'
            }
    
    def populate_table(self, systems):
        """Populate table with systems data"""
        self.systems_table.setRowCount(len(systems))
        
        for row, system in enumerate(systems):
            # Map the query results to the correct indices including new fields
            system_dict = {
                'id': system[0],
                'customer_id': system[1], 
                'company': system[2],
                'project': system[3],
                'key_code': system[4],
                'key_profile': system[5],
                'series_id': system[6],
                'fabrikat': system[7],
                'koncept': system[8],
                'last_sequence_number': system[9],
                'is_paid': (system[10] if isinstance(system[10], (int, bool)) else 0),
                'billing_plan': system[11],
                'paid_at': system[12],
                'invoice_count': system[13] if system[13] is not None else 0,
                'last_invoice_date': system[14],
                'key_responsible_1': system[15],
                'created_date': system[16],
                # Standard & System-nycklar fields
                'key_code2': system[17] or '',
                'system_number': system[18] or '',
                'profile2': system[19] or '',
                'delning': system[20] or '',
                'key_location2': system[21] or '',
                'fabrikat2': system[22] or '',
                'koncept2': system[23] or '',
                'flex1': system[24] or '',
                'flex2': system[25] or '',
                'flex3': system[26] or '',
                'key_location': system[27] or '',  # From customers table
                'customer_number': system[28] or '',
                'org_number': system[29] or '',
                'street_address': system[30] or '',  # address -> street_address for consistency
                'postal_code': system[31] or '',
                'postal_address': system[32] or '',
                'phone': system[33] or '',
                'mobile_phone': system[34] or '',
                'email': system[35] or '',
                'website': system[36] or '',
                'key_responsible_2': system[37] or '',
                'key_responsible_3': system[38] or '',
                'notes': system[39] or '',
                'price_one_time': system[40] or 0.0
            }
            
            # Apply smart data logic to get display values
            smart_data = self.get_smart_display_data(system_dict)
            
            self.systems_table.setItem(row, 0, QTableWidgetItem(str(system_dict['id'])))
            self.systems_table.setItem(row, 1, QTableWidgetItem(system_dict['company'] or ''))
            self.systems_table.setItem(row, 2, QTableWidgetItem(system_dict['project'] or ''))
            # Use smart data for key fields
            self.systems_table.setItem(row, 3, QTableWidgetItem(smart_data.get('key_code', '') or ''))
            self.systems_table.setItem(row, 4, QTableWidgetItem(smart_data.get('key_profile', '') or ''))
            self.systems_table.setItem(row, 5, QTableWidgetItem(smart_data.get('series_id', '') or ''))
            self.systems_table.setItem(row, 6, QTableWidgetItem(str(system_dict['last_sequence_number'] or 0)))
            self.systems_table.setItem(row, 7, QTableWidgetItem(system_dict['key_responsible_1'] or ''))
            # Auto-revert status if period elapsed
            try:
                bp = (system_dict.get('billing_plan') or '').lower()
                if system_dict.get('is_paid') and bp in ['månadskostnad', 'halvårskostnad', 'helårskostnad'] and system_dict.get('paid_at'):
                    from datetime import datetime, timedelta
                    try:
                        paid_dt = datetime.fromisoformat(system_dict['paid_at']) if isinstance(system_dict['paid_at'], str) else system_dict['paid_at']
                    except Exception:
                        paid_dt = None
                    if paid_dt:
                        delta_days = (datetime.now() - paid_dt).days
                        threshold = 30 if 'månad' in bp else (182 if 'halvår' in bp else 365)
                        if delta_days >= threshold:
                            # Revert to Obetald in DB and memory
                            self.db_manager.execute_update(
                                "UPDATE key_systems SET is_paid = 0 WHERE id = ?",
                                (system_dict['id'],)
                            )
                            system_dict['is_paid'] = 0
            except Exception:
                pass
            # Paid status cell
            paid_item = QTableWidgetItem("Betald" if system_dict.get('is_paid') else "Obetald")
            if system_dict.get('is_paid'):
                paid_item.setBackground(QColor(198, 239, 206))
                paid_item.setForeground(QColor(0, 97, 0))
            else:
                paid_item.setBackground(QColor(255, 199, 206))
                paid_item.setForeground(QColor(156, 0, 6))
            self.systems_table.setItem(row, 8, paid_item)
            # Next due date
            next_due_text = ""
            try:
                bp = (system_dict.get('billing_plan') or '').lower()
                paid_at = system_dict.get('paid_at')
                if paid_at and bp in ['månadskostnad', 'halvårskostnad', 'helårskostnad']:
                    from datetime import datetime, timedelta
                    try:
                        paid_dt = datetime.fromisoformat(paid_at) if isinstance(paid_at, str) else paid_at
                    except Exception:
                        paid_dt = None
                    if paid_dt:
                        add_days = 30 if 'månad' in bp else (182 if 'halvår' in bp else 365)
                        due_dt = paid_dt + timedelta(days=add_days)
                        next_due_text = due_dt.strftime('%Y-%m-%d')
            except Exception:
                pass
            self.systems_table.setItem(row, 9, QTableWidgetItem(next_due_text))
            # Add hover tooltip over company cell to hint right-click options
            try:
                company_item = self.systems_table.item(row, 1)
                if company_item:
                    company_item.setToolTip("Högerklicka för flera val")
            except Exception:
                pass
            # Build tooltip for Faktura cell
            try:
                tooltip_lines = []
                plan_val = system_dict.get('billing_plan') or ''
                paid_at_txt = ''
                if system_dict.get('paid_at'):
                    if isinstance(system_dict.get('paid_at'), str):
                        paid_at_txt = system_dict.get('paid_at')[:16].replace('T', ' ')
                    else:
                        from datetime import datetime
                        paid_at_txt = str(system_dict.get('paid_at'))
                tooltip_lines.append(f"Plan: {plan_val}")
                tooltip_lines.append(f"Betald: {paid_at_txt or '-'}")
                tooltip_lines.append(f"Nästa förfallodatum: {next_due_text or '-'}")
                tooltip_lines.append(f"Antal fakturor: {system_dict.get('invoice_count', 0)}")
                paid_item.setToolTip("\n".join(tooltip_lines))
            except Exception:
                pass
            self.systems_table.setItem(row, 10, QTableWidgetItem(system_dict['created_date'] or ''))
            
            # Store full system data in first column
            item = self.systems_table.item(row, 0)
            item.setData(Qt.UserRole, system_dict)

    def on_systems_item_double_clicked(self, item):
        """On double-click: open Faktura-historik when clicking the 'Faktura' column."""
        try:
            if item.column() == 8:  # Faktura column
                row = item.row()
                id_item = self.systems_table.item(row, 0)
                if not id_item:
                    return
                system_id = int(id_item.text())
                self.show_invoice_history(system_id)
        except Exception:
            pass

    def set_selected_invoice_status(self, paid: bool):
        """Set Faktura status (Betald/Obetald) for the currently selected row and update UI."""
        try:
            row = self.systems_table.currentRow()
            if row < 0:
                return
            id_item = self.systems_table.item(row, 0)
            if not id_item:
                return
            system_id = int(id_item.text())
            # Update DB
            if paid:
                from datetime import datetime
                now_iso = datetime.now().isoformat()
                self.db_manager.execute_update(
                    "UPDATE key_systems SET is_paid = 1, paid_at = COALESCE(paid_at, ?), invoice_count = invoice_count + 1, last_invoice_date = ? WHERE id = ?",
                    (now_iso, now_iso, system_id)
                )
            else:
                self.db_manager.execute_update(
                    "UPDATE key_systems SET is_paid = 0 WHERE id = ?",
                    (system_id,)
                )
            # Update UI status cell
            status_item = self.systems_table.item(row, 8)
            if not status_item:
                status_item = QTableWidgetItem()
                self.systems_table.setItem(row, 8, status_item)
            if paid:
                status_item.setText("Betald")
                status_item.setBackground(QColor(198, 239, 206))
                status_item.setForeground(QColor(0, 97, 0))
            else:
                status_item.setText("Obetald")
                status_item.setBackground(QColor(255, 199, 206))
                status_item.setForeground(QColor(156, 0, 6))
            # Update next due date cell (recompute based on billing_plan and paid_at)
            try:
                # Use cached dict stored in first column
                first_item = self.systems_table.item(row, 0)
                data = first_item.data(Qt.UserRole) if first_item else {}
                # Ensure we have billing plan; if missing, fetch from DB
                bp = (data.get('billing_plan') or '').lower()
                if not bp:
                    try:
                        res = self.db_manager.execute_query("SELECT billing_plan FROM key_systems WHERE id = ?", (system_id,))
                        if res and res[0]['billing_plan']:
                            bp = str(res[0]['billing_plan']).lower()
                            data['billing_plan'] = res[0]['billing_plan']
                    except Exception:
                        bp = ''
                # Update cached is_paid and paid_at
                if paid:
                    from datetime import datetime, timedelta
                    now_dt = datetime.now()
                    data['is_paid'] = 1
                    data['paid_at'] = now_iso if 'now_iso' in locals() else now_dt.isoformat()
                    # Increment invoice_count in cache to match DB
                    try:
                        data['invoice_count'] = int(data.get('invoice_count') or 0) + 1
                    except Exception:
                        data['invoice_count'] = 1
                    # Compute next due
                    add_days = 30 if 'månad' in bp else (182 if 'halvår' in bp else 365)
                    next_due_text = ''
                    if add_days:
                        due_dt = now_dt + timedelta(days=add_days)
                        next_due_text = due_dt.strftime('%Y-%m-%d')
                    self.systems_table.setItem(row, 9, QTableWidgetItem(next_due_text))
                    # Update tooltip
                    tooltip_lines = [
                        f"Plan: {data.get('billing_plan') or ''}",
                        f"Betald: {now_dt.strftime('%Y-%m-%d %H:%M')}",
                        f"Nästa förfallodatum: {next_due_text or '-'}",
                        f"Antal fakturor: {data.get('invoice_count', 0)}",
                    ]
                    status_item.setToolTip("\n".join(tooltip_lines))
                else:
                    data['is_paid'] = 0
                    self.systems_table.setItem(row, 9, QTableWidgetItem(''))
                    status_item.setToolTip("Plan: \nBetald: -\nNästa förfallodatum: -\nAntal fakturor: -")
                # Save back cached data
                if first_item:
                    first_item.setData(Qt.UserRole, data)
            except Exception:
                pass
            
            # If fakturahistorik-dialogen är öppen för samma system, uppdatera den live
            try:
                if hasattr(self, '_invoice_history') and self._invoice_history:
                    info = self._invoice_history
                    if info.get('system_id') == system_id and info.get('dialog') and info.get('table') and info.get('count'):
                        rows = self.db_manager.execute_query(
                            "SELECT pdf_encrypted, created_at FROM invoices WHERE system_id = ? ORDER BY created_at DESC",
                            (system_id,)
                        )
                        tw = info['table']
                        tw.setRowCount(len(rows))
                        for r, rec in enumerate(rows):
                            created = rec[1] or ""
                            created_item = QTableWidgetItem(str(created))
                            created_item.setData(Qt.UserRole, rec[0])
                            tw.setItem(r, 0, created_item)
                        info['count'].setText(f"Antal fakturor: {len(rows)}")
            except Exception:
                pass
        except Exception:
            pass

    def show_invoice_history(self, system_id: int):
        """Fakturahistorik med högerklicksmeny (visa, maila, sätt betald/obetald)."""
        try:
            rows = self.db_manager.execute_query(
                "SELECT pdf_encrypted, created_at FROM invoices WHERE system_id = ? ORDER BY created_at DESC",
                (system_id,)
            )
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
            dlg = QDialog(self)
            dlg.setWindowTitle("Fakturahistorik")
            dlg.resize(520, 320)
            v = QVBoxLayout(dlg)
            # Antal
            count_label = QLabel(f"Antal fakturor: {len(rows)}")
            v.addWidget(count_label)
            # Info om högerklick (beautified)
            info_label = QLabel("Högerklicka för fler val.")
            info_label.setProperty("kb_label_type", "caption")
            # Info label styling handled by global CSS
            v.addWidget(info_label)
            # Tabell
            tw = QTableWidget()
            tw.setColumnCount(1)
            tw.setHorizontalHeaderLabels(["Skapad"])
            tw.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            # No in-table editing or accidental activation
            try:
                from PySide6.QtWidgets import QAbstractItemView
                tw.setEditTriggers(QAbstractItemView.NoEditTriggers)
                tw.setSelectionBehavior(QAbstractItemView.SelectRows)
                tw.setSelectionMode(QAbstractItemView.SingleSelection)
            except Exception:
                pass
            tw.setRowCount(len(rows))
            for r, rec in enumerate(rows):
                created = rec[1] or ""
                item = QTableWidgetItem(str(created))
                item.setData(Qt.UserRole, rec[0])
                tw.setItem(r, 0, item)
            v.addWidget(tw)

            # Högerklicksmeny
            def on_history_context_menu(point):
                try:
                    index = tw.indexAt(point)
                    if not index.isValid():
                        return
                    row_idx = index.row()
                    menu = QMenu(tw)
                    menu.setObjectName("newDropdownMenu")  # Use new styling
                    # Frameless/translucent for rounded corners
                    try:
                        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                        menu.setAttribute(Qt.WA_TranslucentBackground, True)
                    except Exception:
                        pass
                    # Use global menu styling instead of inline styles
                    act_view = menu.addAction("Visa faktura")
                    act_email = menu.addAction("Maila faktura")
                    act_create = menu.addAction("Skapa faktura")
                    act_delete = menu.addAction("Ta bort faktura")
                    menu.addSeparator()
                    act_paid = menu.addAction("Sätt betald")
                    act_unpaid = menu.addAction("Sätt obetald")
                    chosen = menu.exec(tw.mapToGlobal(point))
                    if chosen == act_view:
                        enc_b64 = tw.item(row_idx, 0).data(Qt.UserRole)
                        if not enc_b64:
                            return
                        import base64, tempfile
                        b64 = self.db_manager.decrypt_data(enc_b64)
                        pdf_bytes = base64.b64decode(b64.encode('utf-8'))
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                        tmp.write(pdf_bytes); tmp.flush(); tmp.close()
                        OrderPDFGenerator().open_pdf_in_browser(tmp.name)
                    elif chosen == act_email:
                        self.email_invoice_stub()
                    elif chosen == act_create:
                        self.create_invoice_stub()
                    elif chosen == act_delete:
                        try:
                            from .copyable_message_box import CopyableMessageBox
                            enc_b64 = tw.item(row_idx, 0).data(Qt.UserRole)
                            if not enc_b64:
                                return
                            reply = CopyableMessageBox.question(
                                self,
                                "Ta bort faktura",
                                "Är du säker på att du vill ta bort denna faktura?",
                                CopyableMessageBox.Yes | CopyableMessageBox.No
                            )
                            if reply == CopyableMessageBox.Yes:
                                # Delete by encrypted content value
                                self.db_manager.execute_update(
                                    "DELETE FROM invoices WHERE pdf_encrypted = ?",
                                    (enc_b64,)
                                )
                                # Refresh list
                                rows2 = self.db_manager.execute_query(
                                    "SELECT pdf_encrypted, created_at FROM invoices WHERE system_id = ? ORDER BY created_at DESC",
                                    (system_id,)
                                )
                                tw.setRowCount(len(rows2))
                                for r, rec in enumerate(rows2):
                                    created = rec[1] or ""
                                    item = QTableWidgetItem(str(created))
                                    item.setData(Qt.UserRole, rec[0])
                                    item.setToolTip("Högerklicka för fler val")
                                    tw.setItem(r, 0, item)
                                count_label.setText(f"Antal fakturor: {len(rows2)}")
                        except Exception:
                            pass
                    elif chosen == act_paid:
                        self.set_selected_invoice_status(True)
                    elif chosen == act_unpaid:
                        self.set_selected_invoice_status(False)
                except Exception:
                    pass
            tw.setContextMenuPolicy(Qt.CustomContextMenu)
            tw.customContextMenuRequested.connect(on_history_context_menu)
            # Tooltips on rows
            try:
                for r in range(tw.rowCount()):
                    it = tw.item(r, 0)
                    if it:
                        it.setToolTip("Högerklicka för fler val")
            except Exception:
                pass

            # Spara referenser för live‑uppdatering
            self._invoice_history = {
                'dialog': dlg,
                'table': tw,
                'count': count_label,
                'system_id': system_id,
            }
            # Städa när dialogen stängs
            def on_close():
                try:
                    self._invoice_history = None
                except Exception:
                    pass
            dlg.finished.connect(lambda _: on_close())
            dlg.exec()
        except Exception as e:
            CopyableMessageBox.warning(self, "Fakturahistorik", f"Kunde inte visa historik: {str(e)}")
    
    def filter_systems(self):
        """Filter systems based on search text"""
        search_text = self.search_edit.text().lower()
        status_filter = None
        try:
            status_text = self.invoice_status_combo.currentText() if hasattr(self, 'invoice_status_combo') else "Alla"
            if status_text == "Betald":
                status_filter = 'betald'
            elif status_text == "Obetald":
                status_filter = 'obetald'
        except Exception:
            status_filter = None
        
        for row in range(self.systems_table.rowCount()):
            show_row = False
            
            if not search_text:
                show_row = True
            else:
                # Search only in specific columns: Företag (1), Projekt (2), Nyckelkod (3), Profil (4), Nyckelansvarig (7)
                # Exclude: ID (0), Serie-ID (5), Senaste löpnr (6), Skapad (8)
                searchable_columns = [1, 2, 3, 4, 7]
                for col in searchable_columns:
                    item = self.systems_table.item(row, col)
                    if item and search_text in item.text().lower():
                        show_row = True
                        break
            # Apply Faktura status filter
            if show_row and status_filter:
                status_item = self.systems_table.item(row, 8)  # Faktura column
                if not status_item or status_item.text().lower() != status_filter:
                    show_row = False
            self.systems_table.setRowHidden(row, not show_row)

    def bulk_set_invoice_status(self, paid: bool):
        """Set Faktura status for all selected rows."""
        try:
            selected_indexes = self.systems_table.selectedIndexes()
            rows = sorted({idx.row() for idx in selected_indexes})
            if not rows:
                return
            for row in rows:
                id_item = self.systems_table.item(row, 0)
                if not id_item:
                    continue
                system_id = int(id_item.text())
                # Update DB with side-effects if setting paid
                if paid:
                    from datetime import datetime
                    now_iso = datetime.now().isoformat()
                    self.db_manager.execute_update(
                        "UPDATE key_systems SET is_paid = 1, paid_at = COALESCE(paid_at, ?), invoice_count = invoice_count + 1, last_invoice_date = ? WHERE id = ?",
                        (now_iso, now_iso, system_id)
                    )
                else:
                    self.db_manager.execute_update(
                        "UPDATE key_systems SET is_paid = 0 WHERE id = ?",
                        (system_id,)
                    )
                # Update UI cell
                status_item = self.systems_table.item(row, 8)
                if not status_item:
                    status_item = QTableWidgetItem()
                    self.systems_table.setItem(row, 8, status_item)
                if paid:
                    status_item.setText("Betald")
                    status_item.setBackground(QColor(198, 239, 206))
                    status_item.setForeground(QColor(0, 97, 0))
                else:
                    status_item.setText("Obetald")
                    status_item.setBackground(QColor(255, 199, 206))
                    status_item.setForeground(QColor(156, 0, 6))
        except Exception:
            pass
    
    def create_key_order(self):
        """Create new key manufacturing order"""
        current_row = self.systems_table.currentRow()
        if current_row < 0:
            self.show_message('warning', "Ingen rad vald", "Välj ett system från tabellen för att tillverka nycklar.")
            return
        
        # Get system data
        item = self.systems_table.item(current_row, 0)
        system_data = item.data(Qt.UserRole)
        
        # Show create key dialog
        dialog = CreateKeyDialog(self, system_data, self.translation_manager)
        
        if dialog.exec() == QDialog.Accepted:
            order_data = dialog.get_order_data()
            self.save_key_order(system_data, order_data)
    
    def save_key_order(self, system_data, order_data):
        """Save key manufacturing order"""
        try:
            current_user = self.app_manager.get_current_user()
            if not current_user:
                self.show_message('critical', "Fel", "Ingen användare inloggad")
                return
            
            # Calculate sequence end
            sequence_start = order_data['sequence_start']
            quantity = order_data['quantity']
            sequence_end = sequence_start + quantity - 1
            
            # Insert order
            order_id = self.db_manager.execute_update(
                """INSERT INTO orders (
                    customer_id, key_system_id, key_code, key_profile,
                    quantity, sequence_start, sequence_end, key_responsible, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    system_data['customer_id'],
                    system_data['id'],
                    system_data['key_code'],
                    system_data['key_profile'],
                    quantity,
                    sequence_start,
                    sequence_end,
                    order_data['key_responsible'],
                    current_user['user_id']
                )
            )
            
            # Update last sequence number in key system
            self.db_manager.execute_update(
                "UPDATE key_systems SET last_sequence_number = ? WHERE id = ?",
                (sequence_end, system_data['id'])
            )
            
            # Generate Order PDF and Receipt sequentially
            self.generate_pdfs_sequentially(system_data, order_data, order_id)
            
            CopyableMessageBox.information(
                self,
                "Order skapad",
                f"Nyckelorder #{order_id} har skapats framgångsrikt.\n"
                f"Antal: {quantity}\n"
                f"Löpnummer: {sequence_start}-{sequence_end}"
            )
            
            # Emit signal to notify other windows about the new order
            self.order_created.emit()
            
            # Refresh data to show updated sequence number
            self.refresh_data()
            
        except Exception as e:
            CopyableMessageBox.critical(
                self,
                "Databasfel",
                f"Kunde inte skapa order: {str(e)}"
            )
    
    def generate_pdfs_sequentially(self, system_data, order_data, order_id):
        """Generate PDFs sequentially: first TILLVERKNINGSORDER, then Nyckelkvittens"""
        try:
            # First generate TILLVERKNINGSORDER NYCKEL
            order_pdf_path = self.generate_order_pdf_only(system_data, order_data, order_id)
            
            # Open TILLVERKNINGSORDER NYCKEL in browser
            if order_pdf_path:
                from ..core.pdf_generator import OrderPDFGenerator
                pdf_generator = OrderPDFGenerator()
                pdf_generator.open_pdf_in_browser(order_pdf_path)
                
                # Show dialog asking if user wants to continue to Nyckelkvittens
                if order_data.get('create_receipt', True):
                    reply = CopyableMessageBox.question(
                        self,
                        "Nästa steg",
                        "TILLVERKNINGSORDER NYCKEL har öppnats.\n\n"
                        "Vill du nu öppna Nyckelkvittens?",
                        CopyableMessageBox.Yes | CopyableMessageBox.No
                    )
                    
                    if reply == CopyableMessageBox.Yes:
                        try:
                            self.generate_and_store_receipt(system_data, order_data, order_id)
                        except Exception as e:
                            print(f"Receipt generation error: {e}")
                            CopyableMessageBox.warning(
                                self,
                                "Nyckelkvittens fel",
                                f"Kunde inte generera Nyckelkvittens: {str(e)}"
                            )
        except Exception as e:
            CopyableMessageBox.warning(
                self,
                "PDF-export fel", 
                f"Kunde inte generera PDF-export: {str(e)}\n\nOrdern har ändå skapats framgångsrikt."
            )

    def generate_order_pdf_only(self, system_data, order_data, order_id):
        """Generate PDF export for the order (without opening it)"""
        try:
            # Get complete system data including all fields for smart data selection
            system_query = """SELECT key_code, key_profile, series_id, fabrikat, koncept, last_sequence_number, notes,
                                    key_code2, system_number, profile2, delning, key_location2, fabrikat2, koncept2,
                                    flex1, flex2, flex3
                             FROM key_systems WHERE id = ?"""
            system_result = self.db_manager.execute_query(system_query, (system_data['id'],))
            
            if system_result:
                # Update system_data with complete information from database
                row = system_result[0]
                system_data.update({
                    'key_code': row[0] or '',
                    'key_profile': row[1] or '',
                    'series_id': row[2] or '',
                    'fabrikat': row[3] or '',
                    'koncept': row[4] or '',
                    'last_sequence_number': row[5] or 0,
                    'notes': row[6] or '',
                    # Standard & System-nycklar fields
                    'key_code2': row[7] or '',
                    'system_number': row[8] or '',
                    'profile2': row[9] or '',
                    'delning': row[10] or '',
                    'key_location2': row[11] or '',
                    'fabrikat2': row[12] or '',
                    'koncept2': row[13] or '',
                    'flex1': row[14] or '',
                    'flex2': row[15] or '',
                    'flex3': row[16] or '',
                })
            
            # Get customer data for the PDF
            cust_row = self.db_manager.execute_query(
                "SELECT company, project, key_responsible_1, key_location FROM customers WHERE id = ?",
                (system_data.get('customer_id'),)
            )
            if cust_row:
                customer_data = {
                    'company': cust_row[0][0] or '',
                    'project': cust_row[0][1] or '',
                    'key_responsible_1': cust_row[0][2] or '',
                    'key_location': cust_row[0][3] or ''
                }
            else:
                customer_data = {
                    'company': system_data.get('company', ''),
                    'project': system_data.get('project', ''),
                    'key_responsible_1': system_data.get('key_responsible_1', ''),
                    'key_location': ''
                }
            
            # Get logo path using GLOBAL logo manager
            from ..core.logo_manager import LogoManager
            logo_path = LogoManager.get_logo_path()
            if not os.path.exists(logo_path):
                logo_path = None
            
            # Get current user information
            current_user = self.app_manager.get_current_user()
            
            # Generate PDF (without opening it)
            from ..core.pdf_generator import OrderPDFGenerator
            pdf_generator = OrderPDFGenerator()
            pdf_path = pdf_generator.generate_order_pdf(
                system_data, 
                order_data, 
                customer_data, 
                current_user,
                logo_path
            )
            
            return pdf_path  # Return path instead of opening
            
        except Exception as e:
            print(f"Order PDF generation error: {e}")
            return None

    def generate_and_store_receipt(self, system_data, order_data, order_id):
        """Generate Nyckelkvittens PDF, encrypt and store in DB, and open it"""
        try:
            # Enrich system data with all fields for smart data selection
            system_query = (
                "SELECT key_code, key_profile, series_id, fabrikat, koncept, last_sequence_number, notes, "
                "key_code2, system_number, profile2, delning, key_location2, fabrikat2, koncept2, "
                "flex1, flex2, flex3 "
                "FROM key_systems WHERE id = ?"
            )
            system_result = self.db_manager.execute_query(system_query, (system_data['id'],))
            if system_result:
                row = system_result[0]
                system_data.update({
                    'key_code': row[0] or '',
                    'key_profile': row[1] or '',
                    'series_id': row[2] or '',
                    'fabrikat': row[3] or '',
                    'koncept': row[4] or '',
                    'last_sequence_number': row[5] or 0,
                    'notes': row[6] or '',
                    # Standard & System-nycklar fields
                    'key_code2': row[7] or '',
                    'system_number': row[8] or '',
                    'profile2': row[9] or '',
                    'delning': row[10] or '',
                    'key_location2': row[11] or '',
                    'fabrikat2': row[12] or '',
                    'koncept2': row[13] or '',
                    'flex1': row[14] or '',
                    'flex2': row[15] or '',
                    'flex3': row[16] or '',
                })

            # Customer data for recipient info
            customer_query = (
                "SELECT company, project, mobile_phone, address, postal_code, postal_address, "
                "key_responsible_1, org_number FROM customers WHERE id = ?"
            )
            customer_result = self.db_manager.execute_query(customer_query, (system_data['customer_id'],))
            customer_data = {
                'company': '', 'project': '', 'mobile_phone': '', 'address': '',
                'postal_code': '', 'postal_address': '', 'key_responsible_1': '', 'org_number': ''
            }
            if customer_result:
                cr = customer_result[0]
                customer_data.update({
                    'company': cr[0] or '',
                    'project': cr[1] or '',
                    'mobile_phone': cr[2] or '',
                    'address': cr[3] or '',
                    'postal_code': cr[4] or '',
                    'postal_address': cr[5] or '',
                    'key_responsible_1': cr[6] or '',
                    'org_number': cr[7] or ''
                })

            # Current user and logo using GLOBAL standard
            current_user = self.app_manager.get_current_user()
            import base64, tempfile
            from ..core.logo_manager import LogoManager
            logo_path = LogoManager.get_logo_path()
            if not os.path.exists(logo_path):
                logo_path = None

            # Generate receipt PDF
            from ..core.pdf_generator import OrderPDFGenerator
            gen = OrderPDFGenerator()
            receipt_pdf_path = gen.generate_key_receipt_pdf(system_data, order_data, customer_data, current_user, logo_path)

            # Read and encrypt
            with open(receipt_pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            encrypted = self.db_manager.encrypt_data(b64)

            # Insert or update into key_receipts
            try:
                self.db_manager.execute_update(
                    "INSERT INTO key_receipts (order_id, pdf_encrypted) VALUES (?, ?)",
                    (order_id, encrypted)
                )
            except Exception:
                self.db_manager.execute_update(
                    "UPDATE key_receipts SET pdf_encrypted = ? WHERE order_id = ?",
                    (encrypted, order_id)
                )

            # Open the generated PDF in browser
            gen.open_pdf_in_browser(receipt_pdf_path)
        except Exception as e:
            print(f"Receipt generation/storage error: {e}")

    def clear_data(self):
        """Clear sensitive data"""
        self.systems_table.setRowCount(0)
        self.search_edit.clear()

    def _get_selected_system(self):
        row = self.systems_table.currentRow()
        if row < 0:
            return None
        item = self.systems_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def create_invoice_stub(self):
        try:
            system = self._get_selected_system()
            if not system:
                return
            # Load customer for system
            customer_row = self.db_manager.execute_query(
                "SELECT company, project FROM customers WHERE id = ?",
                (system['customer_id'],)
            )
            customer_data = {'company': '', 'project': ''}
            if customer_row:
                customer_data['company'] = customer_row[0][0] or ''
                customer_data['project'] = customer_row[0][1] or ''
            current_user = self.app_manager.get_current_user()
            logo_path = None
            gen = OrderPDFGenerator()
            pdf_path = gen.generate_invoice_stub_pdf(system, customer_data, current_user, logo_path)
            # Encrypt and store
            import base64
            with open(pdf_path, 'rb') as f:
                data = f.read()
            b64 = base64.b64encode(data).decode('utf-8')
            enc = self.db_manager.encrypt_data(b64)
            self.db_manager.execute_update(
                "INSERT INTO invoices (system_id, pdf_encrypted) VALUES (?, ?)",
                (system['id'], enc)
            )
            gen.open_pdf_in_browser(pdf_path)
            CopyableMessageBox.information(self, "Faktura", "Faktura skapad och sparad.")
        except Exception as e:
            CopyableMessageBox.warning(self, "Faktura", f"Kunde inte skapa: {str(e)}")

    def _load_invoice_encrypted(self, system_id):
        rows = self.db_manager.execute_query(
            "SELECT pdf_encrypted FROM invoices WHERE system_id = ? ORDER BY created_at DESC LIMIT 1",
            (system_id,)
        )
        return rows[0][0] if rows else None

    def view_invoice_stub(self):
        try:
            system = self._get_selected_system()
            if not system:
                return
            enc = self._load_invoice_encrypted(system['id'])
            if not enc:
                CopyableMessageBox.information(self, "Faktura", "Ingen sparad faktura hittades. Skapa först.")
                return
            import base64, tempfile
            b64 = self.db_manager.decrypt_data(enc)
            pdf_bytes = base64.b64decode(b64.encode('utf-8'))
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            tmp.write(pdf_bytes)
            tmp.flush(); tmp.close()
            OrderPDFGenerator().open_pdf_in_browser(tmp.name)
        except Exception as e:
            CopyableMessageBox.warning(self, "Faktura", f"Kunde inte visa: {str(e)}")

    def email_invoice_stub(self):
        try:
            system = self._get_selected_system()
            if not system:
                return
            enc = self._load_invoice_encrypted(system['id'])
            if not enc:
                CopyableMessageBox.information(self, "Faktura", "Ingen sparad faktura hittades. Skapa först.")
                return
            # Decode to bytes
            import base64
            b64 = self.db_manager.decrypt_data(enc)
            pdf_bytes = base64.b64decode(b64.encode('utf-8'))
            # Prepare email
            auth = AuthManager(self.db_manager)
            smtp = auth.get_smtp_config()
            
            # Determine recipient from system's customer email
            recipient = None
            try:
                cust_row = self.db_manager.execute_query(
                    "SELECT email FROM customers WHERE id = ?",
                    (system.get('customer_id'),)
                )
                if cust_row and cust_row[0] and cust_row[0][0]:
                    recipient = cust_row[0][0]
            except Exception:
                recipient = None
            
            # Fallback to current user's email only if customer email missing
            if not recipient:
                current_user = self.app_manager.get_current_user() or {}
                recipient = current_user.get('email', '')
            if not recipient:
                CopyableMessageBox.warning(self, "E‑post", "Ingen e‑postadress hittades för systemet eller användaren.")
                return
            if not smtp.get('enabled', False):
                CopyableMessageBox.warning(self, "E‑post", "SMTP är inaktiverat i inställningarna.")
                return
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders as _enc
            msg = MIMEMultipart()
            msg['Subject'] = "KeyBuddy – Faktura"
            msg['From'] = smtp['email']
            msg['To'] = recipient
            html = f"""
                <html><body style='font-family:Segoe UI,Arial;'>
                <h3>Faktura</h3>
                <p>Bifogat hittar du fakturan för systemet {system.get('key_code','')}.</p>
                <p>Genererad av KeyBuddy.</p>
                </body></html>
            """
            msg.attach(MIMEText(html, 'html'))
            # Attach
            part = MIMEBase('application', 'pdf')
            part.set_payload(pdf_bytes)
            _enc.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename='faktura.pdf')
            msg.attach(part)
            with smtplib.SMTP(smtp['server'], smtp['port']) as server:
                if smtp.get('use_tls', True):
                    server.starttls()
                server.login(smtp['email'], smtp['password'])
                server.sendmail(smtp['email'], [recipient], msg.as_string())
            CopyableMessageBox.information(self, "E‑post", f"Fakturan skickades till: {recipient}")
        except Exception as e:
            CopyableMessageBox.warning(self, "E‑post", f"Kunde inte skicka: {str(e)}")

    def on_selection_changed(self):
        """Handle table selection changes"""
        selected_items = self.systems_table.selectedItems()
        
        # Enable/disable buttons based on selection
        # Add any buttons that should be enabled/disabled here
        has_sel = self.systems_table.currentRow() >= 0
        if hasattr(self, 'invoice_btn') and self.invoice_btn.isVisible():
            self.invoice_btn.setEnabled(has_sel)
        if hasattr(self, 'invoice_history_btn'):
            self.invoice_history_btn.setEnabled(has_sel)
    
    def update_edit_button_state(self):
        """Update edit button state based on selection"""
        current_row = self.systems_table.currentRow()
        self.edit_system_btn.setEnabled(current_row >= 0)
        self.return_key_fob_btn.setEnabled(current_row >= 0)
    
    def edit_selected_system(self):
        """Edit selected system data"""
        current_row = self.systems_table.currentRow()
        if current_row < 0:
            CopyableMessageBox.warning(
                self,
                "Ingen rad vald",
                "Välj ett system från tabellen för att redigera."
            )
            return
        
        # Get system data
        item = self.systems_table.item(current_row, 0)
        system_data = item.data(Qt.UserRole)
        
        # Create edit dialog
        dialog = ModernEditSystemDialog(system_data, self.db_manager, self.translation_manager, self)
        dialog.system_updated.connect(self.refresh_data)
        if dialog.exec() == QDialog.Accepted:
            # Refresh table to show updated data
            self.refresh_data()
            CopyableMessageBox.information(
                self,
                "System uppdaterat",
                "Systemdata har uppdaterats framgångsrikt."
            )
    
    def return_key_fob(self):
        """Handle key fob return and data deletion"""
        current_row = self.systems_table.currentRow()
        if current_row < 0:
            CopyableMessageBox.warning(
                self,
                "Ingen rad vald",
                "Välj ett system från tabellen för att återlämna nyckelbricka."
            )
            return
        
        # Get system data
        item = self.systems_table.item(current_row, 0)
        system_data = item.data(Qt.UserRole)
        
        # Create confirmation dialog
        dialog = KeyFobReturnDialog(system_data, self.db_manager, self)
        if dialog.exec() == QDialog.Accepted:
            # Refresh table to show updated data
            self.refresh_data()
            CopyableMessageBox.information(
                self,
                "Nyckelbricka återlämnad",
                "Systemdata har uppdaterats framgångsrikt."
            )
    
    def update_ui_text(self):
        """Update UI text for current language"""
        pass
