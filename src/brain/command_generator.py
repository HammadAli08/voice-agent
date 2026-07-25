import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Athena, a helpful desktop assistant for Fedora Linux.

USER CONTEXT:
- Current time: {time}
- Active application: {app}
- Previous command: {last_command} (Result: {last_result})
- Conversation history: {history}

RESPONSE FORMAT:
You must respond with valid JSON only. No other text.
{{
  "thoughts": "Brief reasoning about user intent",
  "speech": "Natural, conversational response to speak",
  "action": {{
    "type": "none|command|query|confirm",
    "command_type": "shell|input|system|none",
    "command": "actual command if applicable",
    "risk_level": "low|medium|high",
    "requires_confirmation": true|false
  }},
  "meta": {{
    "tone": "neutral|excited|serious|playful",
    "speech_pace": 1.0,
    "interruptible": true
  }}
}}

CAPABILITIES:
- Execute system commands safely (bash)
- Open/close applications
- Type text, control mouse (ydotool)
- Search web, answer questions
- Control media playback (playerctl)
- File operations (with confirmation)
- System monitoring

SAFETY RULES:
- Never execute destructive commands (rm -rf, mkfs) without HIGH risk and explicit confirmation.
- Warn user about risky operations.
- Suggest safer alternatives.
- Use full paths when possible.
"""

class CommandGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.history = []

    def process_query(self, user_text, context=None):
        """
        Processes a user query and returns a structured response.
        """
        context = context or {}
        
        # Format system prompt
        formatted_prompt = SYSTEM_PROMPT.format(
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            app=context.get("active_app", "Unknown"),
            last_command=context.get("last_command", "None"),
            last_result=context.get("last_result", "None"),
            history=self._format_history()
        )

        messages = [
            {"role": "system", "content": formatted_prompt},
            {"role": "user", "content": user_text}
        ]

        # Call LLM
        response_message = self.llm.generate_response(messages)
        
        if not response_message:
            return None

        content = response_message.content
        
        # Parse JSON
        try:
            # Llama 3 is good at JSON, but sometimes adds markdown blocks
            clean_content = content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]
            
            structured_response = json.loads(clean_content)
            
            # Update history
            self.history.append({"user": user_text, "assistant": structured_response["speech"]})
            if len(self.history) > 10:
                self.history.pop(0)
                
            return structured_response
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {content}")
            return {
                "thoughts": "Failed to parse response",
                "speech": "I had trouble understanding my own thoughts. Please try again.",
                "action": {"type": "none"},
                "meta": {"tone": "serious"}
            }

    def _format_history(self):
        return "\n".join([f"User: {h['user']}\nAthena: {h['assistant']}" for h in self.history])
