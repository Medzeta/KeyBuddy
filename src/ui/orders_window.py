"""
Orders window for viewing and managing key manufacturing orders
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QTableWidget, QTableWidgetItem, QPushButton, 
                              QHeaderView, QMessageBox, QFileDialog, QDateEdit,
                              QFormLayout, QGroupBox, QComboBox, QAbstractItemView,
                              QSizePolicy, QMenu, QAbstractScrollArea)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QEvent
from PySide6.QtGui import QFont
# Print and PDF imports removed - will be rebuilt
import os
from datetime import datetime

from .styles import AnimatedButton
from .copyable_message_box import CopyableMessageBox
from ..core.pdf_generator import OrderPDFGenerator

class OrdersTable(QTableWidget):
    """Custom table to ensure right-click context menu works reliably."""
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self._parent_window = parent_window

    def contextMenuEvent(self, event):
        try:
            print("DEBUG: OrdersTable.contextMenuEvent")
            # event.pos() is already in viewport coordinates in item views
            vp_point = event.pos()
            # Do NOT change selection here to avoid row jumping; selection is done in mousePressEvent
            self._parent_window.on_orders_context_menu(vp_point)
        except Exception:
            pass

    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.RightButton:
                print("DEBUG: OrdersTable.mousePressEvent RightButton")
                # event.pos() is already in viewport coordinates in item views
                vp_point = event.pos()
                row = self.rowAt(vp_point.y())
                if row is not None and row >= 0:
                    self.selectRow(row)
                self._parent_window.on_orders_context_menu(vp_point)
                return
        except Exception:
            pass
        super().mousePressEvent(event)


class OrdersWindow(QWidget):
    """Window for viewing and managing orders"""
    
    navigate_home = Signal()
    
    def __init__(self, app_manager, db_manager, translation_manager):
        super().__init__()
        self.app_manager = app_manager
        self.db_manager = db_manager
        self.translation_manager = translation_manager
        
        self.setup_ui()
        self.refresh_data()
        
        # Setup timer for automatic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start(3000)  # Update every 3 seconds
    
    def setup_ui(self):
        """Setup orders UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Tillverkningsordrar")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Filter section - expanded layout to prevent overlapping
        filter_group = QGroupBox("Filter")
        filter_group.setMaximumWidth(900)  # Increased width to accommodate all elements
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(15)  # More spacing between elements
        filter_layout.setContentsMargins(15, 15, 15, 15)  # Add margins to center content in the box
        
        # Get current theme colors
        theme_manager = getattr(self.app_manager, 'theme_manager', None)
        if theme_manager and hasattr(theme_manager, 'get_current_theme'):
            theme = theme_manager.get_current_theme()
            text_color = theme.get('text_primary', '#2c3e50')
            bg_color = theme.get('background', 'white')
            border_color = theme.get('border', '#bdc3c7')
            focus_color = theme.get('primary', '#3498db')
        else:
            # Fallback to light theme colors
            text_color = '#2c3e50'
            bg_color = 'white'
            border_color = '#bdc3c7'
            focus_color = '#3498db'
        
        # Filter styling handled by global CSS system
        
        # From date
        from_label = QLabel("Från:")
        from_label.setFixedHeight(30)
        from_label.setProperty("kb_label_type", "caption")
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setMinimumWidth(130)
        self.date_from.setMaximumWidth(150)
        self.date_from.setMinimumHeight(28)
        self.date_from.setMaximumHeight(28)
        # Date styling handled by global CSS
        self.date_from.dateChanged.connect(self.refresh_data)
        
        # To date
        to_label = QLabel("Till:")
        to_label.setFixedHeight(30)
        to_label.setProperty("kb_label_type", "caption")
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setMinimumWidth(130)
        self.date_to.setMaximumWidth(150)
        self.date_to.setMinimumHeight(28)
        self.date_to.setMaximumHeight(28)
        # Date styling handled by global CSS
        self.date_to.dateChanged.connect(self.refresh_data)
        
        # Company dropdown
        company_label = QLabel("Företag:")
        company_label.setFixedHeight(30)
        company_label.setProperty("kb_label_type", "caption")
        self.company_combo = QComboBox()
        self.company_combo.addItem("Alla")
        self.populate_company_filter()
        self.company_combo.setMinimumWidth(200)
        self.company_combo.setMaximumWidth(280)
        self.company_combo.setMinimumHeight(28)
        self.company_combo.setMaximumHeight(28)
        # Combo styling handled by global CSS
        self.company_combo.currentTextChanged.connect(self.refresh_data)
        
        # Nyckelansvarig dropdown
        responsible_label = QLabel("Ansvarig:")
        responsible_label.setFixedHeight(30)
        responsible_label.setProperty("kb_label_type", "caption")
        self.responsible_combo = QComboBox()
        self.responsible_combo.addItem("Alla")
        self.populate_responsible_filter()
        self.responsible_combo.setMinimumWidth(200)
        self.responsible_combo.setMaximumWidth(280)
        self.responsible_combo.setMinimumHeight(28)
        self.responsible_combo.setMaximumHeight(28)
        # Combo styling handled by global CSS
        self.responsible_combo.currentTextChanged.connect(self.refresh_data)
        
        # Add widgets to horizontal layout - no filter button needed
        filter_layout.addWidget(from_label)
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(to_label)
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(company_label)
        filter_layout.addWidget(self.company_combo)
        filter_layout.addWidget(responsible_label)
        filter_layout.addWidget(self.responsible_combo)
        filter_layout.addStretch()  # Push everything to the left
        
        layout.addWidget(filter_group)
        
        # Removed info box per request
        
        # (Removed) info box about double-clicking to open receipts
        
        # Orders table
        self.orders_table = OrdersTable(self)
        self.setup_table()
        layout.addWidget(self.orders_table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        home_btn = AnimatedButton(self.translation_manager.get_text("home"))
        home_btn.clicked.connect(self.navigate_home.emit)
        home_btn.setProperty("class", "secondary")
        
        # Export and print buttons removed - will be rebuilt
        
        export_btn = QPushButton("Export")
        export_btn.setProperty("class", "primary")
        export_btn.clicked.connect(self.export_to_pdf)
        
        button_layout.addWidget(home_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def setup_table(self):
        """Setup orders table"""
        headers = [
            "ID", "Datum", "Företag", "Nyckelkod", "Profil", 
            "Antal", "Löp.nr", "Nyckelansvarig 1"
        ]
        
        self.orders_table.setColumnCount(len(headers))
        self.orders_table.setHorizontalHeaderLabels(headers)
        
        # Set column widths
        header = self.orders_table.horizontalHeader()
        # Resize strategy: keep everything visible without horizontal scroll
        header.setSectionResizeMode(0, QHeaderView.Fixed)              # ID (fixed & narrow)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)   # Datum
        header.setSectionResizeMode(2, QHeaderView.Stretch)            # Företag (stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)   # Nyckelkod
        header.setSectionResizeMode(4, QHeaderView.Fixed)              # Profil (fixed small)
        header.setSectionResizeMode(5, QHeaderView.Fixed)              # Antal (fixed small)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)   # Löp.nr
        header.setSectionResizeMode(7, QHeaderView.Stretch)            # Nyckelansvarig (stretch)
        # Ensure Företag and Nyckelansvarig have reasonable minimum widths
        try:
            header.setMinimumSectionSize(120)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            vp = self.orders_table.viewport() if hasattr(self, 'orders_table') else None
            if obj == vp or obj == self.orders_table:
                if event.type() == QEvent.ContextMenu:
                    print("DEBUG: Orders eventFilter - ContextMenu event (obj:", "table" if obj == self.orders_table else "viewport", ")")
                    pos = event.pos()
                    if obj == self.orders_table:
                        pos = self.orders_table.viewport().mapFrom(self.orders_table, pos)
                    self.on_orders_context_menu(pos)
                    return True
                if event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
                    print("DEBUG: Orders eventFilter - RightButtonPress (obj:", "table" if obj == self.orders_table else "viewport", ")")
                    pos = event.pos()
                    if obj == self.orders_table:
                        pos = self.orders_table.viewport().mapFrom(self.orders_table, pos)
                    self.on_orders_context_menu(pos)
                    return True
        except Exception:
            pass
        return super().eventFilter(obj, event)
        # Explicit widths for compact columns
        try:
            self.orders_table.setColumnWidth(0, 50)   # ID
            self.orders_table.setColumnWidth(4, 70)   # Profil
            self.orders_table.setColumnWidth(5, 60)   # Antal
        except Exception:
            pass
        
        # Enable sorting
        self.orders_table.setSortingEnabled(True)

        # Use DefaultContextMenu; our OrdersTable subclass handles contextMenuEvent
        try:
            self.orders_table.setContextMenuPolicy(Qt.DefaultContextMenu)
            self.orders_table.viewport().setContextMenuPolicy(Qt.DefaultContextMenu)
        except Exception:
            pass

        # Set selection behavior - select entire rows, single selection for clarity
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.orders_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.orders_table.setAlternatingRowColors(True)
        # Table styling handled by global CSS
        # Force full-row selection when any cell is pressed
        try:
            self.orders_table.itemPressed.connect(lambda it: self.orders_table.selectRow(it.row()))
        except Exception:
            pass
        # Do not use double-click to open items; use context menu instead

        # Disable editing - prevent double-click editing
        self.orders_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Ensure we keep CustomContextMenu to use our styled popup (no ActionsContextMenu)

    def on_orders_context_menu(self, point):
        try:
            # Map point to viewport if needed
            sender_obj = self.sender()
            if sender_obj == self.orders_table:
                vp_point = self.orders_table.viewport().mapFrom(self.orders_table, point)
            else:
                vp_point = point
            index = self.orders_table.indexAt(vp_point)
            row = index.row() if index.isValid() else self.orders_table.rowAt(vp_point.y())
            if row is None or row < 0:
                row = self.orders_table.currentRow()
            if row is None or row < 0:
                return
            # Ensure the row is selected for user feedback
            try:
                self.orders_table.selectRow(row)
            except Exception:
                pass
            menu = QMenu(self)
            menu.setObjectName("newDropdownMenu")  # Use new styling
            # Make menu frameless/translucent so rounded corners render
            try:
                menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                menu.setAttribute(Qt.WA_TranslucentBackground, True)
            except Exception:
                pass
            # Menu styling handled by global CSS
            act_open_receipt = menu.addAction("Öppna nyckelkvittens")
            act_open_mo = menu.addAction("Öppna tillverkningsorder")
            chosen = menu.exec(self.orders_table.viewport().mapToGlobal(vp_point))
            order_id = int(self.orders_table.item(row, 0).text())
            if chosen == act_open_receipt:
                # Only open if a receipt exists
                data_rows = self.db_manager.execute_query(
                    "SELECT pdf_encrypted FROM key_receipts WHERE order_id = ?",
                    (order_id,)
                )
                if not data_rows:
                    return
                enc = data_rows[0][0]
                b64 = self.db_manager.decrypt_data(enc)
                import base64, tempfile
                pdf_bytes = base64.b64decode(b64.encode('utf-8'))
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                tmp.write(pdf_bytes); tmp.flush(); tmp.close()
                OrderPDFGenerator().open_pdf_in_browser(tmp.name)
            elif chosen == act_open_mo:
                # Open if exists, else generate
                data_rows = self.db_manager.execute_query(
                    "SELECT pdf_encrypted FROM manufacturing_orders WHERE order_id = ?",
                    (order_id,)
                )
                if data_rows:
                    enc = data_rows[0][0]
                    b64 = self.db_manager.decrypt_data(enc)
                    import base64, tempfile
                    pdf_bytes = base64.b64decode(b64.encode('utf-8'))
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    tmp.write(pdf_bytes); tmp.flush(); tmp.close()
                    OrderPDFGenerator().open_pdf_in_browser(tmp.name)
                else:
                    self.generate_and_store_manufacturing(order_id)
        except Exception:
            pass

    def open_receipt_for_row(self, row: int):
        try:
            if row is None or row < 0:
                return
            order_id_item = self.orders_table.item(row, 0)
            if not order_id_item:
                return
            order_id = int(order_id_item.text())
            data_rows = self.db_manager.execute_query(
                "SELECT pdf_encrypted FROM key_receipts WHERE order_id = ?",
                (order_id,)
            )
            if not data_rows:
                return
            enc = data_rows[0][0]
            b64 = self.db_manager.decrypt_data(enc)
            import base64, tempfile
            pdf_bytes = base64.b64decode(b64.encode('utf-8'))
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            tmp.write(pdf_bytes); tmp.flush(); tmp.close()
            OrderPDFGenerator().open_pdf_in_browser(tmp.name)
        except Exception:
            pass

    def open_or_create_manufacturing_for_row(self, row: int):
        try:
            if row is None or row < 0:
                return
            order_id_item = self.orders_table.item(row, 0)
            if not order_id_item:
                return
            order_id = int(order_id_item.text())
            data_rows = self.db_manager.execute_query(
                "SELECT pdf_encrypted FROM manufacturing_orders WHERE order_id = ?",
                (order_id,)
            )
            if data_rows:
                enc = data_rows[0][0]
                b64 = self.db_manager.decrypt_data(enc)
                import base64, tempfile
                pdf_bytes = base64.b64decode(b64.encode('utf-8'))
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                tmp.write(pdf_bytes); tmp.flush(); tmp.close()
                OrderPDFGenerator().open_pdf_in_browser(tmp.name)
            else:
                self.generate_and_store_manufacturing(order_id)
        except Exception:
            pass

    def populate_company_filter(self):
        """Populate company filter dropdown with available companies"""
        try:
            query = "SELECT DISTINCT company FROM customers ORDER BY company"
            companies = self.db_manager.execute_query(query)
            for company in companies:
                self.company_combo.addItem(company[0])
        except Exception:
            pass  # Silently handle error
    
    def populate_responsible_filter(self):
        """Populate responsible filter dropdown with all key responsibles from database"""
        try:
            # Get all unique key responsibles from customers table
            query = """
                SELECT DISTINCT responsible FROM (
                    SELECT key_responsible_1 as responsible FROM customers WHERE key_responsible_1 IS NOT NULL AND key_responsible_1 != ''
                    UNION
                    SELECT key_responsible_2 as responsible FROM customers WHERE key_responsible_2 IS NOT NULL AND key_responsible_2 != ''
                    UNION
                    SELECT key_responsible_3 as responsible FROM customers WHERE key_responsible_3 IS NOT NULL AND key_responsible_3 != ''
                ) ORDER BY responsible
            """
            responsibles = self.db_manager.execute_query(query)
            
            for responsible in responsibles:
                if responsible[0] and responsible[0].strip():
                    self.responsible_combo.addItem(responsible[0].strip())
                
        except Exception as e:
            # Fallback to default if database query fails
            self.responsible_combo.addItem("Jonaz Hogedal")
    
    def refresh_data(self):
        """Refresh orders data from database"""
        try:
            # Get date range
            date_from = self.date_from.date().toString("yyyy-MM-dd")
            date_to = self.date_to.date().toString("yyyy-MM-dd")
            
            query = """
                SELECT 
                    o.id,
                    date(o.order_date) as order_date,
                    c.company,
                    o.key_code,
                    o.key_profile,
                    o.quantity,
                    o.sequence_start,
                    o.sequence_end,
                    datetime(o.order_date) as full_order_date,
                    ks.key_code as ks_key_code,
                    ks.key_profile as ks_key_profile,
                    ks.key_code2,
                    ks.profile2,
                    ks.delning,
                    ks.fabrikat2,
                    ks.koncept2
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                JOIN key_systems ks ON o.key_system_id = ks.id
                WHERE date(o.order_date) BETWEEN ? AND ?
            """
            
            params = [date_from, date_to]
            
            # Add company filter if not "Alla"
            selected_company = self.company_combo.currentText()
            if selected_company != "Alla":
                query += " AND c.company = ?"
                params.append(selected_company)
            
            # Add responsible filter if not "Alla"
            selected_responsible = self.responsible_combo.currentText()
            if selected_responsible != "Alla":
                query += " AND c.key_responsible_1 = ?"
                params.append(selected_responsible)
            
            query += " ORDER BY o.order_date DESC"
            
            orders = self.db_manager.execute_query(query, params)
            
            self.populate_table(orders)
            
        except Exception as e:
            CopyableMessageBox.critical(
                self,
                "Databasfel",
                f"Kunde inte ladda ordrar: {str(e)}"
            )
    
    def get_smart_display_data(self, system_data):
        """Smart logic to choose between Nyckelkort and Standard & System-nycklar data for display"""
        # Check if Nyckelkort data exists
        nyckelkort_has_data = (
            system_data.get('key_code', '').strip() or
            system_data.get('key_profile', '').strip() or
            system_data.get('key_location', '').strip()
        )
        
        # Check if Standard & System-nycklar data exists
        standard_has_data = (
            system_data.get('key_code2', '').strip() or
            system_data.get('profile2', '').strip() or
            system_data.get('delning', '').strip() or
            system_data.get('key_location2', '').strip()
        )
        
        # Return the appropriate data set for display
        if nyckelkort_has_data:
            return {
                'key_code': system_data.get('key_code', ''),
                'key_profile': system_data.get('key_profile', ''),
                'key_location': system_data.get('key_location', ''),
                'data_source': 'nyckelkort'
            }
        elif standard_has_data:
            return {
                'key_code': system_data.get('key_code2', ''),  # Map key_code2 -> key_code
                'key_profile': system_data.get('profile2', ''),  # Map profile2 -> key_profile
                'key_location': system_data.get('key_location2', ''),  # Map key_location2 -> key_location
                'data_source': 'standard'
            }
        else:
            # No data in either, return empty
            return {
                'key_code': '',
                'key_profile': '',
                'key_location': '',
                'data_source': 'none'
            }
    
    def populate_table(self, orders):
        """Populate table with orders data"""
        self.orders_table.setRowCount(len(orders))
        
        for row, order in enumerate(orders):
            # Apply smart data logic for display
            system_data = {
                'key_code': order[9] if len(order) > 9 else '',  # ks.key_code
                'key_profile': order[10] if len(order) > 10 else '',  # ks.key_profile
                'key_code2': order[11] if len(order) > 11 else '',
                'profile2': order[12] if len(order) > 12 else '',
                'delning': order[13] if len(order) > 13 else '',
                'fabrikat2': order[14] if len(order) > 14 else '',
                'koncept2': order[15] if len(order) > 15 else '',
            }
            smart_data = self.get_smart_display_data(system_data)
            
            # Access by index to avoid key errors
            id_item = QTableWidgetItem(str(order[0]))
            id_item.setTextAlignment(Qt.AlignCenter)
            try:
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            except Exception:
                pass
            self.orders_table.setItem(row, 0, id_item)  # id
            
            # Use smart data for key fields, original data for others
            display_data = [
                order[1] or '',  # date
                order[2] or '',  # company
                smart_data.get('key_code', '') or '',  # smart key_code
                smart_data.get('key_profile', '') or '',  # smart key_profile
                str(order[5] or 0)  # quantity
            ]
            
            for col, val in enumerate(display_data, 1):
                item = QTableWidgetItem(val)
                try:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                except Exception:
                    pass
                self.orders_table.setItem(row, col, item)
            
            # Create sequence range from start and end
            sequence_range = f"{order[6]}-{order[7]}" if order[6] and order[7] else ''
            seq_item = QTableWidgetItem(sequence_range)
            try:
                seq_item.setFlags(seq_item.flags() & ~Qt.ItemIsEditable)
            except Exception:
                pass
            self.orders_table.setItem(row, 6, seq_item)
            
            # Get responsible from order data (key_responsible column)
            try:
                # Get key_responsible from orders table
                responsible_query = "SELECT key_responsible FROM orders WHERE id = ?"
                responsible_result = self.db_manager.execute_query(responsible_query, (order[0],))
                responsible = responsible_result[0][0] if responsible_result and responsible_result[0] else 'Nyckelansvarig 1'
                resp_item = QTableWidgetItem(responsible or 'Nyckelansvarig 1')
                try:
                    resp_item.setFlags(resp_item.flags() & ~Qt.ItemIsEditable)
                except Exception:
                    pass
                self.orders_table.setItem(row, 7, resp_item)
            except:
                empty_item = QTableWidgetItem('')
                try:
                    empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsEditable)
                except Exception:
                    pass
                self.orders_table.setItem(row, 7, empty_item)

            # Store order data as dictionary for export
            order_dict = {
                'id': order[0],
                'order_date': order[1],
                'company': order[2],
                'key_code': order[3],
                'key_profile': order[4],
                'quantity': order[5],
                'sequence_start': order[6],
                'sequence_end': order[7]
            }
            
            item = self.orders_table.item(row, 0)
            item.setData(Qt.UserRole, order_dict)
            # No extra columns stored
            # Add hover tooltip to the entire row
            try:
                for c in range(self.orders_table.columnCount()):
                    cell = self.orders_table.item(row, c)
                    if cell:
                        cell.setToolTip("Högerklicka för flera val")
            except Exception:
                pass

        # After populating, resize and enforce no horizontal scroll
        try:
            self.orders_table.resizeColumnsToContents()
            self.orders_table.setColumnWidth(0, 50)
            self.orders_table.setColumnWidth(4, 70)
            self.orders_table.setColumnWidth(5, 60)
            self.orders_table.horizontalHeader().setStretchLastSection(True)
            self.orders_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            # Reinforce row selection behavior
            self.orders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.orders_table.setSelectionMode(QAbstractItemView.SingleSelection)
        except Exception:
            pass

    def on_table_double_clicked(self, item):
        """Open receipt or manufacturing order PDF on double-click"""
        try:
            row = item.row()
            order_id_item = self.orders_table.item(row, 0)
            if not order_id_item:
                return
            order_id = int(order_id_item.text())
            col = item.column()
            if col == 8:  # Nyckelkvittens column
                receipt_item = self.orders_table.item(row, 8)
                has_receipt = receipt_item and (receipt_item.data(Qt.UserRole) is True or receipt_item.text() == "Ja")
                if not has_receipt:
                    return
                # Fetch and decrypt PDF
                data_rows = self.db_manager.execute_query(
                    "SELECT pdf_encrypted FROM key_receipts WHERE order_id = ?",
                    (order_id,)
                )
                if not data_rows:
                    return
                enc = data_rows[0][0]
                b64 = self.db_manager.decrypt_data(enc)
                import base64, tempfile
                pdf_bytes = base64.b64decode(b64.encode('utf-8'))
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                tmp.write(pdf_bytes)
                tmp.flush()
                tmp.close()
                from ..core.pdf_generator import OrderPDFGenerator
                gen = OrderPDFGenerator()
                gen.open_pdf_in_browser(tmp.name)
            elif col == 9:  # Tillverkningsorder column
                mo_item = self.orders_table.item(row, 9)
                has_mo = mo_item and (mo_item.data(Qt.UserRole) is True or mo_item.text() == "Öppna")
                if has_mo:
                    # Open existing manufacturing order
                    data_rows = self.db_manager.execute_query(
                        "SELECT pdf_encrypted FROM manufacturing_orders WHERE order_id = ?",
                        (order_id,)
                    )
                    if not data_rows:
                        return
                    enc = data_rows[0][0]
                    b64 = self.db_manager.decrypt_data(enc)
                    import base64, tempfile
                    pdf_bytes = base64.b64decode(b64.encode('utf-8'))
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    tmp.write(pdf_bytes)
                    tmp.flush()
                    tmp.close()
                    from ..core.pdf_generator import OrderPDFGenerator
                    gen = OrderPDFGenerator()
                    gen.open_pdf_in_browser(tmp.name)
                else:
                    # Generate, store, and open manufacturing order PDF
                    self.generate_and_store_manufacturing(order_id)
        except Exception as e:
            CopyableMessageBox.warning(self, "Öppna", f"Kunde inte öppna: {str(e)}")

    def generate_and_store_manufacturing(self, order_id: int):
        """Generate manufacturing order PDF, encrypt & store, then open."""
        try:
            # Fetch full data for order including all fields for smart data selection
            row = self.db_manager.execute_query(
                """
                SELECT o.id, o.quantity, o.sequence_start, o.sequence_end, o.key_responsible,
                       ks.id as system_id, ks.key_code, ks.key_profile, ks.series_id, ks.fabrikat, ks.koncept,
                       ks.key_code2, ks.system_number, ks.profile2, ks.delning, ks.key_location2, 
                       ks.fabrikat2, ks.koncept2, ks.flex1, ks.flex2, ks.flex3, ks.notes,
                       c.company, c.project
                FROM orders o
                JOIN key_systems ks ON o.key_system_id = ks.id
                JOIN customers c ON o.customer_id = c.id
                WHERE o.id = ?
                """,
                (order_id,)
            )
            if not row:
                return
            row = row[0]
            system_data = {
                'id': row['system_id'] if 'system_id' in row.keys() else row[5],
                'key_code': row['key_code'] if 'key_code' in row.keys() else row[6],
                'key_profile': row['key_profile'] if 'key_profile' in row.keys() else row[7],
                'series_id': row['series_id'] if 'series_id' in row.keys() else row[8],
                'fabrikat': row['fabrikat'] if 'fabrikat' in row.keys() else row[9],
                'koncept': row['koncept'] if 'koncept' in row.keys() else row[10],
                # Standard & System-nycklar fields
                'key_code2': row['key_code2'] if 'key_code2' in row.keys() else row[11],
                'system_number': row['system_number'] if 'system_number' in row.keys() else row[12],
                'profile2': row['profile2'] if 'profile2' in row.keys() else row[13],
                'delning': row['delning'] if 'delning' in row.keys() else row[14],
                'key_location2': row['key_location2'] if 'key_location2' in row.keys() else row[15],
                'fabrikat2': row['fabrikat2'] if 'fabrikat2' in row.keys() else row[16],
                'koncept2': row['koncept2'] if 'koncept2' in row.keys() else row[17],
                'flex1': row['flex1'] if 'flex1' in row.keys() else row[18],
                'flex2': row['flex2'] if 'flex2' in row.keys() else row[19],
                'flex3': row['flex3'] if 'flex3' in row.keys() else row[20],
                'notes': row['notes'] if 'notes' in row.keys() else row[21],
            }
            order_data = {
                'quantity': row['quantity'] if 'quantity' in row.keys() else row[1],
                'sequence_start': row['sequence_start'] if 'sequence_start' in row.keys() else row[2],
                'sequence_end': row['sequence_end'] if 'sequence_end' in row.keys() else row[3],
                'key_responsible': row['key_responsible'] if 'key_responsible' in row.keys() else row[4],
            }
            customer_data = {
                'company': row['company'] if 'company' in row.keys() else row[22],
                'project': row['project'] if 'project' in row.keys() else row[23],
            }
            current_user = self.app_manager.get_current_user()
            logo_path = self.get_logo_path()
            gen = OrderPDFGenerator()
            pdf_path = gen.generate_order_pdf(system_data, order_data, customer_data, current_user, logo_path)
            # Read and encrypt
            import base64
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            enc = self.db_manager.encrypt_data(b64)
            try:
                self.db_manager.execute_update(
                    "INSERT INTO manufacturing_orders (order_id, pdf_encrypted) VALUES (?, ?)",
                    (order_id, enc)
                )
            except Exception:
                self.db_manager.execute_update(
                    "UPDATE manufacturing_orders SET pdf_encrypted = ? WHERE order_id = ?",
                    (enc, order_id)
                )
            gen.open_pdf_in_browser(pdf_path)
            # Update cell to 'Öppna'
            self.refresh_data()
        except Exception as e:
            CopyableMessageBox.warning(self, "Export", f"Kunde inte skapa tillverkningsorder: {str(e)}")
    
    def clear_data(self):
        """Clear sensitive data"""
        self.orders_table.setRowCount(0)
    
    def export_to_pdf(self):
        """Export selected or all filtered orders data to PDF"""
        try:
            # Gather selected order IDs (if any)
            selected_ids = set()
            for item in self.orders_table.selectedItems():
                if item.column() == 0:  # ID column
                    try:
                        selected_ids.add(int(item.text()))
                    except Exception:
                        pass
            # If selection includes cells other than ID, map rows to IDs
            if not selected_ids and self.orders_table.selectedItems():
                rows = {it.row() for it in self.orders_table.selectedItems()}
                for r in rows:
                    id_item = self.orders_table.item(r, 0)
                    if id_item:
                        try:
                            selected_ids.add(int(id_item.text()))
                        except Exception:
                            pass

            # Build DB query based on filters (and selection if present)
            date_from = self.date_from.date().toString("yyyy-MM-dd")
            date_to = self.date_to.date().toString("yyyy-MM-dd")

            query = (
                "SELECT o.id, date(o.order_date) as order_date, c.company, o.key_code, o.key_profile, "
                "o.quantity, o.sequence_start, o.sequence_end, o.key_responsible "
                "FROM orders o JOIN customers c ON o.customer_id = c.id "
                "JOIN key_systems ks ON o.key_system_id = ks.id "
                "WHERE date(o.order_date) BETWEEN ? AND ?"
            )
            params = [date_from, date_to]

            selected_company = self.company_combo.currentText()
            if selected_company != "Alla":
                query += " AND c.company = ?"
                params.append(selected_company)

            selected_responsible = self.responsible_combo.currentText()
            if selected_responsible != "Alla":
                query += " AND c.key_responsible_1 = ?"
                params.append(selected_responsible)

            if selected_ids:
                placeholders = ",".join(["?"] * len(selected_ids))
                query += f" AND o.id IN ({placeholders})"
                params.extend(list(selected_ids))

            query += " ORDER BY o.order_date DESC"

            rows = self.db_manager.execute_query(query, tuple(params))

            # Map rows to export format
            orders_data = []
            for r in rows:
                seq_start = r[6]
                seq_end = r[7]
                if seq_start and seq_end:
                    sequence_range = f"{seq_start}-{seq_end}"
                else:
                    sequence_range = ""
                orders_data.append({
                    'id': str(r[0]),
                    'order_date': r[1] or '',
                    'company': r[2] or '',
                    'key_code': r[3] or '',
                    'key_profile': r[4] or '',
                    'quantity': str(r[5] or ''),
                    'sequence_range': sequence_range,
                    'key_responsible': r[8] or ''
                })
            
            if not orders_data:
                QMessageBox.information(self, "Export", "Inga ordrar att exportera.")
                return
            
            # Show info about what's being exported
            if len(selected_ids) > 0:
                export_msg = f"Exporterar {len(orders_data)} markerade ordrar."
            else:
                export_msg = f"Exporterar alla {len(orders_data)} synliga ordrar."
            
            # Generate PDF with orders list
            pdf_generator = OrderPDFGenerator()
            pdf_path = pdf_generator.generate_orders_list_pdf(
                orders_data, 
                self.get_filter_info(),
                self.get_logo_path()
            )
            
            # Open PDF in browser
            if pdf_generator.open_pdf_in_browser(pdf_path):
                QMessageBox.information(
                    self, 
                    "Export lyckades", 
                    f"{export_msg}\nPDF-filen har skapats och öppnats i din webbläsare."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Export varning",
                    f"{export_msg}\nPDF skapad men kunde inte öppnas automatiskt.\nFil sparad som: {pdf_path}"
                )
                
        except Exception as e:
            CopyableMessageBox.critical(
                self,
                "Export fel",
                f"Kunde inte skapa PDF: {str(e)}"
            )
    
    def get_filter_info(self):
        """Get current filter information for PDF header"""
        return {
            'date_from': self.date_from.date().toString("yyyy-MM-dd"),
            'date_to': self.date_to.date().toString("yyyy-MM-dd"),
            'company': self.company_combo.currentText(),
            'responsible': self.responsible_combo.currentText()
        }
    
    def get_logo_path(self):
        """Get logo path for PDF using GLOBAL standard"""
        from ..core.logo_manager import LogoManager
        logo_path = LogoManager.get_logo_path()
        return logo_path if os.path.exists(logo_path) else None

    def update_ui_text(self):
        """Update UI text for current language"""
        pass
