#!/usr/bin/env python3
"""Highguy AI Assistant - runs in the CMD window.

Usage:
    python src/main.py              (uses the language saved in Settings)
    python src/main.py swahili      (or: english, auto)
    python src/main.py chat         (jump straight into chat)
    python src/main.py voice        (jump straight into voice mode)
"""

import getpass
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import ui
from ui import Color, paint
from ai_brain import DEFAULT_MODEL, AIBrain, BrainError
from ai_engine import AIEngine
from command_processor import CommandProcessor
from config import save_env_value
from memory_manager import MemoryManager
from reminders import ReminderManager

APP_TITLE = "Highguy AI Assistant"
LANGUAGES = ("auto", "english", "swahili")
EXIT_WORDS = {"exit", "quit", "bye", "goodbye", "back", "menu", "q",
              "kwaheri", "rudi", "toka", "ondoka"}
# What speech recognition usually hears when you say "Hey Highguy".
WAKE_WORDS = re.compile(r"\b(?:hey |hi |ok |okay |hello |habari |)(?:high ?guy|hi ?guy|hai ?guy|highgai)\b[,.!]?\s*")

# Text used by the menus, in both languages.
TEXT = {
    "english": {
        "subtitle": "Your personal AI assistant  •  English & Kiswahili",
        "main_menu": "MAIN MENU",
        "menu": [
            ("1", "Chat with Highguy      " + paint("type anything", Color.GRAY)),
            ("2", "Voice mode             " + paint("talk using your microphone", Color.GRAY)),
            (None, ""),
            ("3", "Add memory"),
            ("4", "Search memories"),
            ("5", "Show all memories"),
            ("6", "Edit memory"),
            ("7", "Delete memory"),
            (None, ""),
            ("8", "Settings"),
            ("9", "Help"),
            ("0", "Exit"),
        ],
        "choose": "Choose an option",
        "invalid": "Invalid choice. Please enter a number from the menu.",
        "goodbye": "Goodbye! See you later.",
        "you": "You",
        "good_morning": "Good morning", "good_afternoon": "Good afternoon",
        "good_evening": "Good evening",
        "brain_online": "AI brain online",
        "brain_offline": "offline mode (Settings -> AI brain to go online)",
        "reminders_pending": "{count} reminder(s) pending",
        "chat_title": "CHAT",
        "chat_hint": "Type anything. 'new' starts a fresh conversation, 'back' returns to the menu.",
        "chat_hint_offline": "Type a command or question. 'help' shows ideas, 'back' returns to the menu.",
        "new_chat": "Started a new conversation.",
        "thinking": "thinking",
        "recognizing": "understanding your words...",
        "offline": "offline",
        "fallback_offline": "Answering offline instead.",
        "voice_title": "VOICE MODE",
        "voice_hint": "Speak after 'Listening...'. Say 'back' or press Ctrl+C to return.",
        "wake_hint": "Say 'Hey Highguy' to wake me, then your request. Ctrl+C returns to the menu.",
        "listening": "Listening...",
        "waiting_wake": "Waiting for 'Hey Highguy'...",
        "yes": "Yes?",
        "not_heard": "Sorry, I didn't catch that.",
        "voice_off_title": "VOICE INPUT IS NOT AVAILABLE",
        "reminder_title": "REMINDER",
        "reminder_say": "Reminder: {message}",
        "title": "Title",
        "content": "Content",
        "tags": "Tags (comma separated)",
        "keyword": "Search keyword",
        "memory_id": "Memory ID",
        "saved": "Memory saved successfully (ID {id}).",
        "empty_fields": "Title and content cannot be empty.",
        "empty_keyword": "Search keyword cannot be empty.",
        "empty_id": "Memory ID cannot be empty.",
        "bad_id": "Memory ID must be a number.",
        "not_found": "Memory not found.",
        "no_results": "No memories found for '{keyword}'.",
        "no_memories": "No memories saved yet. Choose [3] to add one, or say 'remember ...' in chat.",
        "found": "Found {count} memory(ies).",
        "view_prompt": "Type an ID to read it in full, or press Enter to go back",
        "edit_hint": "Press Enter to keep the current value.",
        "updated": "Memory updated successfully.",
        "no_changes": "Nothing changed.",
        "delete_confirm": "Delete this memory?",
        "deleted": "Memory deleted successfully.",
        "kept": "Okay, the memory was not deleted.",
        "settings_title": "SETTINGS",
        "language": "Language",
        "voice_replies": "Voice replies",
        "wake_word": "Wake word",
        "sb_voice": "Voice",
        "sb_memories": "Memories",
        "sb_brain": "AI",
        "your_name": "Your name",
        "city": "Your city",
        "music_folder": "Music folder",
        "voice_check": "Check voice setup",
        "ai_brain": "AI brain",
        "api_key": "API key",
        "ai_model": "AI model",
        "back": "Back",
        "pick_language": "1 = auto, 2 = english, 3 = swahili",
        "name_prompt": "Your name (leave empty to remove)",
        "city_prompt": "Your city, e.g. Dar es Salaam (leave empty to remove)",
        "folder_prompt": "Full path of your music folder",
        "folder_missing": "That folder does not exist.",
        "songs_found": "Found {count} song(s).",
        "key_help": "Get a FREE key at https://aistudio.google.com/apikey (Create API key). It is saved in .env, "
                    "which is never committed to git.",
        "key_prompt": "Paste your Gemini API key (hidden, Enter = keep, '-' = remove)",
        "key_saved": "API key saved.",
        "key_removed": "API key removed.",
        "model_prompt": "Gemini model id, e.g. gemini-3.8-flash or gemini-3.5-flash-lite (Enter = keep)",
        "brain_not_ready": "The AI brain is not ready: {problem}",
        "help_title": "HELP",
        "press_enter": "Press Enter to continue...",
    },
    "swahili": {
        "subtitle": "Msaidizi wako binafsi wa AI  •  Kiswahili & English",
        "main_menu": "MENYU KUU",
        "menu": [
            ("1", "Ongea na Highguy       " + paint("andika chochote", Color.GRAY)),
            ("2", "Hali ya sauti          " + paint("ongea kwa kipaza sauti", Color.GRAY)),
            (None, ""),
            ("3", "Ongeza kumbukumbu"),
            ("4", "Tafuta kumbukumbu"),
            ("5", "Onyesha kumbukumbu zote"),
            ("6", "Hariri kumbukumbu"),
            ("7", "Futa kumbukumbu"),
            (None, ""),
            ("8", "Mipangilio"),
            ("9", "Msaada"),
            ("0", "Toka"),
        ],
        "choose": "Chagua namba",
        "invalid": "Chaguo si sahihi. Tafadhali andika namba iliyo kwenye menyu.",
        "goodbye": "Kwaheri! Tutaonana baadaye.",
        "you": "Wewe",
        "good_morning": "Habari za asubuhi", "good_afternoon": "Habari za mchana",
        "good_evening": "Habari za jioni",
        "brain_online": "Akili ya AI iko hewani",
        "brain_offline": "hali ya nje ya mtandao (Mipangilio -> AI brain)",
        "reminders_pending": "vikumbusho {count} vinasubiri",
        "chat_title": "MAZUNGUMZO",
        "chat_hint": "Andika chochote. 'mpya' kuanza upya, 'rudi' kurudi kwenye menyu.",
        "chat_hint_offline": "Andika amri au swali. 'msaada' kwa mawazo, 'rudi' kurudi kwenye menyu.",
        "new_chat": "Mazungumzo mapya yameanza.",
        "thinking": "ninafikiri",
        "recognizing": "ninatambua maneno yako...",
        "offline": "bila mtandao",
        "fallback_offline": "Ninajibu bila mtandao badala yake.",
        "voice_title": "HALI YA SAUTI",
        "voice_hint": "Ongea baada ya 'Ninasikiliza...'. Sema 'rudi' au bonyeza Ctrl+C kurudi.",
        "wake_hint": "Sema 'Hey Highguy' kuniamsha, kisha ombi lako. Ctrl+C kurudi kwenye menyu.",
        "listening": "Ninasikiliza...",
        "waiting_wake": "Ninasubiri 'Hey Highguy'...",
        "yes": "Naam?",
        "not_heard": "Samahani, sijasikia vizuri.",
        "voice_off_title": "SAUTI HAIPATIKANI",
        "reminder_title": "KIKUMBUSHO",
        "reminder_say": "Kikumbusho: {message}",
        "title": "Kichwa",
        "content": "Maelezo",
        "tags": "Lebo (tenganisha kwa koma)",
        "keyword": "Neno la kutafuta",
        "memory_id": "Namba ya kumbukumbu (ID)",
        "saved": "Kumbukumbu imehifadhiwa (ID {id}).",
        "empty_fields": "Kichwa na maelezo havitakiwi kuwa tupu.",
        "empty_keyword": "Neno la kutafuta haliwezi kuwa tupu.",
        "empty_id": "ID haiwezi kuwa tupu.",
        "bad_id": "ID lazima iwe namba.",
        "not_found": "Kumbukumbu haipatikani.",
        "no_results": "Hakuna kumbukumbu za '{keyword}'.",
        "no_memories": "Hakuna kumbukumbu bado. Chagua [3] kuongeza, au sema 'kumbuka ...'.",
        "found": "Nimepata kumbukumbu {count}.",
        "view_prompt": "Andika ID kusoma yote, au bonyeza Enter kurudi",
        "edit_hint": "Bonyeza Enter kubaki na thamani ya sasa.",
        "updated": "Kumbukumbu imesasishwa.",
        "no_changes": "Hakuna kilichobadilika.",
        "delete_confirm": "Futa kumbukumbu hii?",
        "deleted": "Kumbukumbu imefutwa.",
        "kept": "Sawa, kumbukumbu haijafutwa.",
        "settings_title": "MIPANGILIO",
        "language": "Lugha",
        "voice_replies": "Majibu kwa sauti",
        "wake_word": "Neno la kuamsha",
        "sb_voice": "Sauti",
        "sb_memories": "Kumbukumbu",
        "sb_brain": "AI",
        "your_name": "Jina lako",
        "city": "Mji wako",
        "music_folder": "Folda ya muziki",
        "voice_check": "Kagua mipangilio ya sauti",
        "ai_brain": "Akili ya AI",
        "api_key": "Ufunguo wa API",
        "ai_model": "Modeli ya AI",
        "back": "Rudi",
        "pick_language": "1 = auto, 2 = english, 3 = swahili",
        "name_prompt": "Jina lako (acha tupu kuondoa)",
        "city_prompt": "Mji wako, mfano Dar es Salaam (acha tupu kuondoa)",
        "folder_prompt": "Njia kamili ya folda ya muziki",
        "folder_missing": "Folda hiyo haipo.",
        "songs_found": "Nimepata nyimbo {count}.",
        "key_help": "Pata ufunguo wa BURE kwenye https://aistudio.google.com/apikey (Create API key). Unahifadhiwa kwenye "
                    ".env, ambayo haiwekwi kwenye git.",
        "key_prompt": "Bandika ufunguo wako wa Gemini API (umefichwa, Enter = baki, '-' = ondoa)",
        "key_saved": "Ufunguo wa API umehifadhiwa.",
        "key_removed": "Ufunguo wa API umeondolewa.",
        "model_prompt": "Jina la modeli ya Gemini, mfano gemini-3.8-flash au gemini-3.5-flash-lite (Enter = baki)",
        "brain_not_ready": "Akili ya AI haiko tayari: {problem}",
        "help_title": "MSAADA",
        "press_enter": "Bonyeza Enter kuendelea...",
    },
}


