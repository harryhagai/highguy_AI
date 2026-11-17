"""Speech input (microphone) and speech output (text-to-speech).

Everything here is optional. If a package is missing, the assistant keeps
working with typed commands and explains what to install.

- Listening needs:  SpeechRecognition + a microphone library - PyAudio, or
                    sounddevice (works on Python 3.14) - and internet for
                    Google speech recognition.
- Speaking uses:    pyttsx3 if installed, otherwise the voice built into
                    Windows (through PowerShell). No install needed.
"""

import math
import os
import shutil
import subprocess
import threading
from array import array
from collections import deque

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import sounddevice as sd
except (ImportError, OSError):  # OSError: PortAudio library missing
    sd = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

CHUNK_SECONDS = 0.1
SILENCE_TO_STOP = 0.8  # seconds of quiet that end a phrase


def loudness(chunk):
    """RMS loudness of 16-bit mono audio."""
    samples = array("h", chunk)
    if not samples:
        return 0.0
    return math.sqrt(sum(x * x for x in samples) / len(samples))


class VoiceHandler:
    def __init__(self, language="english"):
        self.language = language
        self.recognizer = sr.Recognizer() if sr else None
        self.backend = None  # "pyaudio" or "sounddevice"
        self.listen_problem = self._check_microphone()
        self.engine = self._start_tts_engine()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def can_listen(self):
        return self.listen_problem is None

    @property
    def can_speak(self):
        return self.engine is not None or self._windows_voice_available()

    def _check_microphone(self):
        """Return None when the microphone works, otherwise a reason why not."""
        if sr is None:
            return "SpeechRecognition is not installed (pip install SpeechRecognition)."
        try:
            if sr.Microphone.list_microphone_names():
                self.backend = "pyaudio"
                return None
        except Exception:  # PyAudio missing or broken - try sounddevice
            pass
        if sd is None:
            return "No microphone library found (pip install sounddevice)."
        try:
            sd.query_devices(kind="input")
        except Exception:
            return "No microphone was found."
        self.backend = "sounddevice"
        return None

    def _start_tts_engine(self):
        if pyttsx3 is None:
            return None
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.setProperty("volume", 1.0)
            return engine
        except Exception:
            return None

    @staticmethod
    def _windows_voice_available():
        return os.name == "nt" and shutil.which("powershell") is not None

    def set_language(self, language):
        self.language = language

    # ------------------------------------------------------------------
    # Listening
    # ------------------------------------------------------------------

    def listen(self, timeout=6, phrase_limit=10, on_sound=None):
        """Record one phrase and return it as lowercase text.

        Returns (text, None) on success or (None, reason) when nothing was
        understood. Ctrl+C is passed on so the caller can stop voice mode.
        on_sound(level, recording) is called about 10 times a second while
        listening (sounddevice only): level is 0.0-1.0, recording is True
        once speech has started. on_sound(None, False) means "recognizing".
        """
        if not self.can_listen:
            return None, self.listen_problem

        try:
            if self.backend == "pyaudio":
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                    audio = self.recognizer.listen(
                        source, timeout=timeout, phrase_time_limit=phrase_limit
                    )
            else:
                audio = self._record_with_sounddevice(timeout, phrase_limit, on_sound)
        except sr.WaitTimeoutError:
            return None, "timeout"
        except Exception as error:  # OSError, sounddevice.PortAudioError
            return None, f"Microphone error: {error}"

        if on_sound:
            on_sound(None, False)

        # Swahili mode asks Google for Swahili (Tanzania) first.
        if self.language == "swahili":
            languages = ["sw-TZ", "en-US"]
        else:
            languages = ["en-US", "sw-TZ"]

        for code in languages:
            try:
                text = self.recognizer.recognize_google(audio, language=code)
                return text.lower(), None
            except sr.UnknownValueError:
                continue
            except sr.RequestError as error:
                return None, f"Speech service unavailable (check internet): {error}"
        return None, "not_understood"

    @staticmethod
    def _record_with_sounddevice(timeout, phrase_limit, on_sound=None):
        """Wait for speech, record until the speaker stops, return AudioData."""
        rate = int(sd.query_devices(kind="input")["default_samplerate"])
        frames_per_chunk = int(rate * CHUNK_SECONDS)

        with sd.RawInputStream(samplerate=rate, channels=1, dtype="int16",
                               blocksize=frames_per_chunk) as stream:
            def read():
                data, _overflowed = stream.read(frames_per_chunk)
                return bytes(data)

            def report(chunk, recording):
                if on_sound:
                    on_sound(min(1.0, loudness(chunk) / (threshold * 3)), recording)

            for _ in range(3):  # the first chunks are silent while the mic starts
                read()
            # Measure the room noise, then wait for something clearly louder.
            ambient = max(loudness(read()) for _ in range(5))
            threshold = max(ambient * 2.5, 300)
            report(b"", False)

            before = deque(maxlen=4)  # keep the start of the first word
            loud_in_a_row = 0
            waited = 0.0
            while loud_in_a_row < 2:  # 0.2 s of sound, so a click does not count
                chunk = read()
                before.append(chunk)
                loud_in_a_row = loud_in_a_row + 1 if loudness(chunk) > threshold else 0
                report(chunk, False)
                waited += CHUNK_SECONDS
                if waited >= timeout:
                    raise sr.WaitTimeoutError("no speech")

            frames = list(before)
            length = quiet = 0.0
            while length < phrase_limit and quiet < SILENCE_TO_STOP:
                chunk = read()
                frames.append(chunk)
                report(chunk, True)
                length += CHUNK_SECONDS
                quiet = 0.0 if loudness(chunk) > threshold else quiet + CHUNK_SECONDS

        return sr.AudioData(b"".join(frames), rate, 2)

    # ------------------------------------------------------------------
    # Speaking
    # ------------------------------------------------------------------

    def speak(self, text):
        """Read text out loud. Waits until speaking is finished."""
        text = " ".join(str(text).split())  # one line, no extra spaces
        if not text:
            return
        with self._lock:
            # pyttsx3 must stay on the thread that created it; background
            # speech (reminders, async replies) uses the Windows voice instead.
            on_main_thread = threading.current_thread() is threading.main_thread()
            if self.engine is not None and on_main_thread:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                    return
                except Exception:
                    self.engine = None  # fall back to the Windows voice
            if self._windows_voice_available():
                self._speak_with_windows(text)

    def speak_async(self, text):
        """Speak in the background so the UI does not freeze."""
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()
        return thread

    @staticmethod
    def _speak_with_windows(text):
        # The text is passed through an environment variable, never pasted
        # into the command itself, so it cannot run as code.
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Speak($env:HIGHGUY_SAY)"
        )
        env = dict(os.environ, HIGHGUY_SAY=text)
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
