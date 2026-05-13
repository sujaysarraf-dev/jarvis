# JARVIS - Voice Assistant for Windows

## Features

### Voice Commands
- Wake word "Jarvis" activates listening mode
- Natural language processing via OpenRouter AI
- Continuous listening loop with auto-sleep after 25s silence
- Background wake-word listener (`--bg` mode)

### App Launcher
- Open apps: calculator, notepad, browser, terminal, paint, word, excel, spotify, discord, vscode, whatsapp, etc.
- Fuzzy matching for app names
- Open websites: "open youtube.com"
- System actions: show desktop, lock, restart, shutdown, sleep

### System Controls
- Volume up/down/mute
- Wi-Fi on/off, Bluetooth on/off
- Dark/light mode toggle
- Screenshot capture
- Clipboard read/write

### Productivity
- Typing assistant ("type hello world")
- Pomodoro timer
- Reminders / todo list
- Notes ("note this...")
- Alarm / timer
- System info (RAM, storage)

### Memory
- Remembers personal facts about you
- Extracts facts automatically from conversation
- Recall: "what do you know about me"
- Forget/clear commands
- Context-aware AI responses

### Text Input
- Type commands in the info panel
- Non-blocking — GUI stays responsive

### GUI
- Draggable bubble overlay
- Color-coded status dot (idle/listening/processing/speaking)
- Pulse animation when listening
- Transcript panel showing conversation history
- Right-click menu: Shutdown or Hide
- Startup on boot (auto-enabled)

### Hand Gesture Detection (`out/hand_signs.py`)
- MediaPipe hand tracking
- Gestures: PALM, FIST, THUMBS_UP, POINT, PEACE, THREE, ROCK, OK
- Face detection overlay
- Run separately: `python out/hand_signs.py`

## Tech

- **STT**: Google Speech Recognition
- **TTS**: Google gTTS (primary) → Windows SAPI fallback
- **AI**: OpenRouter (streaming, sentence-by-sentence)
- **GUI**: tkinter overlay
- **Memory**: JSON file with keyword search
- **Project**: Modular `jarvis/` package

## Project Structure

```
jarvis/
├── jarvis/           # Python package
│   ├── config.py     # Constants, API keys, command maps
│   ├── memory.py     # Personal facts storage
│   ├── utils.py      # Logging, text cleaning, helpers
│   ├── speech.py     # TTS, wake word, command listening
│   ├── llm.py        # OpenRouter API with streaming
│   ├── commands.py   # Command handlers
│   └── gui.py        # tkinter overlay + main loop
├── out/              # Standalone scripts
│   ├── hand_signs.py
│   └── hand_landmarker.task
├── data/             # Runtime data
│   ├── user_memory.json
│   ├── command_history.txt
│   └── todo.txt
├── ss/               # Screenshots
├── main.py           # Entry point
└── requirements.txt
```

## Latest Fixes

- Modular refactor from 1000-line monolith → 7 modules
- Streaming API responses — first token in ~1-2s
- Sentence-by-sentence progressive TTS
- Retry logic + 3-model fallback for AI
- Log rotation (2MB cap)
- Startup .env loading for API key
- gTTS primary voice engine
- Right-click context menu (Shutdown / Hide)
- ``bye jarvis`` → full shutdown
