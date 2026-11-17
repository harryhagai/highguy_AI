"""Highguy's AI brain, powered by Google Gemini (free tier).

Gemini understands any request (English or Kiswahili), answers questions,
and uses Highguy's tools to act on the computer: open apps, play music, save
memories, set reminders, check the weather, look things up on Wikipedia...

Needs:  pip install google-genai
        and a free API key from https://aistudio.google.com/apikey
        (Settings -> API key, or the GEMINI_API_KEY variable).
Without them Highguy falls back to its offline, rule-based commands.

Note: on the free tier Google may use your conversations to improve its products.
"""

import os
import time
from datetime import datetime, timedelta

try:
    from google import genai
    from google.genai import errors, types
except ImportError:
    genai = None

import online_tools
from reminders import time_today

DEFAULT_MODEL = "gemini-3.8-flash"
# Used automatically when the main model's free limit is used up or its
# servers are busy. Highguy then stays on it for a while before trying again.
BACKUP_MODEL = "gemini-3.5-flash-lite"
BACKUP_MINUTES = 10
BUSY_CODES = (429, 500, 503)
MAX_TOOL_ROUNDS = 10
MAX_HISTORY_MESSAGES = 80  # start a fresh conversation after this many messages

SYSTEM_PROMPT = """You are Highguy, a personal AI assistant that lives on the user's Windows PC and talks with them in a CMD window, and sometimes out loud.

Personality: calm, capable and loyal, like a trusted butler with a dry sense of humour. Be warm but brief. Get things done rather than talking about doing them.

Language: the user speaks English and Kiswahili. Reply in the language of their latest message (Kiswahili if they wrote Kiswahili, English if English), unless the context block says otherwise.

Style: your replies are shown in a terminal and often read aloud, so:
- Keep most replies to one to three short sentences. Give more detail only when the user asks for it or the task needs it.
- Use plain text. No markdown headings, tables, bold or code fences. Short dash lists are fine when listing several items.

Each user message starts with a [Context] block written by the Highguy app (current time, the user's name and city, reminders, possibly relevant saved memories). The user did not type it and cannot see it. Use it quietly; don't repeat it back unless it helps.

Tools:
- Use the PC tools to act: opening and closing apps, websites, music, files, locking the screen, shutdown or restart. Only say something was done if the tool result says it succeeded; if it failed, say so briefly and suggest an alternative.
- Shutdown and restart ask the user for a y/n confirmation on the keyboard; the tool result tells you what they chose.
- Weather: use get_weather (use the user's city from the context when they don't name one).
- Facts about people, places, history and science: use wikipedia (language "sw" for Kiswahili topics or when the user writes Kiswahili). You have no live news or web search; if asked for today's news or prices, say so and offer to open a search in the browser with open_search_in_browser.
- Memory: when the user shares a lasting fact about themselves, their projects or preferences, or asks you to remember something, save it with save_memory. When a question may depend on something they told you before, check search_memory. Saved memories also appear in the context block when they look relevant.
- Reminders: use set_reminder for "remind me ..." / "nikumbushe ..." requests (minutes from now, or a clock time).
- If the user tells you their name or city, save it with set_user_name or set_city.

Daily briefing: when the user says good morning or asks for a briefing, give a short briefing: a greeting, the day and time, the weather for their city (skip it if no city is known and suggest they tell you their city), any pending reminders, and one useful or encouraging note.

Never invent facts about the user. If you don't know, say so or ask."""


def _tool(name, description, properties=None, required=None):
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties or {},
            "required": required or [],
        },
    }


