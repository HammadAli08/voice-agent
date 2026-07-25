import sounddevice as sd
import numpy as np
import webrtcvad
import logging
from queue import Queue, Empty
from src.core.config_manager import config

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.sample_rate = config.get("voice.sample_rate", 16000)
        self.frame_duration_ms = 30
        self.chunk_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        
        self.vad = webrtcvad.Vad(3) # Aggressiveness mode 3
        self.input_queue = Queue()
        self.is_listening = False
        self.stream = None

    def start_stream(self):
        if self.stream is not None:
            return

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                blocksize=self.chunk_size,
                callback=self._audio_callback
            )
            self.stream.start()
            self.is_listening = True
            logger.info("Audio stream started.")
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")

    def stop_stream(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.is_listening = False
            logger.info("Audio stream stopped.")

    def _audio_callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"Audio status: {status}")
        self.input_queue.put(bytes(indata))

    def get_audio_chunk(self):
        try:
            return self.input_queue.get(timeout=0.1)
        except Empty:
            return None

    def is_speech(self, audio_chunk):
        """
        Robust RMS-based speech detection.
        """
        try:
             # Convert bytes to numpy int16 then normalize
            data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            rms = np.sqrt(np.mean(np.square(data)))
            
            # Threshold should be configurable, typically 0.01 - 0.03 for mic
            threshold = 0.02
            return rms > threshold
        except Exception:
            return False
