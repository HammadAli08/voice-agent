import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPoint, QPointF, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QColor, QPainter, QRadialGradient

from src.gui.voice_visualizer import VoiceVisualizer

class MainOrbWindow(QMainWindow):
    # Signals to communicate with controller
    status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.dragging = False
        self.offset = QPoint()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 220, 220)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Visualizer
        self.visualizer = VoiceVisualizer()
        self.layout.addWidget(self.visualizer, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: white; font-weight: bold; font-family: 'Inter';")
        self.layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Orb Background
        gradient = QRadialGradient(QPointF(self.rect().center()), self.width() / 2)
        gradient.setColorAt(0, QColor(0, 0, 0, 200))
        gradient.setColorAt(1, QColor(0, 0, 0, 50))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def set_status(self, status):
        self.status_label.setText(status)
        
        # Map status text to visualizer state
        status_map = {
            "Listening...": "listening",
            "Processing...": "processing",
            "Speaking...": "speaking",
            "Ready": "idle",
            "Did not hear anything.": "idle"
        }
        
        visualizer_state = status_map.get(status, "idle")
        self.visualizer.set_state(visualizer_state)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainOrbWindow()
    window.show()
    sys.exit(app.exec())
