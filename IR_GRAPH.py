import sys
from collections import deque
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QFontDatabase, QPainterPath
from PyQt5.QtCore import Qt, QTimer, QPointF
import ctypes
from ctypes import c_int, byref, sizeof
import re

# Font paths - NOTE: Adjust these to match your local paths
CUSTOM_FONT_PATH_POPSTAR = r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage\POPSTAR.TTF"
CUSTOM_FONT_PATH_EQUINOX = r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage\Groningen-Regular.ttf"

class IRSensorWidget(QWidget):
    """
    Real-time IR Sensor Display Widget - UPDATED FOR NEW ARDUINO CODE
    
    NEW FEATURES:
    - Parses Arduino's Serial.print debug output (e.g., "L:45(W) R:120(B)")
    - No longer sends INPUT requests (Arduino now continuously prints IR values)
    - Displays line follower status (white/black detection, line loss direction)
    - Matches 15ms loop rate of Arduino (~67Hz update)
    
    PROTOCOL CHANGES:
    - OLD: Alternating INPUT1/INPUT2 requests with 4-byte responses
    - NEW: Continuous Serial.print() parsing from Arduino's debug output
    """
    
    # ===== CONFIGURABLE PARAMETERS =====
    # Update rate: Match Arduino's delay(15) = ~67Hz
    UPDATE_INTERVAL_MS = 50  # 50ms polling (20Hz) - faster than Arduino's 15ms loop
    
    # Graph settings
    GRAPH_HISTORY_LENGTH = 50  # Number of data points to display
    SENSOR_MIN = 0             # Minimum sensor value (ADC range)
    SENSOR_MAX = 1023          # Maximum sensor value (10-bit ADC)
    
    # Visual settings
    LEFT_IR_COLOR = QColor(255, 30, 30)    # Red for Left IR
    RIGHT_IR_COLOR = QColor(30, 100, 255)  # Dark Blue for Right IR
    
    def __init__(self, serial_manager=None):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Serial manager reference (passed from parent)
        self.serial_manager = serial_manager
        
        # Font loading
        font_id_popstar = QFontDatabase.addApplicationFont(CUSTOM_FONT_PATH_POPSTAR)
        font_id_equinox = QFontDatabase.addApplicationFont(CUSTOM_FONT_PATH_EQUINOX)
        self.font_popstar = QFontDatabase.applicationFontFamilies(font_id_popstar)[0] if font_id_popstar != -1 else "Segoe UI"
        self.font_equinox = QFontDatabase.applicationFontFamilies(font_id_equinox)[0] if font_id_equinox != -1 else "Segoe UI"
        
        self.setWindowTitle("IR Sensor Monitor")
        self.setGeometry(100, 100, 350, 320)  # Increased height for status info
        
        # Data storage: Circular buffers for graph history
        self.left_ir_history = deque([0] * self.GRAPH_HISTORY_LENGTH, maxlen=self.GRAPH_HISTORY_LENGTH)
        self.right_ir_history = deque([0] * self.GRAPH_HISTORY_LENGTH, maxlen=self.GRAPH_HISTORY_LENGTH)
        
        # Current sensor values
        self.left_ir_value = 0
        self.right_ir_value = 0
        
        # NEW: Line follower status tracking
        self.left_is_white = False
        self.right_is_white = False
        self.line_loss_direction = "-"  # "L", "R", or "-"
        self.last_output = 0  # -1, 0, or +1
        
        self.setup_ui()
        self.apply_windows_blur()
        
        # Timer for continuous sensor polling
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.poll_sensors)
        self.update_timer.start(self.UPDATE_INTERVAL_MS)
        
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
        """Draw chamfered frame with glowing red outline (matching motor gauge style)"""
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
        
        # Glowing red outline segments (top-right and bottom-left)
        base_red = QColor(255, 30, 30)
        
        # Top-Right segment path
        tr_path = QPainterPath()
        tr_path.moveTo(w * 0.4, 0)
        tr_path.lineTo(w - chamfer, 0)
        tr_path.lineTo(w, chamfer)
        tr_path.lineTo(w, h * 0.25)
        
        # Bottom-Left segment path
        bl_path = QPainterPath()
        bl_path.moveTo(w * 0.6, h)
        bl_path.lineTo(chamfer, h)
        bl_path.lineTo(0, h - chamfer)
        bl_path.lineTo(0, h * 0.75)
        
        # Draw glow layers
        for i in range(3, 0, -1):
            painter.setPen(QPen(QColor(255, 30, 30, int(25/i)), 2 + i*1.5))
            painter.drawPath(tr_path)
            painter.drawPath(bl_path)
            
        # Draw main outline
        painter.setPen(QPen(base_red, 2))
        painter.drawPath(tr_path)
        painter.drawPath(bl_path)
        painter.end()
    
    def setup_ui(self):
        """Build the widget UI structure"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 5, 8, 5)
        main_layout.setSpacing(3)
        
        # Title
        title = QLabel("IR SENSOR READINGS")
        title.setFont(QFont(self.font_popstar, 11, QFont.Bold))
        title.setStyleSheet("color: #FF3030; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Numeric displays (Left and Right IR values)
        numeric_layout = QHBoxLayout()
        numeric_layout.setSpacing(10)
        
        # Left IR Display
        left_container = QVBoxLayout()
        left_container.setSpacing(0)
        left_label = QLabel("LEFT IR (A6)")
        left_label.setFont(QFont(self.font_popstar, 7, QFont.Bold))
        left_label.setStyleSheet("color: white; background: transparent;")
        left_label.setAlignment(Qt.AlignCenter)
        self.left_value_label = QLabel("0")
        self.left_value_label.setFont(QFont(self.font_popstar, 20, QFont.Bold))
        self.left_value_label.setStyleSheet("color: #FF3030; background: transparent;")
        self.left_value_label.setAlignment(Qt.AlignCenter)
        left_container.addWidget(left_label)
        left_container.addWidget(self.left_value_label)
        
        # NEW: White/Black indicator for Left
        self.left_status_label = QLabel("●")
        self.left_status_label.setFont(QFont(self.font_popstar, 12))
        self.left_status_label.setStyleSheet("color: #888888; background: transparent;")
        self.left_status_label.setAlignment(Qt.AlignCenter)
        left_container.addWidget(self.left_status_label)
        
        numeric_layout.addLayout(left_container)
        
        # Right IR Display
        right_container = QVBoxLayout()
        right_container.setSpacing(0)
        right_label = QLabel("RIGHT IR (A7)")
        right_label.setFont(QFont(self.font_popstar, 7, QFont.Bold))
        right_label.setStyleSheet("color: white; background: transparent;")
        right_label.setAlignment(Qt.AlignCenter)
        self.right_value_label = QLabel("0")
        self.right_value_label.setFont(QFont(self.font_popstar, 20, QFont.Bold))
        self.right_value_label.setStyleSheet("color: #1E64FF; background: transparent;")
        self.right_value_label.setAlignment(Qt.AlignCenter)
        right_container.addWidget(right_label)
        right_container.addWidget(self.right_value_label)
        
        # NEW: White/Black indicator for Right
        self.right_status_label = QLabel("●")
        self.right_status_label.setFont(QFont(self.font_popstar, 12))
        self.right_status_label.setStyleSheet("color: #888888; background: transparent;")
        self.right_status_label.setAlignment(Qt.AlignCenter)
        right_container.addWidget(self.right_status_label)
        
        numeric_layout.addLayout(right_container)
        
        main_layout.addLayout(numeric_layout)
        
        # NEW: Line Follower Status Display
        status_container = QHBoxLayout()
        status_container.setSpacing(10)
        status_container.setAlignment(Qt.AlignCenter)
        
        # Loss Direction Indicator
        loss_label = QLabel("LOSS DIR:")
        loss_label.setFont(QFont(self.font_popstar, 7))
        loss_label.setStyleSheet("color: #888888; background: transparent;")
        self.loss_indicator = QLabel("-")
        self.loss_indicator.setFont(QFont(self.font_popstar, 10, QFont.Bold))
        self.loss_indicator.setStyleSheet("color: #FF3030; background: transparent;")
        
        # Output Direction Indicator
        output_label = QLabel("OUTPUT:")
        output_label.setFont(QFont(self.font_popstar, 7))
        output_label.setStyleSheet("color: #888888; background: transparent;")
        self.output_indicator = QLabel("0")
        self.output_indicator.setFont(QFont(self.font_popstar, 10, QFont.Bold))
        self.output_indicator.setStyleSheet("color: #1E64FF; background: transparent;")
        
        status_container.addWidget(loss_label)
        status_container.addWidget(self.loss_indicator)
        status_container.addSpacing(15)
        status_container.addWidget(output_label)
        status_container.addWidget(self.output_indicator)
        
        main_layout.addLayout(status_container)
        
        # Graph display widget (custom painted)
        self.graph_widget = QWidget()
        self.graph_widget.setMinimumHeight(120)
        self.graph_widget.paintEvent = self.paint_graph
        main_layout.addWidget(self.graph_widget)
        
        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setAlignment(Qt.AlignCenter)
        legend_layout.setSpacing(15)
        
        left_legend = QLabel("● Left IR")
        left_legend.setFont(QFont(self.font_popstar, 7))
        left_legend.setStyleSheet("color: #FF3030; background: transparent;")
        
        right_legend = QLabel("● Right IR")
        right_legend.setFont(QFont(self.font_popstar, 7))
        right_legend.setStyleSheet("color: #1E64FF; background: transparent;")
        
        legend_layout.addWidget(left_legend)
        legend_layout.addWidget(right_legend)
        main_layout.addLayout(legend_layout)
    
    def paint_graph(self, event):
        """
        Draw the scrolling line graph with glowing lines
        - Red line for Left IR (A6)
        - Dark Blue line for Right IR (A7)
        """
        painter = QPainter(self.graph_widget)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.graph_widget.width()
        h = self.graph_widget.height()
        
        # Background
        painter.fillRect(0, 0, w, h, QColor(10, 10, 10, 150))
        
        # Grid lines (horizontal - for sensor values)
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        grid_steps = 4
        for i in range(grid_steps + 1):
            y = h - (i * h / grid_steps)
            painter.drawLine(0, int(y), w, int(y))
            # Value labels
            value = int(self.SENSOR_MIN + (self.SENSOR_MAX - self.SENSOR_MIN) * (i / grid_steps))
            painter.setPen(QColor(80, 80, 80))
            painter.setFont(QFont("Consolas", 7))
            painter.drawText(5, int(y) - 2, str(value))
            painter.setPen(QPen(QColor(40, 40, 40), 1))
        
        # Convert data to screen coordinates
        def map_to_screen(value, index, total_points):
            """Map sensor value and index to screen coordinates"""
            x = (index / (total_points - 1)) * w if total_points > 1 else 0
            y = h - ((value - self.SENSOR_MIN) / (self.SENSOR_MAX - self.SENSOR_MIN)) * h
            return QPointF(x, max(0, min(h, y)))
        
        # Draw Left IR line (RED with glow)
        if len(self.left_ir_history) > 1:
            points = [map_to_screen(val, i, len(self.left_ir_history)) 
                     for i, val in enumerate(self.left_ir_history)]
            
            # Glow layers (3 passes with decreasing alpha)
            for glow_width in [6, 4, 2]:
                painter.setPen(QPen(QColor(255, 30, 30, 40), glow_width))
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
            
            # Main line
            painter.setPen(QPen(self.LEFT_IR_COLOR, 2))
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        
        # Draw Right IR line (DARK BLUE with glow)
        if len(self.right_ir_history) > 1:
            points = [map_to_screen(val, i, len(self.right_ir_history)) 
                     for i, val in enumerate(self.right_ir_history)]
            
            # Glow layers
            for glow_width in [6, 4, 2]:
                painter.setPen(QPen(QColor(30, 100, 255, 40), glow_width))
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
            
            # Main line
            painter.setPen(QPen(self.RIGHT_IR_COLOR, 2))
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        
        painter.end()
    
    def poll_sensors(self):
        """
        NEW METHOD: Parse Arduino's Serial.print() debug output
        
        Expected format from Arduino (example):
        "L:45(W) R:120(B) Loss:L Out:-1"
        
        Regex patterns:
        - L:(\d+)     → Left IR raw value
        - \(W\|\(B\)  → White/Black detection
        - R:(\d+)     → Right IR raw value
        - Loss:([LR-])→ Line loss direction
        - Out:([-+]?\d+) → Output direction
        """
        if not self.serial_manager or not self.serial_manager.is_connected:
            return
        
        try:
            port = self.serial_manager.serial_port
            
            # Read all available lines (Arduino prints at ~67Hz)
            while port.in_waiting > 0:
                line = port.readline().decode('utf-8', errors='ignore').strip()
                
                if line and "L:" in line and "R:" in line:
                    # Parse left sensor value
                    left_match = re.search(r'L:(\d+)', line)
                    if left_match:
                        self.left_ir_value = int(left_match.group(1))
                        self.left_ir_history.append(self.left_ir_value)
                        self.left_value_label.setText(str(self.left_ir_value))
                    
                    # Parse left white/black status
                    if "(W)" in line[:line.index("R:")]:
                        self.left_is_white = True
                        self.left_status_label.setText("⬜")
                        self.left_status_label.setStyleSheet("color: #FFFFFF; background: transparent;")
                    elif "(B)" in line[:line.index("R:")]:
                        self.left_is_white = False
                        self.left_status_label.setText("⬛")
                        self.left_status_label.setStyleSheet("color: #333333; background: transparent;")
                    
                    # Parse right sensor value
                    right_match = re.search(r'R:(\d+)', line)
                    if right_match:
                        self.right_ir_value = int(right_match.group(1))
                        self.right_ir_history.append(self.right_ir_value)
                        self.right_value_label.setText(str(self.right_ir_value))
                    
                    # Parse right white/black status
                    if "(W)" in line[line.index("R:"):]:
                        self.right_is_white = True
                        self.right_status_label.setText("⬜")
                        self.right_status_label.setStyleSheet("color: #FFFFFF; background: transparent;")
                    elif "(B)" in line[line.index("R:"):]:
                        self.right_is_white = False
                        self.right_status_label.setText("⬛")
                        self.right_status_label.setStyleSheet("color: #333333; background: transparent;")
                    
                    # Parse line loss direction
                    loss_match = re.search(r'Loss:([LR\-])', line)
                    if loss_match:
                        self.line_loss_direction = loss_match.group(1)
                        self.loss_indicator.setText(self.line_loss_direction)
                    
                    # Parse output direction
                    output_match = re.search(r'Out:([-+]?\d+)', line)
                    if output_match:
                        self.last_output = int(output_match.group(1))
                        self.output_indicator.setText(str(self.last_output))
        
        except Exception as e:
            # Silently handle errors to prevent UI freezing
            pass
        
        # Force graph redraw
        self.graph_widget.update()
    
    def set_serial_manager(self, serial_manager):
        """Allow external assignment of serial manager (for layout integration)"""
        self.serial_manager = serial_manager
    
    # Mouse events for dragging the frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPos() - self.drag_pos)


# ===== STANDALONE TESTING =====
if __name__ == '__main__':
    """
    Test the widget standalone without serial connection
    Simulates random sensor data for visualization testing
    """
    import random
    
    app = QApplication(sys.argv)
    
    # Create widget without serial manager (simulation mode)
    window = IRSensorWidget(serial_manager=None)
    
    # Simulate sensor data with a timer
    def simulate_data():
        window.left_ir_value = random.randint(20, 800)
        window.right_ir_value = random.randint(20, 800)
        window.left_ir_history.append(window.left_ir_value)
        window.right_ir_history.append(window.right_ir_value)
        window.left_value_label.setText(str(window.left_ir_value))
        window.right_value_label.setText(str(window.right_ir_value))
        
        # Simulate white/black detection
        window.left_is_white = window.left_ir_value < 100
        window.right_is_white = window.right_ir_value < 100
        
        window.left_status_label.setText("⬜" if window.left_is_white else "⬛")
        window.left_status_label.setStyleSheet(f"color: {'#FFFFFF' if window.left_is_white else '#333333'}; background: transparent;")
        window.right_status_label.setText("⬜" if window.right_is_white else "⬛")
        window.right_status_label.setStyleSheet(f"color: {'#FFFFFF' if window.right_is_white else '#333333'}; background: transparent;")
        
        # Simulate line loss/output
        window.loss_indicator.setText(random.choice(["L", "R", "-"]))
        window.output_indicator.setText(str(random.choice([-1, 0, 1])))
        
        window.graph_widget.update()
    
    sim_timer = QTimer()
    sim_timer.timeout.connect(simulate_data)
    sim_timer.start(50)  # Match UPDATE_INTERVAL_MS
    
    window.show()
    sys.exit(app.exec_())