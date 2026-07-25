import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        load_dotenv()
        self.config_dir = Path("config")
        self.config = self._load_default_config()

    def _load_default_config(self):
        # Default configuration
        return {
            "voice": {
                "groq_api_key": os.getenv("GROQ_API_KEY"),
                "openai_api_key": os.getenv("OPENAI_API_KEY"),
                "picovoice_access_key": os.getenv("PICOVOICE_ACCESS_KEY"),
                "voice_id": os.getenv("VOICE_ID", "orpheus-v1-english"),
                "wake_word": os.getenv("WAKE_WORD", "hey_assistant"),
                "sample_rate": 16000,
            },
            "app": {
                "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
            }
        }

    def get(self, key, default=None):
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

# Global instance
config = ConfigManager()
