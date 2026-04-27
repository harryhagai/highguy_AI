import os
import subprocess
from pathlib import Path

class MusicPlayer:
    def __init__(self):
        self.is_playing = False
        self.current_track = None
        self.playlist = []
        self.current_index = 0
        self.load_playlist()
        self.process = None
    
    def load_playlist(self):
        """Load music files from Music folder"""
        music_path = str(Path.home() / "Music")
        try:
            for file in os.listdir(music_path):
                if file.endswith(('.mp3', '.wav', '.flac', '.m4a')):
                    self.playlist.append(os.path.join(music_path, file))
        except Exception as e:
            print(f"Error loading playlist: {e}")
    
    def play(self):
        """Play music"""
        try:
            if not self.playlist:
                return "No music files found in Music folder"
            
            track = self.playlist[self.current_index]
            self.current_track = os.path.basename(track)
            
            # Use Windows Media Player or default player
            self.process = subprocess.Popen(['start', track], shell=True)
            self.is_playing = True
            return f"Playing: {self.current_track}"
        except Exception as e:
            return f"Error playing music: {e}"
    
    def pause(self):
        """Pause music"""
        try:
            if self.is_playing and self.process:
                # Media player controls would go here
                return f"Paused: {self.current_track}"
            return "No music is playing"
        except Exception as e:
            return f"Error: {e}"
    
    def stop(self):
        """Stop music"""
        try:
            if self.process:
                self.process.terminate()
            self.is_playing = False
            return "Music stopped"
        except Exception as e:
            return f"Error: {e}"
    
    def next_track(self):
        """Play next track"""
        try:
            if not self.playlist:
                return "No music files found"
            
            self.stop()
            self.current_index = (self.current_index + 1) % len(self.playlist)
            return self.play()
        except Exception as e:
            return f"Error: {e}"
    
    def get_playlist_info(self):
        """Get playlist information"""
        if not self.playlist:
            return "No music files found"
        
        info = f"Playlist ({len(self.playlist)} songs):\n"
        for i, track in enumerate(self.playlist[:5], 1):
            info += f"{i}. {os.path.basename(track)}\n"
        return info
