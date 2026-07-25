import logging
import json
from groq import Groq
from src.core.config_manager import config

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = config.get("voice.groq_api_key")
        if not self.api_key:
            logger.error("Groq API key not found for LLM.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile" # Updated model

    def generate_response(self, messages, tools=None):
        """
        Generates a response from the LLM.
        messages: List of message dicts [{"role": "user", "content": "..."}]
        tools: Optional list of tool definitions for function calling
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024,
                "top_p": 1,
                "stop": None,
                "stream": False # Streaming could be added for lower latency
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            
            completion = self.client.chat.completions.create(**params)
            return completion.choices[0].message
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return None
