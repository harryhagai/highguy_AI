# Highguy AI Assistant

A Jarvis-style personal assistant for Windows that runs in the **CMD window**. It talks in
**English and Kiswahili**, controls your PC (apps, websites, music, lock, shutdown),
**remembers things** you teach it, sets **reminders**, gives a **daily briefing**, and wakes
up when you say **"Hey Highguy"**.

- **AI brain (online, FREE):** powered by Google Gemini's free tier. Talk about anything,
  ask for the weather or look things up on Wikipedia, or say "open chrome and play some
  music" - it uses Highguy's tools to do it. Needs a free Gemini API key.
- **Offline mode:** without a key (or internet) Highguy still understands its built-in
  commands. Plain Python 3.8+ is enough.

```
        _   _  ___   ____  _   _   ____  _   _ __   __      _     ___
       | | | ||_ _| / ___|| | | | / ___|| | | |\ \ / /     / \   |_ _|
       | |_| | | | | |  _ | |_| || |  _ | | | | \ V /     / _ \   | |
       |  _  | | | | |_| ||  _  || |_| || |_| |  | |     / ___ \  | |
       |_| |_||___| \____||_| |_| \____| \___/   |_|    /_/   \_\|___|

  AI: online  │  Language: auto  │  Voice: off  │  Memories: 3  │  ♪: off  │  13:12

  Good afternoon, Harry.  AI brain online  •  1 reminder(s) pending

╭─ MAIN MENU ────────────────────────────────────────────────────────────────╮
│   [1]  Chat with Highguy      type anything                                │
│   [2]  Voice mode             talk using your microphone                   │
│                                                                            │
│   [3]  Add memory                                                          │
│   [4]  Search memories                                                     │
│   [5]  Show all memories                                                   │
│   [6]  Edit memory                                                         │
│   [7]  Delete memory                                                       │
│                                                                            │
│   [8]  Settings                                                            │
│   [9]  Help                                                                │
│   [0]  Exit                                                                │
╰────────────────────────────────────────────────────────────────────────────╯
```

## Start it

**Double-click `open_highguy_ai.bat`**, or from CMD:

```bat
python src\main.py            :: uses the language saved in Settings
python src\main.py swahili    :: or: english, auto
python src\main.py chat       :: open the chat straight away
python src\main.py voice      :: open voice mode straight away
```

The launcher uses `.venv` if it exists, otherwise the `py` launcher or `python`.

## Install the extras

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## AI brain (Jarvis mode) - free with Google Gemini

1. Get a **free** API key at https://aistudio.google.com/apikey (sign in with Google,
   click *Create API key*). No credit card needed.
2. In Highguy: **Settings → [9] API key**, paste it (it is hidden while you type).
   It is saved in `.env`, which git ignores. The `GEMINI_API_KEY` environment variable
   also works.
3. Chat normally. Examples:

```
You › good morning
  ⚙ get weather: Dar es Salaam
Highguy › Good morning, Harry. It's Tuesday 08:05, 27°C and sunny in Dar es Salaam.
          No reminders today. Big day - go get it.

You › open chrome and play some music
  ⚙ open app: chrome
  ⚙ music: play
Highguy › Chrome is open and the music is playing.

You › nikumbushe baada ya dakika 20 kumpigia Mama
  ⚙ set reminder: kumpigia Mama, 20
Highguy › Sawa, nitakukumbusha kumpigia Mama baada ya dakika 20.
```

What the brain can do: answer anything, check the weather (Open-Meteo, free), look things
up on Wikipedia (English and Kiswahili), open/close apps and websites, control music, list
files, lock the PC, shutdown/restart (always asks y/n), save and search memories, search
earlier conversations, set/list/cancel reminders, and save your name and city.

- **Model:** `gemini-3.8-flash` by default. When its free limit runs out, Highguy switches to
  `gemini-3.5-flash-lite` automatically. Change it in **Settings → AI model**.
- **Free tier limits:** a limited number of requests per day; they reset daily.
- **No live news search:** Google Search is not free for these models, so for news or prices
  Highguy opens a Google search in your browser instead.
- **Privacy:** on the free tier, Google may use your conversations to improve its products.
  Don't share passwords or secrets with the AI brain.
- In chat, type `new` to start a fresh conversation. If the AI fails (no internet, limit
  reached), Highguy answers that message offline instead.

## Voice (optional)

- **Speaking replies** works out of the box with the built-in Windows voice
  (`pyttsx3` is used instead when installed). Turn it on in **Settings → Voice replies**.
