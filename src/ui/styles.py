"""
Förbättrat globalt designsystem för KeyBuddy
Hanterar alla UI-komponenter med konsekvent styling och teman
"""

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect, Property, Qt
from PySide6.QtWidgets import QPushButton, QWidget, QLineEdit, QTextEdit, QLabel, QComboBox, QGroupBox
from PySide6.QtGui import QColor, QPalette, QFont
from typing import Dict, Optional
from enum import Enum

class ButtonType(Enum):
    """Standardiserade knappstorlekar och typer"""
    PRIMARY = "primary"           # Huvudknappar (standard storlek)
    SECONDARY = "secondary"       # Sekundära knappar 
    SMALL = "small"              # Små knappar (60x20 - som logout)
    LARGE = "large"              # Stora knappar (navigation)
    DANGER = "danger"            # Farliga åtgärder (röd)
    SUCCESS = "success"          # Framgångsrika åtgärder (grön)
    WARNING = "warning"          # Varningsknappar (orange)

class FieldType(Enum):
    """Standardiserade fälttyper"""
    STANDARD = "standard"        # Standard input fält
    SEARCH = "search"           # Sökfält
    READONLY = "readonly"       # Skrivskyddade fält
    ERROR = "error"             # Fält med fel
    SUCCESS = "success"         # Fält med framgång

class LabelType(Enum):
    """Standardiserade labeltyper"""
    STANDARD = "standard"       # Standard text
    TITLE = "title"            # Huvudrubriker
    SUBTITLE = "subtitle"      # Underrubriker
    CAPTION = "caption"        # Små texter
    ERROR = "error"            # Felmeddelanden
    SUCCESS = "success"        # Framgångsmeddelanden
    WARNING = "warning"        # Varningar

