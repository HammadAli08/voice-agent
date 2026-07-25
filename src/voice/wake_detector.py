import logging
import numpy as np
import time
from src.core.config_manager import config

logger = logging.getLogger(__name__)

class WakeDetector:
    """
    Simple Energy-based Wake Detector as a fallback.
    Detects loud sounds (potential speech) to trigger listening.
    """
    def __init__(self):
        # Config
        self.threshold = float(config.get("voice.wake_word_threshold", 0.01)) # Lowered default for better sensitivity
        self.min_duration = 0.3 # Shorter duration for faster response
        self.speech_start = None
        
        logger.info(f"Energy WakeDetector initialized. Threshold: {self.threshold}")

    def process_frame(self, audio_frame):
        """
        Processes audio frame (PCM bytes).
        """
        try:
            # Convert bytes to numpy int16 then normalize to 0-1 float
            audio_data = np.frombuffer(audio_frame, dtype=np.int16).astype(np.float32) / 32768.0
            rms = np.sqrt(np.mean(np.square(audio_data)))
            
            if rms > self.threshold:
                if self.speech_start is None:
                    self.speech_start = time.time()
                    # Optionally return True immediately if we want fast trigger
                    # But verifying duration reduces clicks/pops triggering it
                elif (time.time() - self.speech_start) > self.min_duration:
                    logger.info(f"Energy trigger: {rms:.4f}")
                    self.speech_start = None
                    return True
            else:
                # Reset if noise stops before min_duration
                self.speech_start = None
                    
        except Exception as e:
            pass
            
        return False

    def get_frame_length(self):
        return 1024

    def cleanup(self):
        pass
