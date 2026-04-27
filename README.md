# Voice-Controlled AI Assistant

A local, rule-based Python AI assistant for Windows that responds to voice commands in **English and Swahili**. No external AI API required.

## Features
- 🎤 Voice input (local speech recognition)
- 🔊 Voice output (text-to-speech)
- 🌍 **Bilingual Support**: English and Swahili
- 💻 Safe terminal command execution
- 🌐 Open applications and browsers
- 🎵 Play music
- 🔒 Local processing - no external AI dependencies

## Installation

1. Install Python 3.8 or higher
2. Navigate to the project directory
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. For Windows, install PyAudio:
   ```bash
   pip install pyaudio
   ```
   
   If you encounter issues, download a pre-built wheel from:
   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

## Usage

### Auto-Detect Language (Default)
```bash
python src/main.py
```
The assistant will automatically detect English or Swahili from your commands.

### English Only
```bash
python src/main.py english
```

### Swahili Only
```bash
python src/main.py swahili
```

## Voice Commands Examples

### English
- "Open Chrome"
- "Play music"
- "What is the time?"
- "Open Notepad"
- "List files"
- "Help"
- "Exit"

### Swahili
- "Fungua Chrome"
- "Cheza muziki"
- "Saa gani?"
- "Fungua Notepad"
- "Orodha ya faili"
- "Msaada"
- "Kwaheri"

## Configuration

Edit `config/commands.json` to add or modify voice commands in both languages.

## Project Structure
```
highguy_ai/
├── src/
│   ├── main.py              # Main assistant entry point
│   ├── voice_handler.py     # Speech recognition and text-to-speech
│   ├── command_processor.py # Command parsing and execution
│   ├── system_commands.py   # Terminal/system operations
│   └── music_player.py      # Music playback
├── config/
│   └── commands.json        # Command definitions (English & Swahili)
├── requirements.txt
└── README.md
```

## Supported Commands

### Greetings
- **English**: Hello, Hi, Hey
- **Swahili**: Habari, Salaam, Jambo

### Help
- **English**: Help, What can you do
- **Swahili**: Msaada, Unaweza kufanya nini

### Time & Date
- **English**: What time is it, What is the date, Today
- **Swahili**: Saa gani, Tarehe gani, Leo

### Applications
Open: Chrome, Firefox, Edge, Notepad, Calculator, Spotify, VLC

### Music
- **Play**: Play music, Start music
- **Stop**: Stop music, Pause music
- **Next**: Next song, Skip

### System
- List files
- Lock screen

## Troubleshooting

- **No microphone detected**: Check your audio input device in System Settings
- **PyAudio installation fails**: Use pre-built wheels or anaconda
- **Commands not recognized**: Check `config/commands.json` for correct keywords
- **Language not detected**: Try specifying language explicitly (english/swahili)

## Safety
- Only whitelisted commands can be executed
- Terminal commands are restricted to safe operations only
- Add custom commands in config file

## Language Support
- Currently supports **English** and **Swahili**
- Language detection is automatic but can be overridden
- Responses are provided in the detected language