class KeyBuddyButton(QPushButton):
    """Standardiserad knapp med animationer och konsekvent styling"""
    
    def __init__(self, text="", button_type: ButtonType = ButtonType.PRIMARY, parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.original_size = None
        
        # Sätt standardegenskaper baserat på typ
        self._apply_button_type()
        
    def _apply_button_type(self):
        """Applicera storlek och egenskaper baserat på knappens typ"""
        self.setProperty("kb_button_type", self.button_type.value)
        
        # Sätt storlekar baserat på typ
        if self.button_type == ButtonType.SMALL:
            self.setFixedSize(60, 20)
        elif self.button_type == ButtonType.LARGE:
            self.setMinimumHeight(60)
            self.setMinimumWidth(120)
        elif self.button_type in [ButtonType.PRIMARY, ButtonType.SECONDARY]:
            self.setMinimumHeight(32)
            self.setMinimumWidth(80)
        elif self.button_type in [ButtonType.DANGER, ButtonType.SUCCESS, ButtonType.WARNING]:
            self.setMinimumHeight(32)
            self.setMinimumWidth(100)
    
    def enterEvent(self, event):
        """Hantera hover-effekt"""
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hantera när musen lämnar knappen"""
        super().leaveEvent(event)

class KeyBuddyLineEdit(QLineEdit):
    """Standardiserat textfält med konsekvent styling"""
    
    def __init__(self, field_type: FieldType = FieldType.STANDARD, placeholder="", parent=None):
        super().__init__(parent)
        print(f"Creating KeyBuddyLineEdit with placeholder: {placeholder}")
        self.field_type = field_type
        self.setProperty("kb_field_type", field_type.value)
        if placeholder:
            self.setPlaceholderText(placeholder)
        
        # Force apply styling directly
        self.apply_direct_styling()
    
    def apply_direct_styling(self):
        """Apply beautiful, modern styling directly to this field"""
        # Set reasonable size
        self.setMinimumHeight(45)  # Nice height
        self.setMinimumWidth(250)  # Good width
        
        # Set modern font
        font = QFont("Segoe UI", 11)
        font.setWeight(QFont.Weight.Normal)
        self.setFont(font)
        
        # Set reasonable margins
        self.setContentsMargins(8, 8, 8, 8)
        
        # Allow flexible sizing
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Use global styling - no direct setStyleSheet to allow theme system to work
        # The global QLineEdit styling in ThemeManager will handle all styling
        
        print(f"Beautiful styling applied to KeyBuddyLineEdit: {self.objectName() or 'unnamed'}")
        print(f"Size: {self.minimumSize()}, Font: {self.font().family()}, {self.font().pointSize()}pt")

class KeyBuddyTextEdit(QTextEdit):
    """Standardiserat textområde med konsekvent styling"""
    
    def __init__(self, field_type: FieldType = FieldType.STANDARD, parent=None):
        super().__init__(parent)
        self.field_type = field_type
        self.setProperty("kb_field_type", field_type.value)

class KeyBuddyLabel(QLabel):
    """Standardiserad label med konsekvent styling"""
    
    def __init__(self, text="", label_type: LabelType = LabelType.STANDARD, parent=None):
        super().__init__(text, parent)
        self.label_type = label_type
        self.setProperty("kb_label_type", label_type.value)

class KeyBuddyComboBox(QComboBox):
    """Standardiserad combobox med konsekvent styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("kb_combo", "standard")

class KeyBuddyGroupBox(QGroupBox):
    """Standardiserad gruppbox med konsekvent styling"""
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setProperty("kb_group", "standard")

class ThemeManager:
    """Förbättrad temahanterare med utökade stilar"""
    
    def __init__(self):
        self.current_theme = "light"
        self.themes = self._create_themes()
    
    def _create_themes(self) -> Dict[str, Dict[str, str]]:
        """Skapa temadefinitioner"""
        return {
            "light": {
                "background": "#FFFFFF",
                "surface": "#F5F5F5",
                "surface_elevated": "#FAFAFA",
                "primary": "#2196F3",
                "primary_dark": "#1976D2",
                "primary_light": "#64B5F6",
                "secondary": "#FFC107",
                "secondary_dark": "#F57C00",
                "text_primary": "#212121",
                "text_secondary": "#757575",
                "text_disabled": "#BDBDBD",
                "border": "#E0E0E0",
                "border_focus": "#2196F3",
                "success": "#4CAF50",
                "success_dark": "#388E3C",
                "warning": "#FF9800",
                "warning_dark": "#F57C00",
                "error": "#F44336",
                "error_dark": "#D32F2F",
                "shadow": "rgba(0, 0, 0, 0.1)",
                "shadow_elevated": "rgba(0, 0, 0, 0.15)"
            },
            "dark": {
                "background": "#121212",
                "surface": "#1E1E1E",
                "surface_elevated": "#2D2D2D",
                "primary": "#BB86FC",
                "primary_dark": "#985EFF",
                "primary_light": "#D7B9FF",
                "secondary": "#03DAC6",
                "secondary_dark": "#00A693",
                "text_primary": "#FFFFFF",
                "text_secondary": "#B3B3B3",
                "text_disabled": "#666666",
                "border": "#333333",
                "border_focus": "#BB86FC",
                "success": "#4CAF50",
                "success_dark": "#388E3C",
                "warning": "#FF9800",
                "warning_dark": "#F57C00",
                "error": "#CF6679",
                "error_dark": "#B00020",
                "shadow": "rgba(0, 0, 0, 0.3)",
                "shadow_elevated": "rgba(0, 0, 0, 0.4)"
            },
            "smokey": {
                "background": "#282828",
                "surface": "#3C3C3C",
                "surface_elevated": "#4A4A4A",
                "primary": "#64B5F6",
                "primary_dark": "#42A5F5",
                "primary_light": "#90CAF9",
                "secondary": "#FFB74D",
                "secondary_dark": "#FF8F00",
                "text_primary": "#FFFFFF",
                "text_secondary": "#E0E0E0",
                "text_disabled": "#999999",
                "border": "#555555",
                "border_focus": "#64B5F6",
                "success": "#81C784",
                "success_dark": "#66BB6A",
                "warning": "#FFB74D",
                "warning_dark": "#FF8F00",
                "error": "#E57373",
                "error_dark": "#EF5350",
                "shadow": "rgba(0, 0, 0, 0.4)",
                "shadow_elevated": "rgba(0, 0, 0, 0.5)"
            },
            "ocean": {
                "background": "#F0F8FF",
                "surface": "#E6F3FF",
                "surface_elevated": "#D1E9FF",
                "primary": "#0077BE",
                "primary_dark": "#005A8B",
                "primary_light": "#4A9FD1",
                "secondary": "#00CED1",
                "secondary_dark": "#008B8B",
                "text_primary": "#1E3A5F",
                "text_secondary": "#4682B4",
                "text_disabled": "#B0C4DE",
                "border": "#87CEEB",
                "border_focus": "#0077BE",
                "success": "#20B2AA",
                "success_dark": "#008080",
                "warning": "#FF8C00",
                "warning_dark": "#FF7F00",
                "error": "#DC143C",
                "error_dark": "#B22222",
                "shadow": "rgba(0, 119, 190, 0.1)",
                "shadow_elevated": "rgba(0, 119, 190, 0.15)"
            },
            "forest": {
                "background": "#F5F8F0",
                "surface": "#E8F5E8",
                "surface_elevated": "#D4F1D4",
                "primary": "#228B22",
                "primary_dark": "#006400",
                "primary_light": "#32CD32",
                "secondary": "#8FBC8F",
                "secondary_dark": "#556B2F",
                "text_primary": "#2F4F2F",
                "text_secondary": "#556B2F",
                "text_disabled": "#9ACD32",
                "border": "#90EE90",
                "border_focus": "#228B22",
                "success": "#00FF7F",
                "success_dark": "#00FA54",
                "warning": "#FFD700",
                "warning_dark": "#FFA500",
                "error": "#DC143C",
                "error_dark": "#B22222",
                "shadow": "rgba(34, 139, 34, 0.1)",
                "shadow_elevated": "rgba(34, 139, 34, 0.15)"
            },
            "sunset": {
                "background": "#FFF8F0",
                "surface": "#FFE4E1",
                "surface_elevated": "#FFDAB9",
                "primary": "#FF6347",
                "primary_dark": "#FF4500",
                "primary_light": "#FF7F7F",
                "secondary": "#FFB347",
                "secondary_dark": "#FF8C00",
                "text_primary": "#8B4513",
                "text_secondary": "#CD853F",
                "text_disabled": "#DEB887",
                "border": "#F4A460",
                "border_focus": "#FF6347",
                "success": "#32CD32",
                "success_dark": "#228B22",
                "warning": "#FFD700",
                "warning_dark": "#FFA500",
                "error": "#DC143C",
                "error_dark": "#B22222",
                "shadow": "rgba(255, 99, 71, 0.1)",
                "shadow_elevated": "rgba(255, 99, 71, 0.15)"
            },
            "purple": {
                "background": "#F8F0FF",
                "surface": "#F0E6FF",
                "surface_elevated": "#E6D7FF",
                "primary": "#8A2BE2",
                "primary_dark": "#6A1B9A",
                "primary_light": "#BA68C8",
                "secondary": "#DA70D6",
                "secondary_dark": "#C71585",
                "text_primary": "#4B0082",
                "text_secondary": "#663399",
                "text_disabled": "#DDA0DD",
                "border": "#D8BFD8",
                "border_focus": "#8A2BE2",
                "success": "#32CD32",
                "success_dark": "#228B22",
                "warning": "#FFD700",
                "warning_dark": "#FFA500",
                "error": "#DC143C",
                "error_dark": "#B22222",
                "shadow": "rgba(138, 43, 226, 0.1)",
                "shadow_elevated": "rgba(138, 43, 226, 0.15)"
            },
            "midnight": {
                "background": "#0F0F23",
                "surface": "#1A1A2E",
                "surface_elevated": "#16213E",
                "primary": "#00D4AA",
                "primary_dark": "#00A693",
                "primary_light": "#4DFFDB",
                "secondary": "#FF6B6B",
                "secondary_dark": "#FF5252",
                "text_primary": "#E94560",
                "text_secondary": "#A0A0A0",
                "text_disabled": "#666666",
                "border": "#0E3460",
                "border_focus": "#00D4AA",
                "success": "#00FF7F",
                "success_dark": "#00FA54",
                "warning": "#FFD700",
                "warning_dark": "#FFA500",
                "error": "#FF6B6B",
                "error_dark": "#FF5252",
                "shadow": "rgba(0, 212, 170, 0.2)",
                "shadow_elevated": "rgba(0, 212, 170, 0.3)"
            },
            "neon_cyber": {
                "background": "#0A0A0A",
                "surface": "#1A0A1A",
                "surface_elevated": "#2A0A2A",
                "primary": "#FF00FF",
                "primary_dark": "#CC00CC",
                "primary_light": "#FF66FF",
                "secondary": "#00FFFF",
                "secondary_dark": "#00CCCC",
                "text_primary": "#00FF00",
                "text_secondary": "#FFFF00",
                "text_disabled": "#666666",
                "border": "#FF00FF",
                "border_focus": "#00FFFF",
                "success": "#00FF00",
                "success_dark": "#00CC00",
                "warning": "#FFFF00",
                "warning_dark": "#CCCC00",
                "error": "#FF0080",
                "error_dark": "#CC0066",
                "shadow": "rgba(255, 0, 255, 0.5)",
                "shadow_elevated": "rgba(0, 255, 255, 0.6)"
            },
            "volcanic_rage": {
                "background": "#1A0000",
                "surface": "#330000",
                "surface_elevated": "#4D0000",
                "primary": "#FF4500",
                "primary_dark": "#CC3300",
                "primary_light": "#FF6633",
                "secondary": "#FFD700",
                "secondary_dark": "#CC9900",
                "text_primary": "#FFAA00",
                "text_secondary": "#FF6600",
                "text_disabled": "#663300",
                "border": "#990000",
                "border_focus": "#FF4500",
                "success": "#FF8C00",
                "success_dark": "#CC6600",
                "warning": "#FF0000",
                "warning_dark": "#CC0000",
                "error": "#DC143C",
                "error_dark": "#B22222",
                "shadow": "rgba(255, 69, 0, 0.4)",
                "shadow_elevated": "rgba(255, 69, 0, 0.6)"
            },
            "arctic_storm": {
                "background": "#F0F8FF",
                "surface": "#E0F0FF",
                "surface_elevated": "#D0E8FF",
                "primary": "#4169E1",
                "primary_dark": "#0000CD",
                "primary_light": "#6495ED",
                "secondary": "#00CED1",
                "secondary_dark": "#008B8B",
                "text_primary": "#191970",
                "text_secondary": "#4682B4",
                "text_disabled": "#B0C4DE",
                "border": "#87CEEB",
                "border_focus": "#4169E1",
                "success": "#20B2AA",
                "success_dark": "#008080",
                "warning": "#FF8C00",
                "warning_dark": "#FF7F00",
                "error": "#DC143C",
                "error_dark": "#B22222",
                "shadow": "rgba(65, 105, 225, 0.3)",
                "shadow_elevated": "rgba(65, 105, 225, 0.4)"
            },
            "toxic_waste": {
                "background": "#0D1B0D",
                "surface": "#1A331A",
                "surface_elevated": "#264D26",
                "primary": "#39FF14",
                "primary_dark": "#32CD32",
                "primary_light": "#7FFF00",
                "secondary": "#ADFF2F",
                "secondary_dark": "#9ACD32",
                "text_primary": "#00FF00",
                "text_secondary": "#90EE90",
                "text_disabled": "#556B2F",
                "border": "#228B22",
                "border_focus": "#39FF14",
                "success": "#00FF7F",
                "success_dark": "#00FA54",
                "warning": "#FFFF00",
                "warning_dark": "#CCCC00",
                "error": "#FF6347",
                "error_dark": "#FF4500",
                "shadow": "rgba(57, 255, 20, 0.4)",
                "shadow_elevated": "rgba(57, 255, 20, 0.6)"
            },
            "galaxy_dream": {
                "background": "#0B0B2F",
                "surface": "#1A1A4D",
                "surface_elevated": "#2A2A6B",
                "primary": "#9932CC",
                "primary_dark": "#8A2BE2",
                "primary_light": "#BA55D3",
                "secondary": "#FF1493",
                "secondary_dark": "#DC143C",
                "text_primary": "#E6E6FA",
                "text_secondary": "#DDA0DD",
                "text_disabled": "#9370DB",
                "border": "#6A5ACD",
                "border_focus": "#9932CC",
                "success": "#FF69B4",
                "success_dark": "#FF1493",
                "warning": "#FFD700",
                "warning_dark": "#FFA500",
                "error": "#FF6347",
                "error_dark": "#FF4500",
                "shadow": "rgba(153, 50, 204, 0.5)",
                "shadow_elevated": "rgba(255, 20, 147, 0.4)"
            },
            "desert_mirage": {
                "background": "#FFF8DC",
                "surface": "#F5DEB3",
                "surface_elevated": "#DEB887",
                "primary": "#CD853F",
                "primary_dark": "#A0522D",
                "primary_light": "#D2B48C",
                "secondary": "#DAA520",
                "secondary_dark": "#B8860B",
                "text_primary": "#8B4513",
                "text_secondary": "#A0522D",
                "text_disabled": "#D2B48C",
                "border": "#F4A460",
                "border_focus": "#CD853F",
                "success": "#32CD32",
                "success_dark": "#228B22",
                "warning": "#FF8C00",
                "warning_dark": "#FF7F00",
                "error": "#DC143C",
                "error_dark": "#B22222",
                "shadow": "rgba(205, 133, 63, 0.3)",
                "shadow_elevated": "rgba(205, 133, 63, 0.4)"
            },
            "electric_blue": {
                "background": "#001122",
                "surface": "#002244",
                "surface_elevated": "#003366",
                "primary": "#0080FF",
                "primary_dark": "#0066CC",
                "primary_light": "#3399FF",
                "secondary": "#00BFFF",
                "secondary_dark": "#0099CC",
                "text_primary": "#87CEEB",
                "text_secondary": "#4682B4",
                "text_disabled": "#2F4F4F",
                "border": "#1E90FF",
                "border_focus": "#0080FF",
                "success": "#00CED1",
                "success_dark": "#008B8B",
                "warning": "#FFD700",
                "warning_dark": "#FFA500",
                "error": "#FF6347",
                "error_dark": "#FF4500",
                "shadow": "rgba(0, 128, 255, 0.4)",
                "shadow_elevated": "rgba(0, 191, 255, 0.5)"
            },
            "cherry_bomb": {
                "background": "#2D0A0A",
                "surface": "#4D1A1A",
                "surface_elevated": "#6D2A2A",
                "primary": "#DC143C",
                "primary_dark": "#B22222",
                "primary_light": "#F08080",
                "secondary": "#FF69B4",
                "secondary_dark": "#FF1493",
                "text_primary": "#FFB6C1",
                "text_secondary": "#FFC0CB",
                "text_disabled": "#8B4B5C",
                "border": "#CD5C5C",
                "border_focus": "#DC143C",
                "success": "#FF69B4",
                "success_dark": "#FF1493",
                "warning": "#FFD700",
                "warning_dark": "#FFA500",
                "error": "#FF0000",
                "error_dark": "#CC0000",
                "shadow": "rgba(220, 20, 60, 0.4)",
                "shadow_elevated": "rgba(255, 105, 180, 0.5)"
            },
            "matrix_code": {
                "background": "#000000",
                "surface": "#001100",
                "surface_elevated": "#002200",
                "primary": "#00FF41",
                "primary_dark": "#00CC33",
                "primary_light": "#33FF66",
                "secondary": "#39FF14",
                "secondary_dark": "#32CD32",
                "text_primary": "#00FF00",
                "text_secondary": "#90EE90",
                "text_disabled": "#006600",
                "border": "#008000",
                "border_focus": "#00FF41",
                "success": "#00FF7F",
                "success_dark": "#00FA54",
                "warning": "#FFFF00",
                "warning_dark": "#CCCC00",
                "error": "#FF4500",
                "error_dark": "#CC3300",
                "shadow": "rgba(0, 255, 65, 0.6)",
                "shadow_elevated": "rgba(57, 255, 20, 0.7)"
            },
            "royal_gold": {
                "background": "#1A1A0D",
                "surface": "#2D2D1A",
                "surface_elevated": "#404026",
                "primary": "#FFD700",
                "primary_dark": "#DAA520",
                "primary_light": "#FFFF99",
                "secondary": "#FFA500",
                "secondary_dark": "#FF8C00",
                "text_primary": "#FFFACD",
                "text_secondary": "#F0E68C",
                "text_disabled": "#BDB76B",
                "border": "#B8860B",
                "border_focus": "#FFD700",
                "success": "#ADFF2F",
                "success_dark": "#9ACD32",
                "warning": "#FF8C00",
                "warning_dark": "#FF7F00",
                "error": "#DC143C",
                "error_dark": "#B22222",
                "shadow": "rgba(255, 215, 0, 0.4)",
                "shadow_elevated": "rgba(255, 165, 0, 0.5)"
            }
        }
    
    def get_stylesheet(self, theme_name: str = None) -> str:
        """Generera komplett stylesheet för tema"""
        if theme_name:
            self.current_theme = theme_name
        
        theme = self.themes.get(self.current_theme, self.themes["light"])
        
        return f"""
        /* === GLOBALA INSTÄLLNINGAR === */
        QMainWindow {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 20px;
        }}
        
        /* === CUSTOM TITLE BAR === */
        
        QWidget#titleBar {{
            background-color: {theme['background']};
            border: none;
            min-height: 45px;
            max-height: 45px;
        }}
        
        
        /* Modern window control buttons - matching menu button style */
        QPushButton#modernWindowControlButton {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 6px;
            font-size: 10pt;
            font-weight: 500;
            padding: 4px 8px;
            margin: 2px;
            min-width: 28px;
            min-height: 18px;
        }}
        
        QPushButton#modernWindowControlButton:hover {{
            background-color: {theme['primary_light']};
            color: white;
            border-color: {theme['primary_light']};
        }}
        
        QPushButton#modernWindowControlButton:pressed {{
            background-color: {theme['primary']};
            color: white;
            border-color: {theme['primary']};
        }}
        
        /* Special styling for close button */
        QPushButton#modernWindowControlCloseButton {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 6px;
            font-size: 10pt;
            font-weight: 500;
            padding: 4px 8px;
            margin: 2px;
            min-width: 28px;
            min-height: 18px;
        }}
        
        QPushButton#modernWindowControlCloseButton:hover {{
            background-color: #e74c3c;
            color: white;
            border-color: #e74c3c;
        }}
        
        QPushButton#modernWindowControlCloseButton:pressed {{
            background-color: #c0392b;
            color: white;
            border-color: #c0392b;
        }}
        
        QLabel#titleLabel {{
            color: {theme['text_primary']};
            font-size: 12pt;
            font-weight: 500;
            padding-left: 10px;
        }}
        
        QLabel#titleLabelSmall {{
            color: {theme['text_secondary']};
            font-size: 8pt;
            font-weight: 400;
            padding-right: 5px;
            opacity: 0.7;
        }}
        
        
        /* HELT NYA MENU BUTTONS - INGA KONFLIKTER */
        QPushButton#newMenuButton {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 12px;
            padding: 10px 18px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11pt;
            font-weight: 600;
            min-width: 90px;
            min-height: 36px;
        }}
        
        QPushButton#newMenuButton:hover {{
            background-color: {theme['primary_light']};
            color: white;
            border-color: {theme['primary_light']};
        }}
        
        QPushButton#newMenuButton:pressed {{
            background-color: {theme['primary']};
            color: white;
            border-color: {theme['primary']};
        }}
        
        QPushButton#newMenuButton::menu-indicator {{
            width: 0px;
            height: 0px;
        }}
        
        /* RADICAL NEW MENU SYSTEM - COMPLETELY FRESH START */
        QPushButton#radicalNewMenuButton {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 12px;
            padding: 12px 20px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12pt;
            font-weight: 700;
            min-width: 100px;
            min-height: 40px;
        }}
        
        QPushButton#radicalNewMenuButton:hover {{
            background-color: {theme['primary_light']};
            color: white;
            border-color: {theme['primary_light']};
        }}
        
        QPushButton#radicalNewMenuButton:pressed {{
            background-color: {theme['primary']};
            color: white;
            border-color: {theme['primary']};
        }}
        
        /* RADICAL NEW POPUP MENUS */
        QMenu#radicalNewPopupMenu {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 3px solid {theme['border']};
            border-radius: 15px;
            padding: 4px 0;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12pt;
            /* Automatisk breddanpassning - bredden anpassas efter längsta textraden */
        }}
        
        QMenu#radicalNewPopupMenu::item {{
            background-color: transparent;
            color: {theme['text_primary']};
            padding: 8px 12px;
            border: none;
            border-radius: 10px;
            margin: 2px 6px;
            font-weight: 600;
        }}
        
        QMenu#radicalNewPopupMenu::item:hover {{
            background-color: {theme['primary_light']};
            color: white;
        }}
        
        QMenu#radicalNewPopupMenu::item:selected {{
            background-color: {theme['primary']};
            color: white;
        }}
        
        QMenu#radicalNewPopupMenu::separator {{
            height: 2px;
            background-color: {theme['border']};
            margin: 6px 12px;
            border-radius: 1px;
        }}
        
        QWidget {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }}
        
        /* Rundare hörn för top-level widgets (fönster) */
        QWidget[windowType="window"] {{
            border-radius: 12px;
        }}
        
        /* Specifika fönsterklasser med rundare hörn */
        LoginWindow, HomeWindow, SettingsWindow, AddSystemWindow, 
        MySystemsWindow, OrdersWindow, PermissionsWindow, UsersWindow {{
            border-radius: 12px;
        }}
        
        /* === KNAPPAR - GLOBALT SYSTEM === */
        
        /* Standard knappar */
        QPushButton {{
            background-color: {theme['primary']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 22px;
            outline: none;
        }}
        
        QPushButton:hover {{
            background-color: {theme['primary_dark']};
        }}
        
        QPushButton:pressed {{
            background-color: {theme['primary_dark']};
        }}
        
        QPushButton:disabled {{
            background-color: {theme['border']};
            color: {theme['text_disabled']};
        }}
        
        /* Knappstorlekar och typer */
        QPushButton[kb_button_type="primary"] {{
            background-color: {theme['primary']};
            color: white;
            font-weight: 600;
            min-height: 32px;
            min-width: 80px;
            padding: 8px 16px;
        }}
        
        QPushButton[kb_button_type="primary"]:hover {{
            background-color: {theme['primary_dark']};
        }}
        
        QPushButton[kb_button_type="secondary"] {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            font-weight: 500;
            min-height: 32px;
            min-width: 80px;
            padding: 8px 16px;
        }}
        
        QPushButton[kb_button_type="secondary"]:hover {{
            background-color: {theme['surface_elevated']};
            border-color: {theme['primary']};
        }}
        
        QPushButton[kb_button_type="small"] {{
            background-color: {theme['primary']};
            color: white;
            font-size: 9pt;
            font-weight: 500;
            padding: 2px 6px;
            min-width: 60px;
            max-width: 60px;
            min-height: 20px;
            max-height: 20px;
            border-radius: 4px;
        }}
        
        QPushButton[kb_button_type="small"]:hover {{
            background-color: {theme['primary_dark']};
        }}
        
        QPushButton[kb_button_type="large"] {{
            background-color: {theme['primary']};
            color: white;
            font-size: 12pt;
            font-weight: 600;
            min-height: 60px;
            min-width: 120px;
            padding: 12px 24px;
        }}
        
        QPushButton[kb_button_type="large"]:hover {{
            background-color: {theme['primary_dark']};
        }}
        
        QPushButton[kb_button_type="success"] {{
            background-color: {theme['success']};
            color: white;
            font-weight: 600;
        }}
        
        QPushButton[kb_button_type="success"]:hover {{
            background-color: {theme['success_dark']};
        }}
        
        QPushButton[kb_button_type="warning"] {{
            background-color: {theme['warning']};
            color: white;
            font-weight: 600;
        }}
        
        QPushButton[kb_button_type="warning"]:hover {{
            background-color: {theme['warning_dark']};
        }}
        
        QPushButton[kb_button_type="danger"] {{
            background-color: {theme['error']};
            color: white;
            font-weight: 600;
            min-width: 100px;
        }}
        
        QPushButton[kb_button_type="danger"]:hover {{
            background-color: {theme['error_dark']};
        }}
        
        /* === TOPMENYKNAPPAR - GLOBALT SYSTEM === */
        
        QPushButton#EXTREME_NEW_MENU_BUTTON {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 6px;
            padding: 3px 10px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 9pt;
            font-weight: 400;
            min-width: 50px;
            min-height: 18px;
        }}
        
        QPushButton#EXTREME_NEW_MENU_BUTTON:hover {{
            background-color: {theme['primary_light']};
            color: white;
            border-color: {theme['primary_light']};
        }}
        
        QPushButton#EXTREME_NEW_MENU_BUTTON:pressed {{
            background-color: {theme['primary']};
            color: white;
            border-color: {theme['primary']};
        }}
        
        /* Backup styling för modernTopMenuButton (om det används) */
        QPushButton#modernTopMenuButton {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 6px;
            padding: 3px 10px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 9pt;
            font-weight: 400;
            min-width: 50px;
            min-height: 18px;
        }}
        
        QPushButton#modernTopMenuButton:hover {{
            background-color: {theme['primary_light']};
            color: white;
            border-color: {theme['primary_light']};
        }}
        
        QPushButton#modernTopMenuButton:pressed {{
            background-color: {theme['primary']};
            color: white;
            border-color: {theme['primary']};
        }}
        
        /* === LOGO PLACEHOLDER - GLOBALT SYSTEM === */
        
        QLabel#logoPlaceholder {{
            border: 2px dashed {theme['border']};
            color: {theme['text_disabled']};
            background-color: {theme['surface_elevated']};
            border-radius: 8px;
            padding: 20px;
            font-size: 14pt;
            font-weight: 500;
        }}
        
        /* === PROFILBILD - GLOBALT SYSTEM === */
        
        QLabel#profilePicture {{
            border: 1px solid {theme['border']};
            border-radius: 32px;
            background-color: {theme['surface_elevated']};
            color: {theme['text_disabled']};
            font-size: 20px;
        }}
        
        /* === TEXTFÄLT - GLOBALT SYSTEM === */
        
        QLineEdit {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 400;
            min-height: 45px;
        }}
        
        /* === TEXTOMRÅDEN - GLOBALT SYSTEM === */
        
        QTextEdit, QPlainTextEdit {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 400;
            selection-background-color: {theme['primary_light']};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {theme['border_focus']};
            outline: none;
        }}
        
        QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
            border-color: {theme['primary_light']};
        }}
        
        QLineEdit[kb_field_type="search"] {{
            background-color: {theme['surface_elevated']};
            border-radius: 20px;
            padding-left: 16px;
        }}
        
        QLineEdit[kb_field_type="readonly"] {{
            background-color: {theme['surface_elevated']};
            color: {theme['text_secondary']};
            border-style: dashed;
        }}
        
        QLineEdit[kb_field_type="error"] {{
            border-color: {theme['error']};
            background-color: rgba(244, 67, 54, 0.1);
        }}
        
        /* === DROPDOWN-MENYER OCH DATUM - GLOBALT SYSTEM === */
        
        QComboBox {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 400;
            min-height: 18px;
            max-height: 18px;
        }}
        
        QComboBox:hover {{
            border-color: {theme['primary_light']};
            background-color: {theme['surface_elevated']};
        }}
        
        QComboBox:focus {{
            border-color: {theme['border_focus']};
            outline: none;
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 0px;
            height: 0px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            width: 0px;
            height: 0px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 8px;
            selection-background-color: {theme['primary_light']};
            selection-color: white;
        }}
        
        QDateEdit {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 400;
            min-height: 18px;
            max-height: 18px;
        }}
        
        QDateEdit:hover {{
            border-color: {theme['primary_light']};
            background-color: {theme['surface_elevated']};
        }}
        
        QDateEdit:focus {{
            border-color: {theme['border_focus']};
            outline: none;
        }}
        
        QDateEdit::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid {theme['border']};
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            background-color: {theme['surface_elevated']};
        }}
        
        QDateEdit::drop-down:hover {{
            background-color: {theme['primary_light']};
        }}
        
        QDateEdit::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {theme['text_secondary']};
            width: 0px;
            height: 0px;
        }}
        
        QDateEdit::down-arrow:hover {{
            border-top-color: white;
        }}
        
        /* Kalender popup styling */
        QCalendarWidget {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 12px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        
        QCalendarWidget QToolButton {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 6px;
            padding: 5px;
            margin: 2px;
        }}
        
        QCalendarWidget QToolButton:hover {{
            background-color: {theme['primary_light']};
            color: white;
        }}
        
        QCalendarWidget QMenu {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 8px;
        }}
        
        QCalendarWidget QSpinBox {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            padding: 2px;
        }}
        
        QCalendarWidget QAbstractItemView {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: none;
            selection-background-color: {theme['primary']};
            selection-color: white;
        }}
        
        QLineEdit[kb_field_type="success"] {{
            border-color: {theme['success']};
            background-color: rgba(76, 175, 80, 0.1);
        }}
        
        /* === LABELS - GLOBALT SYSTEM === */
        
        QLabel {{
            color: {theme['text_primary']};
            font-size: 10pt;
        }}
        
        QLabel[kb_label_type="title"] {{
            font-size: 18pt;
            font-weight: bold;
            color: {theme['primary']};
            margin: 10px 0;
        }}
        
        QLabel[kb_label_type="subtitle"] {{
            font-size: 12pt;
            font-weight: 600;
            color: {theme['text_secondary']};
            margin: 5px 0;
        }}
        
        QLabel[kb_label_type="caption"] {{
            font-size: 9pt;
            color: {theme['text_secondary']};
        }}
        
        QLabel[kb_label_type="error"] {{
            color: {theme['error']};
            font-weight: 500;
        }}
        
        QLabel[kb_label_type="success"] {{
            color: {theme['success']};
            font-weight: 500;
        }}
        
        QLabel[kb_label_type="warning"] {{
            color: {theme['warning']};
            font-weight: 500;
        }}
        
        /* === COMBOBOX - GLOBALT SYSTEM === */
        
        QComboBox {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 400;
            min-width: 100px;
            min-height: 18px;
        }}
        
        QComboBox:hover {{
            border-color: {theme['primary_light']};
            background-color: {theme['surface_elevated']};
        }}
        
        QComboBox:focus {{
            border-color: {theme['border_focus']};
            outline: none;
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
            background-color: transparent;
        }}
        
        QComboBox::drop-down:hover {{
            background-color: {theme['primary_light']};
            border-radius: 4px;
        }}
        
        QComboBox::down-arrow {{
            width: 0px;
            height: 0px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 8px;
            selection-background-color: {theme['primary']};
            selection-color: white;
            outline: none;
            padding: 4px;
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            border-radius: 4px;
            margin: 2px;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: {theme['primary_light']};
            color: white;
        }}
        
        QComboBox QAbstractItemView::item:selected {{
            background-color: {theme['primary']};
            color: white;
        }}
        
        /* === SPINBOX - GLOBALT SYSTEM === */
        
        QSpinBox {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 400;
            min-height: 18px;
        }}
        
        QSpinBox:focus {{
            border-color: {theme['border_focus']};
            outline: none;
        }}
        
        QSpinBox:hover {{
            border-color: {theme['primary_light']};
        }}
        
        QSpinBox::up-button {{
            background-color: {theme['surface_elevated']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            width: 25px;
            height: 20px;
            subcontrol-origin: border;
            subcontrol-position: top right;
            font-size: 12px;
            font-weight: bold;
            color: {theme['text_primary']};
        }}
        
        QSpinBox::down-button {{
            background-color: {theme['surface_elevated']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            width: 25px;
            height: 20px;
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            font-size: 12px;
            font-weight: bold;
            color: {theme['text_primary']};
        }}
        
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {theme['primary_light']};
            color: white;
        }}
        
        QSpinBox::up-arrow {{
            width: 0px;
            height: 0px;
        }}
        
        QSpinBox::down-arrow {{
            width: 0px;
            height: 0px;
        }}
        
        
        /* HELT NYA DROPDOWN MENUS - INGA KONFLIKTER */
        QMenu#newDropdownMenu {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 12px;
            padding: 4px 0;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11pt;
            /* Automatisk breddanpassning - bredden anpassas efter längsta textraden */
        }}
        
        QMenu#newDropdownMenu::item {{
            background-color: transparent;
            color: {theme['text_primary']};
            padding: 8px 12px;
            border: none;
            border-radius: 8px;
            margin: 2px 6px;
            font-weight: 500;
        }}
        
        QMenu#newDropdownMenu::item:hover {{
            background-color: {theme['primary_light']};
            color: white;
        }}
        
        QMenu#newDropdownMenu::item:selected {{
            background-color: {theme['primary']};
            color: white;
        }}
        
        QMenu#newDropdownMenu::separator {{
            height: 1px;
            background-color: {theme['border']};
            margin: 4px 8px;
            border-radius: 1px;
        }}
        
        /* FALLBACK STYLING FÖR ALLA ANDRA QMENU (högerklick etc) */
        QMenu {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 12px;
            padding: 4px 0;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11pt;
            /* Automatisk breddanpassning - bredden anpassas efter längsta textraden */
        }}
        
        QMenu::item {{
            background-color: transparent;
            color: {theme['text_primary']};
            padding: 8px 12px;
            border: none;
            border-radius: 8px;
            margin: 2px 6px;
            font-weight: 500;
        }}
        
        QMenu::item:hover {{
            background-color: {theme['primary_light']};
            color: white;
        }}
        
        QMenu::item:selected {{
            background-color: {theme['primary']};
            color: white;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {theme['border']};
            margin: 4px 8px;
            border-radius: 1px;
        }}
        
        /* === GLOBALA POPUP & DIALOG STILAR === */
        
        QMessageBox {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            border: none;
            border-radius: 12px;
        }}
        
        QMessageBox QLabel {{
            color: {theme['text_primary']};
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        
        QMessageBox QPushButton {{
            background-color: {theme['primary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 10pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 500;
            min-width: 80px;
        }}
        
        QMessageBox QPushButton:hover {{
            background-color: {theme['primary_light']};
        }}
        
        QFileDialog {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            border-radius: 12px;
        }}
        
        QInputDialog {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            border-radius: 12px;
        }}
        
        /* === STATUS BAR === */
        
        QStatusBar {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            border: none;
            font-size: 10pt;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        
        QLabel#statusKeyBuddyName {{
            color: {theme['text_secondary']};
            font-size: 9pt;
            font-weight: 500;
            padding-right: 15px;
        }}
        
        /* === TABS - GLOBALT SYSTEM === */
        
        QTabWidget::pane {{
            border: 2px solid {theme['border']};
            border-radius: 8px;
            background-color: {theme['surface']};
            padding: 8px;
        }}
        
        QTabBar::tab {{
            background-color: {theme['surface_elevated']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            padding: 12px 24px;
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 500;
            min-width: 100px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {theme['primary']};
            color: white;
            border-color: {theme['primary']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {theme['primary_light']};
            border-color: {theme['primary_light']};
        }}
        
        QTabBar::tab:focus {{
            outline: none;
        }}
        
        /* === GRUPPBOXAR === */
        
        QGroupBox {{
            font-weight: 600;
            border: 2px solid {theme['border']};
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 15px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px;
            color: {theme['text_primary']};
            background-color: {theme['background']};
        }}
        
        /* === TABELLER === */
        
        QTableWidget {{
            background-color: {theme['surface']};
            color: {theme['text_primary']};
            gridline-color: {theme['border']};
            border: 1px solid {theme['border']};
            selection-background-color: {theme['primary']};
            outline: none;
            border-radius: 6px;
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {theme['border']};
            outline: none;
            border: none;
        }}
        
        QTableWidget::item:hover {{
            background-color: {theme['primary_light']};
        }}
        
        QTableWidget::item:selected {{
            background-color: {theme['primary']};
            color: white;
        }}
        
        QHeaderView::section {{
            background-color: {theme['primary']};
            color: white;
            padding: 12px;
            border: none;
            font-weight: bold;
        }}
        
        /* Fix för det vita hörnet - tabellens intersection */
        QTableWidget QTableCornerButton::section {{
            background-color: {theme['primary']};
            border: none;
        }}
        
        QTableCornerButton::section {{
            background-color: {theme['primary']};
            border: none;
        }}
        
        /* === SCROLLBARS === */
        
        QScrollBar:vertical {{
            background-color: transparent;
            width: 12px;
            border: none;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {theme['border']};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {theme['primary']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
            height: 0px;
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        
        
        /* === DIALOGER === */
        
        QDialog {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            border-radius: 12px;
        }}
        
        QMessageBox QPushButton, QDialogButtonBox QPushButton {{
            font-size: 10px;
            padding: 4px 8px;
            min-width: 60px;
            min-height: 24px;
            border-radius: 4px;
        }}
        
        /* === PROGRESS BARS === */
        
        QProgressBar {{
            border: 2px solid {theme['border']};
            border-radius: 8px;
            text-align: center;
            background-color: {theme['surface']};
            font-weight: 500;
        }}
        
        QProgressBar::chunk {{
            background-color: {theme['primary']};
            border-radius: 6px;
        }}
        
        /* === CHECKBOXES OCH RADIO BUTTONS === */
        
        QCheckBox, QRadioButton {{
            color: {theme['text_primary']};
            spacing: 8px;
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 2px solid {theme['border']};
            border-radius: 3px;
            background-color: {theme['surface']};
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {theme['primary']};
            border-color: {theme['primary']};
        }}
        
        /* === TOOLTIPS === */
        
        QToolTip {{
            background-color: {theme['surface_elevated']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            padding: 6px;
            font-size: 9pt;
        }}
        
        /* === STATUS BAR === */
        
        QStatusBar {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            border: none;
        }}
        
        /* === DASHBOARD-KORT - GLOBALT SYSTEM === */
        
        QFrame#dashboardCard {{
            border: 1px solid {theme['surface']};
            border-radius: 12px;
            background-color: {theme['surface']};
            margin: 5px;
        }}
        
        QFrame#dashboardCard:hover {{
            background-color: {theme['surface_elevated']};
            border-color: {theme['primary_light']};
        }}
        
        QFrame#dashboardCard:hover QLabel#dashboardIcon {{
            background-color: {theme['surface_elevated']};
        }}
        
        QFrame#dashboardCard:hover QLabel#dashboardTitle {{
            background-color: {theme['surface_elevated']};
        }}
        
        QFrame#dashboardCard:hover QLabel#dashboardDescription {{
            background-color: {theme['surface_elevated']};
        }}
        
        QLabel#dashboardIcon {{
            font-size: 32px;
            color: {theme['primary']};
            border: none;
            background-color: {theme['surface']};
            border-radius: 8px;
            padding: 5px;
        }}
        
        QLabel#dashboardTitle {{
            font-size: 14pt;
            font-weight: bold;
            color: {theme['text_primary']};
            border: none;
            background-color: {theme['surface']};
            border-radius: 8px;
            padding: 5px;
        }}
        
        QLabel#dashboardDescription {{
            font-size: 10pt;
            color: {theme['text_secondary']};
            border: none;
            background-color: {theme['surface']};
            border-radius: 8px;
            padding: 5px;
        }}
        """
    
    def get_theme_colors(self, theme_name: str = None) -> Dict[str, str]:
        """Hämta temafärger som dictionary"""
        if theme_name:
            self.current_theme = theme_name
        return self.themes.get(self.current_theme, self.themes["light"])
    
    def set_theme(self, theme_name: str):
        """Sätt aktuellt tema"""
        if theme_name in self.themes:
            self.current_theme = theme_name

# Hjälpfunktioner för enkel användning
def create_button(text: str, button_type: ButtonType = ButtonType.PRIMARY, parent=None) -> KeyBuddyButton:
    """Skapa en standardiserad knapp"""
    return KeyBuddyButton(text, button_type, parent)

def create_field(field_type: FieldType = FieldType.STANDARD, placeholder: str = "", parent=None) -> KeyBuddyLineEdit:
    """Skapa ett standardiserat textfält"""
    return KeyBuddyLineEdit(field_type, placeholder, parent)

def create_label(text: str, label_type: LabelType = LabelType.STANDARD, parent=None) -> KeyBuddyLabel:
    """Skapa en standardiserad label"""
    return KeyBuddyLabel(text, label_type, parent)

def create_combo(parent=None) -> KeyBuddyComboBox:
    """Skapa en standardiserad combobox"""
    return KeyBuddyComboBox(parent)

def create_group(title: str, parent=None) -> KeyBuddyGroupBox:
    """Skapa en standardiserad gruppbox"""
    return KeyBuddyGroupBox(title, parent)

# Bakåtkompatibilitet
AnimatedButton = KeyBuddyButton  # För befintlig kod som använder AnimatedButton
