"""Understand typed or spoken commands (English and Swahili) and run them."""

import json
import os
import re
from datetime import datetime

from ai_engine import AIEngine
from memory_manager import MemoryManager
from music_player import MusicPlayer
from reminders import parse_reminder
from system_commands import SystemCommands

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "commands.json")

# Words that tell us which language the user is speaking.
SWAHILI_HINTS = {
    "habari", "salaam", "jambo", "mambo", "hujambo", "shikamoo", "muziki",
    "mziki", "fungua", "saa", "ngapi", "tarehe", "leo", "msaada", "cheza",
    "kumbuka", "tafuta", "nini", "gani", "wimbo", "nyimbo", "faili",
    "kompyuta", "zima", "funga", "asante", "kwaheri", "ni", "ya", "na",
    "kwa", "jina", "langu", "wewe", "mimi", "onyesha", "orodha", "sitisha",
    "simama", "endelea", "unaweza", "kufanya", "amri", "skrini", "upya",
    "niite", "unakumbuka", "kuhusu", "nikumbushe", "hifadhi", "ruka",
    "betri", "mipangilio", "kikokotoo", "nani", "hali", "poa", "sana",
}
ENGLISH_HINTS = {
    "hello", "hi", "hey", "time", "date", "play", "open", "help", "what",
    "the", "is", "my", "show", "list", "search", "remember", "stop", "music",
    "song", "you", "how", "please", "thanks", "thank", "file", "files",
    "computer", "today", "next", "name", "who", "are", "lock", "about",
    "close", "pause", "resume", "shuffle", "previous", "skip", "songs",
    "screen", "info", "system", "shutdown", "restart", "cancel", "call",
}

SWAHILI_DAYS = ["Jumatatu", "Jumanne", "Jumatano", "Alhamisi", "Ijumaa", "Jumamosi", "Jumapili"]
SWAHILI_MONTHS = ["Januari", "Februari", "Machi", "Aprili", "Mei", "Juni", "Julai",
                  "Agosti", "Septemba", "Oktoba", "Novemba", "Desemba"]

# Filler words removed from "play ..." so "play some music" means "any song".
PLAY_FILLER = {"music", "song", "songs", "some", "a", "the", "muziki", "mziki", "wimbo", "nyimbo"}

