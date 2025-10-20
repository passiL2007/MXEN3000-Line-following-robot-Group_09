import sys
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QLineEdit, QPushButton, QLabel, QScrollArea)
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QFontDatabase, QPainterPath, QTextCursor
from PyQt5.QtCore import Qt, QTimer
import ctypes
from ctypes import c_int, byref, sizeof

# Font paths
CUSTOM_FONT_PATH_POPSTAR = r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage\POPSTAR.TTF"
CUSTOM_FONT_PATH_EQUINOX = r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage\Groningen-Regular.ttf"


class AITerminalWidget(QWidget):
    """
    AI-Powered Terminal Assistant Widget
    
    Features:
    - Chat interface for asking questions about the mechatronics project
    - Context-aware responses about motors, sensors, Arduino code
    - Example prompts to guide users
    - Web search capability placeholder
    - Cyberpunk red/black aesthetic matching the GUI
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Font loading
        font_id_popstar = QFontDatabase.addApplicationFont(CUSTOM_FONT_PATH_POPSTAR)
        font_id_equinox = QFontDatabase.addApplicationFont(CUSTOM_FONT_PATH_EQUINOX)
        self.font_popstar = QFontDatabase.applicationFontFamilies(font_id_popstar)[0] if font_id_popstar != -1 else "Consolas"
        self.font_equinox = QFontDatabase.applicationFontFamilies(font_id_equinox)[0] if font_id_equinox != -1 else "Consolas"
        
        self.setWindowTitle("AI Terminal Assistant")
        self.setGeometry(100, 100, 610, 500)
        
        # Chat state
        self.is_typing = False
        
        self.setup_ui()
        self.apply_windows_blur()
        
        # Add initial messages with examples
        self.add_system_message("AI TERMINAL INITIALIZED")
        self.show_welcome_with_examples()
    
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
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Title with status indicator
        title_container = QHBoxLayout()
        title_container.setSpacing(8)
        
        title = QLabel("AI TERMINAL ASSISTANT")
        title.setFont(QFont(self.font_popstar, 11, QFont.Bold))
        title.setStyleSheet("color: #FF3030; background: transparent;")
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont(self.font_popstar, 10))
        self.status_indicator.setStyleSheet("color: #00FF00; background: transparent;")
        
        status_text = QLabel("ONLINE")
        status_text.setFont(QFont(self.font_popstar, 7))
        status_text.setStyleSheet("color: #888888; background: transparent;")
        
        title_container.addWidget(title)
        title_container.addWidget(self.status_indicator)
        title_container.addWidget(status_text)
        title_container.addStretch()
        
        header_layout.addLayout(title_container)
        
        # Clear button
        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setFont(QFont(self.font_popstar, 7, QFont.Bold))
        self.clear_btn.setMaximumWidth(60)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(60, 60, 60, 180);
                color: #888888;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 80, 200);
                color: white;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_chat)
        header_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 9))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(10, 10, 10, 200);
                color: white;
                border: 1px solid rgba(255, 30, 30, 0.3);
                border-radius: 5px;
                padding: 8px;
            }
            QScrollBar:vertical {
                background: rgba(30, 30, 30, 180);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 30, 30, 0.5);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 30, 30, 0.7);
            }
        """)
        main_layout.addWidget(self.chat_display)
        
        # Quick actions - UPDATED with better labels
        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setSpacing(5)
        
        actions = [
            ('📋 Examples', 'show examples'),
            ('🔧 Motors', 'how do motors work'),
            ('📡 Serial', 'explain serial protocol'),
            ('👁️ Sensors', 'how do IR sensors work'),
            ('🌐 Search', 'search web for')
        ]
        
        for label, command in actions:
            btn = QPushButton(label)
            btn.setFont(QFont(self.font_popstar, 6))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(40, 40, 40, 150);
                    color: #888888;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: rgba(80, 30, 30, 180);
                    color: #FF3030;
                    border: 1px solid #FF3030;
                }
            """)
            btn.clicked.connect(lambda checked, cmd=command: self.input_field.setText(cmd))
            quick_actions_layout.addWidget(btn)
        
        main_layout.addLayout(quick_actions_layout)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your question here... (e.g., 'show examples')")
        self.input_field.setFont(QFont("Consolas", 9))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 30, 30, 180);
                color: white;
                border: 2px solid rgba(255, 30, 30, 0.5);
                border-radius: 5px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(255, 30, 30, 0.8);
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("SEND")
        self.send_btn.setFont(QFont(self.font_popstar, 9, QFont.Bold))
        self.send_btn.setMaximumWidth(80)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 30, 30, 200);
                color: white;
                border: 2px solid #FF3030;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 60, 60, 220);
            }
            QPushButton:disabled {
                background-color: rgba(100, 30, 30, 150);
                color: #666666;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        main_layout.addLayout(input_layout)
        
        # Status bar
        status_layout = QHBoxLayout()
        status_layout.setSpacing(15)
        
        self.msg_count_label = QLabel("Messages: 0")
        self.msg_count_label.setFont(QFont("Consolas", 7))
        self.msg_count_label.setStyleSheet("color: #666666; background: transparent;")
        
        search_label = QLabel("🔍 Web Search Available")
        search_label.setFont(QFont("Consolas", 7))
        search_label.setStyleSheet("color: #666666; background: transparent;")
        
        help_label = QLabel("Press Enter to send • Type 'show examples' for help")
        help_label.setFont(QFont("Consolas", 7))
        help_label.setStyleSheet("color: #666666; background: transparent;")
        
        status_layout.addWidget(self.msg_count_label)
        status_layout.addStretch()
        status_layout.addWidget(search_label)
        status_layout.addStretch()
        status_layout.addWidget(help_label)
        
        main_layout.addLayout(status_layout)
        
        self.message_count = 0
    
    def show_welcome_with_examples(self):
        """Show welcome message with example queries"""
        welcome = """Hello! I'm your mechatronics lab assistant. 

