import subprocess
import os
import platform
import sys

class SystemCommands:
    def __init__(self):
        self.os_type = platform.system()
    
    def list_files(self):
        """List files in current directory"""
        try:
            if self.os_type == "Windows":
                result = subprocess.run(["cmd", "/c", "dir"], 
                                      capture_output=True, text=True)
            else:
                result = subprocess.run(["ls", "-la"], 
                                      capture_output=True, text=True)
            return result.stdout[:500]  # Return first 500 chars
        except Exception as e:
            return f"Error: {e}"
    
    def open_application(self, app_name):
        """Open application by name (Windows)"""
        app_paths = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            "spotify": "spotify.exe",
            "vlc": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
        }
        
        try:
            if app_name.lower() in app_paths:
                path = app_paths[app_name.lower()]
                subprocess.Popen(path)
                return f"Opening {app_name}..."
            else:
                # Try to find it in PATH
                subprocess.Popen(app_name)
                return f"Opening {app_name}..."
        except Exception as e:
            return f"Error opening {app_name}: {e}"
    
    def open_browser(self, url=""):
        """Open default browser"""
        import webbrowser
        try:
            if url:
                webbrowser.open(url)
                return f"Opening {url}"
            else:
                webbrowser.open("http://www.google.com")
                return "Opening browser"
        except Exception as e:
            return f"Error: {e}"
    
    def get_time(self):
        """Get current time"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def get_date(self):
        """Get current date"""
        from datetime import datetime
        return datetime.now().strftime("%A, %B %d, %Y")
    
    def shutdown(self):
        """Shutdown computer"""
        try:
            if self.os_type == "Windows":
                subprocess.run(["shutdown", "/s", "/t", "60"])
                return "Computer will shutdown in 60 seconds"
            else:
                subprocess.run(["sudo", "shutdown", "-h", "now"])
                return "Computer shutting down"
        except Exception as e:
            return f"Error: {e}"
    
    def restart(self):
        """Restart computer"""
        try:
            if self.os_type == "Windows":
                subprocess.run(["shutdown", "/r", "/t", "60"])
                return "Computer will restart in 60 seconds"
            else:
                subprocess.run(["sudo", "shutdown", "-r", "now"])
                return "Computer restarting"
        except Exception as e:
            return f"Error: {e}"
    
    def lock_screen(self):
        """Lock the screen"""
        try:
            if self.os_type == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
                return "Screen locked"
            else:
                return "Lock screen not supported on this OS"
        except Exception as e:
            return f"Error: {e}"