RESPONSES = {
    "english": {
        "greeting": "Hello{name}! How can I help you?",
        "how_are_you": "I'm doing great, thanks for asking{name}! How can I help?",
        "thanks": "You're welcome{name}!",
        "about": ("I'm Highguy AI, your local assistant. I can open apps and websites, "
                  "play music, tell the time and date, and remember things for you."),
        "time": "The time is {time}.",
        "date": "Today is {date}.",
        "opening_app": "Opening {app}...",
        "closing_app": "Closing {app}.",
        "close_failed": "{app} is not open, or I can't close it.",
        "app_not_found": "I couldn't find '{app}' on this computer.",
        "opening_website": "Opening {site} in your browser.",
        "searching": "Searching the web for: {query}",
        "search_empty": "What should I search for? Example: search python tutorials",
        "playing": "Now playing: {track}",
        "paused": "Paused: {track}",
        "stopped": "Music stopped.",
        "no_music_playing": "No music is playing.",
        "no_music": "No music files found in {track}. You can change the folder in Settings.",
        "song_not_found": "I couldn't find a song called '{track}'.",
        "music_error": "Could not play the song: {track}",
        "playlist": "Your songs ({count}):\n{songs}",
        "lock": "Locking the screen.",
        "shutdown_confirm": "Shut down the computer in 60 seconds?",
        "restart_confirm": "Restart the computer in 60 seconds?",
        "shutdown_started": "The computer will shut down in 60 seconds. Say 'cancel shutdown' to stop it.",
        "restart_started": "The computer will restart in 60 seconds. Say 'cancel shutdown' to stop it.",
        "cancelled": "Okay, I won't do that.",
        "cancel_done": "Shutdown cancelled.",
        "cancel_none": "There was no shutdown or restart to cancel.",
        "not_supported": "That only works on Windows.",
        "memory_saved": "Got it! I'll remember: {text}",
        "memory_empty": "What should I remember? Example: remember my keys are on the table",
        "recall_none": "I don't remember anything about '{topic}' yet.",
        "recall_summary": "I remember {count} things. Latest:\n{items}",
        "recall_nothing": "I don't remember anything yet. Teach me with: remember <something>",
        "name_saved": "Nice to meet you, {name}!",
        "name_empty": "What's your name? Example: my name is Harry",
        "reminder_set": "Okay{name}, I'll remind you to {message} at {time}.",
        "reminder_none": "You have no reminders.",
        "reminder_list": "Your reminders:\n{items}",
        "good_morning": "Good morning", "good_afternoon": "Good afternoon",
        "good_evening": "Good evening",
        "briefing": "{greeting}{name}! It's {time} on {date}.",
        "briefing_battery": "Battery: {battery}.",
        "briefing_reminders": "Reminders today: {items}.",
        "briefing_no_reminders": "No reminders waiting.",
        "briefing_memories": "I'm keeping {count} memories for you.",
        "not_understood": ("I didn't understand that. Type 'help' to see what I can do, "
                           "or teach me with 'remember ...'."),
        "error": "An error occurred: {error}",
    },
    "swahili": {
        "greeting": "Habari{name}! Nikusaidie nini?",
        "how_are_you": "Niko poa sana, asante{name}! Nikusaidie nini?",
        "thanks": "Karibu sana{name}!",
        "about": ("Mimi ni Highguy AI, msaidizi wako wa kompyuta. Naweza kufungua programu "
                  "na tovuti, kucheza muziki, kukuambia saa na tarehe, na kukumbuka mambo."),
        "time": "Sasa ni {time}.",
        "date": "Leo ni {date}.",
        "opening_app": "Ninafungua {app}...",
        "closing_app": "Ninafunga {app}.",
        "close_failed": "{app} haijafunguliwa, au siwezi kuifunga.",
        "app_not_found": "Sikuweza kupata '{app}' kwenye kompyuta hii.",
        "opening_website": "Ninafungua {site} kwenye kivinjari.",
        "searching": "Ninatafuta mtandaoni: {query}",
        "search_empty": "Nitafute nini? Mfano: tafuta habari za leo",
        "playing": "Sasa inacheza: {track}",
        "paused": "Nimesimamisha: {track}",
        "stopped": "Muziki umesimama.",
        "no_music_playing": "Hakuna muziki unaocheza.",
        "no_music": "Hakuna nyimbo kwenye {track}. Badilisha folda kwenye Mipangilio.",
        "song_not_found": "Sikupata wimbo unaoitwa '{track}'.",
        "music_error": "Imeshindikana kucheza wimbo: {track}",
        "playlist": "Nyimbo zako ({count}):\n{songs}",
        "lock": "Ninafunga skrini.",
        "shutdown_confirm": "Kuzima kompyuta baada ya sekunde 60?",
        "restart_confirm": "Kuwasha upya kompyuta baada ya sekunde 60?",
        "shutdown_started": "Kompyuta itazima baada ya sekunde 60. Sema 'sitisha kuzima' kuzuia.",
        "restart_started": "Kompyuta itawaka upya baada ya sekunde 60. Sema 'sitisha kuzima' kuzuia.",
        "cancelled": "Sawa, sitafanya hivyo.",
        "cancel_done": "Kuzima kumesitishwa.",
        "cancel_none": "Hakukuwa na kuzima kwa kusitisha.",
        "not_supported": "Hii inafanya kazi kwenye Windows tu.",
        "memory_saved": "Sawa! Nitakumbuka: {text}",
        "memory_empty": "Nikumbuke nini? Mfano: kumbuka funguo ziko mezani",
        "recall_none": "Sikumbuki chochote kuhusu '{topic}' bado.",
        "recall_summary": "Ninakumbuka mambo {count}. Ya karibuni:\n{items}",
        "recall_nothing": "Sikumbuki chochote bado. Nifundishe kwa: kumbuka <jambo>",
        "name_saved": "Nimefurahi kukufahamu, {name}!",
        "name_empty": "Jina lako nani? Mfano: jina langu ni Harry",
        "reminder_set": "Sawa{name}, nitakukumbusha {message} saa {time}.",
        "reminder_none": "Huna vikumbusho.",
        "reminder_list": "Vikumbusho vyako:\n{items}",
        "good_morning": "Habari za asubuhi", "good_afternoon": "Habari za mchana",
        "good_evening": "Habari za jioni",
        "briefing": "{greeting}{name}! Sasa ni {time}, {date}.",
        "briefing_battery": "Betri: {battery}.",
        "briefing_reminders": "Vikumbusho vya leo: {items}.",
        "briefing_no_reminders": "Hakuna vikumbusho vinavyosubiri.",
        "briefing_memories": "Ninakuhifadhia kumbukumbu {count}.",
        "not_understood": ("Sijaelewa. Andika 'msaada' kuona ninachoweza kufanya, "
                           "au nifundishe kwa 'kumbuka ...'."),
        "error": "Hitilafu ilitokea: {error}",
    },
}

