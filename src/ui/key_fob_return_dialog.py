"""
Key Fob Return Dialog for handling data deletion and GDPR compliance
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QMessageBox, QTextEdit, QCheckBox,
                              QGroupBox, QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime
from ..core.gdpr_pdf_generator import GDPRDeletionPDFGenerator
from .copyable_message_box import CopyableMessageBox

class KeyFobReturnDialog(QDialog):
    """Dialog for confirming key fob return and data deletion"""
    
    def __init__(self, system_data, db_manager, parent=None):
        super().__init__(parent)
        self.system_data = system_data
        self.db_manager = db_manager
        self.setWindowTitle("Återlämna Nyckelbricka")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Warning header
        warning_label = QLabel("⚠️ VARNING: PERMANENT DATARADERING")
        warning_label.setProperty("class", "warning-header")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_font = QFont()
        warning_font.setBold(True)
        warning_font.setPointSize(14)
        warning_label.setFont(warning_font)
        warning_label.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin: 5px 0;
            }
        """)
        layout.addWidget(warning_label)
        
        # System information
        info_group = QGroupBox("Systeminfo som kommer att raderas")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("Företag:", QLabel(self.system_data.get('company', 'N/A')))
        info_layout.addRow("Projekt:", QLabel(self.system_data.get('project', 'N/A')))
        info_layout.addRow("Nyckelkod:", QLabel(self.system_data.get('key_code', 'N/A')))
        info_layout.addRow("Kundnummer:", QLabel(self.system_data.get('customer_number', 'N/A')))
        info_layout.addRow("Nyckelansvarig:", QLabel(self.system_data.get('key_responsible_1', 'N/A')))
        
        layout.addWidget(info_group)
        
        # Confirmation text
        confirmation_text = QTextEdit()
        confirmation_text.setReadOnly(True)
        confirmation_text.setMaximumHeight(150)
        confirmation_text.setHtml("""
        <p><strong>Genom att fortsätta kommer följande att ske:</strong></p>
        <ul>
            <li>All data för detta system raderas <strong>permanent</strong> från databasen</li>
            <li>Alla tillhörande beställningar och nycklar raderas</li>
            <li>Denna åtgärd kan <strong>INTE</strong> ångras</li>
            <li>En bekräftelse på dataradering kan genereras enligt GDPR</li>
        </ul>
        <p><em>Detta görs i enlighet med GDPR och vår integritetspolicy.</em></p>
        """)
        layout.addWidget(confirmation_text)
        
        # Confirmation checkbox
        self.confirm_checkbox = QCheckBox("Jag bekräftar att jag vill radera all data för detta system permanent")
        self.confirm_checkbox.setStyleSheet("font-weight: bold; color: #e74c3c;")
        layout.addWidget(self.confirm_checkbox)
        
        # GDPR PDF option
        self.gdpr_pdf_checkbox = QCheckBox("Generera GDPR-bekräftelse (PDF) efter radering")
        self.gdpr_pdf_checkbox.setChecked(True)
        layout.addWidget(self.gdpr_pdf_checkbox)
        
        # Buttons
        button_box = QDialogButtonBox()
        
        self.delete_btn = QPushButton("Radera Data Permanent")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.confirm_deletion)
        
        cancel_btn = QPushButton("Avbryt")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        
        button_box.addButton(cancel_btn, QDialogButtonBox.RejectRole)
        button_box.addButton(self.delete_btn, QDialogButtonBox.AcceptRole)
        
        # Enable delete button only when checkbox is checked
        self.confirm_checkbox.toggled.connect(self.delete_btn.setEnabled)
        
        layout.addWidget(button_box)
    
    def confirm_deletion(self):
        """Confirm and execute data deletion"""
        if not self.confirm_checkbox.isChecked():
            CopyableMessageBox.warning(
                self,
                "Bekräftelse krävs",
                "Du måste bekräfta att du vill radera data permanent."
            )
            return
        
        # Final confirmation
        reply = CopyableMessageBox.question(
            self,
            "Sista varning",
            f"Är du helt säker på att du vill radera ALL data för:\n\n"
            f"Företag: {self.system_data.get('company', 'N/A')}\n"
            f"Projekt: {self.system_data.get('project', 'N/A')}\n"
            f"Nyckelkod: {self.system_data.get('key_code', 'N/A')}\n\n"
            f"Denna åtgärd kan INTE ångras!",
            CopyableMessageBox.Yes | CopyableMessageBox.No
        )
        
        if reply == CopyableMessageBox.Yes:
            self.delete_system_data()
    
    def delete_system_data(self):
        """Delete all system data from database"""
        try:
            customer_id = self.system_data.get('customer_id')
            key_system_id = self.system_data.get('id')  # The key system ID is stored as 'id'
            
            if not customer_id or not key_system_id:
                CopyableMessageBox.critical(
                    self,
                    "Fel",
                    "Kunde inte hitta system-ID för radering."
                )
                return
            
            # Delete in correct order (foreign key constraints)
            # 1. Delete orders first
            self.db_manager.execute_update(
                "DELETE FROM orders WHERE key_system_id = ?",
                (key_system_id,)
            )
            
            # 2. Delete key system
            self.db_manager.execute_update(
                "DELETE FROM key_systems WHERE id = ?",
                (key_system_id,)
            )
            
            # 3. Check if customer has other systems, if not delete customer
            remaining_systems = self.db_manager.execute_query(
                "SELECT COUNT(*) FROM key_systems WHERE customer_id = ?",
                (customer_id,)
            )
            
            if remaining_systems and remaining_systems[0][0] == 0:
                self.db_manager.execute_update(
                    "DELETE FROM customers WHERE id = ?",
                    (customer_id,)
                )
            
            # Generate GDPR PDF if requested
            if self.gdpr_pdf_checkbox.isChecked():
                self.generate_gdpr_pdf()
            
            # Show success message
            CopyableMessageBox.information(
                self,
                "Data raderad",
                f"All data för systemet har raderats permanent från databasen.\n\n"
                f"Raderat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"System: {self.system_data.get('company', 'N/A')} - {self.system_data.get('project', 'N/A')}"
            )
            
            self.accept()
            
        except Exception as e:
            CopyableMessageBox.critical(
                self,
                "Fel vid radering",
                f"Ett fel uppstod vid radering av data:\n{str(e)}"
            )
    
    def generate_gdpr_pdf(self):
        """Generate GDPR deletion confirmation PDF"""
        try:
            pdf_generator = GDPRDeletionPDFGenerator()
            pdf_path = pdf_generator.generate_deletion_confirmation_pdf(
                self.system_data,
                datetime.now()
            )
            
            if pdf_path:
                # Open PDF in browser for viewing/printing/saving
                pdf_generator.open_pdf_in_browser(pdf_path)
                
        except Exception as e:
            CopyableMessageBox.warning(
                self,
                "PDF-generering misslyckades",
                f"Kunde inte generera GDPR-bekräftelse:\n{str(e)}"
            )
