import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QFontDatabase, QPainterPath
from PyQt5.QtCore import Qt, pyqtSignal
import ctypes
from ctypes import c_int, byref, sizeof

# Font paths - NOTE: Adjust these to match your local paths
CUSTOM_FONT_PATH_POPSTAR = r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage\POPSTAR.TTF"
CUSTOM_FONT_PATH_EQUINOX = r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage\Groningen-Regular.ttf"

# ===== OPERATION PROFILES DEFINITIONS =====
OPERATION_MODES = {
    'race': {
        'name': 'RACE MODE',
        'color': '#FF3030',
        'speed_multiplier': 1.2,
        'turn_aggression': 1.4,
        'search_aggression': 1.5,
        'description': 'Maximum speed, aggressive turns'
    },
    'precision': {
        'name': 'PRECISION',
        'color': '#1E64FF',
        'speed_multiplier': 0.7,
        'turn_aggression': 0.9,
        'search_aggression': 1.0,
        'description': 'Slower, smoother tracking'
    },
    'powersave': {
        'name': 'POWER SAVER',
        'color': '#FFD700',
        'speed_multiplier': 0.5,
        'turn_aggression': 0.8,
        'search_aggression': 0.9,
        'description': 'Optimized for battery life'
    },
    'learning': {
        'name': 'LEARNING',
        'color': '#00FF00',
        'speed_multiplier': 0.6,
        'turn_aggression': 1.0,
        'search_aggression': 1.1,
        'description': 'Logs data for analysis'
    }
}