- **Microphone input** needs `SpeechRecognition` + `sounddevice` (works on Python 3.14) and
  an internet connection. `PyAudio` is used instead when it is installed.
  Check everything in **Settings → Check voice setup**.

## What you can say

| | English | Kiswahili |
|---|---|---|
| Greet | hello, how are you, who are you | habari, mambo, wewe ni nani |
| Time / date | what time is it, what is the date | saa ngapi, tarehe gani |
| Open apps | open chrome / notepad / calculator / paint / settings | fungua chrome / kikokotoo / mipangilio |
| Close apps | close chrome | funga chrome |
| Websites | open youtube, open gmail, open example.com | fungua youtube |
| Web search | search python tutorials | tafuta habari za leo |
| Music | play music, play *song name*, pause, resume, stop, next song, previous song, shuffle, list songs | cheza muziki, simamisha, endelea, zima muziki, wimbo unaofuata, changanya, orodha ya nyimbo |
| Memory | remember *title*: *details*, what do you remember about *topic* | kumbuka *jambo*, unakumbuka nini kuhusu *mada* |
| Your name | my name is Harry | jina langu ni Harry |
| Reminders | remind me in 10 minutes to stretch, remind me at 15:30 to pray, my reminders | nikumbushe baada ya dakika 5 kupika, vikumbusho vyangu |
| Briefing | good morning, briefing | habari za asubuhi, taarifa ya leo |
| Computer | list files, system info, lock screen, shutdown, restart, cancel shutdown | orodha ya faili, taarifa za kompyuta, funga skrini, zima kompyuta, sitisha kuzima |

These work offline too. Without the AI brain, any other question is answered from your
saved memories. For example:

```
You › remember Python audio setup: Use Python 3.11 for SpeechRecognition and PyAudio
Highguy › Got it! I'll remember: Use Python 3.11 for SpeechRecognition and PyAudio

You › Which Python version should I use for audio?
Highguy › From my memory: Use Python 3.11 for SpeechRecognition and PyAudio
```

In **auto** mode, Highguy replies in the language you used. Swahili time is given the
Swahili way, e.g. *saa 7:05 mchana (13:05)*.

## Project structure

```
highguy_ai/
├── open_highguy_ai.bat      # Double-click launcher (CMD)
├── highguy_ai.db            # SQLite database (memories, settings, reminders, chat log)
├── .env                     # Your API key (created by Settings, ignored by git)
├── config/commands.json     # Command keywords in English & Kiswahili - edit to add more
├── src/
│   ├── main.py              # CMD app: menus, chat, voice mode, settings
│   ├── ai_brain.py          # Gemini-powered brain: conversation and tools
│   ├── online_tools.py      # Free weather (Open-Meteo) and Wikipedia lookups
│   ├── reminders.py         # Reminders stored in SQLite, checked in the background
│   ├── ui.py                # Colors, boxes, tables and prompts for the CMD window
│   ├── command_processor.py # Understands commands and picks the right action
│   ├── ai_engine.py         # Finds relevant memories and builds answers
│   ├── memory_manager.py    # SQLite storage (memory and settings tables)
│   ├── system_commands.py   # Open/close apps, websites, files, lock, shutdown
│   ├── music_player.py      # Plays songs from your Music folder (Windows MCI)
│   ├── voice_handler.py     # Optional microphone input and spoken replies
│   └── config.py            # Paths
├── demo.py                  # Old text-only demo
└── documentations/database.md
```

## Settings

Saved in the database, so they survive restarts:

- **Language**: auto / english / swahili (menus switch to Kiswahili too)
- **Voice replies**: read answers out loud
- **Your name** and **city**: used in greetings, the briefing and weather
- **Wake word**: in voice mode, only respond after "Hey Highguy"
- **AI brain / API key / AI model**: see above
- **Music folder**: defaults to your `Music` folder, including sub-folders

## Safety

- Shutdown and restart always ask **y/n** on the keyboard first, and wait 60 seconds
  (say *cancel shutdown* to stop it).
- "open ..." only starts programs that are actually installed.
- "close ..." never closes Windows Explorer, CMD, PowerShell or Python.

## Troubleshooting

- **Weird symbols instead of boxes**: use Windows Terminal, or set the CMD font to Consolas.
  Set `NO_COLOR=1` to turn colors off.
- **No music found**: change the folder in Settings → Music folder.
- **Microphone not working**: see the Voice section above, then Settings → Check voice setup.
- **Testing without touching your memories**: set `HIGHGUY_DB` to another file path.
