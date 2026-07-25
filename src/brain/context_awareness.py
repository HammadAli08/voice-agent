import psutil
import datetime
import subprocess
import logging
import shutil

logger = logging.getLogger(__name__)

class ContextAwareness:
    def get_context(self):
        return {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
            "active_app": self.get_active_window(),
            # "clipboard": self.get_clipboard_content() # Optional, might be sensitive
        }

    def get_active_window(self):
        """
        Attempts to get the active window title on Fedora (GNOME/Wayland).
        """
        # Method 1: PyGObject with Wnck (often fails on Wayland/pip)
        # Method 2: GNOME Shell extensions via DBus
        # Method 3: Parsing `gnome-shell` evaluations (unsafe/restricted)
        # Method 4: External tools like `wlrctl` (if installed)
        
        # Trying a common GNOME Shell script via gdbus (may require specialized extension)
        # Fallback to "Unknown" if not possible.
        
        try:
            # Simple check for simple environments, but on Wayland strict, this is hard.
            # We will try to use `gdbus` to ask introspection if available.
            # For now, return a placeholder or try `xdotool` if XWayland is active? No, native Wayland requested.
            
            # Using a safer, generic stub for now as accurate Wayland window tracking 
            # often requires a specific GNOME Shell extension to be installed.
            # The prompt mentioned "GNOME Introspection API".
            
            # Let's try to see if we can get the primitive focus from localized shell
            return "Unknown (Wayland Restricted)"
        except Exception:
            return "Unknown"

    def get_clipboard_content(self):
        if shutil.which("wl-paste"):
            try:
                return subprocess.check_output(["wl-paste"], text=True).strip()
            except:
                return ""
        return ""
