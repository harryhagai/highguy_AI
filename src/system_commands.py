"""Safe system actions: open apps and websites, show files, lock, shut down."""

import os
import platform
import shutil
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

# Name -> what Windows should start. Windows finds most of these through its
# "App Paths" registry, so we do not need full install paths.
APP_TARGETS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "spotify": "spotify:",
    "vlc": "vlc.exe",
    "explorer": "explorer.exe",
    "paint": "mspaint.exe",
    "settings": "ms-settings:",
    "task manager": "taskmgr.exe",
    "cmd": "cmd.exe",
}

PROTECTED_PROCESSES = {
    "explorer.exe", "cmd.exe", "powershell.exe", "pwsh.exe", "conhost.exe",
    "windowsterminal.exe", "python.exe", "py.exe", "taskmgr.exe",
}

WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
}


class SystemCommands:
    def __init__(self):
        self.os_type = platform.system()

    def list_files(self, folder=None):
        """Return a short listing of the files in a folder."""
        folder = Path(folder or Path.cwd())
        try:
            entries = sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError as error:
            return f"Error: {error}"

        lines = [f"{folder}"]
        for entry in entries[:25]:
            if entry.is_dir():
                lines.append(f"  [DIR]  {entry.name}")
            else:
                try:
                    size = entry.stat().st_size
                except OSError:
                    size = 0
                lines.append(f"  {self._format_size(size):>7}  {entry.name}")
        if len(entries) > 25:
            lines.append(f"  ... and {len(entries) - 25} more")
        return "\n".join(lines)

    def find_application(self, app_name):
        """Return what to start for an app name, or None if it is not installed."""
        name = app_name.lower().strip()
        if name in APP_TARGETS:
            return APP_TARGETS[name]

        # Program on the PATH (e.g. "code", "python")
        found = shutil.which(name) or shutil.which(name.replace(" ", ""))
        if found:
            return found

        # Program registered in Windows "App Paths" (e.g. "winword", "excel")
        if self.os_type == "Windows":
            import winreg

            exe = name.replace(" ", "") + ".exe"
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths" + "\\" + exe
            for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                try:
                    with winreg.OpenKey(root, key_path):
                        return exe
                except OSError:
                    continue
        return None

    def open_application(self, app_name):
        """Start an application. Returns (ok, app_name)."""
        target = self.find_application(app_name)
        if target is None:
            return False, app_name
        try:
            if self.os_type == "Windows":
                # startfile uses the Windows shell, which knows installed apps.
                os.startfile(target)
            else:
                subprocess.Popen([target])
            return True, app_name
        except OSError:
            return False, app_name

    def close_application(self, app_name):
        """Ask an app to close (like clicking X). Returns True on success."""
        if self.os_type != "Windows":
            return False
        target = self.find_application(app_name)
        if not target or not target.lower().endswith(".exe"):
            return False
        exe = Path(target).name.lower()
        # Never close Windows itself or the window this assistant runs in.
        if exe in PROTECTED_PROCESSES:
            return False
        result = subprocess.run(["taskkill", "/IM", exe], capture_output=True, check=False)
        return result.returncode == 0

    def open_website(self, name_or_url):
        url = WEBSITES.get(name_or_url.lower(), name_or_url)
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return url

    def web_search(self, query):
        url = "https://www.google.com/search?q=" + quote_plus(query)
        webbrowser.open(url)
        return query

    def get_time(self):
        return datetime.now().strftime("%H:%M:%S")

    def get_date(self):
        return datetime.now().strftime("%A, %d %B %Y")

    def system_info(self):
        """Return OS, battery and disk information."""
        lines = [
            f"Computer: {platform.node()}",
            f"System:   {platform.system()} {platform.release()}",
            f"Python:   {platform.python_version()}",
        ]

        disk = shutil.disk_usage(Path.home().anchor or "/")
        lines.append(
            f"Disk:     {self._format_size(disk.free)} free of {self._format_size(disk.total)}"
        )

        battery = self._battery_status()
        if battery:
            lines.append(f"Battery:  {battery}")
        return "\n".join(lines)

    def shutdown(self):
        """Shut down in 60 seconds (can be cancelled)."""
        return self._power_command(["shutdown", "/s", "/t", "60"])

    def restart(self):
        """Restart in 60 seconds (can be cancelled)."""
        return self._power_command(["shutdown", "/r", "/t", "60"])

    def cancel_shutdown(self):
        return self._power_command(["shutdown", "/a"])

    def lock_screen(self):
        if self.os_type != "Windows":
            return False
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _power_command(self, command):
        if self.os_type != "Windows":
            return False
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result.returncode == 0

    def _battery_status(self):
        """Read the battery level using the Windows API (no extra packages)."""
        if self.os_type != "Windows":
            return None
        try:
            import ctypes

            class PowerStatus(ctypes.Structure):
                _fields_ = [
                    ("ACLineStatus", ctypes.c_ubyte),
                    ("BatteryFlag", ctypes.c_ubyte),
                    ("BatteryLifePercent", ctypes.c_ubyte),
                    ("SystemStatusFlag", ctypes.c_ubyte),
                    ("BatteryLifeTime", ctypes.c_ulong),
                    ("BatteryFullLifeTime", ctypes.c_ulong),
                ]

            status = PowerStatus()
            if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
                return None
            if status.BatteryFlag == 128 or status.BatteryLifePercent == 255:
                return "No battery (desktop PC)"
            plugged = "charging" if status.ACLineStatus == 1 else "on battery"
            return f"{status.BatteryLifePercent}% ({plugged})"
        except (OSError, AttributeError):
            return None

    @staticmethod
    def _format_size(size):
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