class OperationProfilesWidget(QWidget):
    """
    Compact widget for switching between 4 operation modes
    Fits 4 buttons in 2x2 grid layout
    Emits signal when mode changes
    Applies speed multipliers and sends updated speeds to Arduino
    """
    
    mode_changed = pyqtSignal(str)  # Emits the selected mode key
    
    def __init__(self, parent=None, serial_manager=None, motor_gauge=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Font loading
        font_id_popstar = QFontDatabase.addApplicationFont(CUSTOM_FONT_PATH_POPSTAR)
        self.font_popstar = QFontDatabase.applicationFontFamilies(font_id_popstar)[0] if font_id_popstar != -1 else "Segoe UI"
        
        self.setWindowTitle("Operation Profiles")
        self.setGeometry(100, 100, 350, 150)
        
        self.current_mode = 'precision'  # Default mode
        self.mode_buttons = {}
        
        # Serial and motor gauge references
        self.serial_manager = serial_manager
        self.motor_gauge = motor_gauge
        
        self.setup_ui()
        self.apply_windows_blur()
    
    def apply_windows_blur(self):
        """Apply Windows Acrylic/Blur effect to window background"""
        try:
            hwnd = int(self.winId())
            class ACCENTPOLICY(ctypes.Structure):
                _fields_ = [("AccentState", c_int), ("AccentFlags", c_int), ("GradientColor", c_int), ("AnimationId", c_int)]
            class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
                _fields_ = [("Attrib", c_int), ("Data", ctypes.POINTER(c_int)), ("SizeOfData", c_int)]
            accent = ACCENTPOLICY()
            accent.AccentState = 3
            accent.GradientColor = 0x40000000
            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attrib = 19
            data.SizeOfData = sizeof(accent)
            data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(c_int))
            ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, byref(data))
        except: pass
    
    def paintEvent(self, event):
        """Draw chamfered frame with glowing red outline"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        chamfer = 10
        w, h = self.width(), self.height()
        
        # Chamfered background path
        path = QPainterPath()
        path.moveTo(chamfer, 0)
        path.lineTo(w - chamfer, 0)
        path.lineTo(w, chamfer)
        path.lineTo(w, h - chamfer)
        path.lineTo(w - chamfer, h)
        path.lineTo(chamfer, h)
        path.lineTo(0, h - chamfer)
        path.lineTo(0, chamfer)
        path.lineTo(chamfer, 0)
        painter.fillPath(path, QColor(18, 18, 18, 90))
        
        # Glowing red outline segments
        base_red = QColor(255, 30, 30)
        
        tr_path = QPainterPath()
        tr_path.moveTo(w * 0.4, 0)
        tr_path.lineTo(w - chamfer, 0)
        tr_path.lineTo(w, chamfer)
        tr_path.lineTo(w, h * 0.25)
        
        bl_path = QPainterPath()
        bl_path.moveTo(w * 0.6, h)
        bl_path.lineTo(chamfer, h)
        bl_path.lineTo(0, h - chamfer)
        bl_path.lineTo(0, h * 0.75)
        
        for i in range(3, 0, -1):
            painter.setPen(QPen(QColor(255, 30, 30, int(25/i)), 2 + i*1.5))
            painter.drawPath(tr_path)
            painter.drawPath(bl_path)
        
        painter.setPen(QPen(base_red, 2))
        painter.drawPath(tr_path)
        painter.drawPath(bl_path)
        painter.end()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 5, 8, 5)
        main_layout.setSpacing(5)
        
        # Title
        title = QLabel("OPERATION MODES")
        title.setFont(QFont(self.font_popstar, 9, QFont.Bold))
        title.setStyleSheet("color: #FF3030; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # 2x2 Grid of Mode Buttons
        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(8)
        
        modes_list = ['race', 'precision', 'powersave', 'learning']
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        
        for mode_key, position in zip(modes_list, positions):
            mode_info = OPERATION_MODES[mode_key]
            btn = QPushButton(mode_info['name'])
            btn.setFont(QFont(self.font_popstar, 8, QFont.Bold))
            btn.setMinimumSize(80, 40)
            btn.setCheckable(True)
            
            # Set initial checked state
            if mode_key == self.current_mode:
                btn.setChecked(True)
            
            # Store reference
            self.mode_buttons[mode_key] = btn
            
            # Set styling
            self.update_button_style(btn, mode_key, mode_key == self.current_mode)
            
            # Connect click event
            btn.clicked.connect(lambda checked, mk=mode_key: self.set_mode(mk))
            
            buttons_layout.addWidget(btn, position[0], position[1])
        
        main_layout.addLayout(buttons_layout)
    
    def update_button_style(self, button, mode_key, is_selected):
        """Update button styling based on selection state"""
        mode_info = OPERATION_MODES[mode_key]
        color = mode_info['color']
        
        if is_selected:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({self.hex_to_rgb(color)[0]}, {self.hex_to_rgb(color)[1]}, {self.hex_to_rgb(color)[2]}, 220);
                    color: white;
                    border: 2px solid {color};
                    border-radius: 5px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: rgba({self.hex_to_rgb(color)[0]}, {self.hex_to_rgb(color)[1]}, {self.hex_to_rgb(color)[2]}, 240);
                }}
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(60, 60, 60, 180);
                    color: #888888;
                    border: 1px solid #555555;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: rgba(80, 80, 80, 200);
                    color: white;
                }}
            """)
    
    def set_mode(self, mode_key):
        """Switch to a new operation mode and apply speed multipliers"""
        # Uncheck all buttons
        for mk, btn in self.mode_buttons.items():
            btn.setChecked(mk == mode_key)
            self.update_button_style(btn, mk, mk == mode_key)
        
        # Update current mode
        self.current_mode = mode_key
        mode_info = OPERATION_MODES[mode_key]
        speed_multiplier = mode_info['speed_multiplier']
        
        # Apply speed multiplier to current motor speeds and send to Arduino
        if self.motor_gauge and self.serial_manager and self.serial_manager.is_connected:
            # Get current slider values
            speed_a6 = self.motor_gauge.slider_a6.value()
            speed_a7 = self.motor_gauge.slider_a7.value()
            
            # Apply multiplier
            new_speed_a6 = int(speed_a6 * speed_multiplier)
            new_speed_a7 = int(speed_a7 * speed_multiplier)
            
            # Clamp to 0-100 range
            new_speed_a6 = max(0, min(100, new_speed_a6))
            new_speed_a7 = max(0, min(100, new_speed_a7))
            
            # Send commands to Arduino
            success_left, msg_left = self.serial_manager.sendSpeedCommand(new_speed_a6, motor='left')
            success_right, msg_right = self.serial_manager.sendSpeedCommand(new_speed_a7, motor='right')
            
            # Update GUI sliders to reflect new speeds
            self.motor_gauge.slider_a6.blockSignals(True)
            self.motor_gauge.slider_a7.blockSignals(True)
            self.motor_gauge.slider_a6.setValue(new_speed_a6)
            self.motor_gauge.slider_a7.setValue(new_speed_a7)
            self.motor_gauge.slider_a6.blockSignals(False)
            self.motor_gauge.slider_a7.blockSignals(False)
            
            print(f"[Operation Profiles] Mode: {mode_info['name']} | Multiplier: {speed_multiplier}x")
            print(f"[Operation Profiles] New speeds - A6: {new_speed_a6}%, A7: {new_speed_a7}%")
        else:
            print(f"[Operation Profiles] Mode changed to: {mode_info['name']} (No motor connection)")
        
        # Emit signal
        self.mode_changed.emit(mode_key)
    
    def get_current_mode(self):
        """Return current mode key"""
        return self.current_mode
    
    def get_mode_info(self, mode_key=None):
        """Get detailed info about a mode"""
        if mode_key is None:
            mode_key = self.current_mode
        return OPERATION_MODES.get(mode_key)
    
    def set_serial_manager(self, serial_manager):
        """Allow external assignment of serial manager"""
        self.serial_manager = serial_manager
    
    def set_motor_gauge(self, motor_gauge):
        """Allow external assignment of motor gauge reference"""
        self.motor_gauge = motor_gauge
    
    @staticmethod
    def hex_to_rgb(hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPos() - self.drag_pos)


