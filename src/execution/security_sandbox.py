import re
import logging
import shutil

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.forbidden_commands = [
            r"rm -rf /", r"mkfs", r"dd if=", r":\(\)\{ :\|:& \};:"
        ]
        self.high_risk_commands = [
            r"rm", r"mv", r"systemctl stop", r"shutdown", r"reboot"
        ]
        
    def assess_risk(self, command):
        """
        Returns a risk level: 'low', 'medium', 'high', or 'blocked'.
        """
        for pattern in self.forbidden_commands:
            if re.search(pattern, command):
                return "blocked"
                
        for pattern in self.high_risk_commands:
            if re.search(pattern, command):
                return "high"
                
        if command.strip().startswith("sudo"):
            return "high"
            
        return "low"

    def validate_command(self, command):
        """
        Checks if a command is safe to execute.
        """
        risk = self.assess_risk(command)
        if risk == "blocked":
            logger.warning(f"Blocked dangerous command: {command}")
            return False, "Command is blocked by security policy."
        return True, risk
