"""PDF Generator for order exports"""

import os
import tempfile
import webbrowser
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from .logo_manager import LogoManager

class OrderPDFGenerator:
    """Generate PDF exports for key manufacturing orders"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def get_smart_system_data(self, system_data):
        """Smart logic to choose between Nyckelkort and Standard & System-nycklar data"""
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
        
        # Return the appropriate data set
        if nyckelkort_has_data:
            return {
                'key_code': system_data.get('key_code', ''),
                'series_id': system_data.get('series_id', ''),
                'key_profile': system_data.get('key_profile', ''),
                'key_location': smart_key_location,  # Use smart key_location
                'delning': system_data.get('delning', ''),  # Delning is always from standard fields
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
                'delning': system_data.get('delning', ''),  # Delning is always from standard fields
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
                'key_location': smart_key_location,  # Use smart key_location even when no other data
                'delning': system_data.get('delning', ''),  # Delning is always available
                'fabrikat': '',
                'koncept': '',
                'data_source': 'none'
            }
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black
        ))
        
        # Left-aligned title
        self.styles.add(ParagraphStyle(
            'LeftTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_LEFT,
            textColor=colors.black
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=colors.black
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        ))
    
    
    def generate_order_pdf(self, system_data, order_data, customer_data, current_user=None, logo_path=None):
        """Generate PDF for key manufacturing order with custom template"""
        # Get smart system data (chooses between Nyckelkort and Standard data)
        smart_data = self.get_smart_system_data(system_data)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        # Build content
        story = []
        
        # Get current user's company name (system user's company)
        user_company = current_user.get('company_name', 'KeyBuddy') if current_user else 'KeyBuddy'
        
        # Header section with system user's company (replacing KeyBuddy branding)
        header_data = []
        
        # Center: System user's company (replaces both company and KeyBuddy branding)
        company_para = Paragraph(f"<b>{user_company}</b>", self.styles['Normal'])
        company_para.fontSize = 16
        
        # Add company logo using GLOBAL standard
        logo_element = LogoManager.create_logo_element()
        
        # Create header with system user's company centered at top
        company_header = Table([[company_para]], colWidths=[180*mm])
        company_header.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
        ]))
        story.append(company_header)
        story.append(Spacer(1, 10))
        
        # Title section - vänsterjusterad titel + logo och kod/profil på höger sida
        key_code = smart_data.get('key_code', '')
        key_profile = smart_data.get('key_profile', '')
        title_text = f"TILLVERKNINGSORDER NYCKEL"
        code_profile_text = f"{key_code} {key_profile}"
        
        # Skapa titel med samma stil som Nyckelkvittens (blå färg, storlek 18)
        title_style = ParagraphStyle(
            'BlueTitle',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#87CEEB'),  # Samma blå som kolumnerna
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=20  # Extra utrymme efter titel
        )
        title_para = Paragraph(title_text, title_style)
        
        # Lägg till extra utrymme (2 enterslag)
        story.append(Spacer(1, 20))  # Extra utrymme innan titel
        story.append(title_para)
        story.append(Spacer(1, 10))  # Extra utrymme efter titel
        
        # Lägg till logo och kod/profil på höger sida (om logo finns)
        if logo_element:
            # Skapa tabell för logo och kod/profil på höger sida
            right_content = Table([[logo_element], [code_profile_text]], colWidths=[LogoManager.LOGO_WIDTH])
            right_content.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Logo aligned to middle
                ('VALIGN', (0, 1), (0, 1), 'TOP'),     # Code/profile at top
                ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (0, 1), 14),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (0, 0), 5),
                ('BOTTOMPADDING', (0, 1), (0, 1), 0),
            ]))
            
            # Placera logo/kod på höger sida med tom vänster kolumn
            logo_table = Table([["", right_content]], colWidths=[120*mm, LogoManager.LOGO_WIDTH])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), -10),  # Flytta upp för att vara på samma höjd som titel
            ]))
            story.append(logo_table)
        else:
            # Ingen logo, bara kod/profil på höger sida
            code_table = Table([["", code_profile_text]], colWidths=[120*mm, LogoManager.LOGO_WIDTH])
            code_table.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (1, 0), 14),
                ('TOPPADDING', (0, 0), (-1, -1), -10),  # Flytta upp för att vara på samma höjd som titel
            ]))
            story.append(code_table)
        
        # Main info section with Nyckelansvarig 1 under project
        key_responsible = order_data.get('key_responsible', customer_data.get('key_responsible_1', 'N/A'))
        
        # Use smart data for key_location (prioritizes nyckelplats, falls back to nyckelplats 2)
        smart_key_location = smart_data.get('key_location', 'N/A')
        
        info_data = [
            [f"Företag: {customer_data.get('company', 'N/A')}", f"   Fabrikat: {smart_data.get('fabrikat', 'N/A')}"],
            [f"Projekt: {customer_data.get('project', 'N/A')}", f"   Koncept: {smart_data.get('koncept', 'N/A')}"],
            [f"Nyckelplats: {smart_key_location}", ""],
            [f"Nyckelansvarig 1: {key_responsible}", ""]
        ]
        
        # Justera kolumnbredd så höger kolumn börjar där nyckelkoden börjar
        info_table = Table(info_data, colWidths=[130*mm, 50*mm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),    # Båda kolumner vänsterjusterade
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),  # Minskat från 8 till 2
            ('TOPPADDING', (0, 0), (-1, -1), 2),     # Minskat från 8 till 2
        ]))
        story.append(info_table)
        story.append(Spacer(1, 8))  # Minskat från 15 till 8
        
        # Order details table with light blue header - updated field mappings
        table_headers = ['ID', 'Nyckelkod', 'Delning', 'Löpnr', 'Flex', 'Syst.nr', 'Profil']
        
        # Create order row data according to new specifications
        # Calculate sequence range (start - end)
        sequence_start = order_data.get('sequence_start', 0)
        quantity = order_data.get('quantity', 1)
        try:
            start_num = int(sequence_start) if sequence_start else 0
            end_num = start_num + int(quantity) - 1
            sequence_range = f"{start_num} - {end_num}"
        except (ValueError, TypeError):
            sequence_range = str(sequence_start)
        
        order_row = [
            str(system_data.get('id', '')),  # ID (was Pos)
            smart_data.get('key_code', ''),  # Nyckelkod
            smart_data.get('delning', ''),  # Delning (was Nyckelfunktion)
            sequence_range,  # Löpnr range (start - end)
            system_data.get('flex1', ''),  # Flex (was Nyckeltyp) - using flex1 from original data
            smart_data.get('series_id', ''),  # Syst.nr (systemnummer from smart data)
            smart_data.get('key_profile', ''),  # Profil
        ]
        
        table_data = [table_headers, order_row]
        
        # Calculate column widths to fit the page (7 columns now)
        # Total width should match quantity table width (180mm)
        col_widths = [25*mm, 30*mm, 30*mm, 25*mm, 25*mm, 20*mm, 25*mm]  # Total: 180mm
        
        order_table = Table(table_data, colWidths=col_widths)
        order_table.setStyle(TableStyle([
            # Header row with light blue background
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#87CEEB')),  # Light blue
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Data row
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ]))
        
        story.append(order_table)
        story.append(Spacer(1, 10))
        
        # Quantity row
        quantity_data = [[f"Antal nycklar: {order_data.get('quantity', 0)}"]]
        quantity_table = Table(quantity_data, colWidths=[180*mm])
        quantity_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(quantity_table)
        
        # Logo is now in header, no need for separate logo section
        
        story.append(Spacer(1, 20))
        
        # Notes / Övrigt section if provided (always from original system_data)
        notes_text = (system_data.get('notes') or '').strip()
        if notes_text:
            notes_table = Table([[f"Övrigt: {notes_text}"]], colWidths=[180*mm])
            notes_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(notes_table)
            story.append(Spacer(1, 10))
        
        # Sidnummer och datum flyttade till botten (se onPage callback)
        
        # Footer flyttad till botten av sidan (se onPage callback)
        
        # Skapa footer callback för botten av sidan
        def add_footer(canvas, doc):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            current_date = datetime.now().strftime("%Y-%m-%d")
            user_name = current_user.get('username', 'Okänd användare') if current_user else 'Okänd användare'
            footer_text = f"Skapad av: {user_name} | Datum: {timestamp} | Genererad av KeyBuddy"
            
            canvas.saveState()
            canvas.setFont('Helvetica', 10)
            canvas.setFillColor(colors.black)
            
            # Sidnummer vänster (25mm från botten)
            canvas.drawString(doc.leftMargin, 25*mm, "Sida: 1 / 1")
            
            # Datum höger (25mm från botten)
            canvas.drawRightString(doc.width + doc.leftMargin, 25*mm, current_date)
            
            # Footer centrerad (15mm från botten)
            canvas.setFont('Helvetica', 9)
            canvas.setFillColor(colors.grey)
            canvas.drawCentredString(doc.width/2 + doc.leftMargin, 15*mm, footer_text)
            canvas.restoreState()
        
        # Build PDF med footer callback
        doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
        
        return temp_file.name
    
    def generate_orders_list_pdf(self, orders_data, filter_info, logo_path=None):
        """Generate PDF with list of orders"""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Build content
        story = []
        
        # Header with title and logo
        header_data = []
        title_para = Paragraph("Tillverkningsordrar", self.styles['LeftTitle'])
        
        logo = LogoManager.create_logo_element()
        if logo:
            header_data = [[title_para, logo]]
            header_table = Table(header_data, colWidths=[140*mm, LogoManager.LOGO_WIDTH])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(header_table)
        else:
            story.append(title_para)
        
        story.append(Spacer(1, 20))
        
        # Orders table header with rectangle background
        # Create table width to match the data table
        col_widths = [15*mm, 25*mm, 35*mm, 25*mm, 20*mm, 15*mm, 25*mm, 30*mm]
        total_width = sum(col_widths)
        
        # Remove the "Orderlista" header - no longer needed
        
        # Table headers
        table_data = [['ID', 'Datum', 'Företag', 'Nyckelkod', 'Profil', 'Antal', 'Löpnummer', 'Ansvarig']]
        
        # Add order data
        for order in orders_data:
            table_data.append([
                order['id'],
                order['order_date'],
                order['company'][:20] + '...' if len(order['company']) > 20 else order['company'],
                order['key_code'],
                order['key_profile'],
                order['quantity'],
                order['sequence_range'],
                order['key_responsible'][:15] + '...' if len(order['key_responsible']) > 15 else order['key_responsible']
            ])
        
        # Create table with appropriate column widths
        col_widths = [15*mm, 25*mm, 35*mm, 25*mm, 20*mm, 15*mm, 25*mm, 30*mm]
        orders_table = Table(table_data, colWidths=col_widths)
        
        # Style the table
        orders_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#87CEEB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # ID column center
            ('ALIGN', (4, 1), (5, -1), 'CENTER'),  # Profil and Antal columns center
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(orders_table)
        story.append(Spacer(1, 20))
        
        # Summary
        total_orders = len(orders_data)
        total_keys = sum(int(order['quantity']) for order in orders_data if order['quantity'].isdigit())
        
        summary_data = [
            ['Totalt antal ordrar:', str(total_orders)],
            ['Totalt antal nycklar:', str(total_keys)]
        ]
        
        summary_table = Table(summary_data, colWidths=[40*mm, 30*mm])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
        ]))
        
        story.append(summary_table)
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
            print(f"Error opening PDF: {e}")
            return False

    def generate_invoice_stub_pdf(self, system_data, customer_data, current_user=None, logo_path=None):
        """Generate a simple invoice stub PDF labeled 'FAKTURAUNDERLAG'."""
        # Get smart system data (chooses between Nyckelkort and Standard data)
        smart_data = self.get_smart_system_data(system_data)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()

        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        story = []

        # Header: company name left, logo right (same size as nyckelkvitto)
        user_company = (current_user or {}).get('company_name', 'KeyBuddy')
        
        # Create logo element using GLOBAL standard
        logo_element = LogoManager.create_logo_element()
        
        # Create header with company name and logo (or fallback text)
        if logo_element:
            header_data = [[
                Paragraph(user_company, self.styles['LeftTitle']),
                logo_element
            ]]
        else:
            # Fallback: just company name, no KeyBuddy text
            header_data = [[
                Paragraph(user_company, self.styles['LeftTitle']),
                Paragraph('', self.styles['CustomTitle'])  # Empty right side
            ]]

        col_widths = [90*mm, 90*mm]
        header_table = Table(header_data, colWidths=col_widths)
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT')
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))

        # Title
        story.append(Paragraph('FAKTURAUNDERLAG', self.styles['SectionHeader']))
        story.append(Spacer(1, 6))

        # Info section (using smart data)
        info_data = [
            ["Företag:", customer_data.get('company', 'N/A')],
            ["Projekt:", customer_data.get('project', 'N/A')],
            ["Fabrikat:", smart_data.get('fabrikat', 'N/A')],
            ["Koncept:", smart_data.get('koncept', 'N/A')]
        ]
        info_table = Table(info_data, colWidths=[90*mm, 90*mm])
        info_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))

        # Placeholder content
        story.append(Paragraph("Denna PDF är ett enkelt underlag. Innehåll anpassas senare.", self.styles['Normal']))
        story.append(Spacer(1, 20))

        # Footer
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        user_name = (current_user or {}).get('username', '')
        footer = Paragraph(f"Skapad av: {user_name} | Datum: {timestamp} | Genererad av KeyBuddy", self.styles['Footer'])
        story.append(Spacer(1, 40))
        story.append(footer)

        doc.build(story)
        return temp_file.name

    def generate_key_receipt_pdf(self, system_data, order_data, customer_data, current_user=None, logo_path=None):
        """Generate 'Nyckelkvittens' PDF according to specified layout"""
        # Get smart system data (chooses between Nyckelkort and Standard data)
        smart_data = self.get_smart_system_data(system_data)
        # Temp PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        c = canvas.Canvas(temp_file.name, pagesize=A4)
        width, height = A4

        # Margins
        left = 25*mm
        right = width - 25*mm
        top = height - 25*mm

        # Header values
        user_company = (current_user or {}).get('company_name', 'KeyBuddy')
        user_org = (current_user or {}).get('org_number', '')
        fabrikat = smart_data.get('fabrikat', '') or ''
        koncept = smart_data.get('koncept', '') or ''
        systemnr_text = f"Fabrikat: {fabrikat}   Koncept: {koncept}"

        # Header: company name left
        c.setFont("Helvetica-Bold", 14)
        c.drawString(left, top, user_company)

        # Header: logo using GLOBAL standard - top-right corner
        logo_path = LogoManager.get_logo_path()
        if logo_path and os.path.exists(logo_path):
            try:
                # Use GLOBAL standard size with natural proportions
                from PIL import Image as PILImage
                with PILImage.open(logo_path) as pil_img:
                    original_width, original_height = pil_img.size
                    aspect_ratio = original_width / original_height
                    
                    logo_w = LogoManager.LOGO_WIDTH
                    logo_h = logo_w / aspect_ratio  # Natural proportions
                
                # Position: exact top-right
                logo_x = right - logo_w
                logo_y = top - logo_h
                
                # Use ImageReader for robust PNG handling
                from reportlab.lib.utils import ImageReader
                img_reader = ImageReader(logo_path)
                # Use mask='auto' so PNG transparency is respected (avoid black box)
                c.drawImage(img_reader, logo_x, logo_y, width=logo_w, height=logo_h, mask='auto')
            except Exception as e:
                print(f"Logo draw error: {e}")
                # Ingen fallback-text, bara hoppa över logotypen
        # Ingen fallback-text om logotyp saknas

        # Header: © year KeyBuddy under Fabrikat/Koncept line (left-aligned under that text)
        c.setFont("Helvetica", 9)
        c.drawString(left, top-12*mm, "© 2025 KeyBuddy")

        # Header: Systemnr line equivalent -> use fabrikat/koncept on left under company
        # Reduce spacing by one step
        c.setFont("Helvetica", 10)
        c.drawString(left, top-8*mm, systemnr_text)

        # Title left-aligned with copyright: Nyckelkvittens (blå färg som kolumnerna)
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(colors.HexColor('#87CEEB'))  # Samma blå som kolumnerna
        title_y = top - 30*mm
        c.drawString(left, title_y, "Nyckelkvittens")
        c.setFillColor(colors.black)  # Återställ till svart för annan text

        # Nyckelmottagare block (left) leave two blank lines under title (~10mm)
        rec_y = top-45*mm
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(left, rec_y, "Nyckelmottagare")
        c.setFont("Helvetica", 10)
        lines_left = [
            customer_data.get('company',''),
            customer_data.get('key_responsible_1',''),
            customer_data.get('mobile_phone',''),
            customer_data.get('address',''),
            f"{customer_data.get('postal_code','')} {customer_data.get('postal_address','')}",
        ]
        y = rec_y - 6*mm
        for line in lines_left:
            if line:
                c.drawString(left, y, str(line))
                y -= 5*mm

        # Servicestation block (right)
        right_x = right - 70*mm
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(right_x, rec_y, "Servicestation")
        c.setFont("Helvetica", 10)
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines_right = [
            user_company,
            f"Org.nr: {user_org}" if user_org else "",
            now_text
        ]
        y2 = rec_y - 6*mm
        for line in lines_right:
            if line:
                c.drawString(right_x, y2, str(line))
                y2 -= 5*mm

        # Boxed table with blue header: Nyckel | Löpnummer | Antal
        table_top = top-75*mm
        table_left = left
        table_width = right - left
        header_h = 8*mm
        row_h = 10*mm
        # Column widths
        col1_w = 95*mm
        col2_w = 60*mm
        col3_w = table_width - col1_w - col2_w
        if col3_w < 25*mm:
            extra = 25*mm - col3_w
            # steal from col1 if possible else from col2
            if col1_w - extra >= 80*mm:
                col1_w -= extra
            else:
                remaining = extra - (col1_w - 80*mm)
                col1_w = 80*mm
                col2_w = max(40*mm, col2_w - remaining)
            col3_w = 25*mm
        # Header background
        from reportlab.lib import colors as _colors
        c.setFillColor(_colors.HexColor('#87CEEB'))
        c.rect(table_left, table_top - header_h, table_width, header_h, stroke=0, fill=1)
        c.setFillColor(_colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(table_left + 2*mm, table_top - header_h + 2*mm, "Nyckel")
        c.drawString(table_left + col1_w + 2*mm, table_top - header_h + 2*mm, "Löpnummer")
        c.drawRightString(table_left + col1_w + col2_w + col3_w - 2*mm, table_top - header_h + 2*mm, "Antal")
        # Outer box and grid
        c.setLineWidth(1)
        c.rect(table_left, table_top - header_h - row_h, table_width, header_h + row_h, stroke=1, fill=0)
        # Separator between header and row
        c.line(table_left, table_top - header_h, table_left + table_width, table_top - header_h)
        # Vertical lines
        c.line(table_left + col1_w, table_top - header_h - row_h, table_left + col1_w, table_top)
        c.line(table_left + col1_w + col2_w, table_top - header_h - row_h, table_left + col1_w + col2_w, table_top)
        # Row data
        key_number = smart_data.get('key_code', '')
        seq_start = int(order_data.get('sequence_start', 0) or 0)
        qty = int(order_data.get('quantity', 1) or 1)
        seq_end = seq_start + qty - 1
        seq_range = f"{seq_start}-{seq_end}" if qty > 1 else f"{seq_start}"
        row_baseline = table_top - header_h - row_h + 3*mm
        c.setFont("Helvetica", 10)
        c.drawString(table_left + 2*mm, row_baseline, str(key_number))
        c.drawString(table_left + col1_w + 2*mm, row_baseline, seq_range)
        c.drawRightString(table_left + col1_w + col2_w + col3_w - 2*mm, row_baseline, str(qty))

        # Totalt antal row (place below the table box)
        total_y = (table_top - header_h - row_h) - 6*mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, total_y, "Totalt antal")
        c.drawRightString(right, total_y, str(qty))

        # Signature area adjustments:
        # - Show plain date text
        # - Draw the signature line for recipient name (moved from date to name)
        sig_y = total_y - 25*mm
        sig_text = f"{(customer_data.get('key_responsible_1') or (current_user or {}).get('username','')).strip()}"
        c.setFont("Helvetica", 10)
        # Date (plain)
        from datetime import datetime as _dt
        c.drawString(left, sig_y - 6*mm, f"Datum: {_dt.now().strftime('%Y-%m-%d')}")
        # Recipient name with line underneath
        name_y = sig_y - 15*mm
        c.drawString(left, name_y, sig_text)
        c.setLineWidth(0.8)
        # Move the bottom line down by ~15mm (3 enter steps)
        c.line(left, name_y - 2*mm - 15*mm, left + 80*mm, name_y - 2*mm - 15*mm)

        # Footer: same style as order export
        from datetime import datetime as _dt
        user_name = (current_user or {}).get('username', 'Okänd användare')
        footer_text = f"Skapad av: {user_name} | Datum: {_dt.now().strftime('%Y-%m-%d %H:%M')} | Genererad av KeyBuddy"
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.grey)
        c.drawCentredString(width/2, 15*mm, footer_text)

        c.showPage()
        c.save()
        return temp_file.name
