import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont

sys.path.append(r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage")
from MOTOR_METER import MainWindow as MotorGauge
from DAC_PIN_VISUALISER import DualDACWidget
from IR_GRAPH import IRSensorWidget
from STOPWATCH import StopwatchControlWidget
from MODE import OperationProfilesWidget, ModeDisplayWidget
from ASSISTANT import AITerminalWidget  # NEW IMPORT

# ============================================================
# RESOLUTION CONFIGURATION
# ============================================================
# Adjust these values based on your screen resolution
# Current setup: 1366x768 (your laptop)
# 
# To change for a different screen:
# 1. Check the new resolution (e.g., 1920x1080, 2560x1440)
# 2. Update SCREEN_WIDTH and SCREEN_HEIGHT below
# 3. Optionally adjust SCALE_FACTOR for widget sizes
# ============================================================

SCREEN_WIDTH = 1366   # Change this to match target screen width
SCREEN_HEIGHT = 768   # Change this to match target screen height

# Scale factor: Adjust if widgets appear too large/small on different screens
# 1.0 = default size, 0.8 = 80% size, 1.2 = 120% size
SCALE_FACTOR = 1.0

# Widget sizes (scaled based on SCALE_FACTOR)
MOTOR_GAUGE_WIDTH = int(350 * SCALE_FACTOR)
MOTOR_GAUGE_HEIGHT = int(350 * SCALE_FACTOR)

DAC_VISUALIZER_WIDTH = int(350 * SCALE_FACTOR)
DAC_VISUALIZER_HEIGHT = int(200 * SCALE_FACTOR)

# NEW: Operation Profiles Widget (under DAC)
PROFILES_WIDGET_WIDTH = int(350 * SCALE_FACTOR)
PROFILES_WIDGET_HEIGHT = int(150 * SCALE_FACTOR)

# NEW: Mode Display Widget (in middle column)
MODE_DISPLAY_WIDTH = 610
MODE_DISPLAY_HEIGHT = int(200 * SCALE_FACTOR)

IR_SENSOR_WIDTH = int(350 * SCALE_FACTOR)
IR_SENSOR_HEIGHT = int(280 * SCALE_FACTOR)

# Stopwatch widget size
STOPWATCH_WIDTH = int(350 * SCALE_FACTOR)
STOPWATCH_HEIGHT = int(400 * SCALE_FACTOR)

# AI Terminal Widget size (replaces PCB placeholder)
AI_TERMINAL_WIDTH = 610
AI_TERMINAL_HEIGHT = int(500 * SCALE_FACTOR)

# Spacing between widgets
WIDGET_SPACING = int(5 * SCALE_FACTOR)

# Position offsets from edges (adjust for different layouts)
LEFT_MARGIN = int(10 * SCALE_FACTOR)
TOP_MARGIN = int(10 * SCALE_FACTOR)
RIGHT_MARGIN = int(10 * SCALE_FACTOR)

# ============================================================


class MatrixBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.columns = []
        self.column_width = 4
        self.font_size = 10
        self.animation_speed = 30
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_matrix)
        self.timer.start(self.animation_speed)
        
    def showEvent(self, event):
        super().showEvent(event)
        if not self.columns:
            self.init_columns()
    
    def init_columns(self):
        if self.width() == 0 or self.height() == 0:
            return
        self.columns.clear()
        num_columns = max(1, self.width() // self.column_width)
        for i in range(num_columns):
            speed = random.uniform(3.0, 7.0)
            length = random.randint(12, 25)
            self.columns.append({
                'x': i * self.column_width,
                'y': random.randint(-self.height(), 0),
                'speed': speed,
                'length': length,
                'chars': [str(random.randint(0, 9)) for _ in range(30)]
            })
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.init_columns()
    
    def update_matrix(self):
        if not self.columns:
            self.init_columns()
        for col in self.columns:
            col['y'] += col['speed']
            if col['y'] > self.height() + col['length'] * 20:
                col['y'] = random.randint(-300, -50)
                col['speed'] = random.uniform(3.0, 7.0)
                col['length'] = random.randint(12, 25)
            if random.random() < 0.05:
                idx = random.randint(0, len(col['chars']) - 1)
                col['chars'][idx] = str(random.randint(0, 9))
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont("Consolas", self.font_size, QFont.Bold)
        painter.setFont(font)
        for col in self.columns:
            x = col['x']
            y = col['y']
            for i in range(col['length']):
                char_y = y + i * 18
                if -20 <= char_y <= self.height() + 20:
                    fade_factor = max(0, 1.0 - (i / col['length']))
                    if i < 2:
                        r, g, b, alpha = 255, int(50 * fade_factor), 0, int(255 * fade_factor)
                    elif i < 5:
                        r, g, b, alpha = int(255 * fade_factor), int(40 * fade_factor), 0, int(220 * fade_factor)
                    else:
                        r, g, b, alpha = int(200 * fade_factor), int(30 * fade_factor), 0, int(180 * fade_factor)
                    painter.setPen(QColor(r, g, b, alpha))
                    char_idx = i % len(col['chars'])
                    painter.drawText(int(x), int(char_y), col['chars'][char_idx])
        painter.end()


class MechatronicsConsole(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mechatronics Lab Control Console")
        
        # ============================================================
        # WINDOW SETUP - RESOLUTION AWARE
        # ============================================================
        # Set window to match screen resolution
        self.setGeometry(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Maximize window on startup (fixes the "slightly offset" issue)
        self.showMaximized()
        
        # Store references to child windows for cleanup
        self.child_windows = []
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Matrix background
        self.matrix_bg = MatrixBackground(central_widget)
        self.matrix_bg.setGeometry(0, 0, self.width(), self.height())
        self.matrix_bg.lower()
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(LEFT_MARGIN, TOP_MARGIN, LEFT_MARGIN, 10)
        self.main_layout.setSpacing(10)
        
        # ============================================================
        # WIDGET LAYOUT STRUCTURE
        # Layout: [Motor+DAC+Profiles] [Mode Display + AI Terminal] [IR Sensor + Stopwatch]
        # ============================================================
        
        widgets_container = QHBoxLayout()
        widgets_container.setSpacing(WIDGET_SPACING)
        widgets_container.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # ===== LEFT COLUMN: Motor Gauge + DAC Visualizer + Profiles =====
        left_column = QVBoxLayout()
        left_column.setSpacing(WIDGET_SPACING)
        left_column.setAlignment(Qt.AlignTop)
        
        # Motor Gauge
        self.motor_gauge = MotorGauge()
        self.motor_gauge.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.motor_gauge.setAttribute(Qt.WA_TranslucentBackground)
        self.motor_gauge.setFixedSize(MOTOR_GAUGE_WIDTH, MOTOR_GAUGE_HEIGHT)
        self.gauge_placeholder = QWidget()
        self.gauge_placeholder.setFixedSize(MOTOR_GAUGE_WIDTH, MOTOR_GAUGE_HEIGHT)
        left_column.addWidget(self.gauge_placeholder, alignment=Qt.AlignTop)
        
        # DAC Visualizer (below motor gauge)
        self.dac_visualizer = DualDACWidget()
        self.dac_visualizer.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.dac_visualizer.setAttribute(Qt.WA_TranslucentBackground)
        self.dac_visualizer.setFixedSize(DAC_VISUALIZER_WIDTH, DAC_VISUALIZER_HEIGHT)
        self.dac_placeholder = QWidget()
        self.dac_placeholder.setFixedSize(DAC_VISUALIZER_WIDTH, DAC_VISUALIZER_HEIGHT)
        left_column.addWidget(self.dac_placeholder, alignment=Qt.AlignTop)
        
        # Operation Profiles Widget (below DAC)
        self.profiles_widget = OperationProfilesWidget(serial_manager=None, motor_gauge=None)
        self.profiles_widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.profiles_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.profiles_widget.setFixedSize(PROFILES_WIDGET_WIDTH, PROFILES_WIDGET_HEIGHT)
        self.profiles_placeholder = QWidget()
        self.profiles_placeholder.setFixedSize(PROFILES_WIDGET_WIDTH, PROFILES_WIDGET_HEIGHT)
        left_column.addWidget(self.profiles_placeholder, alignment=Qt.AlignTop)
        
        widgets_container.addLayout(left_column)
        
        # ===== MIDDLE COLUMN: Mode Display + AI Terminal =====
        middle_column = QVBoxLayout()
        middle_column.setSpacing(WIDGET_SPACING)
        middle_column.setAlignment(Qt.AlignTop)
        
        # Mode Display Widget (top)
        self.mode_display = ModeDisplayWidget()
        self.mode_display.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.mode_display.setAttribute(Qt.WA_TranslucentBackground)
        self.mode_display.setFixedSize(MODE_DISPLAY_WIDTH, MODE_DISPLAY_HEIGHT)
        self.mode_display_placeholder = QWidget()
        self.mode_display_placeholder.setFixedSize(MODE_DISPLAY_WIDTH, MODE_DISPLAY_HEIGHT)
        middle_column.addWidget(self.mode_display_placeholder, alignment=Qt.AlignTop)
        
        # ===== AI TERMINAL WIDGET (NEW - replaces PCB placeholder) =====
        self.ai_terminal = AITerminalWidget()
        self.ai_terminal.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.ai_terminal.setAttribute(Qt.WA_TranslucentBackground)
        self.ai_terminal.setFixedSize(AI_TERMINAL_WIDTH, AI_TERMINAL_HEIGHT)
        self.ai_terminal_placeholder = QWidget()
        self.ai_terminal_placeholder.setFixedSize(AI_TERMINAL_WIDTH, AI_TERMINAL_HEIGHT)
        middle_column.addWidget(self.ai_terminal_placeholder, alignment=Qt.AlignTop)
        
        widgets_container.addLayout(middle_column)
        
        # ===== RIGHT COLUMN: IR Sensor Widget + Stopwatch =====
        right_column = QVBoxLayout()
        right_column.setSpacing(WIDGET_SPACING)
        right_column.setAlignment(Qt.AlignTop)
        
        # IR Sensor Widget (top-right position)
        self.ir_sensor = IRSensorWidget(serial_manager=None)
        self.ir_sensor.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.ir_sensor.setAttribute(Qt.WA_TranslucentBackground)
        self.ir_sensor.setFixedSize(IR_SENSOR_WIDTH, IR_SENSOR_HEIGHT)
        self.ir_placeholder = QWidget()
        self.ir_placeholder.setFixedSize(IR_SENSOR_WIDTH, IR_SENSOR_HEIGHT)
        right_column.addWidget(self.ir_placeholder, alignment=Qt.AlignTop)
        
        # Stopwatch Widget (below IR sensor)
        self.stopwatch = StopwatchControlWidget(serial_manager=None, motor_gauge=None)
        self.stopwatch.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.stopwatch.setAttribute(Qt.WA_TranslucentBackground)
        self.stopwatch.setFixedSize(STOPWATCH_WIDTH, STOPWATCH_HEIGHT)
        self.stopwatch_placeholder = QWidget()
        self.stopwatch_placeholder.setFixedSize(STOPWATCH_WIDTH, STOPWATCH_HEIGHT)
        right_column.addWidget(self.stopwatch_placeholder, alignment=Qt.AlignTop)
        
        widgets_container.addLayout(right_column)
        widgets_container.addStretch()  # Push all widgets to left/top
        
        self.main_layout.addLayout(widgets_container)
        self.main_layout.addStretch()  # Push everything to top
        
        # ============================================================
        # SERIAL MANAGER SHARING & CONNECTIONS
        # ============================================================
        # Share the motor gauge's serial manager with all widgets
        self.ir_sensor.set_serial_manager(self.motor_gauge.serial_manager)
        self.stopwatch.set_serial_manager(self.motor_gauge.serial_manager)
        self.stopwatch.set_motor_gauge(self.motor_gauge)
        
        # Connect profiles widget to serial manager and motor gauge
        self.profiles_widget.set_serial_manager(self.motor_gauge.serial_manager)
        self.profiles_widget.set_motor_gauge(self.motor_gauge)
        
        # Connect profiles widget signal to mode display
        self.profiles_widget.mode_changed.connect(self.mode_display.update_mode_display)
        
        # ============================================================
        # DATA FLOW CONNECTIONS
        # ============================================================
        # One-way sync: Motor Gauge -> DAC Visualizer
        self.motor_gauge.slider_a6.valueChanged.connect(lambda v: self.update_dac_from_gauge(v, 'a6'))
        self.motor_gauge.slider_a7.valueChanged.connect(lambda v: self.update_dac_from_gauge(v, 'a7'))
        
        # ============================================================
        # SERIAL DEBUG MONITOR TIMER
        # ============================================================
        # Monitor Arduino's Serial.print debug output
        self.serial_monitor_timer = QTimer(self)
        self.serial_monitor_timer.timeout.connect(self.read_arduino_debug)
        self.serial_monitor_timer.start(100)  # Check every 100ms
        
        # ============================================================
        # WINDOW POSITIONING TIMER
        # ============================================================
        # Timer to keep frameless widgets positioned correctly over placeholders
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_widget_positions)
        self.move_timer.start(50)  # Update every 50ms
        
        # Store child window references for cleanup
        self.child_windows = [
            self.motor_gauge, 
            self.dac_visualizer, 
            self.profiles_widget, 
            self.mode_display,
            self.ai_terminal,  # NEW: AI Terminal added
            self.ir_sensor, 
            self.stopwatch
        ]
        
        # Show all child windows
        self.motor_gauge.show()
        self.dac_visualizer.show()
        self.profiles_widget.show()
        self.mode_display.show()
        self.ai_terminal.show()  # NEW: Show AI Terminal
        self.ir_sensor.show()
        self.stopwatch.show()

    def update_dac_from_gauge(self, percentage, motor):
        """
        Update DAC visualizer based on motor gauge percentage
        Uses exact same formula as Arduino (2.55 * percentage)
        """
        byte_value = int(round(2.55 * percentage))
        if byte_value > 255:
            byte_value = 255
        if byte_value < 0:
            byte_value = 0
        
        self.dac_visualizer.update_pins(byte_value, motor)

    def read_arduino_debug(self):
        """
        Read Arduino's Serial.print() debug output
        Parses line follower status messages
        """
        if not hasattr(self.motor_gauge, 'serial_manager'):
            return
        
        serial_mgr = self.motor_gauge.serial_manager
        if not serial_mgr.is_connected or not serial_mgr.serial_port:
            return
        
        try:
            port = serial_mgr.serial_port
            
            if port.in_waiting > 0:
                line = port.readline().decode('utf-8', errors='ignore').strip()
                
                if line:
                    print(f"[Arduino Debug] {line}")
                    
                    if "L:" in line and "R:" in line:
                        try:
                            left_start = line.index("L:") + 2
                            left_end = line.index("(", left_start)
                            left_val = int(line[left_start:left_end])
                            
                            right_start = line.index("R:") + 2
                            right_end = line.index("(", right_start)
                            right_val = int(line[right_start:right_end])
                            
                        except (ValueError, IndexError):
                            pass
                            
        except Exception as e:
            pass

    def update_widget_positions(self):
        """
        Update positions of all frameless child windows to match their placeholders
        """
        if not hasattr(self, 'gauge_placeholder'):
            return
        
        # Motor Gauge position
        gauge_pos = self.gauge_placeholder.mapToGlobal(QPoint(0, 0))
        self.motor_gauge.move(gauge_pos)
        
        # DAC Visualizer position
        dac_pos = self.dac_placeholder.mapToGlobal(QPoint(0, 0))
        self.dac_visualizer.move(dac_pos)
        
        # Profiles Widget position
        profiles_pos = self.profiles_placeholder.mapToGlobal(QPoint(0, 0))
        self.profiles_widget.move(profiles_pos)
        
        # Mode Display position
        mode_display_pos = self.mode_display_placeholder.mapToGlobal(QPoint(0, 0))
        self.mode_display.move(mode_display_pos)
        
        # AI Terminal position (NEW)
        ai_terminal_pos = self.ai_terminal_placeholder.mapToGlobal(QPoint(0, 0))
        self.ai_terminal.move(ai_terminal_pos)
        
        # IR Sensor position
        ir_pos = self.ir_placeholder.mapToGlobal(QPoint(0, 0))
        self.ir_sensor.move(ir_pos)
        
        # Stopwatch position
        stopwatch_pos = self.stopwatch_placeholder.mapToGlobal(QPoint(0, 0))
        self.stopwatch.move(stopwatch_pos)

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        
        if hasattr(self, 'matrix_bg'):
            self.matrix_bg.setGeometry(0, 0, self.width(), self.height())
        
        self.update_widget_positions()

    def closeEvent(self, event):
        """
        Close all child windows when main window closes
        """
        print("Closing main window and all child widgets...")
        
        for child_window in self.child_windows:
            if child_window and child_window.isVisible():
                child_window.close()
        
        if hasattr(self, 'move_timer'):
            self.move_timer.stop()
        if hasattr(self, 'serial_monitor_timer'):
            self.serial_monitor_timer.stop()
        if hasattr(self, 'matrix_bg') and hasattr(self.matrix_bg, 'timer'):
            self.matrix_bg.timer.stop()
        
        if hasattr(self.motor_gauge, 'serial_manager'):
            if self.motor_gauge.serial_manager.is_connected:
                self.motor_gauge.serial_manager.disconnect()
                print("Serial connection closed.")
        
        event.accept()
        print("All windows closed successfully.")

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #08080F;
            }
            QWidget {
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                background-color: transparent;
            }
        """)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    window = MechatronicsConsole()
    window.show()
    sys.exit(app.exec_())