import sys
import struct
import json
import base64
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QOpenGLWidget
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QFontDatabase, QPainterPath
from PyQt5.QtCore import Qt, QTimer
import ctypes
from ctypes import c_int, byref, sizeof
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# Font paths
CUSTOM_FONT_PATH_KA1 = r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage\ka1.ttf"

# 3D Model path
MODEL_PATH = r"C:\Users\Administrator\Documents\MXEN PROJECT\SerialIO_Arduino_Driver_4BytePackage\model.glb"


class GLB3DViewer(QOpenGLWidget):
    """
    OpenGL-based 3D model viewer using PyOpenGL
    Renders GLB models with auto-rotation on pure black background
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(400)
        self.rotation_angle = 0
        self.vertices = []
        self.normals = []
        self.indices = []
        self.has_model = False
        
        # Auto-rotation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_model)
        self.timer.start(16)  # ~60 FPS
        
        # Load model
        self.load_glb_model(MODEL_PATH)
    
    def load_glb_model(self, filepath):
        """Load GLB file and extract mesh data"""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Parse GLB header
            magic = struct.unpack('<I', data[0:4])[0]
            if magic != 0x46546C67:  # "glTF" in hex
                print("Not a valid GLB file")
                return
            
            version = struct.unpack('<I', data[4:8])[0]
            length = struct.unpack('<I', data[8:12])[0]
            
            # Parse JSON chunk
            chunk_length = struct.unpack('<I', data[12:16])[0]
            chunk_type = struct.unpack('<I', data[16:20])[0]
            
            if chunk_type == 0x4E4F534A:  # "JSON"
                json_data = data[20:20+chunk_length].decode('utf-8')
                gltf = json.loads(json_data)
                
                # Parse BIN chunk
                bin_offset = 20 + chunk_length
                bin_chunk_length = struct.unpack('<I', data[bin_offset:bin_offset+4])[0]
                bin_chunk_type = struct.unpack('<I', data[bin_offset+4:bin_offset+8])[0]
                
                if bin_chunk_type == 0x004E4942:  # "BIN"
                    binary_data = data[bin_offset+8:bin_offset+8+bin_chunk_length]
                    self.parse_gltf_data(gltf, binary_data)
                    self.has_model = True
                    print("GLB model loaded successfully")
        except Exception as e:
            print(f"Error loading GLB: {e}")
            self.create_fallback_model()
    
    def parse_gltf_data(self, gltf, binary_data):
        """Extract vertices, normals, and indices from GLTF data"""
        try:
            # Get first mesh
            if 'meshes' not in gltf or len(gltf['meshes']) == 0:
                self.create_fallback_model()
                return
            
            mesh = gltf['meshes'][0]
            primitive = mesh['primitives'][0]
            
            # Get accessors
            attributes = primitive['attributes']
            position_accessor_idx = attributes.get('POSITION')
            normal_accessor_idx = attributes.get('NORMAL')
            indices_accessor_idx = primitive.get('indices')
            
            # Parse positions
            if position_accessor_idx is not None:
                self.vertices = self.parse_accessor(gltf, binary_data, position_accessor_idx)
            
            # Parse normals
            if normal_accessor_idx is not None:
                self.normals = self.parse_accessor(gltf, binary_data, normal_accessor_idx)
            
            # Parse indices
            if indices_accessor_idx is not None:
                self.indices = self.parse_accessor(gltf, binary_data, indices_accessor_idx)
            
            print(f"Loaded {len(self.vertices)//3} vertices, {len(self.indices)} indices")
            
        except Exception as e:
            print(f"Error parsing GLTF: {e}")
            self.create_fallback_model()
    
    def parse_accessor(self, gltf, binary_data, accessor_idx):
        """Parse accessor data from binary buffer"""
        accessor = gltf['accessors'][accessor_idx]
        buffer_view = gltf['bufferViews'][accessor['bufferView']]
        
        offset = buffer_view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        count = accessor['count']
        
        # Determine component type
        component_type = accessor['componentType']
        type_map = {
            5120: ('b', 1),   # BYTE
            5121: ('B', 1),   # UNSIGNED_BYTE
            5122: ('h', 2),   # SHORT
            5123: ('H', 2),   # UNSIGNED_SHORT
            5125: ('I', 4),   # UNSIGNED_INT
            5126: ('f', 4),   # FLOAT
        }
        
        format_char, byte_size = type_map[component_type]
        
        # Determine element count per accessor type
        type_sizes = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
        element_size = type_sizes[accessor['type']]
        
        # Extract data
        data = []
        for i in range(count * element_size):
            byte_offset = offset + i * byte_size
            value = struct.unpack('<' + format_char, binary_data[byte_offset:byte_offset+byte_size])[0]
            data.append(float(value))
        
        return data
    
    def create_fallback_model(self):
        """Create a simple car-like fallback model"""
        self.has_model = True
        
        # Simple box vertices (car body)
        self.vertices = [
            # Front face
            -1, -0.25, 0.5,  1, -0.25, 0.5,  1, 0.25, 0.5,  -1, 0.25, 0.5,
            # Back face
            -1, -0.25, -0.5,  -1, 0.25, -0.5,  1, 0.25, -0.5,  1, -0.25, -0.5,
            # Top face
            -1, 0.25, -0.5,  -1, 0.25, 0.5,  1, 0.25, 0.5,  1, 0.25, -0.5,
            # Bottom face
            -1, -0.25, -0.5,  1, -0.25, -0.5,  1, -0.25, 0.5,  -1, -0.25, 0.5,
            # Right face
            1, -0.25, -0.5,  1, 0.25, -0.5,  1, 0.25, 0.5,  1, -0.25, 0.5,
            # Left face
            -1, -0.25, -0.5,  -1, -0.25, 0.5,  -1, 0.25, 0.5,  -1, 0.25, -0.5,
        ]
        
        self.indices = [
            0,1,2, 0,2,3,       # Front
            4,5,6, 4,6,7,       # Back
            8,9,10, 8,10,11,    # Top
            12,13,14, 12,14,15, # Bottom
            16,17,18, 16,18,19, # Right
            20,21,22, 20,22,23  # Left
        ]
        
        # Generate normals
        self.normals = [0, 0, 1] * 4 + [0, 0, -1] * 4 + [0, 1, 0] * 4 + \
                       [0, -1, 0] * 4 + [1, 0, 0] * 4 + [-1, 0, 0] * 4
        
        print("Using fallback car model")
    
    def initializeGL(self):
        """Initialize OpenGL settings"""
        glClearColor(0.0, 0.0, 0.0, 1.0)  # Pure black background
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Lighting setup
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 10.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.2, 0.2, 1.0])  # Red-ish light
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    
    def resizeGL(self, w, h):
        """Handle window resize"""
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w/h if h > 0 else 1, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Render the 3D model"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Camera position
        glTranslatef(0.0, 0.0, -5.0)
        
        # Apply rotation
        glRotatef(self.rotation_angle, 0, 1, 0)
        
        if not self.has_model:
            return
        
        # Draw model
        glColor3f(1.0, 0.2, 0.2)  # Red color
        
        if len(self.indices) > 0:
            # Draw with indices
            glBegin(GL_TRIANGLES)
            for i in range(0, len(self.indices), 3):
                for j in range(3):
                    idx = int(self.indices[i + j])
                    
                    # Normal
                    if len(self.normals) > idx * 3 + 2:
                        glNormal3f(self.normals[idx*3], self.normals[idx*3+1], self.normals[idx*3+2])
                    
                    # Vertex
                    if len(self.vertices) > idx * 3 + 2:
                        glVertex3f(self.vertices[idx*3], self.vertices[idx*3+1], self.vertices[idx*3+2])
            glEnd()
        else:
            # Draw without indices
            glBegin(GL_TRIANGLES)
            for i in range(0, len(self.vertices), 9):
                for j in range(3):
                    idx = i + j * 3
                    if idx + 2 < len(self.vertices):
                        if len(self.normals) > idx + 2:
                            glNormal3f(self.normals[idx], self.normals[idx+1], self.normals[idx+2])
                        glVertex3f(self.vertices[idx], self.vertices[idx+1], self.vertices[idx+2])
            glEnd()
    
    def rotate_model(self):
        """Auto-rotate the model"""
        self.rotation_angle += 0.5
        if self.rotation_angle >= 360:
            self.rotation_angle = 0
        self.update()


class MXENDisplayWidget(QWidget):
    """
    Central display widget showing "MXEN 3000" and "GROUP 09" with 3D model viewer
    Left side: Text with typewriter effect
    Right side: Auto-rotating 3D model (OpenGL-based)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Font loading
        font_id_ka1 = QFontDatabase.addApplicationFont(CUSTOM_FONT_PATH_KA1)
        self.font_ka1 = QFontDatabase.applicationFontFamilies(font_id_ka1)[0] if font_id_ka1 != -1 else "Courier New"
        
        self.setWindowTitle("MXEN Display")
        self.setGeometry(100, 100, 900, 350)
        
        # Typewriter animation state
        self.char_index = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(100)
        
        # Full text to type
        self.full_text = [
            "MXEN",
            "3000",
            "GROUP",
            "09"
        ]
        
        # Track how many characters of each line have been typed
        self.lines_progress = [0, 0, 0, 0]
        self.animation_complete = False
        
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
    
    def setup_ui(self):
        """Setup UI with text on left and 3D model on right"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left side: Text display (custom painted widget)
        self.text_widget = QWidget()
        self.text_widget.setMinimumWidth(400)
        self.text_widget.paintEvent = self.paint_text_area
        main_layout.addWidget(self.text_widget)
        
        # Right side: OpenGL 3D Model viewer
        self.model_viewer = GLB3DViewer()
        main_layout.addWidget(self.model_viewer)
    
    def paintEvent(self, event):
        """Draw chamfered frame with glowing outline"""
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
        
        # Glowing red outline
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
        
        # Red glow effect
        for i in range(3, 0, -1):
            painter.setPen(QPen(QColor(255, 30, 30, int(40/i)), 2 + i*1.5))
            painter.drawPath(tr_path)
            painter.drawPath(bl_path)
        
        painter.setPen(QPen(base_red, 2))
        painter.drawPath(tr_path)
        painter.drawPath(bl_path)
        
        painter.end()
    
    def paint_text_area(self, event):
        """Draw text with typewriter effect (left side)"""
        painter = QPainter(self.text_widget)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.text_widget.width()
        h = self.text_widget.height()
        
        # Layout configuration
        layout = [
            (self.full_text[0], h * 0.30, 45),    # MXEN
            (self.full_text[1], h * 0.50, 45),    # 3000
            (self.full_text[2], h * 0.70, 27),    # GROUP
            (self.full_text[3], h * 0.87, 27),    # 09
        ]
        
        for line_idx, (full_text, y_pos, font_size) in enumerate(layout):
            visible_chars = self.lines_progress[line_idx]
            
            if visible_chars == 0:
                continue
            
            partial_text = full_text[:visible_chars]
            
            font = QFont(self.font_ka1, font_size, QFont.Bold)
            painter.setFont(font)
            
            x = 50
            
            # Main text - bright red
            painter.setPen(QColor(255, 30, 30))
            painter.drawText(int(x), int(y_pos), partial_text)
            
            # Typing cursor
            if visible_chars < len(full_text):
                text_rect = painter.fontMetrics().boundingRect(partial_text)
                cursor_x = x + text_rect.width() + 2
                
                blink = int(self.char_index / 4) % 2
                if blink:
                    painter.setPen(QColor(255, 30, 30))
                    painter.drawText(int(cursor_x), int(y_pos), "|")
        
        painter.end()
    
    def update_animation(self):
        """Update typewriter animation"""
        if self.animation_complete:
            return
        
        total_chars = sum(len(text) for text in self.full_text)
        
        for line_idx, text in enumerate(self.full_text):
            text_len = len(text)
            start_char = sum(len(self.full_text[i]) for i in range(line_idx))
            
            if self.char_index >= start_char:
                self.lines_progress[line_idx] = min(self.char_index - start_char, text_len)
            else:
                self.lines_progress[line_idx] = 0
        
        self.char_index += 1
        
        if self.char_index > total_chars:
            self.animation_complete = True
            self.animation_timer.stop()
        
        self.text_widget.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPos() - self.drag_pos)


# ===== STANDALONE TESTING =====
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MXENDisplayWidget()
    window.show()
    sys.exit(app.exec_())