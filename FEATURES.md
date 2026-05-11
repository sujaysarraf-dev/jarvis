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

---

## Command History
- All commands logged with timestamps to `command_history.txt`

---

## 🔮 10 Amazing Features to Add Next

### 1. Email/SMS Sender
- `"send email to mom: I'll be late"` → sends via SMTP/Gmail API
- `"send WhatsApp message to [name]: [text]"`

### 2. Smart Home Control
- `"turn on living room lights"` → Philips Hue / smart plug API
- `"set thermostat to 22 degrees"`

### 3. Web Scraper / Price Tracker
- `"track price of iPhone on Amazon"` → scrapes & alerts when price drops
- `"what's the latest news about AI"` → fetches & reads headlines

### 4. Face / Object Recognition (Camera)
- `"who am I"` → takes photo & runs local face recognition
- `"what's in front of me"` → captures & describes via LLava vision model

### 5. Translation Mode
- `"translate hello to French"` → speaks translation
- `"activate translator mode"` → auto-translates everything you say

### 6. Dictation / Typing Assistant
- `"start dictation"` → types everything you say into the active window
- `"type: Dear Sir, ..."` → auto-types text

### 7. Custom Macros / Scripts
- `"run my morning routine"` → executes a user-defined script sequence
- `"set macro: when I say X, do Y"` → creates custom voice macros

### 8. Reading Assistant
- `"read this page"` → OCR + TTS reads screen content
- `"read my emails"` → fetches & reads latest emails aloud

### 9. Calendar Integration
- `"what's on my calendar today"` → reads Google/Outlook calendar
- `"schedule a meeting tomorrow at 3pm"` → creates calendar event

### 10. Voice Profiles / Multiple Users
- `"switch to [name]'s profile"` → loads user-specific settings
- Voice fingerprint recognition to auto-detect who's speaking

---

## 🚀 20 MORE Crazy Features

### 11. AI Dream Interpreter
- Describe your dream → LLM analyzes and interprets it with psychological meaning
- `"I dreamed I was flying..."` → dreams analyzed via local LLM

### 12. Hacker Mode (Terminal Effect)
- `"activate hacker mode"` → GUI turns green matrix-style, TTS voice becomes robotic, fake hack animations
- Commands show as green streams of text before executing

### 13. PC Ghost (Prank Mode)
- `"prank mode on"` → random mouse movements, random pop-ups, opens/closes CD tray, plays random sounds
- `"open the pod bay doors"` → funny HAL 9000 references

### 14. Real-time Translation Earpiece
- `"translate everything to Spanish"` → listens to system audio (via loopback) and translates in real-time
- Works like a live interpreter for YouTube, meetings, etc.

### 15. AI Girlfriend / Companion Mode
- `"activate companion mode"` → switches to conversational personality with memory
- Remembers past conversations, tells stories, gives advice with emotional context

### 16. Screen OCR + Auto-Clicker
- `"find and click the login button"` → OCR scans screen, finds matching text, clicks it
- `"fill this form with my details"` → auto-fills web forms using saved profile

### 17. Voice-Controlled Coding Assistant
- `"create a Python script that downloads YouTube videos"` → LLM generates code, saves to file, and runs it
- `"debug this error: [paste error]"` → reads error, fixes code

### 18. Sleep Detector
- Detects if you snore / say something in sleep via microphone
- Records audio snippets and replays them in the morning
- `"did I snore last night?"` → plays back detected sounds

### 19. Gaming Voice Commander
- `"save game"`, `"quick load"`, `"screenshot"` — hotkeys for any game
- `"record last 30 seconds"` — clips gameplay using GPU capture
- `"turn on night vision"` → adjust game gamma/settings

### 20. AI Butler (Guest Mode)
- `"guest mode on"` → limited commands for visitors (no system control)
- Greets guests by name, tells jokes, checks weather
- `"show guest history"` → logs of what guest asked

### 21. Phone Integration (via ADB)
- `"find my phone"` → makes phone ring via ADB over WiFi
- `"read my texts"` → reads SMS from connected Android
- `"reply to [contact]: [message]"` → sends SMS

### 22. Voice Notes to Obsidian/Notion
- `"take note in Obsidian: idea"` → appends to a markdown file in Obsidian vault
- `"create Notion page: grocery list"` → Notion API integration

### 23. Autonomous Web Research
- `"research quantum computing and summarize"` → opens browser, searches, scrapes multiple pages, returns summary
- `"find cheapest flights to Tokyo"` → searches flight aggregators

### 24. PC Health Monitor
- Alerts when CPU temp exceeds threshold
- `"how's my PC health?"` → speaks CPU temp, GPU temp, fan speeds, disk health
- Auto-warnings: `"Warning: CPU at 90°C"`

### 25. Voice-Controlled DJ
- `"play"`, `"pause"`, `"next track"`, `"previous"` — controls any media player
- `"play upbeat songs"` → analyzes playlist mood and plays matching tracks
- `"crossfade in 5 seconds"` → DJ transition effects

### 26. Accessibility Mode
- Screen reader for visually impaired: reads everything on screen
- High-contrast voice feedback
- `"describe this image"` → vision model describes what's on screen

### 27. Time Travel Mode
- Sets PC date/time to random historical dates
- `"go to 1995"` → changes system date, changes theme to Win95 style
- All apps show old dates — great for retro gaming

### 28. AI Stock Trader
- `"check my portfolio"` → fetches stock prices
- `"buy 10 shares of TSLA at market price"` → executes via brokerage API
- `"set stop loss at 5%"` → monitors and alerts

### 29. Deep Work Mode
- `"deep work for 25 minutes"` → Pomodoro timer, blocks distracting apps/sites, enables Do Not Disturb
- `"what's my focus score today?"` → tracks productive vs distracted time
- Penalty system: "I got distracted, deduct $5 from my allowance"

### 30. Self-Hosted Cloud Sync
- Syncs all notes, history, reminders across multiple computers via your own server
- `"sync with my laptop"` → local network sync
- `"what did I ask yesterday on my work PC?"` → cross-device search

