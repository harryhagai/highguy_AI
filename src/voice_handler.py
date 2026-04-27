import speech_recognition as sr
import pyttsx3
import threading

class VoiceHandler:
    def __init__(self, language="english"):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Speech speed
        self.engine.setProperty('volume', 1.0)  # Volume 0-1
        self.language = language
        
        # Set voice based on language
        self.set_language(language)
    
    def set_language(self, language):
        """Set language for text-to-speech"""
        self.language = language
        voices = self.engine.getProperty('voices')
        
        if language == "swahili":
            # Use a male voice for Swahili if available
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id)
        else:
            # Use default voice for English
            if len(voices) > 0:
                self.engine.setProperty('voice', voices[0].id)
    
    def listen(self, timeout=5):
        """Listen to user voice input and return text"""
        try:
            with sr.Microphone() as source:
                print("🎤 Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=timeout)
                
            print("Processing...")
            # Try to recognize in multiple languages
            try:
                text = self.recognizer.recognize_google(audio, language='en-US')
            except:
                try:
                    text = self.recognizer.recognize_google(audio, language='sw-TZ')
                except:
                    text = self.recognizer.recognize_google(audio)
            
            print(f"You said: {text}")
            return text.lower()
        except sr.UnknownValueError:
            self.speak("Sorry, I didn't catch that")
            return None
        except sr.RequestError as e:
            print(f"Error: {e}")
            self.speak("Sorry, I'm having trouble listening")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def speak(self, text):
        """Convert text to speech"""
        print(f"🤖 Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
    
    def speak_async(self, text):
        """Speak asynchronously (non-blocking)"""
        thread = threading.Thread(target=self.speak, args=(text,))
        thread.daemon = True
        thread.start()
