from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QTextEdit, QPushButton, QScrollArea, QWidget,
                                QFileDialog)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap, QFont, QPainter, QTextDocument
from PySide6.QtPrintSupport import QPrinter
import os
from datetime import datetime
from .copyable_message_box import CopyableMessageBox
from ..core.logo_manager import LogoManager

class GDPRWindow(QDialog):
    def __init__(self, app_manager, parent=None):
        super().__init__(parent)
        self.app_manager = app_manager
        self.setWindowTitle("GDPR - Integritetspolicy")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the GDPR window UI"""
        layout = QVBoxLayout(self)
        
        # Header med bara titel (logotyp visas i HTML-innehållet)
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("Integritetspolicy – KeyBuddy")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # GDPR content
        content_text = self.get_gdpr_content()
        content_label = QLabel(content_text)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setAlignment(Qt.AlignTop)
        
        scroll_layout.addWidget(content_label)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        export_pdf_btn = QPushButton("Exportera som PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        
        close_btn = QPushButton("Stäng")
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(export_pdf_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def get_gdpr_content(self):
        """Get GDPR content with dynamic company information and logo"""
        # Get current user info
        current_user = self.app_manager.get_current_user()
        company_name = "Företagsnamn ej tillgängligt"
        org_number = "Org-nr ej tillgängligt"
        email = "E-post ej tillgänglig"
        
        if current_user:
            company_name = current_user.get('company_name', company_name)
            org_number = current_user.get('org_number', org_number)
            email = current_user.get('email', email)
        
        # Lägg till logo i HTML med absolut sökväg
        logo_path = LogoManager.get_logo_path()
        logo_html = ""
        if logo_path and os.path.exists(logo_path):
            # Konvertera till absolut sökväg för HTML
            abs_logo_path = os.path.abspath(logo_path).replace("\\", "/")
            logo_width, logo_height = LogoManager.get_logo_size_px()
            logo_html = f'<img src="file:///{abs_logo_path}" width="{logo_width}" height="{logo_height}" style="float: right; margin: 10px;" alt="Company Logo">'
        
        content = f"""
<div style="font-size: 10px; line-height: 1.2; margin: 10px;">
{logo_html}
<h2 style="font-size: 14px; margin: 5px 0;">Integritetspolicy – KeyBuddy</h2>
<p style="margin: 3px 0;"><strong>Senast uppdaterad: 2025-09-15</strong></p>

<h3 style="font-size: 11px; margin: 8px 0 3px 0;">Vem ansvarar för dina uppgifter?</h3>
<p style="margin: 3px 0;">{company_name} org-nr: {org_number} är personuppgiftsansvarig för behandlingen av dina personuppgifter i samband med vår nyckelhanteringstjänst.</p>

<h3 style="font-size: 11px; margin: 8px 0 3px 0;">Vilka uppgifter samlar vi in?</h3>
<p style="margin: 3px 0;">Vi sparar endast de uppgifter som är nödvändiga för att hantera nycklar och nyckelbrickor:</p>
<ul style="margin: 3px 0; padding-left: 15px;">
<li>Företag, Namn, org-nr, adress</li>
<li>Kontaktuppgifter (telefonnummer, e-post)</li>
<li>Kundnummer/ID</li>
<li>Nyckelbricka-ID och koppling till utlämnad nyckel</li>
</ul>

<h3 style="font-size: 11px; margin: 8px 0 3px 0;">Varför sparar vi dessa uppgifter?</h3>
<p style="margin: 3px 0;">Vi behandlar dina uppgifter för att:</p>
<ul style="margin: 3px 0; padding-left: 15px;">
<li>Administrera utlämning och återlämning av nycklar</li>
<li>Hålla ordning på vilka nyckelbrickor som är aktiva</li>
<li>Kontakta dig vid behov rörande utlämnade Nyckelkort/bricka</li>
</ul>

<h3 style="font-size: 11px; margin: 8px 0 3px 0;">Hur länge sparas uppgifterna?</h3>
<p style="margin: 3px 0;">Dina personuppgifter sparas endast så länge du har en aktiv nyckelbricka. När nyckelbrickan återlämnas raderas dina uppgifter permanent.</p>

<h3 style="font-size: 11px; margin: 8px 0 3px 0;">Dina rättigheter</h3>
<ul style="margin: 3px 0; padding-left: 15px;">
<li>Få information om vilka uppgifter vi har om dig</li>
<li>Begära rättelse av felaktiga uppgifter</li>
<li>Begära radering av dina uppgifter</li>
<li>Lämna in klagomål till Integritetsskyddsmyndigheten (IMY)</li>
</ul>

<h3 style="font-size: 11px; margin: 8px 0 3px 0;">Säkerhet</h3>
<ul style="margin: 3px 0; padding-left: 15px;">
<li>Kryptering av data (Militär grad kryptering)</li>
<li>Åtkomstkontroller och loggning av administratörsåtgärder</li>
<li>Radering av data i backup när uppgifterna inte längre behövs</li>
</ul>

<h3 style="font-size: 11px; margin: 8px 0 3px 0;">Delning av uppgifter</h3>
<p style="margin: 3px 0;">Vi delar inte dina uppgifter med tredje part.</p>

<h3 style="font-size: 11px; margin: 8px 0 3px 0;">Kontakt</h3>
<p style="margin: 3px 0;">Om du har frågor kring hur vi hanterar dina personuppgifter, kontakta oss på: <strong>{email}</strong></p>
</div>
        """
        
        return content
        
    def export_pdf(self):
        """Export GDPR policy as PDF and open it"""
        try:
            import tempfile
            import webbrowser
            import os
            
            # Create temporary PDF file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_GDPR_Policy_KeyBuddy_{datetime.now().strftime('%Y%m%d')}.pdf",
                delete=False
            )
            temp_file.close()
            
            # Create printer with simpler configuration
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(temp_file.name)
            
            # Create document
            document = QTextDocument()
            document.setHtml(self.get_gdpr_content())
            
            # Print to PDF
            document.print_(printer)
            
            # Open PDF in browser
            if os.path.exists(temp_file.name):
                webbrowser.open(f'file:///{temp_file.name.replace(os.sep, "/")}')
            else:
                CopyableMessageBox.warning(
                    self,
                    "Varning",
                    "PDF-filen kunde inte skapas korrekt."
                )
            
        except Exception as e:
            error_msg = f"Kunde inte exportera PDF:\n{str(e)}"
            
            CopyableMessageBox.critical(
                self,
                "Export misslyckades",
                error_msg
            )