class ModeDisplayWidget(QWidget):
    """
    Display widget showing current operation mode details
    Shows mode name, parameters, and description
    Fits in middle column (200px height)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Font loading
        font_id_popstar = QFontDatabase.addApplicationFont(CUSTOM_FONT_PATH_POPSTAR)
        self.font_popstar = QFontDatabase.applicationFontFamilies(font_id_popstar)[0] if font_id_popstar != -1 else "Segoe UI"
        
        self.setWindowTitle("Mode Display")
        self.setGeometry(100, 100, 610, 200)
        
        self.current_mode = 'precision'
        self.current_color = '#1E64FF'
        
        self.setup_ui()
        self.apply_windows_blur()
    
    def apply_windows_blur(self):
        """Apply Windows Acrylic/Blur effect to window background"""
        try:
            hwnd = int(self.winId())
            class ACCENTPOLICY(ctypes.Structure):
                _fields_ = [("AccentState", c_int), ("AccentFlags", c_int), ("GradientColor", c_int), ("AnimationId", c_int)]
            class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
                _fields_ = [("Attrib", c_int), ("Data", ctypes.POINTER(c_int)), ("SizeOfData", c_int)]
            accent = ACCENTPOLICY()
            accent.AccentState = 3
            accent.GradientColor = 0x40000000
            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attrib = 19
            data.SizeOfData = sizeof(accent)
            data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(c_int))
            ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, byref(data))
        except: pass
    
    def paintEvent(self, event):
        """Draw chamfered frame with dynamic color outline"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        chamfer = 15
        w, h = self.width(), self.height()
        
        # Chamfered background path
        path = QPainterPath()
        path.moveTo(chamfer, 0)
        path.lineTo(w - chamfer, 0)
        path.lineTo(w, chamfer)
        path.lineTo(w, h - chamfer)
        path.lineTo(w - chamfer, h)
        path.lineTo(chamfer, h)
        path.lineTo(0, h - chamfer)
        path.lineTo(0, chamfer)
        path.lineTo(chamfer, 0)
        painter.fillPath(path, QColor(18, 18, 18, 90))
        
        # Parse current color
        rgb = self.hex_to_rgb(self.current_color)
        outline_color = QColor(rgb[0], rgb[1], rgb[2])
        
        tr_path = QPainterPath()
        tr_path.moveTo(w * 0.4, 0)
        tr_path.lineTo(w - chamfer, 0)
        tr_path.lineTo(w, chamfer)
        tr_path.lineTo(w, h * 0.25)
        
        bl_path = QPainterPath()
        bl_path.moveTo(w * 0.6, h)
        bl_path.lineTo(chamfer, h)
        bl_path.lineTo(0, h - chamfer)
        bl_path.lineTo(0, h * 0.75)
        
        for i in range(3, 0, -1):
            painter.setPen(QPen(QColor(rgb[0], rgb[1], rgb[2], int(25/i)), 2 + i*1.5))
            painter.drawPath(tr_path)
            painter.drawPath(bl_path)
        
        painter.setPen(QPen(outline_color, 2))
        painter.drawPath(tr_path)
        painter.drawPath(bl_path)
        painter.end()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(8)
        
        # Mode Name (Large)
        self.mode_name_label = QLabel("PRECISION MODE")
        self.mode_name_label.setFont(QFont(self.font_popstar, 14, QFont.Bold))
        self.mode_name_label.setStyleSheet("color: #1E64FF; background: transparent;")
        self.mode_name_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.mode_name_label)
        
        # Description
        self.description_label = QLabel("Slower, smoother tracking")
        self.description_label.setFont(QFont(self.font_popstar, 10))
        self.description_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.description_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.description_label)
        
        main_layout.addSpacing(5)
        
        # Parameters Grid
        params_layout = QHBoxLayout()
        params_layout.setSpacing(15)
        
        # Speed Multiplier
        speed_container = QVBoxLayout()
        speed_label = QLabel("SPEED")
        speed_label.setFont(QFont(self.font_popstar, 7, QFont.Bold))
        speed_label.setStyleSheet("color: #888888; background: transparent;")
        speed_label.setAlignment(Qt.AlignCenter)
        self.speed_value = QLabel("0.7x")
        self.speed_value.setFont(QFont(self.font_popstar, 12, QFont.Bold))
        self.speed_value.setStyleSheet("color: #1E64FF; background: transparent;")
        self.speed_value.setAlignment(Qt.AlignCenter)
        speed_container.addWidget(speed_label)
        speed_container.addWidget(self.speed_value)
        
        # Turn Aggression
        turn_container = QVBoxLayout()
        turn_label = QLabel("TURN")
        turn_label.setFont(QFont(self.font_popstar, 7, QFont.Bold))
        turn_label.setStyleSheet("color: #888888; background: transparent;")
        turn_label.setAlignment(Qt.AlignCenter)
        self.turn_value = QLabel("0.9x")
        self.turn_value.setFont(QFont(self.font_popstar, 12, QFont.Bold))
        self.turn_value.setStyleSheet("color: #1E64FF; background: transparent;")
        self.turn_value.setAlignment(Qt.AlignCenter)
        turn_container.addWidget(turn_label)
        turn_container.addWidget(self.turn_value)
        
        # Search Aggression
        search_container = QVBoxLayout()
        search_label = QLabel("SEARCH")
        search_label.setFont(QFont(self.font_popstar, 7, QFont.Bold))
        search_label.setStyleSheet("color: #888888; background: transparent;")
        search_label.setAlignment(Qt.AlignCenter)
        self.search_value = QLabel("1.0x")
        self.search_value.setFont(QFont(self.font_popstar, 12, QFont.Bold))
        self.search_value.setStyleSheet("color: #1E64FF; background: transparent;")
        self.search_value.setAlignment(Qt.AlignCenter)
        search_container.addWidget(search_label)
        search_container.addWidget(self.search_value)
        
        params_layout.addLayout(speed_container)
        params_layout.addLayout(turn_container)
        params_layout.addLayout(search_container)
        
        main_layout.addLayout(params_layout)
        main_layout.addStretch()
    
    def update_mode_display(self, mode_key):
        """Update display when mode changes"""
        mode_info = OPERATION_MODES[mode_key]
        
        self.current_mode = mode_key
        self.current_color = mode_info['color']
        
        # Update labels
        self.mode_name_label.setText(mode_info['name'])
        self.mode_name_label.setStyleSheet(f"color: {mode_info['color']}; background: transparent;")
        
        self.description_label.setText(mode_info['description'])
        
        # Update parameters
        self.speed_value.setText(f"{mode_info['speed_multiplier']}x")
        self.speed_value.setStyleSheet(f"color: {mode_info['color']}; background: transparent;")
        
        self.turn_value.setText(f"{mode_info['turn_aggression']}x")
        self.turn_value.setStyleSheet(f"color: {mode_info['color']}; background: transparent;")
        
        self.search_value.setText(f"{mode_info['search_aggression']}x")
        self.search_value.setStyleSheet(f"color: {mode_info['color']}; background: transparent;")
        
        self.update()  # Trigger repaint for outline color change
        
        print(f"[Mode Display] Updated to: {mode_info['name']}")
    
    @staticmethod
    def hex_to_rgb(hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPos() - self.drag_pos)


# ===== STANDALONE TESTING =====
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Test both widgets
    profiles_widget = OperationProfilesWidget()
    display_widget = ModeDisplayWidget()
    
    # Connect signals
    profiles_widget.mode_changed.connect(display_widget.update_mode_display)
    
    profiles_widget.show()
    display_widget.show()
    
    sys.exit(app.exec_())