<b style="color: #FFD700;">TRY THESE COMMANDS:</b>

<span style="color: #FF3030;">▸</span> <b>show examples</b>
   → See all available example queries

<span style="color: #FF3030;">▸</span> <b>how do motors work</b>
   → Learn about DAC motor control

<span style="color: #FF3030;">▸</span> <b>explain serial protocol</b>
   → Understand 4-byte communication

<span style="color: #FF3030;">▸</span> <b>how do IR sensors work</b>
   → IR line follower details

<span style="color: #FF3030;">▸</span> <b>what are operation modes</b>
   → Speed profiles explained

<span style="color: #FF3030;">▸</span> <b>search web for [topic]</b>
   → Search online (coming soon)

<b style="color: #00FF00;">Just type any question or use the quick action buttons above!</b>"""
        
        self.add_assistant_message(welcome)
    
    def add_system_message(self, text):
        """Add a system message (yellow)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f"""
        <div style="margin: 5px 0;">
            <span style="color: #888888; font-size: 8pt;">[{timestamp}] ⚡ SYSTEM</span><br>
            <span style="color: #FFD700; background-color: rgba(100, 80, 0, 0.2); 
                         padding: 5px; border-radius: 3px; border-left: 3px solid #FFD700;">
                {text}
            </span>
        </div>
        """
        self.chat_display.append(html)
        self.scroll_to_bottom()
        self.message_count += 1
        self.update_message_count()
    
    def add_assistant_message(self, text):
        """Add an assistant message (white/gray)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f"""
        <div style="margin: 5px 0;">
            <span style="color: #888888; font-size: 8pt;">[{timestamp}] 🤖 ASSISTANT</span><br>
            <span style="color: #CCCCCC; background-color: rgba(60, 60, 60, 0.4); 
                         padding: 8px; border-radius: 5px; border-left: 3px solid #FF3030; 
                         display: inline-block; max-width: 90%;">
                {text.replace(chr(10), '<br>')}
            </span>
        </div>
        """
        self.chat_display.append(html)
        self.scroll_to_bottom()
        self.message_count += 1
        self.update_message_count()
    
    def add_user_message(self, text):
        """Add a user message (red, right-aligned)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f"""
        <div style="margin: 5px 0; text-align: right;">
            <span style="color: #888888; font-size: 8pt;">YOU [{timestamp}]</span><br>
            <span style="color: white; background-color: rgba(255, 30, 30, 0.3); 
                         padding: 8px; border-radius: 5px; border-right: 3px solid #FF3030; 
                         display: inline-block; max-width: 85%;">
                {text}
            </span>
        </div>
        """
        self.chat_display.append(html)
        self.scroll_to_bottom()
        self.message_count += 1
        self.update_message_count()
    
    def scroll_to_bottom(self):
        """Scroll chat to bottom"""
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_message_count(self):
        """Update message counter"""
        self.msg_count_label.setText(f"Messages: {self.message_count}")
    
    def send_message(self):
        """Send user message and generate AI response"""
        text = self.input_field.text().strip()
        if not text or self.is_typing:
            return
        
        # Add user message
        self.add_user_message(text)
        self.input_field.clear()
        
        # Show typing indicator
        self.is_typing = True
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)
        
        # Simulate AI thinking delay
        QTimer.singleShot(800, lambda: self.generate_response(text))
    
    def generate_response(self, query):
        """Generate AI response based on query"""
        response = self.get_ai_response(query)
        
        self.add_assistant_message(response)
        
        self.is_typing = False
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
    
    def get_ai_response(self, query):
        """Generate context-aware response with examples"""
        query_lower = query.lower()
        
        # Show examples / help
        if 'show examples' in query_lower or 'examples' in query_lower or 'help' in query_lower:
            return """<b style="color: #FFD700;">📚 EXAMPLE QUERIES - COPY & PASTE THESE:</b>

<b style="color: #FF3030;">MOTOR CONTROL:</b>
<span style="color: #00FF00;">▸</span> how do motors work
<span style="color: #00FF00;">▸</span> explain DAC output
<span style="color: #00FF00;">▸</span> what is the motor speed formula
<span style="color: #00FF00;">▸</span> how to tune motor speed
<span style="color: #00FF00;">▸</span> left vs right motor control

<b style="color: #FF3030;">SERIAL COMMUNICATION:</b>
<span style="color: #00FF00;">▸</span> explain serial protocol
<span style="color: #00FF00;">▸</span> what is the 4-byte packet
<span style="color: #00FF00;">▸</span> how to send speed commands
<span style="color: #00FF00;">▸</span> serial debugging tips

<b style="color: #FF3030;">IR SENSORS:</b>
<span style="color: #00FF00;">▸</span> how do IR sensors work
<span style="color: #00FF00;">▸</span> explain line follower logic
<span style="color: #00FF00;">▸</span> white vs black detection
<span style="color: #00FF00;">▸</span> what is line loss recovery

<b style="color: #FF3030;">OPERATION MODES:</b>
<span style="color: #00FF00;">▸</span> what are operation modes
<span style="color: #00FF00;">▸</span> explain race mode
<span style="color: #00FF00;">▸</span> which mode is best for precision
<span style="color: #00FF00;">▸</span> how do speed multipliers work

<b style="color: #FF3030;">STOPWATCH & TIMING:</b>
<span style="color: #00FF00;">▸</span> how does the stopwatch work
<span style="color: #00FF00;">▸</span> explain lap timing
<span style="color: #00FF00;">▸</span> connected vs standalone mode

<b style="color: #FF3030;">WEB SEARCH:</b>
<span style="color: #00FF00;">▸</span> search web for PID tuning
<span style="color: #00FF00;">▸</span> search web for Arduino optimization

<b style="color: #00FF00;">Just copy any question above and paste it here!</b>"""
        
        # Motor control queries
        if 'how do motors work' in query_lower or 'explain dac' in query_lower:
            return """<b style="color: #FFD700;">🔧 MOTOR CONTROL EXPLAINED:</b>

Your system uses <b>dual DAC outputs</b> (A6 and A7) with <b>8-bit resolution</b> (0-255).

<b style="color: #FF3030;">SPEED CALCULATION:</b>
  byte_value = int(2.55 × percentage)
  
  Example: 50% → 2.55 × 50 = 127.5 → 128 byte value

<b style="color: #FF3030;">MOTOR COMMANDS:</b>
  • <b>Left Motor (A6):</b>  "L{speed}\\n"  (e.g., "L75\\n")
  • <b>Right Motor (A7):</b> "R{speed}\\n"  (e.g., "R75\\n")
  • <b>Both Motors:</b>     "S{speed}\\n"  (e.g., "S50\\n")

<b style="color: #00FF00;">TRY ASKING:</b>
  "what is the motor speed formula"
  "how to tune motor speed"
  "left vs right motor control" """
        
        if 'motor speed formula' in query_lower or 'speed formula' in query_lower:
            return """<b style="color: #FFD700;">📐 MOTOR SPEED FORMULA:</b>

<b>Arduino Side:</b>
  speedPercentLeft = 50;  // 0-100%
  byte_value = int(2.55 × speedPercentLeft);
  // Output: 127 (for 50%)

<b>Python GUI Side:</b>
  percentage = slider_value  // 0-100
  byte_value = int(round(2.55 * percentage))
  if byte_value > 255: byte_value = 255

<b>Voltage Mapping:</b>
  voltage = (percentage - 50) × (15 / 50)
  
  0%   → -15V (full reverse)
  50%  → 0V   (stopped)
  100% → +15V (full forward)

<b style="color: #00FF00;">TRY ASKING:</b>
  "how to tune motor speed"
  "explain DAC output" """
        
        # Serial protocol queries
        if 'serial protocol' in query_lower or '4-byte' in query_lower or 'packet' in query_lower:
            return """<b style="color: #FFD700;">📡 SERIAL PROTOCOL EXPLAINED:</b>

<b style="color: #FF3030;">4-BYTE PACKET STRUCTURE:</b>
  [Byte 0] START = 255     (sync marker)
  [Byte 1] PORT = 2 or 3   (2=OUTPUT1/A6, 3=OUTPUT2/A7)
  [Byte 2] DATA = 0-255    (motor speed value)
  [Byte 3] CHECKSUM        (START + PORT + DATA) & 0xFF

<b style="color: #FF3030;">NEW TEXT COMMANDS:</b>
  "L{speed}\\n"  → Left motor  (0-100%)
  "R{speed}\\n"  → Right motor (0-100%)
  "S{speed}\\n"  → Both motors (synchronized)
  "E\\n"         → Enable line follower
  "D\\n"         → Disable line follower

<b style="color: #00FF00;">TRY ASKING:</b>
  "how to send speed commands"
  "serial debugging tips" """
        
        if 'speed commands' in query_lower or 'how to send' in query_lower:
            return """<b style="color: #FFD700;">🚀 SENDING SPEED COMMANDS:</b>

<b>Python Code Example:</b>
  # Send left motor to 75%
  serial_port.write(b"L75\\n")
  
  # Send right motor to 50%
  serial_port.write(b"R50\\n")
  
  # Send both motors to 60%
  serial_port.write(b"S60\\n")

<b>Arduino Receives:</b>
  if (Serial.available()) {{
    char cmd = Serial.read();
    int speed = Serial.parseInt();
    
    if (cmd == 'L') speedPercentLeft = speed;
    if (cmd == 'R') speedPercentRight = speed;
  }}

<b style="color: #FF3030;">REMEMBER:</b>
  • Always include newline '\\n'
  • Speed range: 0-100
  • Commands are case-sensitive

<b style="color: #00FF00;">TRY ASKING:</b>
  "serial debugging tips"
  "what is the 4-byte packet" """
        
        # IR sensor queries
        if 'ir sensors' in query_lower or 'line follower' in query_lower or 'sensors work' in query_lower:
            return """<b style="color: #FFD700;">👁️ IR SENSOR SYSTEM:</b>

Your system monitors <b>two IR sensors</b> (A6=left, A7=right) at ~67Hz.

<b style="color: #FF3030;">SENSOR VALUES:</b>
  • 10-bit ADC: 0-1023 range
  • <b>White surface:</b> Low values (0-100)
  • <b>Black surface:</b> High values (800-1023)

<b style="color: #FF3030;">ARDUINO DEBUG OUTPUT:</b>
  "L:45(W) R:120(B) Loss:L Out:-1"
  
  Breakdown:
  • L:45    → Left sensor = 45 (raw ADC)
  • (W)     → White detected
  • R:120   → Right sensor = 120
  • (B)     → Black detected
  • Loss:L  → Line lost on Left side
  • Out:-1  → Turning left (-1=left, 0=straight, +1=right)

<b style="color: #00FF00;">TRY ASKING:</b>
  "white vs black detection"
  "what is line loss recovery"
  "explain line follower logic" """
        
        if 'white vs black' in query_lower or 'detection' in query_lower:
            return """<b style="color: #FFD700;">⚫⚪ WHITE vs BLACK DETECTION:</b>

<b style="color: #FF3030;">DETECTION LOGIC:</b>
  if (sensorValue < threshold) {{
    // White surface detected
    isWhite = true;
  }} else {{
    // Black line detected
    isWhite = false;
  }}

<b style="color: #FF3030;">TYPICAL THRESHOLDS:</b>
  • White: 0-150
  • Gray: 150-400
  • Black: 400-1023

<b style="color: #FF3030;">LINE FOLLOWER BEHAVIOR:</b>
  Both White → Search for line
  Left Black, Right White → Turn left
  Left White, Right Black → Turn right
  Both Black → Go straight

<b style="color: #00FF00;">TRY ASKING:</b>
  "what is line loss recovery"
  "how do IR sensors work" """
        
        if 'line loss' in query_lower or 'recovery' in query_lower:
            return """<b style="color: #FFD700;">🔄 LINE LOSS RECOVERY:</b>

When both sensors see white (line lost), the car remembers the last turn direction.

<b style="color: #FF3030;">RECOVERY STRATEGY:</b>
  1. Both sensors → white
  2. Check lastOutput variable
  3. If lastOutput = -1 → Continue turning left
  4. If lastOutput = +1 → Continue turning right
  5. Keep turning until line is found

<b style="color: #FF3030;">LOSS DIRECTION INDICATOR:</b>
  • Loss:L  → Lost line on left side
  • Loss:R  → Lost line on right side
  • Loss:-  → Line is found

<b>This prevents the car from stopping when it temporarily loses the line!</b>

<b style="color: #00FF00;">TRY ASKING:</b>
  "explain line follower logic"
  "how do IR sensors work" """
        
        # Operation modes
        if 'operation modes' in query_lower or 'modes' in query_lower or 'profiles' in query_lower:
            return """<b style="color: #FFD700;">⚙️ OPERATION MODES:</b>

Your system has <b>4 speed profiles</b> with different characteristics:

<b style="color: #FF3030;">1. RACE MODE (Red):</b>
   • Speed: 1.2x multiplier
   • Turn: 1.4x aggression
   • Best for: Fast lap times

<b style="color: #1E64FF;">2. PRECISION MODE (Blue):</b>
   • Speed: 0.7x multiplier
   • Turn: 0.9x aggression
   • Best for: Tight corners, accuracy

<b style="color: #FFD700;">3. POWER SAVER (Yellow):</b>
   • Speed: 0.5x multiplier
   • Turn: 0.8x aggression
   • Best for: Battery conservation

<b style="color: #00FF00;">4. LEARNING MODE (Green):</b>
   • Speed: 0.6x multiplier
   • Turn: 1.0x aggression
   • Best for: Data logging, testing

<b style="color: #FF3030;">HOW IT WORKS:</b>
When you switch modes, the current motor speeds are automatically multiplied by the profile's speed factor and sent to Arduino.

<b style="color: #00FF00;">TRY ASKING:</b>
  "explain race mode"
  "which mode is best for precision"
  "how do speed multipliers work" """
        
        if 'race mode' in query_lower:
            return """<b style="color: #FFD700;">🏁 RACE MODE EXPLAINED:</b>

<b style="color: #FF3030;">CHARACTERISTICS:</b>
  • Speed Multiplier: 1.2x
  • Turn Aggression: 1.4x
  • Search Aggression: 1.5x
  • Color: Red

<b style="color: #FF3030;">WHEN TO USE:</b>
  ✓ Straight tracks with gentle curves
  ✓ When maximum speed is priority
  ✓ Competition/time trial mode
  ✓ Well-tested track conditions

<b style="color: #FF3030;">CAUTION:</b>
  ✗ May overshoot tight corners
  ✗ Higher power consumption
  ✗ Requires good line visibility

<b style="color: #00FF00;">TRY ASKING:</b>
  "which mode is best for precision"
  "what are operation modes" """
        
        if 'precision' in query_lower and 'mode' in query_lower:
            return """<b style="color: #FFD700;">🎯 PRECISION MODE EXPLAINED:</b>

<b style="color: #1E64FF;">CHARACTERISTICS:</b>
  • Speed Multiplier: 0.7x
  • Turn Aggression: 0.9x
  • Search Aggression: 1.0x
  • Color: Blue

<b style="color: #1E64FF;">WHEN TO USE:</b>
  ✓ Tracks with sharp turns
  ✓ When accuracy is critical
  ✓ Testing and calibration
  ✓ Complex track layouts

<b style="color: #1E64FF;">BENEFITS:</b>
  ✓ Smooth cornering
  ✓ Less overshooting
  ✓ Better line tracking
  ✓ Reduced oscillation

<b style="color: #00FF00;">TRY ASKING:</b>
  "explain race mode"
  "how do speed multipliers work" """
        
        if 'speed multiplier' in query_lower or 'multipliers work' in query_lower:
            return """<b style="color: #FFD700;">⚡ SPEED MULTIPLIERS EXPLAINED:</b>

<b style="color: #FF3030;">HOW IT WORKS:</b>
When you change modes, your current motor speeds are multiplied:

<b>Example (Race Mode - 1.2x multiplier):</b>
  Current Left Motor: 50%
  Current Right Motor: 50%
  
  After switching to Race Mode:
  New Left Motor: 50 × 1.2 = 60%
  New Right Motor: 50 × 1.2 = 60%
  
  Commands sent:
    serial.write(b"L60\\n")
    serial.write(b"R60\\n")

<b style="color: #FF3030;">CLAMPING:</b>
Values are clamped to 0-100 range:
  85% × 1.4 = 119% → Clamped to 100%

<b style="color: #00FF00;">TRY ASKING:</b>
  "what are operation modes"
  "explain race mode" """
        
        # Stopwatch queries
        if 'stopwatch' in query_lower or 'lap timing' in query_lower or 'timer' in query_lower:
            return """<b style="color: #FFD700;">⏱️ STOPWATCH SYSTEM:</b>

<b style="color: #FF3030;">FEATURES:</b>
  • Threaded timer (accurate timing)
  • Synchronized start/stop with car
  • Best lap time memory
  • Two modes: Connected & Standalone

<b style="color: #FF3030;">CONNECTED MODE:</b>
  When you press START:
    1. Sends "E\\n" (enable line follower)
    2. Sends "S{speed}\\n" (set speed)
    3. Starts timer simultaneously
  
  When you press STOP:
    1. Sends "D\\n" (disable line follower)
    2. Stops timer
    3. Saves best lap if faster

<b style="color: #FF3030;">STANDALONE MODE:</b>
  • Timer only (no car control)
  • Works without Arduino connection
  • Good for manual testing

<b style="color: #00FF00;">TRY ASKING:</b>
  "connected vs standalone mode"
  "explain lap timing" """
        
        if 'connected vs standalone' in query_lower or 'standalone mode' in query_lower:
            return """<b style="color: #FFD700;">🔌 CONNECTED vs STANDALONE:</b>

<b style="color: #FF3030;">CONNECTED MODE:</b>
  ✓ Fully automated control
  ✓ Car starts when timer starts
  ✓ Car stops when timer stops
  ✓ Synchronized timing
  ✓ Requires Arduino connection
  
  Use for: Automated lap timing

<b style="color: #1E64FF;">STANDALONE MODE:</b>
  ✓ Timer only
  ✓ Manual car control
  ✓ Works offline
  ✓ Good for debugging
  ✓ No serial commands sent
  
  Use for: Manual testing, stopwatch only

<b>Switch modes using the buttons at the bottom of the stopwatch widget!</b>

<b style="color: #00FF00;">TRY ASKING:</b>
  "how does the stopwatch work"
  "explain lap timing" """
        
        # Serial debugging
        if 'debugging' in query_lower or 'debug' in query_lower:
            return """<b style="color: #FFD700;">🐛 SERIAL DEBUGGING TIPS:</b>

<b style="color: #FF3030;">COMMON ISSUES:</b>

<b>1. "Not Connected" Error:</b>
  • Check COM port selection
  • Verify Arduino is plugged in
  • Check USB cable connection
  • Try different COM port

<b>2. Motor Not Responding:</b>
  • Verify serial baud rate (9600)
  • Check command format ("L50\\n")
  • Ensure newline character included
  • Monitor Arduino Serial output

<b>3. IR Sensors Not Updating:</b>
  • Check if Arduino is printing values
  • Verify 15ms delay in Arduino loop
  • Check sensor wiring (A6, A7)

<b style="color: #FF3030;">TESTING COMMANDS:</b>
In Arduino Serial Monitor, try:
  L50  → Left motor 50%
  R75  → Right motor 75%
  E    → Enable line follower
  D    → Disable line follower

<b style="color: #00FF00;">TRY ASKING:</b>
  "explain serial protocol"
  "how to send speed commands" """
        
        # Web search
        if 'search web' in query_lower:
            return """<b style="color: #FFD700;">🌐 WEB SEARCH FEATURE:</b>

<b style="color: #FF3030;">COMING SOON!</b>

This feature will allow me to search the internet for:
  • Arduino optimization techniques
  • PID tuning guides
  • Motor driver datasheets
  • Line follower algorithms
  • Python/PyQt5 documentation

<b style="color: #FF3030;">TO IMPLEMENT:</b>
You can integrate with:
  1. <b>SerpAPI</b> - Google search results
  2. <b>Bing Search API</b> - Microsoft search
  3. <b>DuckDuckGo API</b> - Privacy-focused
  4. <b>Claude API</b> - AI with web search

<b style="color: #00FF00;">For now, try asking about topics I already know about your project!</b>

<b style="color: #00FF00;">TRY ASKING:</b>
  "show examples"
  "how do motors work" """
        
        # Default fallback
        return f"""<b style="color: #FFD700;">🤔 QUESTION RECEIVED:</b>

I heard you ask: "<i>{query}</i>"

I'm not sure how to answer that specific question yet, but I can help with:

<b style="color: #FF3030;">AVAILABLE TOPICS:</b>
  • Motor control & DAC outputs
  • Serial communication protocol
  • IR sensor line following
  • Operation mode profiles
  • Stopwatch timing system
  • Arduino code explanations

<b style="color: #00FF00;">TRY THIS:</b>
Type <b>"show examples"</b> to see all available commands, or use the quick action buttons above!

You can also try rephrasing your question using keywords like:
  "how do", "explain", "what is", "how to" """
    
    def clear_chat(self):
        """Clear the chat history"""
        self.chat_display.clear()
        self.message_count = 0
        self.add_system_message("CHAT CLEARED - AI TERMINAL RESET")
        self.show_welcome_with_examples()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPos() - self.drag_pos)


# ===== STANDALONE TESTING =====
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AITerminalWidget()
    window.show()
    sys.exit(app.exec_())