class HighguyApp:
    def __init__(self, language=None):
        self.memory = MemoryManager()
        self.ai = AIEngine(self.memory)

        if language:
            self.memory.set_setting("language", language)
        saved_language = self.memory.get_setting("language", "auto")

        self.processor = CommandProcessor(
            language=saved_language,
            memory_manager=self.memory,
            ai_engine=self.ai,
            music_folder=self.memory.get_setting("music_folder"),
        )
        # Dangerous actions (shutdown/restart) must be confirmed on the keyboard.
        self.processor.confirm = ui.confirm

        # Reminders pop up from a background thread.
        self.reminders = ReminderManager(self.memory.db_path, on_due=self.on_reminder)
        self.processor.reminders = self.reminders

        self.brain = AIBrain(
            self.processor,
            self.reminders,
            model=self._saved_model(),
            confirm=ui.confirm,
        )

        # Voice is created here, on the main thread (speech engines need that).
        from voice_handler import VoiceHandler

        self.voice = VoiceHandler(self.ui_language)
        self.reminders.start()

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    def _saved_model(self):
        """The model chosen in Settings (old Claude settings are ignored)."""
        model = self.memory.get_setting("ai_model", DEFAULT_MODEL)
        return DEFAULT_MODEL if model.startswith("claude") else model

    @property
    def language(self):
        return self.processor.language

    @property
    def ui_language(self):
        """Language used for menus. 'auto' follows the last language used in chat."""
        if self.language == "auto":
            return self.processor.last_language
        return self.language

    def t(self, key, **values):
        text = TEXT[self.ui_language][key]
        return text.format(**values) if values else text

    def setting_on(self, key, default="off"):
        return self.memory.get_setting(key, default) == "on"

    @property
    def voice_replies(self):
        return self.setting_on("voice_replies")

    @property
    def brain_on(self):
        """True when the AI brain is switched on and has what it needs."""
        return self.setting_on("ai_brain", "on") and self.brain.ready

    def user_name(self):
        return self.memory.get_setting("user_name") or self.t("you")

    def greeting_line(self):
        """A short 'good afternoon, Harry' line for the main menu."""
        hour = datetime.now().hour
        key = "good_morning" if hour < 12 else "good_afternoon" if hour < 17 else "good_evening"
        name = self.memory.get_setting("user_name")
        parts = [self.t(key) + (f", {name}" if name else "") + "."]
        parts.append(self.t("brain_online") if self.brain_on else self.t("brain_offline"))
        pending = len(self.reminders.pending())
        if pending:
            parts.append(self.t("reminders_pending", count=pending))
        return "  " + paint(parts[0], Color.WHITE, Color.BOLD) + paint("  " + "  •  ".join(parts[1:]), Color.GRAY)

    def screen(self, title=None):
        """Clear the window and draw the header and status bar."""
        ui.clear()
        ui.banner(self.t("subtitle"))
        print()
        try:
            count = self.memory.count_memories()
        except RuntimeError:
            count = "?"
        ui.status_bar([
            (self.t("sb_brain"), "online" if self.brain_on else "offline"),
            (self.t("language"), self.language),
            (self.t("sb_voice"), "on" if self.voice_replies else "off"),
            (self.t("sb_memories"), str(count)),
            ("♪", self.processor.music.status()),
            ("", datetime.now().strftime("%H:%M")),
        ])
        print()
        if title:
            ui.rule(title)
            print()

    def ask_memory_id(self):
        """Ask for a memory ID and return the memory, or None."""
        text = ui.ask(self.t("memory_id"))
        if not text:
            ui.error(self.t("empty_id"))
            return None
        if not text.isdigit():
            ui.error(self.t("bad_id"))
            return None
        memory = self.memory.get_memory(int(text))
        if memory is None:
            ui.error(self.t("not_found"))
        return memory

    def show_memory(self, memory):
        lines = [
            memory["content"],
            "",
            paint(f"{self.t('tags')}: ", Color.GRAY) + (memory["tags"] or "-"),
            paint("Created: ", Color.GRAY) + memory["created_at"].replace("T", " ")
            + paint("   Updated: ", Color.GRAY) + (memory["updated_at"] or "-").replace("T", " "),
        ]
        ui.box(lines, title=f"#{memory['id']}  {memory['title']}", color=Color.BLUE)

    def speak(self, text, wait=False):
        """Read text out loud (only the first line of long answers)."""
        if not self.voice.can_speak:
            return
        spoken = text if len(text) < 400 else text.splitlines()[0]
        if wait:
            self.voice.speak(spoken)
        else:
            self.voice.speak_async(spoken)

    # ------------------------------------------------------------------
    # Answering: AI brain first, offline commands as a backup
    # ------------------------------------------------------------------

    def answer(self, text):
        """Show (and stream) the reply to one message. Returns the reply text."""
        if self.brain_on:
            try:
                return self._answer_with_brain(text)
            except BrainError:
                ui.hint(self.t("fallback_offline"))
                print()

        response, _language = self.processor.handle(text)
        ui.assistant_says(response, footer=self.t("offline"))
        return response

    def _answer_with_brain(self, text):
        """Stream the brain's answer into a bubble, with a thinking animation."""
        bubble = ui.AssistantBubble()
        bubble.thinking(self.t("thinking"))
        started = time.monotonic()
        footer = ""

        def on_tool(name, args):
            detail = ", ".join(str(v) for v in args.values())
            bubble.step(name.replace("_", " ") + (f": {detail}" if detail else ""))
            bubble.thinking(self.t("thinking"))

        try:
            reply = self.brain.ask(text, on_text=bubble.write, on_tool=on_tool)
            footer = f"{self.brain.last_model} · {time.monotonic() - started:.1f}s"
        except BrainError as error:
            bubble.problem(str(error))
            raise
        finally:
            bubble.close(footer)

        # Answer language may have changed; keep the menus in step.
        self.processor.reply_language(text)
        return reply

    # ------------------------------------------------------------------
    # Reminders (called from the background thread)
    # ------------------------------------------------------------------

    def on_reminder(self, reminder):
        print("\n")
        ui.box([paint(reminder["message"], Color.WHITE, Color.BOLD),
                paint(reminder["due_at"].replace("T", " "), Color.GRAY)],
               title=self.t("reminder_title"), color=Color.YELLOW)
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except (ImportError, RuntimeError):
            pass
        self.speak(self.t("reminder_say", message=reminder["message"]))

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self, start_with=None):
        ui.set_title(APP_TITLE)
        actions = {
            "1": self.chat,
            "2": self.voice_mode,
            "3": self.add_memory,
            "4": self.search_memories,
            "5": self.show_all_memories,
            "6": self.edit_memory,
            "7": self.delete_memory,
            "8": self.settings,
            "9": self.help,
        }
        if start_with == "chat":
            self._run_action(self.chat)
        elif start_with == "voice":
            self._run_action(self.voice_mode)

        while True:
            self.screen()
            print(self.greeting_line())
            print()
            ui.menu(self.t("menu"), self.t("main_menu"))
            print()
            try:
                choice = ui.ask(self.t("choose")).lower()
            except KeyboardInterrupt:
                choice = "0"

            if choice in ("0", "exit", "quit", "q", "toka", "kwaheri"):
                self.processor.music.stop()
                self.reminders.stop()
                print()
                ui.assistant_says(self.t("goodbye"))
                return
            action = actions.get(choice)
            if action:
                self._run_action(action)
            else:
                ui.error(self.t("invalid"))
                ui.pause(self.t("press_enter"))

    def _run_action(self, action):
        """Run one menu screen. Ctrl+C always returns to the main menu."""
        try:
            if action():
                ui.pause(self.t("press_enter"))
        except KeyboardInterrupt:
            print()
        except RuntimeError as error:  # database problems
            ui.error(str(error))
            ui.pause(self.t("press_enter"))

    # ------------------------------------------------------------------
    # 1. Chat
    # ------------------------------------------------------------------

    def chat(self):
        self.screen(self.t("chat_title"))
        ui.hint(self.t("chat_hint") if self.brain_on else self.t("chat_hint_offline"))
        print()
        while True:
            text = ui.ask(self.user_name())
            if not text:
                continue
            lowered = text.lower()
            if lowered in EXIT_WORDS:
                return False
            if lowered in ("cls", "clear", "/clear"):
                self.screen(self.t("chat_title"))
                continue
            if lowered in ("new", "/new", "mpya", "new chat"):
                self.brain.new_conversation()
                ui.success(self.t("new_chat"))
                print()
                continue
            self.show_user_text(text, typed=True)
            reply = self.answer(text)
            if self.voice_replies:
                self.speak(reply)

    # ------------------------------------------------------------------
    # 2. Voice mode
    # ------------------------------------------------------------------

    def voice_mode(self):
        self.screen(self.t("voice_title"))
        voice = self.voice

        if not voice.can_listen:
            ui.box([
                voice.listen_problem,
                "",
                "To use the microphone:",
                "  1. Run:  pip install SpeechRecognition sounddevice",
                "  2. Connect a microphone",
                "  3. Connect to the internet (Google speech recognition)",
                "",
                "You can still type everything in Chat [1].",
            ], title=self.t("voice_off_title"), color=Color.YELLOW)
            return True

        wake_mode = self.setting_on("wake_word")
        ui.hint(self.t("wake_hint") if wake_mode else self.t("voice_hint"))
        print()
        voice.set_language(self.ui_language)
        awake = not wake_mode

        while True:
            text, problem = self.listen_once(awake)
            if problem == "timeout":
                if wake_mode:
                    awake = False
                continue
            if problem == "not_understood":
                if awake:
                    ui.warning(self.t("not_heard"))
                continue
            if problem:
                ui.error(problem)
                return True

            if wake_mode and not awake:
                match = WAKE_WORDS.search(text)
                if not match:
                    continue  # not talking to us
                text = text[match.end():].strip()
                if not text:
                    # Just the wake word: answer and listen for the request.
                    ui.assistant_says(self.t("yes"))
                    self.speak(self.t("yes"), wait=True)
                    awake = True
                    continue

            self.show_user_text(text)
            if text.strip(" .!") in EXIT_WORDS:
                return False
            reply = self.answer(text)
            voice.set_language(self.processor.last_language)
            self.speak(reply, wait=True)
            awake = not wake_mode

    def listen_once(self, awake):
        """Listen for one phrase, showing a live sound meter while you talk."""
        label = self.t("listening") if awake else self.t("waiting_wake")
        color = Color.GREEN if awake else Color.GRAY

        def on_sound(level, recording):
            if level is None:
                ui.status_line(paint(f"  (( {self.t('recognizing')} ))", Color.YELLOW, Color.BOLD))
                return
            meter = paint(ui.sound_meter(level), Color.GREEN if recording else Color.GRAY)
            ui.status_line(paint(f"  (( {label} )) ", color, Color.BOLD) + meter)

        if ui.USE_COLOR:
            on_sound(0.0, False)
        else:
            print(paint(f"  (( {label} ))", color, Color.BOLD))
        try:
            return self.voice.listen(on_sound=on_sound)
        finally:
            ui.clear_status_line()

    def show_user_text(self, text, typed=False):
        """Show what you said or typed in a bubble on the right."""
        if typed:
            # Replace the line you typed on with the bubble.
            typed_width = len(f"  {self.user_name()} › {text}")
            ui.erase_lines(typed_width // ui.terminal_columns() + 1)
        ui.user_bubble(text, name=f"{self.user_name()} · {datetime.now():%H:%M}")

    # ------------------------------------------------------------------
    # 3-7. Memory screens
    # ------------------------------------------------------------------

    def add_memory(self):
        self.screen(self.t("menu")[3][1])
        title = ui.ask(self.t("title"))
        content = ui.ask(self.t("content"))
        tags = ui.ask(self.t("tags"))
        print()
        if not title or not content:
            ui.error(self.t("empty_fields"))
            return True
        memory_id = self.memory.add_memory(title, content, tags)
        ui.success(self.t("saved", id=memory_id))
        return True

    def search_memories(self):
        self.screen(self.t("menu")[4][1])
        keyword = ui.ask(self.t("keyword"))
        print()
        if not keyword:
            ui.error(self.t("empty_keyword"))
            return True

        # Search the exact keyword first, then fall back to smart matching.
        memories = self.memory.search_memory(keyword, limit=20)
        if not memories:
            memories = self.ai.find_relevant_memories(keyword, limit=10)
        if not memories:
            ui.warning(self.t("no_results", keyword=keyword))
            return True

        ui.success(self.t("found", count=len(memories)))
        print()
        for memory in memories:
            self.show_memory(memory)
        return True

    def show_all_memories(self):
        self.screen(self.t("menu")[5][1])
        memories = self.memory.get_all_memories()
        if not memories:
            ui.warning(self.t("no_memories"))
            return True

        rows = [
            (m["id"], m["title"], m["tags"] or "-", m["created_at"][:10])
            for m in memories
        ]
        ui.table(["ID", self.t("title"), "Tags", "Date"], rows)
        print()

        while True:
            choice = ui.ask(self.t("view_prompt"))
            if not choice:
                return False
            if not choice.isdigit():
                ui.error(self.t("bad_id"))
                continue
            memory = self.memory.get_memory(int(choice))
            if memory:
                self.show_memory(memory)
            else:
                ui.error(self.t("not_found"))

    def edit_memory(self):
        self.screen(self.t("menu")[6][1])
        memory = self.ask_memory_id()
        if memory is None:
            return True

        self.show_memory(memory)
        ui.hint(self.t("edit_hint"))
        print()
        title = ui.ask(self.t("title"), default=memory["title"])
        content = ui.ask(self.t("content"), default=memory["content"])
        tags = ui.ask(self.t("tags"), default=memory["tags"] or "")
        print()

        changes = {}
        if title != memory["title"]:
            changes["title"] = title
        if content != memory["content"]:
            changes["content"] = content
        if tags != (memory["tags"] or ""):
            changes["tags"] = tags

        if not changes:
            ui.info(self.t("no_changes"))
            return True
        try:
            self.memory.update_memory(memory["id"], **changes)
        except ValueError as error:
            ui.error(str(error))
            return True
        ui.success(self.t("updated"))
        return True

    def delete_memory(self):
        self.screen(self.t("menu")[7][1])
        memory = self.ask_memory_id()
        if memory is None:
            return True

        self.show_memory(memory)
        if ui.confirm(self.t("delete_confirm")):
            self.memory.delete_memory(memory["id"])
            ui.success(self.t("deleted"))
        else:
            ui.info(self.t("kept"))
        return True

    # ------------------------------------------------------------------
    # 8. Settings
    # ------------------------------------------------------------------

    def settings(self):
        while True:
            self.screen(self.t("settings_title"))
            music = self.processor.music

            def value(text, bold=True):
                return paint(str(text), Color.WHITE, Color.BOLD) if bold else paint(str(text), Color.WHITE)

            def on_off(key, default="off"):
                return "on" if self.setting_on(key, default) else "off"

            brain_state = on_off("ai_brain", "on") if self.brain.ready else "off"
            key_state = "set" if self.brain.ready else "not set"

            ui.menu([
                ("1", f"{self.t('language'):<18} {value(self.language)}"),
                ("2", f"{self.t('your_name'):<18} {value(self.memory.get_setting('user_name') or '-')}"),
                ("3", f"{self.t('city'):<18} {value(self.memory.get_setting('city') or '-')}"),
                ("4", f"{self.t('music_folder'):<18} {value(music.music_folder, False)} ({len(music.playlist)})"),
                (None, ""),
                ("5", f"{self.t('voice_replies'):<18} {value(on_off('voice_replies'))}"),
                ("6", f"{self.t('wake_word'):<18} {value(on_off('wake_word'))}  "
                      + paint("'Hey Highguy' in voice mode", Color.GRAY)),
                ("7", self.t("voice_check")),
                (None, ""),
                ("8", f"{self.t('ai_brain'):<18} {value(brain_state)}"),
                ("9", f"{self.t('api_key'):<18} {value(key_state)}"),
                ("m", f"{self.t('ai_model'):<18} {value(self.brain.model)}"),
                (None, ""),
                ("0", self.t("back")),
            ], self.t("settings_title"))
            if not self.brain.ready:
                ui.hint(f"{self.t('ai_brain')}: {self.brain.problem}")
            print()
            choice = ui.ask(self.t("choose")).lower()

            if choice in ("0", ""):
                return False
            handler = {
                "1": self._set_language,
                "2": lambda: self._set_text("user_name", "name_prompt"),
                "3": lambda: self._set_text("city", "city_prompt"),
                "4": self._set_music_folder,
                "5": lambda: self._toggle("voice_replies"),
                "6": lambda: self._toggle("wake_word"),
                "7": self.voice_check,
                "8": self._toggle_brain,
                "9": self._set_api_key,
                "m": self._set_model,
            }.get(choice)
            if handler is None:
                ui.error(self.t("invalid"))
                ui.pause(self.t("press_enter"))
            elif handler():
                ui.pause(self.t("press_enter"))

    def _toggle(self, key, default="off"):
        self.memory.set_setting(key, "off" if self.setting_on(key, default) else "on")

    def _set_text(self, key, prompt_key):
        self.memory.set_setting(key, ui.ask(self.t(prompt_key)).strip().title())

    def _set_language(self):
        picked = ui.ask(self.t("pick_language"))
        language = {"1": "auto", "2": "english", "3": "swahili"}.get(picked, picked.lower())
        if language not in LANGUAGES:
            ui.error(self.t("invalid"))
            return True
        self.processor.language = language
        if language != "auto":
            self.processor.last_language = language
        self.memory.set_setting("language", language)
        return False

    def _set_music_folder(self):
        folder = ui.ask(self.t("folder_prompt"), default=str(self.processor.music.music_folder))
        path = Path(folder.strip('"')).expanduser()
        if path.is_dir():
            count = self.processor.music.set_folder(path)
            self.memory.set_setting("music_folder", str(path))
            ui.success(self.t("songs_found", count=count))
        else:
            ui.error(self.t("folder_missing"))
        return True

    def _toggle_brain(self):
        if not self.brain.ready:
            ui.warning(self.t("brain_not_ready", problem=self.brain.problem))
            return True
        self._toggle("ai_brain", "on")
        return False

    def _set_api_key(self):
        print()
        ui.hint(self.t("key_help"))
        try:
            key = getpass.getpass(paint(f"  {self.t('key_prompt')} › ", Color.CYAN, Color.BOLD)).strip()
        except EOFError:
            raise KeyboardInterrupt from None
        if not key:
            return False
        if key == "-":
            save_env_value("GEMINI_API_KEY", "")
            ui.success(self.t("key_removed"))
        else:
            save_env_value("GEMINI_API_KEY", key)
            ui.success(self.t("key_saved"))
        self.brain.reconnect()
        if not self.brain.ready:
            ui.warning(self.t("brain_not_ready", problem=self.brain.problem))
        return True

    def _set_model(self):
        model = ui.ask(self.t("model_prompt"), default=self.brain.model).strip()
        if model:
            self.brain.model = model
            self.brain.new_conversation()  # a conversation stays on one model
            self.memory.set_setting("ai_model", model)
        return False

    def voice_check(self):
        print()
        voice = self.voice
        if voice.can_listen:
            ui.success("Microphone: ready")
        else:
            ui.error(f"Microphone: {voice.listen_problem}")
        if voice.engine is not None:
            ui.success("Speech output: pyttsx3")
        elif voice.can_speak:
            ui.success("Speech output: Windows built-in voice")
        else:
            ui.error("Speech output: not available")
        if voice.can_speak:
            ui.info("Testing the voice...")
            voice.speak("Hello! Habari! This is Highguy.")
        return True

    # ------------------------------------------------------------------
    # 9. Help
    # ------------------------------------------------------------------

    def help(self):
        self.screen(self.t("help_title"))
        if self.brain_on:
            ui.box([
                "The AI brain is online: just talk normally, in English or Kiswahili.",
                "Examples:",
                "  • good morning                      (daily briefing with weather)",
                "  • what's the weather in Arusha tomorrow?",
                "  • open chrome and play some music",
                "  • remind me in 20 minutes to call Mama",
                "  • remember that my wifi password is on the router",
                "  • nieleze kuhusu historia ya Zanzibar kwa ufupi",
                "  • what did we talk about yesterday?",
            ], title="AI BRAIN", color=Color.MAGENTA)
            print()
        ui.box(self.processor.get_help(self.ui_language).splitlines(),
               title=self.t("help_title") + ("  (offline commands)" if self.brain_on else ""))
        print()
        ui.box([
            "Menu [3]-[7] manage memories saved in highguy_ai.db.",
            "Settings -> AI brain: add an API key to talk about anything.",
            "Settings -> Wake word: say 'Hey Highguy' in voice mode.",
            "Shutdown and restart always ask you to confirm first.",
            "Ctrl+C returns to the main menu at any time.",
        ], title="TIPS", color=Color.GRAY)
        return True


def parse_arguments(arguments):
    """Read optional language and start mode from the command line."""
    language = None
    start_with = None
    aliases = {"en": "english", "sw": "swahili", "kiswahili": "swahili"}
    for argument in arguments:
        word = aliases.get(argument.lower(), argument.lower())
        if word in LANGUAGES:
            language = word
        elif word in ("chat", "voice"):
            start_with = word
        else:
            print(__doc__)
            sys.exit(1)
    return language, start_with


def main():
    language, start_with = parse_arguments(sys.argv[1:])
    try:
        app = HighguyApp(language)
    except RuntimeError as error:
        ui.error(f"Failed to start assistant: {error}")
        sys.exit(1)

    try:
        app.run(start_with)
    except KeyboardInterrupt:
        print()
        ui.assistant_says(TEXT[app.ui_language]["goodbye"])


if __name__ == "__main__":
    main()
