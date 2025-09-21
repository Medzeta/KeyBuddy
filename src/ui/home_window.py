"""
Home window with navigation buttons and dashboard
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QGridLayout, QPushButton, QFrame, QScrollArea)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap

from .styles import KeyBuddyButton, ButtonType, ThemeManager

class DashboardCard(QFrame):
    """Dashboard card widget using global stylesheet system"""
    
    def __init__(self, title, description, icon_text="", parent=None, app_manager=None):
        super().__init__(parent)
        self.title_label = None
        self.setup_ui(title, description, icon_text)
    
    def update_title(self, new_title):
        """Update the title text"""
        if self.title_label:
            self.title_label.setText(new_title + "\n")
    
    def setup_ui(self, title, description, icon_text):
        """Setup card UI using global stylesheet system"""
        self.setFrameStyle(QFrame.NoFrame)
        self.setObjectName("dashboardCard")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)  # Ta bort spacing
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Icon med extra rad
        icon_label = QLabel(icon_text + "\n")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setObjectName("dashboardIcon")
        layout.addWidget(icon_label)
        
        # Title med extra rad
        self.title_label = QLabel(title + "\n")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("dashboardTitle")
        layout.addWidget(self.title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setObjectName("dashboardDescription")
        layout.addWidget(desc_label)

class HomeWindow(QWidget):
    """Main home window with navigation"""
    
    navigate_to_add_system = Signal()
    navigate_to_my_systems = Signal()
    navigate_to_settings = Signal()
    
    def __init__(self, app_manager, db_manager, translation_manager):
        super().__init__()
        self.app_manager = app_manager
        self.db_manager = db_manager
        self.translation_manager = translation_manager
        self.systems_card = None
        self.orders_card = None
        self.recent_card = None
        self.setup_ui()
        
        # Setup timer for automatic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def setup_ui(self):
        """Setup home UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Welcome section
        welcome_widget = self.create_welcome_section()
        layout.addWidget(welcome_widget)
        
        # Main navigation cards
        nav_widget = self.create_navigation_section()
        layout.addWidget(nav_widget)
        
        # Quick stats
        stats_widget = self.create_stats_section()
        layout.addWidget(stats_widget)
        
        layout.addStretch()
    
    def create_welcome_section(self):
        """Create welcome section"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Welcome title
        welcome_label = QLabel("Välkommen till Keybuddy")
        welcome_label.setProperty("class", "title")
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Subtitle
        subtitle = QLabel("Säker och professionell nyckelhantering")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        return widget
    
    def create_navigation_section(self):
        """Create main navigation section"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        
        # Navigation grid
        nav_grid = QGridLayout()
        nav_grid.setSpacing(15)
        
        # Add System button
        add_system_btn = KeyBuddyButton(self.translation_manager.get_text("add_system"), ButtonType.SUCCESS)
        add_system_btn.setProperty("kb_button_type", "large")
        add_system_btn.clicked.connect(self.navigate_to_add_system.emit)
        
        # My Systems button
        my_systems_btn = KeyBuddyButton(self.translation_manager.get_text("my_systems"), ButtonType.LARGE)
        my_systems_btn.clicked.connect(self.navigate_to_my_systems.emit)
        
        nav_grid.addWidget(add_system_btn, 0, 0)
        nav_grid.addWidget(my_systems_btn, 0, 1)
        
        layout.addLayout(nav_grid)
        
        return widget
    
    def create_stats_section(self):
        """Create quick stats section"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        
        # Stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)
        
        # Get stats from database
        total_systems = self.get_total_systems()
        total_orders = self.get_total_orders()
        recent_orders = self.get_recent_orders()
        
        # Stats cards
        self.systems_card = DashboardCard(
            f"{total_systems}",
            "Totalt antal system",
            "🔧"
        )
        
        # Combined orders card
        self.orders_combined_card = DashboardCard(
            f"{total_orders} | {recent_orders}",
            "Ordrar: Totalt | Senaste 30 dagar",
            "📦"
        )
        
        # Combined key production card
        self.keys_combined_card = DashboardCard(
            "0 | 0 | 0",
            "Nycklar: Idag | Vecka | Månad",
            "🔑"
        )
        
        # Combined revenue card
        self.revenue_combined_card = DashboardCard(
            "0 kr | 0 kr | 0 kr",
            "Intäkter: Idag | Vecka | Månad",
            "💰"
        )
        
        
        stats_grid.addWidget(self.systems_card, 0, 0)
        stats_grid.addWidget(self.orders_combined_card, 0, 1)
        stats_grid.addWidget(self.keys_combined_card, 0, 2)
        stats_grid.addWidget(self.revenue_combined_card, 0, 3)
        
        layout.addLayout(stats_grid)
        
        return widget
    
    def get_total_systems(self):
        """Get total number of systems"""
        try:
            result = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM key_systems"
            )
            return result[0]['count'] if result else 0
        except:
            return 0
    
    def get_total_orders(self):
        """Get total number of orders"""
        try:
            result = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM orders"
            )
            return result[0]['count'] if result else 0
        except:
            return 0
    
    def get_recent_orders(self):
        """Get orders from last 30 days"""
        try:
            result = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM orders WHERE order_date >= date('now', '-30 days')"
            )
            return result[0]['count'] if result else 0
        except:
            return 0
    
    def get_keys_today(self):
        """Get total keys produced today"""
        try:
            result = self.db_manager.execute_query(
                "SELECT SUM(quantity) as total FROM orders WHERE date(order_date) = date('now')"
            )
            return result[0]['total'] if result and result[0]['total'] else 0
        except:
            return 0
    
    def get_keys_this_week(self):
        """Get total keys produced this week"""
        try:
            result = self.db_manager.execute_query(
                "SELECT SUM(quantity) as total FROM orders WHERE date(order_date) >= date('now', 'weekday 0', '-7 days')"
            )
            return result[0]['total'] if result and result[0]['total'] else 0
        except:
            return 0
    
    def get_keys_this_month(self):
        """Get total keys produced this month"""
        try:
            result = self.db_manager.execute_query(
                "SELECT SUM(quantity) as total FROM orders WHERE date(order_date) >= date('now', 'start of month')"
            )
            return result[0]['total'] if result and result[0]['total'] else 0
        except:
            return 0
    
    def get_revenue_today(self):
        """Get total revenue for today"""
        try:
            # Get pricing data from app manager
            pricing_data = self.app_manager.get_setting("key_pricing", {})
            if not pricing_data:
                return 0
            
            # Get orders for today with fabrikat and koncept
            result = self.db_manager.execute_query("""
                SELECT o.quantity, ks.fabrikat, ks.koncept 
                FROM orders o
                JOIN key_systems ks ON o.key_system_id = ks.id
                WHERE date(o.order_date) = date('now')
            """)
            
            total_revenue = 0
            for row in result:
                quantity = row['quantity']
                fabrikat = row['fabrikat']
                koncept = row['koncept']
                
                # Get price for this fabrikat_koncept combination
                price_key = f"{fabrikat}_{koncept}"
                price = pricing_data.get(price_key, 0)
                total_revenue += quantity * price
            
            return total_revenue
        except:
            return 0
    
    def get_revenue_this_week(self):
        """Get total revenue for this week"""
        try:
            pricing_data = self.app_manager.get_setting("key_pricing", {})
            if not pricing_data:
                return 0
            
            result = self.db_manager.execute_query("""
                SELECT o.quantity, ks.fabrikat, ks.koncept 
                FROM orders o
                JOIN key_systems ks ON o.key_system_id = ks.id
                WHERE date(o.order_date) >= date('now', 'weekday 0', '-7 days')
            """)
            
            total_revenue = 0
            for row in result:
                quantity = row['quantity']
                fabrikat = row['fabrikat']
                koncept = row['koncept']
                price_key = f"{fabrikat}_{koncept}"
                price = pricing_data.get(price_key, 0)
                total_revenue += quantity * price
            
            return total_revenue
        except:
            return 0
    
    def get_revenue_this_month(self):
        """Get total revenue for this month"""
        try:
            pricing_data = self.app_manager.get_setting("key_pricing", {})
            if not pricing_data:
                return 0
            
            result = self.db_manager.execute_query("""
                SELECT o.quantity, ks.fabrikat, ks.koncept 
                FROM orders o
                JOIN key_systems ks ON o.key_system_id = ks.id
                WHERE date(o.order_date) >= date('now', 'start of month')
            """)
            
            total_revenue = 0
            for row in result:
                quantity = row['quantity']
                fabrikat = row['fabrikat']
                koncept = row['koncept']
                price_key = f"{fabrikat}_{koncept}"
                price = pricing_data.get(price_key, 0)
                total_revenue += quantity * price
            
            return total_revenue
        except:
            return 0
    
    def clear_data(self):
        """Clear sensitive data"""
        pass
    
    def update_stats(self):
        """Update statistics in real-time"""
        try:
            # Get updated stats
            total_systems = self.get_total_systems()
            total_orders = self.get_total_orders()
            recent_orders = self.get_recent_orders()
            keys_today = self.get_keys_today()
            keys_week = self.get_keys_this_week()
            keys_month = self.get_keys_this_month()
            revenue_today = self.get_revenue_today()
            revenue_week = self.get_revenue_this_week()
            revenue_month = self.get_revenue_this_month()
            
            # Update card titles
            if self.systems_card:
                self.systems_card.update_title(f"{total_systems}")
            if self.orders_combined_card:
                self.orders_combined_card.update_title(f"{total_orders} | {recent_orders}")
            if self.keys_combined_card:
                self.keys_combined_card.update_title(f"{keys_today} | {keys_week} | {keys_month}")
            if self.revenue_combined_card:
                self.revenue_combined_card.update_title(f"{revenue_today:.0f} kr | {revenue_week:.0f} kr | {revenue_month:.0f} kr")
                
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    
    def update_ui_text(self):
        """Update UI text for current language"""
        # This would update all text elements with current language
        pass