HELP_TEXT = {
    "english": """Things you can say or type:
  • Greetings      hello, how are you, who are you
  • Time & date    what time is it, what is the date
  • Open apps      open chrome / notepad / calculator / paint ...
  • Close apps     close chrome, close notepad
  • Websites       open youtube / gmail / github, open example.com
  • Web search     search python tutorials
  • Music          play music, play <song name>, pause, resume, stop,
                   next song, previous song, shuffle, list songs
  • Memory         remember <something>, remember <title>: <details>,
                   what do you remember about <topic>, my name is <name>
  • Reminders      remind me in 10 minutes to <task>,
                   remind me at 15:30 to <task>, my reminders
  • Briefing       good morning, briefing
  • Questions      ask anything - I answer from what you taught me
  • Computer       list files, system info, lock screen,
                   shutdown, restart, cancel shutdown
  • Leave chat     back, exit""",
    "swahili": """Unachoweza kusema au kuandika:
  • Salamu         habari, mambo, wewe ni nani
  • Saa & tarehe   saa ngapi, tarehe gani
  • Programu       fungua chrome / notepad / kikokotoo / mipangilio ...
  • Kufunga        funga chrome, funga notepad
  • Tovuti         fungua youtube / gmail / github
  • Kutafuta       tafuta habari za leo
  • Muziki         cheza muziki, cheza <jina la wimbo>, simamisha,
                   endelea, zima muziki, wimbo unaofuata, wimbo uliopita,
                   changanya, orodha ya nyimbo
  • Kumbukumbu     kumbuka <jambo>, kumbuka <kichwa>: <maelezo>,
                   unakumbuka nini kuhusu <mada>, jina langu ni <jina>
  • Vikumbusho     nikumbushe baada ya dakika 10 <jambo>, vikumbusho vyangu
  • Muhtasari      habari za asubuhi, taarifa ya leo
  • Maswali        uliza chochote - najibu kutoka nilichofundishwa
  • Kompyuta       orodha ya faili, taarifa za kompyuta, funga skrini,
                   zima kompyuta, anzisha upya, sitisha kuzima
  • Kutoka         rudi, kwaheri""",
}


def contains(text, phrase):
    """True when the phrase appears in the text as whole words."""
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text) is not None


def contains_any(text, phrases):
    return any(contains(text, phrase) for phrase in phrases)


def strip_prefix(text, phrases, original=None):
    """If text starts with one of the phrases, return what comes after it.

    `original` is the same text before lowercasing; when given, the result
    keeps the user's capital letters (useful for names and notes).
    """
    source = original if original is not None else text
    for phrase in sorted(phrases, key=len, reverse=True):
        if text == phrase or text.startswith(phrase + " "):
            return source[len(phrase):].strip(" :,-")
    return None