TOOL_SPECS = [
    _tool("open_app", "Start an application installed on this PC, e.g. chrome, notepad, calculator, "
          "paint, vlc, spotify, settings, task manager, explorer, word, excel, code.",
          {"name": {"type": "string", "description": "App name, e.g. 'chrome'"}}, ["name"]),
    _tool("close_app", "Close an open application (like clicking its X).",
          {"name": {"type": "string", "description": "App name, e.g. 'chrome'"}}, ["name"]),
    _tool("open_website", "Open a website in the user's browser.",
          {"site": {"type": "string",
                    "description": "A known name (youtube, gmail, github, whatsapp, google) or a URL/domain"}},
          ["site"]),
    _tool("open_search_in_browser", "Open a Google search results page in the user's browser, "
          "for news, prices and other live information.",
          {"query": {"type": "string"}}, ["query"]),
    _tool("get_weather", "Current weather and forecast for a city (free Open-Meteo service).",
          {"city": {"type": "string", "description": "City name, e.g. 'Dar es Salaam'"},
           "days": {"type": "integer", "description": "Forecast days, 1 to 7 (default 1)"}},
          ["city"]),
    _tool("wikipedia", "Look up a topic on Wikipedia and get a short summary.",
          {"topic": {"type": "string"},
           "language": {"type": "string", "enum": ["en", "sw"],
                        "description": "'sw' for Kiswahili Wikipedia, 'en' for English"}},
          ["topic"]),
    _tool("music", "Control music from the user's Music folder.",
          {"action": {"type": "string",
                      "enum": ["play", "pause", "resume", "stop", "next", "previous", "shuffle", "list"]},
           "song": {"type": "string", "description": "Optional part of a song name, only for action 'play'"}},
          ["action"]),
    _tool("computer_info", "Get computer name, Windows version, free disk space and battery level."),
    _tool("list_files", "List files in a folder on this PC.",
          {"folder": {"type": "string", "description": "Folder path. Omit for the current folder."}}),
    _tool("lock_screen", "Lock the Windows screen."),
    _tool("power", "Shut down or restart the PC (after 60 seconds, the user confirms first), "
          "or cancel a pending shutdown/restart.",
          {"action": {"type": "string", "enum": ["shutdown", "restart", "cancel"]}}, ["action"]),
    _tool("save_memory", "Save a fact to long-term memory (kept in the local database).",
          {"title": {"type": "string", "description": "Short title"},
           "content": {"type": "string", "description": "The fact, in full"},
           "tags": {"type": "string", "description": "Optional comma-separated keywords"}},
          ["title", "content"]),
    _tool("search_memory", "Search long-term memory for facts the user saved before.",
          {"query": {"type": "string"}}, ["query"]),
    _tool("search_chat_history", "Search earlier conversations with the user (from previous days too).",
          {"query": {"type": "string"}}, ["query"]),
    _tool("set_reminder", "Set a reminder that pops up and is spoken at the right time. "
          "Give minutes_from_now OR at_time.",
          {"message": {"type": "string", "description": "What to remind the user about"},
           "minutes_from_now": {"type": "number"},
           "at_time": {"type": "string", "description": "24-hour clock time HH:MM, today or tomorrow"}},
          ["message"]),
    _tool("list_reminders", "List reminders that have not gone off yet."),
    _tool("cancel_reminder", "Cancel a pending reminder by its id.",
          {"id": {"type": "integer"}}, ["id"]),
    _tool("set_user_name", "Save the name the user wants to be called.",
          {"name": {"type": "string"}}, ["name"]),
    _tool("set_city", "Save the user's city (used for weather and local information).",
          {"city": {"type": "string"}}, ["city"]),
]

TYPE_CHECKS = {"string": str, "integer": int, "number": (int, float)}


def validate_input(tool_name, data):
    """Check a tool call against its schema. Returns an error text or None."""
    spec = next((t for t in TOOL_SPECS if t["name"] == tool_name), None)
    if spec is None:
        return f"unknown tool '{tool_name}'"
    schema = spec["parameters"]
    if not isinstance(data, dict):
        return "input must be an object"
    for key in schema["required"]:
        if key not in data:
            return f"missing field '{key}'"
    for key, value in data.items():
        field = schema["properties"].get(key)
        if field is None:
            return f"unknown field '{key}'"
        expected = field["type"]
        if expected == "integer" and isinstance(value, float) and value.is_integer():
            data[key] = value = int(value)  # Gemini may send 3.0 for 3
        if isinstance(value, bool) or not isinstance(value, TYPE_CHECKS[expected]):
            return f"field '{key}' must be a {expected}"
        if "enum" in field and value not in field["enum"]:
            return f"field '{key}' must be one of {field['enum']}"
    return None


