import subprocess
import logging
from src.execution.security_sandbox import SecurityManager

logger = logging.getLogger(__name__)

class ShellExecutor:
    def __init__(self):
        self.security = SecurityManager()

    def execute(self, command, confirm_override=False):
        """
        Executes a shell command if allowed.
        """
        valid, risk = self.security.validate_command(command)
        
        if not valid:
            return {"status": "error", "message": risk}
            
        if risk == "high" and not confirm_override:
            return {"status": "pending_confirmation", "message": "High risk command. Confirmation required.", "risk": "high"}

        try:
            # Using subprocess.run for safer execution
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=10 # Prevent hanging
            )
            
            if result.returncode == 0:
                return {"status": "success", "output": result.stdout.strip()}
            else:
                return {"status": "error", "message": result.stderr.strip()}
        
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Command timed out."}
        except Exception as e:
            logger.error(f"Execution Error: {e}")
            return {"status": "error", "message": str(e)}
