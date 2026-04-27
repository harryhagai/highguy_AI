#!/usr/bin/env python3
"""
Voice-Controlled AI Assistant
Local, rule-based Python assistant with no external AI dependencies
Supports English and Swahili
"""

import sys
import os
from voice_handler import VoiceHandler
from command_processor import CommandProcessor

class AIAssistant:
    def __init__(self, language="auto"):
        print("\n" + "="*50)
        print("🤖 Voice-Controlled AI Assistant")
        print("="*50)
        print("Starting up...\n")
        
        self.language = language
        self.voice = VoiceHandler(language if language != "auto" else "english")
        self.processor = CommandProcessor(language if language != "auto" else "english")
        self.running = True
        self.current_language = language if language != "auto" else "english"
        
        # Greet user based on language
        if self.language == "swahili" or self.language == "auto":
            self.voice.speak("Habari! Mimi ni msaada wako wa sauti. Sema 'msaada' ili kujua amri zinazopatikana.")
        else:
            self.voice.speak("Hello! I'm your AI assistant. Say help to learn what I can do.")
    
    def run(self):
        """Main loop - listen and process commands"""
        if self.language == "swahili":
            print("Listening for Swahili commands... (Say 'kwaheri' to quit)\n")
        elif self.language == "english":
            print("Listening for English commands... (Say 'exit' to quit)\n")
        else:
            print("Listening for commands in any language... (Say 'exit' or 'kwaheri' to quit)\n")
        
        while self.running:
            try:
                # Listen for voice input
                user_input = self.voice.listen(timeout=5)
                
                if user_input is None:
                    continue
                
                # Detect language if in auto mode
                if self.language == "auto":
                    detected_lang = self.processor.detect_language(user_input)
                    self.processor.language = detected_lang
                    self.voice.set_language(detected_lang)
                
                # Check for exit commands in both languages
                exit_keywords = ['exit', 'quit', 'bye', 'goodbye', 'kwaheri', 'karibu', 'pole', 'goodbye']
                if any(word in user_input for word in exit_keywords):
                    if self.language == "swahili" or (self.language == "auto" and self.processor.detect_language(user_input) == "swahili"):
                        self.voice.speak("Kwaheri! Tutaonana baadaye.")
                    else:
                        self.voice.speak("Goodbye! See you later.")
                    self.running = False
                    break
                
                # Process and execute command
                response = self.processor.process_command(user_input)
                
                # Speak response
                self.voice.speak(response)
                
                print("-" * 50 + "\n")
                
            except KeyboardInterrupt:
                print("\n\nShutting down...")
                if self.language == "swahili":
                    self.voice.speak("Kwaheri!")
                else:
                    self.voice.speak("Goodbye!")
                self.running = False
            except Exception as e:
                print(f"Error: {e}")
                if self.language == "swahili":
                    self.voice.speak("Hitilafu ilitokea. Tafadhali jaribu tena.")
                else:
                    self.voice.speak("An error occurred. Please try again.")

def main():
    try:
        # Check for language argument
        language = "auto"  # Default: auto-detect
        
        if len(sys.argv) > 1:
            if sys.argv[1].lower() in ["swahili", "sw"]:
                language = "swahili"
            elif sys.argv[1].lower() in ["english", "en"]:
                language = "english"
            elif sys.argv[1].lower() in ["auto"]:
                language = "auto"
        
        print(f"Language mode: {language.upper()}")
        
        assistant = AIAssistant(language)
        assistant.run()
    except Exception as e:
        print(f"Failed to start assistant: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
