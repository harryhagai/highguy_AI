import json
import os
from system_commands import SystemCommands
from music_player import MusicPlayer

class CommandProcessor:
    def __init__(self, language="english"):
        self.system = SystemCommands()
        self.music = MusicPlayer()
        self.commands = self.load_commands()
        self.language = language
        self.responses = self.load_responses()
    
    def load_commands(self):
        """Load command definitions from JSON"""
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "config", "commands.json"
            )
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading commands: {e}")
            return {}
    
    def load_responses(self):
        """Load response translations"""
        return {
            "english": {
                "greeting_response": "Hello! How can I help you?",
                "help_header": "Available Commands:",
                "time_response": "The time is {time}",
                "date_response": "Today is {date}",
                "opening_app": "Opening {app}",
                "playing_music": "Playing: {track}",
                "paused_music": "Paused: {track}",
                "stopped_music": "Music stopped",
                "no_music": "No music is playing",
                "list_files_label": "• Files: List files, Show files",
                "not_understood": "I didn't understand that command. Say 'help' for available commands.",
                "error": "An error occurred: {error}"
            },
            "swahili": {
                "greeting_response": "Habari! Ninaweza kukusaidia vipi?",
                "help_header": "Amri Zinazopatikana:",
                "time_response": "Saa ni {time}",
                "date_response": "Leo ni {date}",
                "opening_app": "Inafungua {app}",
                "playing_music": "Inacheza: {track}",
                "paused_music": "Imesimama: {track}",
                "stopped_music": "Muziki imesimama",
                "no_music": "Hakuna muziki inayocheza",
                "list_files_label": "• Faili: Orodha ya faili, Onyesha faili",
                "not_understood": "Sijaelewi amri hiyo. Sema 'msaada' kwa amri zinazopatikana.",
                "error": "Hitilafu ilitokea: {error}"
            }
        }
    
    def detect_language(self, user_input):
        """Detect if input is in Swahili or English"""
        swahili_keywords = ["habari", "salaam", "jambo", "muziki", "fungua", "saa", "tarehe", "leo", "msaada"]
        english_keywords = ["hello", "hi", "time", "date", "play", "open", "help"]
        
        swahili_count = sum(1 for word in swahili_keywords if word in user_input)
        english_count = sum(1 for word in english_keywords if word in user_input)
        
        if swahili_count > english_count:
            return "swahili"
        return "english"
    
    def process_command(self, user_input):
        """Process user voice input and execute appropriate action"""
        if not user_input:
            return "Please say something"
        
        user_input = user_input.lower().strip()
        
        # Detect language
        detected_lang = self.detect_language(user_input)
        lang_commands = self.commands.get(detected_lang, {})
        responses = self.responses.get(detected_lang, self.responses["english"])
        
        # Greetings
        if any(word in user_input for word in lang_commands.get("greetings", [])):
            return responses["greeting_response"]
        
        # Help
        if any(word in user_input for word in lang_commands.get("help", [])):
            return self.get_help(detected_lang)
        
        # Time
        if any(word in user_input for word in lang_commands.get("time", [])):
            time_str = self.system.get_time()
            return responses["time_response"].format(time=time_str)
        
        # Date
        if any(word in user_input for word in lang_commands.get("date", [])):
            date_str = self.system.get_date()
            return responses["date_response"].format(date=date_str)
        
        # Open applications
        for app_name, keywords in lang_commands.get("open_apps", {}).items():
            if any(keyword in user_input for keyword in keywords):
                result = self.system.open_application(app_name)
                return responses["opening_app"].format(app=app_name)
        
        # Music commands
        music_commands = lang_commands.get("music", {})
        
        if any(keyword in user_input for keyword in music_commands.get("play", [])):
            return self.music.play()
        
        if any(keyword in user_input for keyword in music_commands.get("stop", [])):
            return self.music.stop()
        
        if any(keyword in user_input for keyword in music_commands.get("next", [])):
            return self.music.next_track()
        
        # System commands
        if any(keyword in user_input for keyword in lang_commands.get("system", {}).get("list_files", [])):
            return self.system.list_files()
        
        if any(keyword in user_input for keyword in lang_commands.get("system", {}).get("lock", [])):
            return self.system.lock_screen()
        
        # Default response
        return responses["not_understood"]
    
    def get_help(self, language="english"):
        """Return list of available commands in specified language"""
        if language == "swahili":
            help_text = """
Amri Zinazopatikana:
• Salamu: Habari, Salaam, Jambo
• Msaada: Msaada, Unaweza kufanya nini
• Saa: Saa gani, Saa ya sasa
• Tarehe: Tarehe gani, Leo
• Fungua Programu: Fungua Chrome, Fungua Notepad, Fungua Calculator, n.k.
• Muziki: Cheza muziki, Simama muziki, Nyimbo inayofuata
• Faili: Orodha ya faili, Onyesha faili
• Mfumo: Funga skrini
            """
        else:
            help_text = """
Available Commands:
• Greetings: Hi, Hello, Hey
• Help: Help, What can you do
• Time: What time is it, Current time
• Date: What is the date, Today
• Open Apps: Open Chrome, Open Notepad, Open Calculator, etc.
• Music: Play music, Stop music, Next song
• Files: List files, Show files
• System: Lock screen
            """
        return help_text
    
    def add_custom_command(self, keyword, response):
        """Add custom command (can be extended)"""
        # This can be extended to dynamically add commands
        pass