class CommandProcessor:
    def __init__(self, language="auto", memory_manager=None, ai_engine=None, music_folder=None):
        self.language = language  # "auto", "english" or "swahili"
        self.last_language = "english" if language == "auto" else language
        self.memory = memory_manager or MemoryManager()
        self.ai = ai_engine or AIEngine(self.memory)
        self.system = SystemCommands()
        self.music = MusicPlayer(music_folder)
        self.commands = self._merge_languages(self.load_commands())
        self.responses = RESPONSES
        # The UI sets this to a function that asks the user yes/no.
        self.confirm = None
        # The app connects a ReminderManager here (see reminders.py).
        self.reminders = None

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def load_commands(self):
        """Load command keywords from config/commands.json."""
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            print(f"Error loading commands: {error}")
            return {}

    @staticmethod
    def _merge_languages(config):
        """Join English and Swahili keywords so every command works in both."""
        merged = {}

        def add(target, source):
            for key, value in source.items():
                if isinstance(value, dict):
                    add(target.setdefault(key, {}), value)
                else:
                    target.setdefault(key, [])
                    target[key].extend(v for v in value if v not in target[key])

        for language_commands in config.values():
            add(merged, language_commands)
        return merged

    # ------------------------------------------------------------------
    # Language
    # ------------------------------------------------------------------

    def detect_language(self, user_input):
        """Guess if input is Swahili or English by counting known words."""
        words = set(re.findall(r"\w+", user_input.lower()))
        swahili = len(words & SWAHILI_HINTS)
        english = len(words & ENGLISH_HINTS)
        if swahili > english:
            return "swahili"
        if english > swahili:
            return "english"
        return self.last_language

    def reply_language(self, user_input):
        if self.language in ("english", "swahili"):
            return self.language
        self.last_language = self.detect_language(user_input)
        return self.last_language

    def say(self, language, key, **values):
        """Fill in a response template in the chosen language."""
        name = self.memory.get_setting("user_name")
        values.setdefault("name", f", {name}" if name else "")
        return self.responses[language][key].format(**values)

    # ------------------------------------------------------------------
    # Main entry points
    # ------------------------------------------------------------------

    def process_command(self, user_input):
        """Return the assistant's reply as text."""
        response, _language = self.handle(user_input)
        return response

    def handle(self, user_input):
        """Return (reply_text, reply_language) for one user message."""
        original = " ".join(str(user_input or "").split()).strip(" ?!.")
        text = original.lower()
        language = self.reply_language(text) if text else self.last_language
        if not text:
            return self.say(language, "not_understood"), language

        try:
            return self._route(text, language, original), language
        except Exception as error:  # Keep the assistant alive on any error
            return self.say(language, "error", error=error), language

    def get_help(self, language="english"):
        return HELP_TEXT.get(language, HELP_TEXT["english"])

    # ------------------------------------------------------------------
    # Routing: checked from most specific to most general
    # ------------------------------------------------------------------

    def _route(self, text, lang, original):
        c = self.commands
        say = lambda key, **v: self.say(lang, key, **v)  # noqa: E731

        # 0. Reminders and the daily briefing
        if self.reminders is not None:
            reminder = parse_reminder(original)
            if reminder:
                due, message = reminder
                self.reminders.add(message, due)
                return say("reminder_set", message=message, time=f"{due:%H:%M}")
            if contains_any(text, c.get("list_reminders", [])):
                return self._list_reminders(lang)
        if contains_any(text, c.get("briefing", [])):
            return self.briefing(lang)

        # 1. Memory commands (they can contain any other word, so go first)
        memory = c.get("memory", {})
        rest = strip_prefix(text, memory.get("recall", []), original)
        if rest is not None:
            return self._recall(rest, lang)
        rest = strip_prefix(text, memory.get("set_name", []), original)
        if rest is not None:
            return self._set_name(rest, lang)
        rest = strip_prefix(text, memory.get("remember", []), original)
        if rest is not None:
            return self._remember(rest, lang)

        # 2. Web search: "search ..." / "tafuta ..."
        rest = strip_prefix(text, c.get("web_search", []))
        if rest:
            return say("searching", query=self.system.web_search(rest))
        if text in ("search", "search for", "tafuta"):
            return say("search_empty")

        # 3. Help
        if contains_any(text, c.get("help", [])):
            return self.get_help(lang)

        # 4. Power and lock (cancel is checked before shutdown on purpose)
        system = c.get("system", {})
        if contains_any(text, system.get("cancel_shutdown", [])):
            return say("cancel_done") if self.system.cancel_shutdown() else say("cancel_none")
        if contains_any(text, system.get("shutdown", [])):
            return self._power_action(lang, "shutdown")
        if contains_any(text, system.get("restart", [])):
            return self._power_action(lang, "restart")
        if contains_any(text, system.get("lock", [])):
            return say("lock") if self.system.lock_screen() else say("not_supported")

        # 5. Close an app: "close chrome" / "funga chrome"
        rest = strip_prefix(text, c.get("close_app", []))
        if rest:
            closed = self.system.close_application(rest)
            return say("closing_app" if closed else "close_failed", app=rest.title())

        # 6. Music
        music_reply = self._music(text, lang)
        if music_reply:
            return music_reply

        # 7. Websites and apps
        for site, keywords in c.get("websites", {}).items():
            if contains_any(text, keywords):
                self.system.open_website(site)
                return say("opening_website", site=site.title())
        for app, keywords in c.get("open_apps", {}).items():
            if contains_any(text, keywords):
                return self._open_app(app, lang)
        rest = strip_prefix(text, ["open", "fungua", "start", "launch"])
        if rest:
            if "." in rest and " " not in rest:
                self.system.open_website(rest)
                return say("opening_website", site=rest)
            return self._open_app(rest, lang)

        # 8. Small talk, then information
        small_talk = c.get("small_talk", {})
        for key in ("about", "how_are_you", "thanks"):
            if contains_any(text, small_talk.get(key, [])):
                return say(key)
        if contains_any(text, system.get("list_files", [])):
            return self.system.list_files()
        if contains_any(text, system.get("system_info", [])):
            return self.system.system_info()
        if contains_any(text, c.get("time", [])):
            return say("time", time=self._time_text(lang))
        if contains_any(text, c.get("date", [])):
            return say("date", date=self._date_text(lang))

        # 9. Greetings
        if contains_any(text, c.get("greetings", [])):
            return say("greeting")

        # 10. Try to answer from saved memories
        answer = self.ai.answer(text, lang)
        if answer:
            return answer

        return say("not_understood")

    # ------------------------------------------------------------------
    # Command helpers
    # ------------------------------------------------------------------

    def _music(self, text, lang):
        music = self.commands.get("music", {})
        result = None

        if contains_any(text, music.get("list", [])):
            if not self.music.playlist:
                result = self.music.play()  # gives the "no music" message
            else:
                return self.say(lang, "playlist", count=len(self.music.playlist),
                                songs=self.music.playlist_info())
        elif contains_any(text, music.get("shuffle", [])):
            result = self.music.shuffle()
        elif contains_any(text, music.get("previous", [])):
            result = self.music.previous_track()
        elif contains_any(text, music.get("next", [])):
            result = self.music.next_track()
        elif contains_any(text, music.get("pause", [])):
            result = self.music.pause()
        elif contains_any(text, music.get("resume", [])):
            result = self.music.resume()
        elif contains_any(text, music.get("stop", [])):
            result = self.music.stop()
        else:
            rest = strip_prefix(text, ["play", "cheza"])
            if rest is not None or contains_any(text, music.get("play", [])):
                words = [w for w in (rest or "").split() if w not in PLAY_FILLER]
                result = self.music.play(" ".join(words) or None)

        if result is None:
            return None
        key, track = result
        return self.say(lang, key, track=track)

    def _open_app(self, app, lang):
        ok, name = self.system.open_application(app)
        key = "opening_app" if ok else "app_not_found"
        return self.say(lang, key, app=name.title())

    def _power_action(self, lang, action):
        if self.confirm is None or not self.confirm(self.say(lang, f"{action}_confirm")):
            return self.say(lang, "cancelled")
        done = self.system.shutdown() if action == "shutdown" else self.system.restart()
        return self.say(lang, f"{action}_started") if done else self.say(lang, "not_supported")

    def _remember(self, text, lang):
        if not text:
            return self.say(lang, "memory_empty")
        if ":" in text:
            title, content = (part.strip() for part in text.split(":", 1))
        else:
            title, content = " ".join(text.split()[:6]), text
        if not title or not content:
            return self.say(lang, "memory_empty")
        tags = ",".join(self.ai._extract_keywords(text)[:5])
        self.memory.add_memory(title, content, tags)
        return self.say(lang, "memory_saved", text=content)

    def _recall(self, topic, lang):
        if topic:
            return self.ai.answer(topic, lang) or self.say(lang, "recall_none", topic=topic)
        memories = self.memory.get_all_memories()
        if not memories:
            return self.say(lang, "recall_nothing")
        items = "\n".join(f"  • {m['title']}: {m['content']}" for m in memories[:5])
        return self.say(lang, "recall_summary", count=len(memories), items=items)

    def _list_reminders(self, lang):
        pending = self.reminders.pending()
        if not pending:
            return self.say(lang, "reminder_none")
        items = "\n".join(f"  • {r['due_at'].replace('T', ' ')[:16]}  {r['message']}" for r in pending)
        return self.say(lang, "reminder_list", items=items)

    def briefing(self, lang):
        """A short daily summary: greeting, time, battery, reminders, memories."""
        hour = datetime.now().hour
        greeting_key = "good_morning" if hour < 12 else "good_afternoon" if hour < 17 else "good_evening"
        lines = [self.say(lang, "briefing", greeting=self.responses[lang][greeting_key],
                          time=self._time_text(lang), date=self._date_text(lang))]

        battery = self.system._battery_status()
        if battery and "No battery" not in battery:
            lines.append(self.say(lang, "briefing_battery", battery=battery))

        if self.reminders is not None:
            today = datetime.now().date().isoformat()
            todays = [r for r in self.reminders.pending() if r["due_at"].startswith(today)]
            if todays:
                items = ", ".join(f"{r['message']} ({r['due_at'][11:16]})" for r in todays)
                lines.append(self.say(lang, "briefing_reminders", items=items))
            else:
                lines.append(self.say(lang, "briefing_no_reminders"))

        count = self.memory.count_memories()
        if count:
            lines.append(self.say(lang, "briefing_memories", count=count))
        return " ".join(lines)

    def _set_name(self, name, lang):
        name = name.strip(" .!").title()
        if not name:
            return self.say(lang, "name_empty")
        self.memory.set_setting("user_name", name)
        return self.say(lang, "name_saved", name=name)

    @staticmethod
    def _time_text(lang):
        now = datetime.now()
        if lang != "swahili":
            return now.strftime("%I:%M %p").lstrip("0")
        # Swahili time starts counting at sunrise (6 am = saa 12, 7 am = saa 1).
        hour = (now.hour - 6) % 12 or 12
        if 4 <= now.hour < 12:
            period = "asubuhi"
        elif 12 <= now.hour < 16:
            period = "mchana"
        elif 16 <= now.hour < 19:
            period = "jioni"
        else:
            period = "usiku"
        return f"saa {hour}:{now.minute:02d} {period} ({now:%H:%M})"

    @staticmethod
    def _date_text(lang):
        now = datetime.now()
        if lang != "swahili":
            return f"{now:%A}, {now.day} {now:%B %Y}"
        return f"{SWAHILI_DAYS[now.weekday()]}, {now.day} {SWAHILI_MONTHS[now.month - 1]} {now.year}"
