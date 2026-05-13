# Future Plans — Jarvis

> Vision: a proactive, context-aware, voice-first desktop AI companion.
>
> Status: ✅ Done | 🔄 Partial | ❌ Not started

---

## ✅ 1. Streaming LLM Responses
Switch OpenRouter to `stream: true`. Process token-by-token, emit sentences to TTS as they arrive. First audio starts in <1s instead of 5s+.
> **Current**: `stream: False` — full response fetched then split into sentences. Transcript has fake word-by-word animation after the fact.

## 🔄 2. Continuous Conversation (no wake word for follow-ups)
After each response, enter a 10-15s follow-up window where Jarvis listens for your next command. If you speak → continues. If silent → sleeps. No more repeating "Jarvis" for every follow-up.
> **Current**: Awake mode exists but no structured follow-up window. Times out after ~50s of silence (25 failed listens). Needs a cleaner "waiting for follow-up" state.

## ❌ 3. Context-aware Screen Vision
Pass screenshots to vision models (gpt-4o, llama-3.2-11b-vision) via OpenRouter. "What's on my screen?", "Read this error", "What's that button?" — Jarvis actually sees your screen.
> **Current**: Screenshot capture works but images are never sent to any vision model.

## 🔄 4. Multi-turn Memory (conversation history)
Rolling 5-10 turn conversation buffer injected into LLM context. Enables follow-ups: "Make that shorter", "Explain more", "What did I just ask?".
> **Current**: Long-term fact memory exists (`memory.py`) but no short-term conversation buffer. Each LLM call is stateless.

## 🔄 5. Scheduled / Recurring Reminders
JSON-based schedule with cron-like syntax + background scheduler. Persists across restarts. "Remind me every weekday at 9 AM", "Remind me in 30 minutes".
> **Current**: Fire-once timer with `time.sleep()` only. No persistence. Lost on restart.

## ❌ 6. Notification Reader
Listen to Windows toast notifications via PowerShell or Windows event logs. Jarvis reads them aloud when idle. Filter by app or priority.

## ❌ 7. Autonomous Coding Agent
"Build a todo app with Flask" → Jarvis writes code, saves files, runs them, reads errors, debugs — all hands-free via voice. Full autonomous development loop.

## ❌ 8. Mood-Aware Music
Voice tone analysis (tired/angry/happy via speechbrain) → auto-plays matching background music. Energetic tracks when you're active, lo-fi when you're focused.

## ❌ 9. Desktop Puppet Master
Fully autonomous browser automation. "Apply to 10 junior dev jobs" → Jarvis navigates LinkedIn, fills forms, submits. Or "Order my usual pizza" — handles the entire checkout flow.

## ❌ 10. Gaming Co-pilot
Reads game wikis aloud, tracks cooldowns, reminds you of quest objectives during gameplay. Voice-controlled overlay for any game.

## ❌ 11. Time Traveler (screen history)
Records your screen every 5s (local, never uploaded). Ask "What was I looking at 10 minutes ago?" → Jarvis rewinds and shows you. Searchable screenshot history.

## ❌ 12. Inbox Zero Assistant
Reads your emails aloud by voice. Reply by speaking: "Draft a response saying I'll review it by Friday and send it." Jarvis writes, you approve.

## ❌ 13. Ghost Mode (keyword listener)
Listens for specific keywords near your desk, logs them with timestamps. "Find that thing we discussed about the server migration last Tuesday" — searches keyword log.

## ❌ 14. AI Dream Interpreter
Describe your dream → Jarvis cross-references with your daily logs, finds patterns, tells you what your subconscious is processing.

## ❌ 15. Desktop Guardian
Detects footsteps via mic → instantly locks PC, hides sensitive windows, opens camera feed. Also auto-locks after idle > 10min.

## ❌ 16. Coding Rival
"Race me" → Jarvis and you write the same function. First one done wins. Jarvis trash-talks, compares code quality, scores your solution.

## ❌ 17. Voice-Controlled Karaoke
Pick any song → shows lyrics, plays instrumental, records your voice, scores your pitch accuracy against the original track.

## ❌ 18. Paranoia Mode
Flip switch → Jarvis monitors door sounds, camera motion, keyboard silence. On detection: black screen, record audio/video, alert your phone.

## ❌ 19. Auto Expense Tracker
"Paid $45 for Uber to airport" → Jarvis categorizes, logs to spreadsheet, emails you weekly spending report. Voice-first bookkeeping.

## ❌ 20. Audio Book Narration
"Read this PDF" → narrates with cloned voice, remembers page position across sessions, supports bookmarks and text highlighting.

## ❌ 21. AI Dungeon Master
Fully voice-controlled text adventure. You describe actions naturally, LLM generates the world, narration, NPCs, and consequences in real-time.

## ❌ 22. Pet Mode
Webcam detects cat/dog via object detection → takes screenshot + alerts you: "Your cat is sitting on your keyboard again."

## ❌ 23. Live Personal Website
"Deploy a portfolio with my GitHub projects" → auto-generates HTML/CSS, deploys to Netlify, gives you the URL. All by voice.

## ❌ 24. OS Level Recall
Every file you open, every URL, every copy-paste is indexed locally. "What was that link I copied yesterday at 3pm?" — instant answer.

## ❌ 25. Jarvis VS Code Extension
Inline AI pair programmer inside VS Code. Highlight code, say "optimize this" → Jarvis rewrites it right inside your editor.

## ❌ 26. Auto Wake Word Generator
Record 3 seconds of anything ("hey computer", "yo bot") → trains a custom wake word in 60 seconds using few-shot learning.

## ❌ 27. Lie Detector
Analyzes voice pitch, hesitation patterns, and micro-expressions (webcam) during conversations. "That sounded uncertain — want me to double-check the facts?"

## ❌ 28. Voice-First Shopping Bot
"Buy a mechanical keyboard under $100" → scrapes Amazon/Flipkart, reads reviews aloud, checks out when you approve.

## ❌ 29. Home Security Voice Panel
Speaks through your speakers when someone rings the doorbell (smart doorbell integration). You reply "Tell them I'm busy" → Jarvis responds via outdoor speaker.

## ❌ 30. AI Therapist Mode
"I'm feeling stressed" → Jarvis runs a CBT-style conversation, logs mood patterns over time, suggests coping strategies based on what worked before.

## ❌ 31. Streaming Co-pilot
Reads chat aloud in your voice, plays sound effects on command, moderates toxic messages automatically during live streams.

## ❌ 32. Offline Survivor Mode
Caches a local LLM (Ollama) + wake word + TTS. When internet drops, Jarvis keeps working seamlessly — zero interruption.

## ❌ 33. Ambient Presence
Jarvis makes subtle background sounds (soft typing hum, breathing, fan noise) so the room doesn't feel empty. Like a white noise machine with personality.

## ❌ 34. Auto Standup Bot
At 9:30 AM every workday: "What did you do yesterday? Any blockers?" → drafts a Slack message, you voice-approve it, Jarvis posts it.

## ❌ 35. Freestyle Rap Battles
You say a topic, Jarvis rhymes insults at you in real-time. You roast it back. LLM-powered improv rap battles.

## ❌ 36. Auto Podcast Clipper
Records your voice throughout the day, finds the most interesting 30s segments (by vocal energy + topic shifts), compiles a daily highlight reel.
