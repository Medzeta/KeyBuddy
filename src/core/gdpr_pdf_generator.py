"""
GDPR Deletion Confirmation PDF Generator
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from datetime import datetime
import tempfile
import os
from .logo_manager import LogoManager

class GDPRDeletionPDFGenerator:
    """Generate GDPR compliant deletion confirmation PDFs"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for the PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='Header',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#34495e'),
            alignment=TA_LEFT
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=TA_CENTER
        ))
        
        # Custom bullet style
        self.styles.add(ParagraphStyle(
            name='CustomBullet',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            bulletIndent=10
        ))
    
    def generate_deletion_confirmation_pdf(self, system_data, deletion_date):
        """Generate GDPR deletion confirmation PDF"""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build story
        story = []
        
        # Add logo using GLOBAL standard
        logo = LogoManager.create_logo_element()
        if logo:
            print("DEBUG: GDPR PDF - Logo created successfully")
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 20))
        else:
            print("DEBUG: GDPR PDF - No logo found")
        
        # Title
        title = Paragraph("BEKRÄFTELSE PÅ DATARADERING", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 30))
        
        # Deletion confirmation
        deletion_info = f"""
        <b>Datum och tid för radering:</b> {deletion_date.strftime('%Y-%m-%d %H:%M:%S')}<br/>
        <b>System som raderats:</b> {system_data.get('company', 'N/A')} - {system_data.get('project', 'N/A')}<br/>
        <b>Nyckelkod:</b> {system_data.get('key_code', 'N/A')}<br/>
        <b>Kundnummer:</b> {system_data.get('customer_number', 'N/A')}
        """
        
        story.append(Paragraph(deletion_info, self.styles['CustomBody']))
        story.append(Spacer(1, 20))
        
        # Confirmation text
        confirmation_text = """
        Härmed bekräftas att all persondata och systemdata kopplad till ovan nämnda nyckelhanteringssystem 
        har raderats permanent från Keybuddy-systemet i enlighet med GDPR (Dataskyddsförordningen).
        """
        story.append(Paragraph(confirmation_text, self.styles['CustomBody']))
        story.append(Spacer(1, 30))
        
        # Footer with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        footer = Paragraph(f"Genererad av Keybuddy: {timestamp}", self.styles['Footer'])
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        
        return temp_file.name
    
    def open_pdf_in_browser(self, pdf_path):
        """Open PDF in default browser for viewing/printing/saving"""
        try:
            webbrowser.open(f'file://{pdf_path}')
            return True
        except Exception as e:
            print(f"Could not open PDF in browser: {e}")
            return False