def has_credentials():
    """True when a Gemini API key is set (in .env or the environment)."""
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


class BrainError(Exception):
    """A problem talking to Gemini, with a message that is safe to show the user."""


class AIBrain:
    def __init__(self, processor, reminders, model=None, confirm=None):
        self.processor = processor          # gives access to system, music, memory
        self.memory = processor.memory
        self.reminders = reminders
        self.model = model or DEFAULT_MODEL
        self.last_model = self.model  # the model that wrote the last answer
        self.confirm = confirm              # function(question) -> bool
        self._main_busy_until = 0.0         # time.monotonic() value
        self.history = []                   # list of types.Content
        self.client = None
        self.problem = None
        self._connect()

    # ------------------------------------------------------------------
    # Setup and status
    # ------------------------------------------------------------------

    def _connect(self):
        if genai is None:
            self.client = None
            self.problem = "The 'google-genai' package is not installed (pip install google-genai)."
            return
        if not has_credentials():
            self.client = None
            self.problem = "No API key yet. Get a free one and add it in Settings -> API key."
            return
        try:
            # Give up after 25 s instead of waiting forever. Busy servers are
            # not retried here: the backup model is tried straight away.
            self.client = genai.Client(http_options=types.HttpOptions(
                timeout=25_000,
                retry_options=types.HttpRetryOptions(attempts=1),
            ))
            self.problem = None
        except Exception as error:
            self.client = None
            self.problem = f"Could not start the AI brain: {error}"

    def reconnect(self):
        self._connect()

    @property
    def ready(self):
        return self.client is not None

    def new_conversation(self):
        self.history = []

    def _config(self):
        return types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name=spec["name"],
                    description=spec["description"],
                    parameters_json_schema=spec["parameters"],
                )
                for spec in TOOL_SPECS
            ])],
            # Highguy runs the tools itself (so it can check and confirm them).
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

    # ------------------------------------------------------------------
    # Talking
    # ------------------------------------------------------------------

    def ask(self, user_text, on_text=None, on_tool=None):
        """Send one user message and return Gemini's full reply text.

        on_text(chunk) is called as text streams in, and on_tool(name, input)
        whenever a tool is used, so the UI can show progress live.
        """
        if not self.ready:
            raise BrainError(self.problem)

        if len(self.history) > MAX_HISTORY_MESSAGES:
            # Start fresh; long-term memories and the chat log are kept.
            self.history = []

        start = len(self.history)
        self.history.append(types.Content(role="user", parts=[
            types.Part.from_text(text=self._context(user_text) + "\n\n" + user_text)]))
        self.memory.log_chat("user", user_text)
        try:
            reply = self._run_turns(on_text, on_tool)
        except (KeyboardInterrupt, BrainError):
            # Forget the unfinished turn so the next question starts clean.
            del self.history[start:]
            raise
        self.memory.log_chat("assistant", reply)
        return reply

    def _run_turns(self, on_text, on_tool):
        reply_parts = []
        for _round in range(MAX_TOOL_ROUNDS):
            parts = self._stream_turn(on_text, reply_parts)
            if not parts:
                if not reply_parts:
                    reply_parts.append("(I don't have an answer for that.)")
                break

            # Keep the model's parts exactly as received (they carry
            # "thought signatures" that Gemini needs on the next turn).
            self.history.append(types.Content(role="model", parts=parts))

            calls = [part.function_call for part in parts if part.function_call]
            if not calls:
                break

            responses = []
            for call in calls:
                args = dict(call.args or {})
                problem = validate_input(call.name, args)
                if problem:
                    result = {"error": f"Invalid input: {problem}"}
                else:
                    if on_tool:
                        on_tool(call.name, args)
                    try:
                        result = {"result": self.run_tool(call.name, args)}
                    except online_tools.OnlineError as error:
                        result = {"error": str(error)}
                    except Exception as error:  # report tool failures back to Gemini
                        result = {"error": f"{type(error).__name__}: {error}"}
                responses.append(self._function_response(call, result))
            # All results go back together in one message (Gemini expects
            # function responses in a "user" turn).
            self.history.append(types.Content(role="user", parts=responses))
        return "".join(reply_parts).strip()

    @staticmethod
    def _function_response(call, result):
        part = types.Part.from_function_response(name=call.name, response=result)
        if call.id:
            part.function_response.id = call.id  # match the call it answers
        return part

    def _stream_turn(self, on_text, reply_parts):
        """Run one streamed request and return all parts the model sent.

        If the main model is busy, out of free quota or too slow, the backup
        model answers instead, and keeps answering for BACKUP_MINUTES.
        """
        main_ok = self.model == BACKUP_MODEL or time.monotonic() >= self._main_busy_until
        model = self.model if main_ok else BACKUP_MODEL
        shown = len(reply_parts)
        try:
            return self._stream_with(model, on_text, reply_parts)
        except Exception as error:
            busy = not isinstance(error, errors.APIError) or error.code in BUSY_CODES
            # Only switch if nothing was shown yet, so text is never repeated.
            if model != BACKUP_MODEL and busy and len(reply_parts) == shown:
                self._main_busy_until = time.monotonic() + BACKUP_MINUTES * 60
                try:
                    return self._stream_with(BACKUP_MODEL, on_text, reply_parts)
                except Exception as backup_error:
                    raise self._friendly(backup_error) from None
            raise self._friendly(error) from None

    def _stream_with(self, model, on_text, reply_parts):
        self.last_model = model
        parts = []
        stream = self.client.models.generate_content_stream(
            model=model, contents=self.history, config=self._config())
        for chunk in stream:
            if not chunk.candidates or not chunk.candidates[0].content:
                continue
            for part in chunk.candidates[0].content.parts or []:
                parts.append(part)
                if part.text and not part.thought:
                    reply_parts.append(part.text)
                    if on_text:
                        on_text(part.text)
        return parts

    def _friendly(self, error):
        if not isinstance(error, errors.APIError):  # no internet, timeouts
            return BrainError(f"I can't reach Gemini right now ({type(error).__name__}). "
                              "Check your internet connection.")
        code = error.code
        message = (error.message or "").lower()
        if code == 400 and "api key" in message:
            return BrainError("The API key was rejected. Check it in Settings -> API key.")
        if code in (401, 403):
            return BrainError("This API key isn't allowed to use Gemini. Check it in Settings.")
        if code == 404:
            return BrainError(f"Model '{self.model}' was not found. Change it in Settings -> AI model.")
        if code == 429:
            return BrainError("The free Gemini limit is used up for now. Try again later "
                              "(limits reset daily).")
        if code and code >= 500:
            return BrainError(f"Gemini's servers had a problem ({code}). Please try again in a moment.")
        return BrainError(f"Gemini error ({code}): {error.message}")

    def _context(self, user_text):
        """Facts about right now, sent at the top of every user message."""
        now = datetime.now()
        lines = ["[Context from the Highguy app - not typed by the user]",
                 f"Now: {now:%A %d %B %Y, %H:%M}"]
        name = self.memory.get_setting("user_name")
        city = self.memory.get_setting("city")
        lines.append(f"User's name: {name or 'unknown'}")
        lines.append(f"User's city: {city or 'unknown'}")
        if self.processor.language == "english":
            lines.append("Reply language: always English.")
        elif self.processor.language == "swahili":
            lines.append("Reply language: always Kiswahili.")
        music = self.processor.music.status()
        if music != "off":
            lines.append(f"Music: {music}")
        pending = self.reminders.pending()
        if pending:
            lines.append("Pending reminders: " + "; ".join(
                f"#{r['id']} {r['message']} at {r['due_at'][11:16]}" for r in pending[:5]))
        memories = self.processor.ai.find_relevant_memories(user_text, limit=3)
        if memories:
            lines.append("Possibly relevant saved memories:")
            lines.extend(f"- #{m['id']} {m['title']}: {m['content']}" for m in memories)
        return "\n".join(lines) + "\n[/Context]"

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def run_tool(self, name, args):
        system = self.processor.system

        if name == "open_app":
            ok, app = system.open_application(args["name"])
            return f"Opened {app}." if ok else f"Could not find '{app}' on this PC."
        if name == "close_app":
            return "Closed." if system.close_application(args["name"]) else \
                f"'{args['name']}' is not running, or it can't be closed."
        if name == "open_website":
            return f"Opened {system.open_website(args['site'])} in the browser."
        if name == "open_search_in_browser":
            system.web_search(args["query"])
            return "Opened the search results in the browser."
        if name == "get_weather":
            return online_tools.get_weather(args["city"], args.get("days", 1))
        if name == "wikipedia":
            return online_tools.wikipedia_summary(args["topic"], args.get("language", "en"))
        if name == "music":
            return self._music(args["action"], args.get("song"))
        if name == "computer_info":
            return system.system_info()
        if name == "list_files":
            return system.list_files(args.get("folder"))
        if name == "lock_screen":
            return "Screen locked." if system.lock_screen() else "Locking only works on Windows."
        if name == "power":
            return self._power(args["action"])
        if name == "save_memory":
            memory_id = self.memory.add_memory(args["title"], args["content"], args.get("tags", ""))
            return f"Saved as memory #{memory_id}."
        if name == "search_memory":
            found = self.processor.ai.find_relevant_memories(args["query"], limit=5)
            if not found:
                return "No matching memories."
            return "\n".join(f"#{m['id']} {m['title']}: {m['content']}" for m in found)
        if name == "search_chat_history":
            rows = self.memory.search_chat(args["query"], limit=8)
            if not rows:
                return "Nothing found in earlier conversations."
            return "\n".join(f"[{r['created_at'][:16]}] {r['role']}: {r['text'][:300]}" for r in rows)
        if name == "set_reminder":
            return self._set_reminder(args)
        if name == "list_reminders":
            pending = self.reminders.pending()
            if not pending:
                return "No pending reminders."
            return "\n".join(f"#{r['id']} {r['message']} at {r['due_at'].replace('T', ' ')[:16]}"
                             for r in pending)
        if name == "cancel_reminder":
            return "Cancelled." if self.reminders.cancel(args["id"]) else "No pending reminder with that id."
        if name == "set_user_name":
            self.memory.set_setting("user_name", args["name"].strip().title())
            return "Name saved."
        if name == "set_city":
            self.memory.set_setting("city", args["city"].strip().title())
            return "City saved."
        raise ValueError(f"unknown tool {name}")

    def _music(self, action, song=None):
        music = self.processor.music
        if action == "list":
            if not music.playlist:
                return f"No songs found in {music.music_folder}."
            return f"{len(music.playlist)} songs:\n" + music.playlist_info(limit=30)
        handlers = {
            "play": lambda: music.play(song or None),
            "pause": music.pause,
            "resume": music.resume,
            "stop": music.stop,
            "next": music.next_track,
            "previous": music.previous_track,
            "shuffle": music.shuffle,
        }
        key, track = handlers[action]()
        return self.processor.say("english", key, track=track)

    def _power(self, action):
        system = self.processor.system
        if action == "cancel":
            return "Cancelled the pending shutdown/restart." if system.cancel_shutdown() else \
                "There was nothing to cancel."
        question = "Shut down the computer in 60 seconds?" if action == "shutdown" else \
            "Restart the computer in 60 seconds?"
        if self.confirm is None or not self.confirm(question):
            return "The user said no; nothing was done."
        done = system.shutdown() if action == "shutdown" else system.restart()
        return f"{action.title()} starts in 60 seconds." if done else "That only works on Windows."

    def _set_reminder(self, args):
        message = args["message"].strip()
        if "minutes_from_now" in args:
            minutes = float(args["minutes_from_now"])
            if minutes <= 0:
                return "Error: minutes_from_now must be more than 0."
            due = datetime.now() + timedelta(minutes=minutes)
        elif "at_time" in args:
            try:
                hour, minute = (int(part) for part in args["at_time"].split(":"))
            except ValueError:
                return "Error: at_time must look like HH:MM."
            due = time_today(hour, minute)
            if due is None:
                return "Error: invalid clock time."
        else:
            return "Error: give minutes_from_now or at_time."
        reminder_id = self.reminders.add(message, due)
        return f"Reminder #{reminder_id} set for {due:%A %H:%M}."
