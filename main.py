import sys
import threading
import time
import logging
from queue import Queue, Empty

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from src.core.config_manager import config
from src.voice.audio_processor import AudioProcessor
from src.voice.stt_engine import STTEngine
from src.voice.tts_engine import TTSEngine
from src.brain.llm_client import LLMClient
from src.brain.command_generator import CommandGenerator
from src.brain.context_awareness import ContextAwareness
from src.execution.shell_executor import ShellExecutor
from src.execution.wayland_executor import WaylandExecutor
from src.gui.main_window import MainOrbWindow

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoiceAgentApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainOrbWindow()
        self.window.status_changed.connect(self.window.set_status)
        
        # Initialize Components
        logger.info("Initializing components...")
        self.audio = AudioProcessor()
        self.stt = STTEngine()
        self.tts = TTSEngine()
        self.llm = LLMClient()
        self.cmd_gen = CommandGenerator(self.llm)
        self.context = ContextAwareness()
        self.shell = ShellExecutor()
        self.wayland = WaylandExecutor()
        
        # State
        self.is_running = True
        self.processing_queue = Queue()
        
        # Start Threads
        self.audio_thread = threading.Thread(target=self.voice_loop, daemon=True)
        self.audio_thread.start()
        
        # Timer for GUI updates from queue
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_gui_updates)
        self.update_timer.start(100)

    def voice_loop(self):
        """
        Main voice processing loop.
        """
        from src.voice.wake_detector import WakeDetector
        self.wake_detector = WakeDetector()
        
        logger.info("Voice loop started.")
        print("\n" + "="*50)
        print(" Fedora Voice Agent is READY!")
        print(" Listening for wake word (Energy/Loudness)...")
        print(" Press Ctrl+C to exit.")
        print("="*50 + "\n")
        self.audio.start_stream()
        
        # Startup Sound/Speech
        try:
            self.tts.speak("System online. I am ready.")
        except:
            pass
        
        frame_buffer = []
        is_recording = False
        silence_frames = 0
        
        while self.is_running:
            chunk = self.audio.get_audio_chunk()
            if not chunk:
                time.sleep(0.01)
                continue
                
            # 1. Wake Word Detection (if not recording)
            if not is_recording:
                # We need to handle frame size matching for Porcupine
                # This is simplified; in production we need a ring buffer to adapt chunk sizes
                if self.wake_detector.process_frame(chunk):
                     logger.info("Wake word detected!")
                     is_recording = True
                     self.window.status_changed.emit("Listening...")
                     frame_buffer = []
            
            # 2. Recording Logic
            if is_recording:
                 frame_buffer.append(chunk)
                 
                 # Check for silence to end command
                 if not self.audio.is_speech(chunk):
                     silence_frames += 1
                 else:
                     silence_frames = 0
                     
                 # End recording on silence (e.g., 1 second = ~33 chunks at 30ms)
                 if silence_frames > 30:
                     logger.info("Silence detected, processing command...")
                     is_recording = False
                     self.window.status_changed.emit("Processing...")
                     
                     # Process Audio
                     full_audio = b"".join(frame_buffer)
                     text = self.stt.transcribe(full_audio)
                     
                     if text:
                         logger.info(f"Transcribed: {text}")
                         self.process_command(text)
                     else:
                         self.window.status_changed.emit("Did not hear anything.")
                         
                     silence_frames = 0
                     frame_buffer = []
                     self.window.status_changed.emit("Ready")

    def process_command(self, text):
        context = self.context.get_context()
        response = self.cmd_gen.process_query(text, context)
        
        if response:
            speech = response.get("speech")
            if speech:
                self.window.status_changed.emit("Speaking...")
                self.tts.speak(speech)
            
            action = response.get("action", {})
            if action.get("type") == "command":
                cmd = action.get("command")
                self.shell.execute(cmd) # TODO: Handle confirmation


    def process_gui_updates(self):
        """
        Process updates from the queue in the main GUI thread.
        """
        try:
            while True:
                update = self.processing_queue.get_nowait()
                # Handle updates if we were using the queue
                # For now, most updates use signals directly
                pass
        except Empty:
            pass

    def run(self):
        self.window.show()
        return self.app.exec()

def main():
    agent = VoiceAgentApp()
    sys.exit(agent.run())

if __name__ == "__main__":
    main()
