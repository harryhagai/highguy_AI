#!/usr/bin/env python3
"""
Voice-Controlled AI Assistant - Demo Version
Shows command processing without speech recognition
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from command_processor import CommandProcessor
from system_commands import SystemCommands

class DemoAssistant:
    def __init__(self, language="english"):
        print("\n" + "="*60)
        print("🤖 Voice-Controlled AI Assistant - DEMO MODE")
        print("="*60)
        print("(Speech Recognition temporarily disabled)")
        print("Type commands directly to test the system\n")
        
        self.processor = CommandProcessor(language)
        self.language = language
        self.running = True
    
    def run(self):
        """Main loop - process text commands"""
        if self.language == "swahili":
            print("Skrini ya Mtihani (Demo) - Kiswahili")
            print("Andika amri za mtihani...\n")
            print("Mifano:")
            print('  "habari" - Salamu')
            print('  "saa gani" - Nini saa?')
            print('  "msaada" - Orodha ya amri')
            print('  "kwaheri" - Kuondoka\n')
        else:
            print("Demo Mode - English")
            print("Type test commands...\n")
            print("Examples:")
            print('  "hello" - Greeting')
            print('  "what time is it" - Get time')
            print('  "help" - List commands')
            print('  "exit" - Quit\n')
        
        while self.running:
            try:
                # Get text input instead of voice
                if self.language == "swahili":
                    user_input = input("Amri (Kiswahili): ").strip()
                else:
                    user_input = input("Command (English): ").strip()
                
                if not user_input:
                    continue
                
                user_input = user_input.lower()
                
                # Check for exit commands
                exit_keywords = ['exit', 'quit', 'bye', 'goodbye', 'kwaheri', 'karibu']
                if any(word in user_input for word in exit_keywords):
                    if self.language == "swahili":
                        print("🤖 Assistant: Kwaheri! Tutaonana baadaye.")
                    else:
                        print("🤖 Assistant: Goodbye! See you later.")
                    self.running = False
                    break
                
                # Process command
                response = self.processor.process_command(user_input)
                print(f"🤖 Assistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nShutting down...")
                if self.language == "swahili":
                    print("🤖 Assistant: Kwaheri!")
                else:
                    print("🤖 Assistant: Goodbye!")
                self.running = False
            except Exception as e:
                print(f"Error: {e}")
                if self.language == "swahili":
                    print("🤖 Assistant: Hitilafu ilitokea. Tafadhali jaribu tena.\n")
                else:
                    print("🤖 Assistant: An error occurred. Please try again.\n")

def main():
    language = "english"
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ["swahili", "sw"]:
            language = "swahili"
        elif sys.argv[1].lower() in ["english", "en"]:
            language = "english"
    
    print(f"Language: {language.upper()}")
    
    assistant = DemoAssistant(language)
    assistant.run()

if __name__ == "__main__":
    main()
