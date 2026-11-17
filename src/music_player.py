"""Music player that plays songs from your Music folder.

On Windows it uses the built-in MCI audio system (winmm.dll), so play,
pause, resume and stop all work without installing anything.
"""

import os
import random
from pathlib import Path

MUSIC_EXTENSIONS = (".mp3", ".wav", ".wma", ".m4a", ".flac", ".aac")
ALIAS = "highguy_song"


class MusicPlayer:
    def __init__(self, music_folder=None):
        self.music_folder = Path(music_folder) if music_folder else Path.home() / "Music"
        self.playlist = []
        self.current_index = 0
        self.state = "stopped"  # "playing", "paused" or "stopped"
        self.uses_mci = os.name == "nt"
        self.load_playlist()

    # ------------------------------------------------------------------
    # Playlist
    # ------------------------------------------------------------------

    def set_folder(self, folder):
        self.stop()
        self.music_folder = Path(folder)
        self.current_index = 0
        return self.load_playlist()

    def load_playlist(self):
        """Find music files in the folder (and its sub-folders)."""
        self.playlist = []
        if self.music_folder.is_dir():
            for path in sorted(self.music_folder.rglob("*")):
                if path.suffix.lower() in MUSIC_EXTENSIONS:
                    self.playlist.append(path)
        return len(self.playlist)

    @property
    def current_track(self):
        if not self.playlist:
            return None
        return self.playlist[self.current_index].stem

    def find(self, query):
        """Return the index of the first song whose name contains the query."""
        query = query.lower().strip()
        for index, path in enumerate(self.playlist):
            if query in path.stem.lower():
                return index
        return None

    def playlist_info(self, limit=15):
        lines = []
        for index, path in enumerate(self.playlist[:limit]):
            marker = "▶" if index == self.current_index and self.state != "stopped" else " "
            lines.append(f"{marker} {index + 1:>2}. {path.stem}")
        if len(self.playlist) > limit:
            lines.append(f"     ... and {len(self.playlist) - limit} more")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Controls. Each returns (result_key, song_name) so the caller can
    # build a message in the right language.
    # ------------------------------------------------------------------

    def play(self, query=None):
        if not self.playlist:
            return "no_music", str(self.music_folder)

        if query:
            index = self.find(query)
            if index is None:
                return "song_not_found", query
            self.current_index = index
        elif self.state == "paused":
            return self.resume()

        self._close()
        track = self.playlist[self.current_index]
        try:
            if self.uses_mci:
                self._mci(f'open "{track}" type mpegvideo alias {ALIAS}')
                self._mci(f"play {ALIAS}")
            else:
                os.startfile(track)  # Fallback: open in the default player
        except (RuntimeError, OSError) as error:
            return "music_error", str(error)

        self.state = "playing"
        return "playing", track.stem

    def pause(self):
        if self.state != "playing":
            return "no_music_playing", None
        if self.uses_mci:
            self._mci(f"pause {ALIAS}")
        self.state = "paused"
        return "paused", self.current_track

    def resume(self):
        if self.state != "paused":
            return "no_music_playing", None
        if self.uses_mci:
            self._mci(f"resume {ALIAS}")
        self.state = "playing"
        return "playing", self.current_track

    def stop(self):
        was_on = self.state != "stopped"
        self._close()
        self.state = "stopped"
        return ("stopped", self.current_track) if was_on else ("no_music_playing", None)

    def next_track(self):
        if not self.playlist:
            return "no_music", str(self.music_folder)
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.state = "stopped"
        return self.play()

    def previous_track(self):
        if not self.playlist:
            return "no_music", str(self.music_folder)
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.state = "stopped"
        return self.play()

    def shuffle(self):
        if not self.playlist:
            return "no_music", str(self.music_folder)
        self.current_index = random.randrange(len(self.playlist))
        self.state = "stopped"
        return self.play()

    def status(self):
        """Short text for the status bar."""
        if self.state == "stopped" or not self.playlist:
            return "off"
        # The song may have finished on its own.
        if self.uses_mci and self.state == "playing":
            try:
                if self._mci(f"status {ALIAS} mode") == "stopped":
                    self.state = "stopped"
                    return "off"
            except RuntimeError:
                self.state = "stopped"
                return "off"
        name = self.current_track
        if len(name) > 22:
            name = name[:21] + "…"
        return ("▶ " if self.state == "playing" else "❚❚ ") + name

    # ------------------------------------------------------------------
    # Windows MCI helpers
    # ------------------------------------------------------------------

    def _close(self):
        if self.uses_mci:
            try:
                self._mci(f"close {ALIAS}")
            except RuntimeError:
                pass  # Nothing was open

    @staticmethod
    def _mci(command):
        """Send a command string to Windows MCI and return its answer."""
        import ctypes

        buffer = ctypes.create_unicode_buffer(256)
        error_code = ctypes.windll.winmm.mciSendStringW(command, buffer, 255, 0)
        if error_code:
            message = ctypes.create_unicode_buffer(256)
            ctypes.windll.winmm.mciGetErrorStringW(error_code, message, 255)
            raise RuntimeError(message.value or f"MCI error {error_code}")
        return buffer.value
