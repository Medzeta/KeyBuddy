"""
Global Logo Manager - EN regel för ALLA exporter
"""
import os
from reportlab.lib.units import mm
from reportlab.platypus import Image

class LogoManager:
    """Global logo manager - samma storlek och placering överallt"""
    
    # GLOBAL STANDARD - mindre storlek som passar alla exporter
    LOGO_WIDTH = 30*mm  # 30mm bredd
    LOGO_HEIGHT = None  # Beräknas dynamiskt baserat på bildens naturliga proportioner
    
    @staticmethod
    def get_logo_path():
        """Get standard logo path - check settings first, then fallback to assets"""
        try:
            # Try to get logo from app settings first (user uploaded logo)
            from .app_manager import AppManager
            app_manager = AppManager()
            settings_logo = app_manager.get_setting("company_logo", "")
            if settings_logo and os.path.exists(settings_logo):
                return settings_logo
        except:
            pass
        
        # Fallback to default assets location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, "assets", "company_logo.png")
    
    @staticmethod
    def create_logo_element():
        """Create standardized logo element for ALL PDF exports"""
        logo_path = LogoManager.get_logo_path()
        
        if not logo_path or not os.path.exists(logo_path):
            print(f"DEBUG: Logo path not found: {logo_path}")
            return None
        
        try:
            # Beräkna höjd baserat på bildens naturliga proportioner
            from PIL import Image as PILImage
            with PILImage.open(logo_path) as pil_img:
                original_width, original_height = pil_img.size
                aspect_ratio = original_width / original_height
                
                # Beräkna höjd för att bevara proportioner
                logo_height = LogoManager.LOGO_WIDTH / aspect_ratio
                
                print(f"DEBUG: Creating logo with size {LogoManager.LOGO_WIDTH} x {logo_height} (natural proportions)")
                return Image(
                    logo_path, 
                    width=LogoManager.LOGO_WIDTH, 
                    height=logo_height
                )
        except Exception as e:
            print(f"DEBUG: Logo creation failed: {e}")
            return None
    
    @staticmethod
    def get_logo_size_px():
        """Get logo size in pixels for HTML/UI with natural proportions"""
        logo_path = LogoManager.get_logo_path()
        width_px = 113  # 30mm ≈ 113px
        
        try:
            if logo_path and os.path.exists(logo_path):
                from PIL import Image as PILImage
                with PILImage.open(logo_path) as pil_img:
                    original_width, original_height = pil_img.size
                    aspect_ratio = original_width / original_height
                    height_px = int(width_px / aspect_ratio)  # Natural proportions
                    print(f"DEBUG: Logo size px: {width_px} x {height_px} (natural proportions)")
                    return width_px, height_px
        except Exception as e:
            print(f"DEBUG: Failed to get natural proportions: {e}")
        
        # Fallback to fixed ratio if image can't be read
        height_px = int(width_px * (8.0/35.0))  # ≈ 26px
        print(f"DEBUG: Logo size px fallback: {width_px} x {height_px}")
        return width_px, height_px
