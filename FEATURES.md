# JARVIS Voice Assistant - Features

## Wake Word
- `"Jarvis"` — activates the assistant
- `"stop"`, `"sleep"`, `"bye"`, `"go to sleep"` — deactivates

## Floating Bubble UI
- Draggable circular bubble always on top
- Color-coded status: idle (gray) → listening (green) → processing (orange) → speaking (blue) → error (red)
- Pulse animation while listening/processing
- Double-click to show/hide info panel

## App Launcher
| Voice Command | Action |
|---------------|--------|
| "open calculator" | Opens Calculator |
| "open notepad" | Opens Notepad |
| "open browser" / "open chrome" | Opens Chrome |
| "open edge" / "open firefox" | Opens Edge/Firefox |
| "open explorer" / "open file explorer" | Opens File Explorer |
| "open terminal" / "open cmd" | Opens Command Prompt |
| "open paint" | Opens Paint |
| "open word" / "open excel" / "open powerpoint" | Opens Office apps |
| "open spotify" | Opens Spotify |
| "open discord" / "open whatsapp" / "open telegram" | Opens chat apps |
| "open vscode" / "open code" | Opens VS Code |
| "open settings" / "open control panel" | Opens system settings |
| "open task manager" / "open taskmgr" | Opens Task Manager |
| "open youtube" | Opens YouTube website |
| "open github" / "open gmail" / "open maps" | Opens websites |

## System Commands
| Voice Command | Action |
|---------------|--------|
| "volume up" / "louder" | Increase volume |
| "volume down" / "quieter" / "lower" | Decrease volume |
| "mute" / "silence" | Mute audio |
| "unmute" | Unmute audio |
| "show desktop" | Minimize all windows |
| "lock" / "lock computer" | Lock PC |
| "restart" / "reboot" | Restart computer |
| "shutdown" / "turn off" | Shutdown computer |
| "sleep" / "hibernate" | Put PC to sleep |
| "open downloads" / "open documents" / "open desktop" | Open user folders |
| "show ss" / "show screenshots" / "open ss" | Open screenshots folder |

## Screenshots
| Voice Command | Action |
|---------------|--------|
| "screenshot" / "capture" | Takes screenshot (saves to ss/) |
| "show screenshots" / "open ss" | Opens ss folder |

## Music Playback
| Voice Command | Action |
|---------------|--------|
| "play music" | Opens Spotify |
| "play [song name]" | Searches YouTube Music and plays |

## Quick Notes
| Voice Command | Action |
|---------------|--------|
| "note this: [text]" | Appends to notes.md |
| "take note: [text]" | Appends to notes.md |
| "remember [text]" | Appends to notes.md |

## Reminders
| Voice Command | Action |
|---------------|--------|
| "remind me to [task]" | Saves to todo.txt |
| "set reminder to [task]" | Saves to todo.txt |

## Alarm / Timer
| Voice Command | Action |
|---------------|--------|
| "set alarm for X minutes" | Runs X-minute timer, speaks when done |
| "set timer for X seconds" | Runs X-second timer, speaks when done |

## Web Opener
| Voice Command | Action |
|---------------|--------|
| "open youtube.com" | Opens any website in browser |
| "go to github.com" | Opens any website |
| "launch google.com" | Opens any website |

## System Info
| Voice Command | Action |
|---------------|--------|
| "how much RAM" / "specs" | Speaks RAM usage |
| "battery" | Speaks battery status |
| "storage" | Speaks storage info |

## Clipboard
| Voice Command | Action |
|---------------|--------|
| "copy [text] to clipboard" | Copies text to clipboard |
| "read clipboard" / "what's on clipboard" | Speaks clipboard content |

## Time & Date
| Voice Command | Action |
|---------------|--------|
| "what time is it" / "time" | Speaks current time |
| "what's the date" / "what day is it" | Speaks current date |

## Dark/Light Mode
| Voice Command | Action |
|---------------|--------|
| "turn on dark mode" | Enables Windows dark theme |
| "turn on light mode" | Enables Windows light theme |

## Typing Assistant
| Voice Command | Action |
|---------------|--------|
| "type: hello world" | Auto-types text into active window |

## Pomodoro Timer
| Voice Command | Action |
|---------------|--------|
| "start pomodoro" | 25-min focus timer with break alert |
| "focus for 15 minutes" | Custom duration pomodoro |

## WiFi & Bluetooth
| Voice Command | Action |
|---------------|--------|
| "turn on wifi" | Enables WiFi |
| "turn off wifi" | Disables WiFi |
| "turn on bluetooth" | Enables Bluetooth |
| "turn off bluetooth" | Disables Bluetooth |

## AI (LLM Integration)
| Voice Command | Action |
|---------------|--------|
| Any unrecognized command | Falls back to phi4 LLM for understanding |
| Questions | LLM answers via text-to-speech |
| Commands | LLM generates & executes PowerShell command |

## Auto-Start
- Automatically adds itself to Windows Startup folder
- Runs at boot without user intervention

## History
- All spoken commands saved to `command_history.txt`

## Tech Stack
- `speech_recognition` — voice input (Google Speech API)
- `gTTS + pygame` — text-to-speech output
- `tkinter` — floating bubble GUI
- `Ollama (phi4)` — local LLM for command understanding
- `psutil` — system info
- `pyperclip` — clipboard access
- `PIL` — screenshots
- Custom PowerShell calls for system controls
## Command History
- All commands logged with timestamps to `command_history.txt`
