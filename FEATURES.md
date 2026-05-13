# JARVIS Voice Assistant - Features

## Wake Word
- `"Jarvis"` — activates the assistant
- `"bye Jarvis"` — closes the app
- `"deactivate"`, `"go to sleep"` — deactivates assistant
- Smart word-boundary matching: "stop playing music" no longer triggers deactivation

## Floating Bubble UI
- Draggable circular bubble always on top
- Color-coded status: idle (gray) → listening (green) → processing (orange) → speaking (blue) → error (red)
- Pulse animation while listening/processing
- Double-click to show/hide info panel with **live transcript**

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
| "play [song name]" | Searches YouTube via yt-dlp and opens video directly |

## Quick Notes
| Voice Command | Action |
|---------------|--------|
| "note this: [text]" | Appends to notes.md |
| "take note: [text]" | Appends to notes.md |
| "remember [text]" | Appends to notes.md |

## Memory / Knowledge Base
| Voice Command | Action |
|---------------|--------|
| "remember I'm a developer" | Saves personal fact to user_memory.json |
| "what do you know about me" | Speaks all saved facts |
| "forget my name" | Deletes matching fact |
| "clear my memory" | Wipes all stored facts |
| Auto-learning | LLM auto-extracts facts from conversations |

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

## LLM Fallback
| Feature | Detail |
|---------|--------|
| Unrecognized commands | Falls back to llama3.2:1b via Ollama |
| Runs in background thread | Doesn't block voice interaction |

## Text Input
- Double-click bubble to open info panel with text entry box
- Type commands and press Enter to test without voice
- Same command processing as voice input

## Live Transcript
- Double-click the bubble to open the info panel
- Bottom section shows a scrolling log of what you said vs what Jarvis replied
- Color-coded: You (blue), Jarvis (green)
- Timestamps on every entry
- Helps verify speech recognition accuracy

## Auto-Start
- Automatically adds itself to Windows Startup folder
- Runs at boot without user intervention
- Fixed path resolution so startup works from any working directory

## Bug Fixes & Improvements
| Fix | Detail |
|-----|--------|
| **Thread-safe GUI** | All tkinter updates routed through `root.after()` — no more random crashes |
| **Keyword matching** | Word-boundary regex prevents false deactivations ("stopwatch", "storage") |
| **Missing deps** | `psutil`, `pyperclip`, `PIL` — graceful ImportError instead of crash |
| **Speech timeout** | `phrase_time_limit=5` prevents infinite listening blocks |
| **LLM prompt** | Raw format (no `[INST]` tags) — stops model from echoing prompt back |
| **Useless responses** | Filter catches "I'm Jarvis", "how can I help" etc. before speaking |
| **Memory cleanup** | Junk auto-extracted facts no longer pollute LLM context |
| **TTS imports** | `gTTS` imported once at module level (not every speak call) |
| **Path handling** | Startup `.bat` uses absolute paths with `cd /d` — works from any folder |

## Tech Stack
- `speech_recognition` — voice input (Google Speech API)
- `gTTS + pygame` — text-to-speech output
- `tkinter` — floating bubble GUI with text input + live transcript
- `rapidfuzz` — instant fuzzy command matching
- `Ollama (llama3.2:1b)` — local LLM fallback for unrecognized commands
- `yt-dlp` — YouTube search for music playback
- `psutil` — system info (optional)
- `pyperclip` — clipboard access (optional)
- `PIL` — screenshots (optional)
- Custom PowerShell calls for system controls

## Command History
- All commands logged with timestamps to `command_history.txt`
