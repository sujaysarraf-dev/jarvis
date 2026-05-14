# Future Plans — Jarvis

> Vision: a proactive, context-aware, voice-first desktop AI companion.
>
> Status: ✅ Done | 🔄 Partial | ❌ Not started

---

## ❌ 1. Streaming LLM Responses
Switch to `stream: true`. Process token-by-token, emit sentences to TTS as they arrive. First audio starts in <1s instead of 5s+.
> **Current**: `stream: False` — full response fetched then split into sentences.

## 🔄 2. Continuous Conversation (no wake word for follow-ups)
After each response, enter a 10-15s follow-up window where Jarvis listens for your next command. If you speak → continues. If silent → sleeps. No more repeating "Jarvis" for every follow-up.
> **Current**: Awake mode exists but no structured follow-up window. Times out after ~50s of silence (25 failed listens).

## ✅ 3. Context-aware Screen Vision
Auto-captures screenshots on queries like "what's on my screen". Sends to vision API (Groq Llama 4 Scout via OpenRouter-compat URL), shares conversation history. Glows cyan with "SCANNING..." label. Falls back to "not sure" if model can't identify anything meaningful.
> **Current**: Working via cloud API (Groq Llama 4 Scout). Local Ollama vision (Gemma 4, LLaVA 7B) downloaded but fails to load — CUDA host buffer errors on this machine.

## ✅ 4. Multi-turn Memory (conversation history)
Rolling 5-turn conversation buffer injected into both text and vision LLM calls. Enables follow-ups: "Make that shorter", "Explain more", "What did I just ask?".
> **Current**: 5-turn history shared between text and vision LLM calls. Bad junk facts cleared from user memory.

## ✅ 5. Dynamic PC Commands via LLM
No hardcoded command handlers. All PC control (WiFi, Bluetooth, volume, brightness, files, etc.) is generated as PowerShell by the LLM dynamically.
> **Current**: LLM generates PowerShell for every command. Echo guard prevents self-triggering from TTS feedback. Forbidden destructive commands enforced in config.py (format, clear, rm, del, etc.).

## ✅ 6. Auto-Elevation for Admin Commands
When a PowerShell command fails with admin errors, `_run_ps` auto-retries via `Start-Process -Verb RunAs`. Returns success/failure with output capture.
> **Current**: Automatic elevation retry for failed admin commands. No manual UAC prompt handling needed.

## ✅ 7. Crash-Resilient GUI Loop
GUI main loop catches all exceptions and restarts automatically. No more silent crashes.
> **Current**: `main_loop()` wraps entire cycle in try/except, sleeps 2s, retries forever.

## ✅ 8. Goodbye Command + Shutdown Awareness
Natural farewell phrases trigger graceful exit. False-positive shutdowns fixed.
> **Current**: "shutdown" removed from goodbye regex to prevent accidental closes. Goodbye phrases like "bye", "see you", "goodnight" work correctly.

## 🔄 9. Scheduled / Recurring Reminders
JSON-based schedule with cron-like syntax + background scheduler. Persists across restarts. "Remind me every weekday at 9 AM", "Remind me in 30 minutes".
> **Current**: Fire-once timer with `time.sleep()` only. No persistence. Lost on restart.

## ❌ 10. Notification Reader
Listen to Windows toast notifications via PowerShell or Windows event logs. Jarvis reads them aloud when idle. Filter by app or priority.

## ❌ 11. Autonomous Coding Agent
"Build a todo app with Flask" → Jarvis writes code, saves files, runs them, reads errors, debugs — all hands-free via voice. Full autonomous development loop.

## ❌ 12. Mood-Aware Music
Voice tone analysis (tired/angry/happy via speechbrain) → auto-plays matching background music. Energetic tracks when you're active, lo-fi when you're focused.

## ❌ 13. Desktop Puppet Master
Fully autonomous browser automation. "Apply to 10 junior dev jobs" → Jarvis navigates LinkedIn, fills forms, submits. Or "Order my usual pizza" — handles the entire checkout flow.

## ❌ 14. Gaming Co-pilot
Reads game wikis aloud, tracks cooldowns, reminds you of quest objectives during gameplay. Voice-controlled overlay for any game.

## ❌ 15. Time Traveler (screen history)
Records your screen every 5s (local, never uploaded). Ask "What was I looking at 10 minutes ago?" → Jarvis rewinds and shows you. Searchable screenshot history.

