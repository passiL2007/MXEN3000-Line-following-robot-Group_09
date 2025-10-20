import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QFontDatabase, QPainterPath, QPolygonF
from PyQt5.QtCore import Qt, QPointF
import ctypes
from ctypes import c_int, byref, sizeof

# NOTE: Font paths remain specific to your local machine
CUSTOM_FONT_PATH_POPSTAR = r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage\POPSTAR.TTF"
CUSTOM_FONT_PATH_EQUINOX = r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage\Groningen-Regular.ttf"

class PinWidget(QWidget):
    def __init__(self, pin_name, parent=None):
        super().__init__(parent)
        self.pin_name = pin_name
        self.state = 0
        self.setMinimumSize(35, 70)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def setState(self, state):
        self.state = state
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() / 2
        pin_width = 18
        pin_height = 45
        top_y = 8
        
        # Parallelogram shape
        polygon = QPolygonF([
            QPointF(center_x - pin_width/2 + 3, top_y),
            QPointF(center_x + pin_width/2 + 3, top_y),
            QPointF(center_x + pin_width/2 - 3, top_y + pin_height),
            QPointF(center_x - pin_width/2 - 3, top_y + pin_height)
        ])
        
        if self.state == 1:
            for i in range(4, 0, -1):
                glow_alpha = int(40 / i)
                painter.setPen(QPen(QColor(255, 30, 30, glow_alpha), i * 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawPolygon(polygon)
            
            painter.setBrush(QBrush(QColor(255, 40, 40)))
            painter.setPen(QPen(QColor(255, 60, 60), 1.5))
            painter.drawPolygon(polygon)
        else:
            painter.setBrush(QBrush(QColor(30, 30, 30)))
            painter.setPen(QPen(QColor(80, 20, 20), 1.5))
            painter.drawPolygon(polygon)
        
        painter.setPen(QPen(QColor(255, 255, 255) if self.state == 1 else QColor(100, 100, 100)))
        font = QFont("Consolas", 7, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignHCenter | Qt.AlignTop, self.pin_name)
        
        painter.end()

class DualDACWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Font Loading
        font_id_popstar = QFontDatabase.addApplicationFont(CUSTOM_FONT_PATH_POPSTAR)
        font_id_equinox = QFontDatabase.addApplicationFont(CUSTOM_FONT_PATH_EQUINOX)
        self.font_popstar = QFontDatabase.applicationFontFamilies(font_id_popstar)[0] if font_id_popstar != -1 else "Segoe UI"
        self.font_equinox = QFontDatabase.applicationFontFamilies(font_id_equinox)[0] if font_id_equinox != -1 else "Segoe UI"
        
        self.setWindowTitle("Dual DAC Visualizer")
        self.setGeometry(100, 100, 350, 200)
        
        # Pin names matching Arduino's DACPIN arrays
        # DACPIN1: {9,8,7,6,5,4,3,2} → IC5-IC12 (LSB to MSB)
        # DACPIN2: {A2,A3,A4,A5,A1,A0,11,10} → IC5-IC12 (LSB to MSB)
        self.pin_names = [" IC5", " IC6", " IC7", " IC8", " IC9", " IC10", " IC11", " IC12"]
        self.pin_widgets_a6 = []
        self.pin_widgets_a7 = []
        
        self.setup_ui()
        self.apply_windows_blur()
        
        # Set initial pin state to 0 (all off)
        self.update_pins(0, 'a6')
        self.update_pins(0, 'a7')
        
    def apply_windows_blur(self):
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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        chamfer = 15
        w, h = self.width(), self.height()
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
        
        base_red = QColor(255, 30, 30)
        
        # Chamfered Outline Path Definitions
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
        
        # Draw Glow Layers
        for i in range(3, 0, -1):
            painter.setPen(QPen(QColor(255, 30, 30, int(25/i)), 2 + i*1.5, Qt.SolidLine, Qt.RoundCap))
            painter.drawPath(tr_path)
            painter.drawPath(bl_path)
            
        # Draw Main Outline
        painter.setPen(QPen(base_red, 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(tr_path)
        painter.drawPath(bl_path)
        painter.end()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 5, 8, 5)
        main_layout.setSpacing(3)
        
        # Title
        title = QLabel("DAC PIN VISUALIZER")
        title.setFont(QFont(self.font_popstar, 11, QFont.Bold))
        title.setStyleSheet("color: #FF3030; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # A6 DAC Section (OUTPUT1 - Left Motor)
        a6_container = self.create_dac_section("A6", self.pin_widgets_a6)
        main_layout.addLayout(a6_container)
        
        # A7 DAC Section (OUTPUT2 - Right Motor)
        a7_container = self.create_dac_section("A7", self.pin_widgets_a7)
        main_layout.addLayout(a7_container)
    
    def create_dac_section(self, label, pin_list):
        container = QVBoxLayout()
        container.setSpacing(2)
        
        # Header (A6/A7, DEC, BIN labels)
        header = QHBoxLayout()
        lbl = QLabel(f"{label}")
        lbl.setFont(QFont(self.font_popstar, 9, QFont.Bold))
        lbl.setStyleSheet("color: white; background: transparent;")
        header.addWidget(lbl)
        
        if label == "A6":
            self.dec_a6 = QLabel("DEC: 0")
            self.dec_a6.setFont(QFont(self.font_popstar, 7))
            self.dec_a6.setStyleSheet("color: white; background: transparent;")
            header.addWidget(self.dec_a6)
            header.addStretch()
            self.bin_a6 = QLabel("BIN: 00000000")
            self.bin_a6.setFont(QFont(self.font_popstar, 7))
            self.bin_a6.setStyleSheet("color: #FF3030; background: transparent;")
            header.addWidget(self.bin_a6)
        else:
            self.dec_a7 = QLabel("DEC: 0")
            self.dec_a7.setFont(QFont(self.font_popstar, 7))
            self.dec_a7.setStyleSheet("color: white; background: transparent;")
            header.addWidget(self.dec_a7)
            header.addStretch()
            self.bin_a7 = QLabel("BIN: 00000000")
            self.bin_a7.setFont(QFont(self.font_popstar, 7))
            self.bin_a7.setStyleSheet("color: #FF3030; background: transparent;")
            header.addWidget(self.bin_a7)
        container.addLayout(header)
        
        # Pins
        pins = QHBoxLayout()
        pins.setSpacing(2)
        for name in self.pin_names:
            pw = PinWidget(name)
            pin_list.append(pw)
            pins.addWidget(pw)
        container.addLayout(pins)
        
        return container
    
    def update_pins(self, value, motor):
        """
        UPDATED: Now matches Arduino's bit ordering exactly
        
        Arduino DAC output uses LSB-first ordering:
        - outputToDAC1/2 loops: for(i=0; i<=7; i++) digitalWrite(pin[i], bit_i)
        - bit 0 (LSB) → DACPIN[0] → IC5
        - bit 7 (MSB) → DACPIN[7] → IC12
        
        Binary format: bit7 bit6 bit5 bit4 bit3 bit2 bit1 bit0
        Visual display: IC5  IC6  IC7  IC8  IC9  IC10 IC11 IC12
        """
        binary = format(value, '08b')
        pins = self.pin_widgets_a6 if motor == 'a6' else self.pin_widgets_a7
        
        # Update pin visuals
        # pins[0] = IC5 (LSB) = binary[7]
        # pins[7] = IC12 (MSB) = binary[0]
        for i, pw in enumerate(pins):
            # Map binary string (MSB-first) to pins (LSB-first)
            pw.setState(int(binary[7 - i]))
            
        # Update decimal/binary labels
        if motor == 'a6':
            self.dec_a6.setText(f"DEC: {value}")
            self.bin_a6.setText(f"BIN: {binary}")
        else:
            self.dec_a7.setText(f"DEC: {value}")
            self.bin_a7.setText(f"BIN: {binary}")
    
    # Mouse events for dragging the frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPos() - self.drag_pos)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DualDACWidget()
    window.show()
    sys.exit(app.exec_())