import asyncio
import edge_tts
import subprocess
import os
import tempfile
import logging
import shutil
from src.core.config_manager import config

logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self):
        self.voice = config.get("voice.tts_voice", "en-US-AvaNeural")
        self.is_speaking = False
        # List of candidate players
        self.players = ["mpv", "ffplay", "play", "aplay", "pw-play", "vlc"]
        self.player = self._find_player()

    def _find_player(self):
        for p in self.players:
            if shutil.which(p):
                logger.info(f"Using {p} for audio playback.")
                return p
        logger.warning("No system audio player found! TTS will not be audible.")
        return None

    def speak(self, text):
        """
        Speak the given text.
        """
        if not text:
            return

        logger.info(f"Speaking: {text}")
        self.is_speaking = True
        
        try:
            asyncio.run(self._generate_and_play(text))
        except Exception as e:
            logger.error(f"TTS Error: {e}")
        finally:
            self.is_speaking = False

    async def _generate_and_play(self, text):
        communicate = edge_tts.Communicate(text, self.voice)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            await communicate.save(tmp_path)
            
            if self.player:
                # Build command
                if self.player == "mpv":
                    cmd = ["mpv", "--no-video", tmp_path]
                elif self.player == "ffplay":
                    cmd = ["ffplay", "-nodisp", "-autoexit", tmp_path]
                elif self.player == "play": # SoX
                    cmd = ["play", tmp_path]
                elif self.player == "vlc":
                    cmd = ["cvlc", "--play-and-exit", tmp_path]
                else:
                    cmd = [self.player, tmp_path]
                
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                logger.error("Cannot play audio: No player available.")
                
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    tts = TTSEngine()
    tts.speak("Hello, this is a test of the edge-TTS engine.")