## ❌ 16. Inbox Zero Assistant
Reads your emails aloud by voice. Reply by speaking: "Draft a response saying I'll review it by Friday and send it." Jarvis writes, you approve.

## ❌ 17. Ghost Mode (keyword listener)
Listens for specific keywords near your desk, logs them with timestamps. "Find that thing we discussed about the server migration last Tuesday" — searches keyword log.

## ❌ 18. AI Dream Interpreter
Describe your dream → Jarvis cross-references with your daily logs, finds patterns, tells you what your subconscious is processing.

## ❌ 19. Desktop Guardian
Detects footsteps via mic → instantly locks PC, hides sensitive windows, opens camera feed. Also auto-locks after idle > 10min.

## ❌ 20. Coding Rival
"Race me" → Jarvis and you write the same function. First one done wins. Jarvis trash-talks, compares code quality, scores your solution.

## ❌ 21. Voice-Controlled Karaoke
Pick any song → shows lyrics, plays instrumental, records your voice, scores your pitch accuracy against the original track.

## ❌ 22. Paranoia Mode
Flip switch → Jarvis monitors door sounds, camera motion, keyboard silence. On detection: black screen, record audio/video, alert your phone.

## ❌ 23. Auto Expense Tracker
"Paid $45 for Uber to airport" → Jarvis categorizes, logs to spreadsheet, emails you weekly spending report. Voice-first bookkeeping.

## ❌ 24. Audio Book Narration
"Read this PDF" → narrates with cloned voice, remembers page position across sessions, supports bookmarks and text highlighting.

## ❌ 25. AI Dungeon Master
Fully voice-controlled text adventure. You describe actions naturally, LLM generates the world, narration, NPCs, and consequences in real-time.

## ❌ 26. Pet Mode
Webcam detects cat/dog via object detection → takes screenshot + alerts you: "Your cat is sitting on your keyboard again."

## ❌ 27. Live Personal Website
"Deploy a portfolio with my GitHub projects" → auto-generates HTML/CSS, deploys to Netlify, gives you the URL. All by voice.

## ❌ 28. OS Level Recall
Every file you open, every URL, every copy-paste is indexed locally. "What was that link I copied yesterday at 3pm?" — instant answer.

## ❌ 29. Jarvis VS Code Extension
Inline AI pair programmer inside VS Code. Highlight code, say "optimize this" → Jarvis rewrites it right inside your editor.

## ❌ 30. Auto Wake Word Generator
Record 3 seconds of anything ("hey computer", "yo bot") → trains a custom wake word in 60 seconds using few-shot learning.

## ❌ 31. Lie Detector
Analyzes voice pitch, hesitation patterns, and micro-expressions (webcam) during conversations. "That sounded uncertain — want me to double-check the facts?"

## ❌ 32. Voice-First Shopping Bot
"Buy a mechanical keyboard under $100" → scrapes Amazon/Flipkart, reads reviews aloud, checks out when you approve.

## ❌ 33. Home Security Voice Panel
Speaks through your speakers when someone rings the doorbell (smart doorbell integration). You reply "Tell them I'm busy" → Jarvis responds via outdoor speaker.

## ❌ 34. AI Therapist Mode
"I'm feeling stressed" → Jarvis runs a CBT-style conversation, logs mood patterns over time, suggests coping strategies based on what worked before.

## ❌ 35. Streaming Co-pilot
Reads chat aloud in your voice, plays sound effects on command, moderates toxic messages automatically during live streams.

## ❌ 36. Offline Survivor Mode
Caches a local LLM (Ollama) + wake word + TTS. When internet drops, Jarvis keeps working seamlessly — zero interruption.

## ❌ 37. Ambient Presence
Jarvis makes subtle background sounds (soft typing hum, breathing, fan noise) so the room doesn't feel empty. Like a white noise machine with personality.

## ❌ 38. Auto Standup Bot
At 9:30 AM every workday: "What did you do yesterday? Any blockers?" → drafts a Slack message, you voice-approve it, Jarvis posts it.

## ❌ 39. Freestyle Rap Battles
You say a topic, Jarvis rhymes insults at you in real-time. You roast it back. LLM-powered improv rap battles.

## ❌ 40. Auto Podcast Clipper
Records your voice throughout the day, finds the most interesting 30s segments (by vocal energy + topic shifts), compiles a daily highlight reel.
