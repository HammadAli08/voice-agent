import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QPen, QBrush

class VoiceVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        
        # State: 'idle', 'listening', 'processing', 'speaking'
        self.state = 'idle'
        
        # Animation variables
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
        
        self.time_offset = 0.0
        self.pulse_val = 1.0
        
        # Waves for 'listening' and 'speaking'
        self.waves = []
        self.max_waves = 5
        self.wave_spawn_timer = 0

    def set_state(self, state):
        self.state = state.lower()
        if self.state not in ['idle', 'listening', 'processing', 'speaking']:
            self.state = 'idle'
        
        # Reset waves when transitioning
        if self.state in ['listening', 'speaking']:
            self.waves = []
        
    def update_animation(self):
        self.time_offset += 0.05
        self.pulse_val = 1.0 + 0.05 * math.sin(self.time_offset * 2)
        
        if self.state in ['listening', 'speaking']:
            # Handle waves
            self.wave_spawn_timer += 1
            if self.wave_spawn_timer > 30: # Spawn every ~0.5s
                self.waves.append({'radius': 30, 'opacity': 0.8})
                self.wave_spawn_timer = 0
            
            # Update existing waves
            for wave in self.waves[:]:
                wave['radius'] += 1.5
                wave['opacity'] -= 0.012
                if wave['opacity'] <= 0:
                    self.waves.remove(wave)
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = QPointF(self.width() / 2, self.height() / 2)
        base_radius = 40 * self.pulse_val
        
        # Draw Waves
        if self.state in ['listening', 'speaking']:
            color = QColor(0, 150, 255) if self.state == 'listening' else QColor(255, 100, 0)
            for wave in self.waves:
                wave_color = QColor(color)
                wave_color.setAlphaF(max(0, wave['opacity']))
                
                pen = QPen(wave_color, 2)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, wave['radius'], wave['radius'])

        # Draw Main Orb
        orb_color = QColor(255, 255, 255)
        if self.state == 'listening':
            orb_color = QColor(0, 200, 255)
        elif self.state == 'processing':
            orb_color = QColor(200, 100, 255)
        elif self.state == 'speaking':
            orb_color = QColor(255, 150, 0)
            
        gradient = QRadialGradient(center, base_radius)
        gradient.setColorAt(0, orb_color)
        gradient.setColorAt(0.7, orb_color.darker(150))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center, base_radius, base_radius)
        
        # Glow Effect
        if self.state != 'idle':
            glow_radius = base_radius * 1.5
            glow_gradient = QRadialGradient(center, glow_radius)
            glow_color = QColor(orb_color)
            glow_color.setAlpha(50)
            glow_gradient.setColorAt(0, glow_color)
            glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(glow_gradient))
            painter.drawEllipse(center, glow_radius, glow_radius)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    vis = VoiceVisualizer()
    vis.set_state('listening')
    vis.show()
    sys.exit(app.exec())
