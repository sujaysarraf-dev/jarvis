import os
import re
import time
import datetime
import subprocess
import urllib.parse
import json
import threading
from rapidfuzz import fuzz, process
from jarvis.config import COMMAND_MAP, KNOWN_ACTIONS, PREFIXES, FUZZY_SCORE, BASE_DIR, DATA_FOLDER, SS_FOLDER, CLOSE_MAP
import random
from jarvis.memory import memory
from jarvis.speech import speak
from jarvis.utils import log_command

def fuzzy_find(cmd, gui):
    cmd_lower = cmd.lower().strip()
    log_command(f"fuzzy_find input: [{cmd_lower}]")

    all_exact = []
    for name, action, phrases in KNOWN_ACTIONS:
        for phrase in phrases:
            all_exact.append((len(phrase), phrase, name, action))
    all_exact.sort(key=lambda x: -x[0])
    for length, phrase, name, action in all_exact:
        if phrase in cmd_lower:
            log_command(f"  exact match: [{name}] via [{phrase}]")
            try:
                action()
            except:
                pass
            speak("Done", gui)
            return True

    for prefix in PREFIXES:
        if cmd_lower.startswith(prefix):
            remainder = cmd_lower[len(prefix):].strip()
            log_command(f"  prefix match: [{prefix}] remainder=[{remainder}]")
            if remainder in COMMAND_MAP:
                subprocess.Popen(COMMAND_MAP[remainder], shell=True)
                speak(f"Opening {remainder}", gui)
                return True
            for key, val in COMMAND_MAP.items():
                if key in remainder:
                    subprocess.Popen(val, shell=True)
                    speak(f"Opening {key}", gui)
                    return True
            result = process.extractOne(remainder, list(COMMAND_MAP.keys()), scorer=fuzz.token_sort_ratio, score_cutoff=FUZZY_SCORE)
            if result:
                log_command(f"  fuzzy app: [{result[0]}] score={result[1]}")
                subprocess.Popen(COMMAND_MAP[result[0]], shell=True)
                speak(f"Opening {result[0]}", gui)
                return True

    for key, val in COMMAND_MAP.items():
        if cmd_lower == key or cmd_lower.startswith(key + " ") or cmd_lower.endswith(" " + key) or (" " + key + " ") in cmd_lower:
            subprocess.Popen(val, shell=True)
            speak(f"Opening {key}", gui)
            return True

    for name, action, phrases in KNOWN_ACTIONS:
        result = process.extractOne(cmd_lower, phrases, scorer=fuzz.ratio, score_cutoff=85)
        if result:
            log_command(f"  fuzzy action: [{name}] score={result[1]} phrase=[{result[0]}]")
            try:
                action()
            except:
                pass
            speak("Done", gui)
            return True

    result = process.extractOne(cmd_lower, list(COMMAND_MAP.keys()), scorer=fuzz.token_sort_ratio, score_cutoff=FUZZY_SCORE)
    if result:
        log_command(f"  fuzzy whole-cmd: [{result[0]}] score={result[1]}")
        subprocess.Popen(COMMAND_MAP[result[0]], shell=True)
        speak(f"Opening {result[0]}", gui)
        return True

    log_command(f"  NO MATCH for: [{cmd_lower}]")
    return False

def handle_cmd(cmd, gui):
    cmd = cmd.lower().strip()
    if not cmd:
        return
    
    # Broad Echo Filter: ignore phrases that sound like Jarvis's own feedback
    echo_phrases = ["i am listen", "i am listening", "listening", "i'm listening", "system ready", "i am awake"]
    if cmd in echo_phrases:
        log_command(f"Echo filter: exact match for [{cmd}]")
        return

    if gui.last_spoken:
        # Check if what we heard is just what we said
        # SAPI and gTTS sometimes sound different to the recognizer
        ratio = fuzz.partial_ratio(cmd, gui.last_spoken.lower())
        if ratio > 80:
            log_command(f"Echo guard: skipped (fuzz={ratio:.0f}%): [{cmd}] vs [{gui.last_spoken[:50]}]")
            return

    # Log and display once we're sure it's not an echo
    gui.add_transcript("You", cmd)
    gui.set_status("processing", f"Accepted: {cmd}")
    log_command(cmd)

    if "time" in cmd:
        t = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {t}", gui)
        return
    if "date" in cmd or "today" in cmd or "day" in cmd:
        d = datetime.datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {d}", gui)
        return
    if re.search(r"\b(?:bye\s+jarvis|bye\s+jar|exit\s+jarvis|goodbye|goodbye\s+jarvis|close\s+jarvis|shutdown)\b", cmd):
        speak("Always a pleasure. Shutting down systems now.", gui)
        gui.close()
        return

    close_match = re.search(r"^(?:close|stop|exit|terminate)\s+(.+)", cmd)
    if close_match:
        app = close_match.group(1).strip()
        if app in CLOSE_MAP:
            proc = CLOSE_MAP[app]
            subprocess.run(f"taskkill /F /IM {proc}", shell=True, capture_output=True)
            speak(f"Terminating {app} process.", gui)
            return
        # Try fuzzy match for close
        result = process.extractOne(app, list(CLOSE_MAP.keys()), scorer=fuzz.token_sort_ratio, score_cutoff=FUZZY_SCORE)
        if result:
            proc = CLOSE_MAP[result[0]]
            subprocess.run(f"taskkill /F /IM {proc}", shell=True, capture_output=True)
            speak(f"Closing {result[0]} as requested.", gui)
            return

    if re.search(r'\b(?:deactivate|go to sleep|exit)\b', cmd) and len(cmd.split()) < 4:
        speak("Entering standby mode.", gui)
        gui.deactivate()
        return
    if re.search(r'\b(?:stop|sleep|bye|quit)\b', cmd) and len(cmd.split()) < 3 and not re.search(r'\b(?:stopwatch|stop the music|stop playing|stopwatch|stopped|stopping|storage|sleeping)\b', cmd):
        speak("Systems entering sleep cycle.", gui)
        gui.deactivate()
        return

    alarm = re.search(r"(?:set|create)\s+(?:alarm|timer)\s+(?:for\s+)?(\d+)\s*(?:minute|second|hour|min|sec)", cmd)
    if alarm:
        t = alarm.group(1).strip()
        speak(f"Alarm set for {t} minutes", gui)
        threading.Thread(target=lambda: (time.sleep(int(t)*60), speak("Time's up!", gui)), daemon=True).start()
        return

    remind = re.search(r"(?:remind me|set reminder)\s+(?:to\s+)?(.+)", cmd)
    if remind:
        text = remind.group(1).strip()
        todo_path = os.path.join(DATA_FOLDER, "todo.txt")
        with open(todo_path, "a") as f:
            f.write(f"- {datetime.datetime.now().strftime('%m/%d')}: {text}\n")
        speak("Reminder saved", gui)
        return

    site = re.search(r"(?:open|go to|launch)\s+(\w+\.\w+)", cmd)
    if site:
        subprocess.Popen(f"start https://{site.group(1)}", shell=True)
        speak(f"Opening {site.group(1)}", gui)
        return

    search = re.search(r"(?:google|search for|look up)\s+(.+)", cmd)
    if search:
        query = search.group(1).strip()
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        subprocess.Popen(f"start {url}", shell=True)
        speak(f"Searching for {query}", gui)
        return

    if "joke" in cmd:
        jokes = [
            "Why did the web developer walk out of a restaurant? Because of the table layout.",
            "How many programmers does it take to change a light bulb? None, it's a hardware problem.",
            "What's the object-oriented way to become wealthy? Inheritance.",
            "Why do programmers always mix up Halloween and Christmas? Because Oct 31 == Dec 25.",
            "An SQL query walks into a bar, walks up to two tables, and asks... 'Can I join you?'"
        ]
        speak(random.choice(jokes), gui)
        return

    if "flip a coin" in cmd or "toss a coin" in cmd:
        res = random.choice(["Heads", "Tails"])
        speak(f"It's {res}", gui)
        return

    if "roll a die" in cmd or "roll a dice" in cmd:
        res = random.randint(1, 6)
        speak(f"You rolled a {res}", gui)
        return

    if "how much ram" in cmd or "system info" in cmd or "specs" in cmd or "battery" in cmd or "storage" in cmd:
        try:
            import psutil
            ram = psutil.virtual_memory()
            usage = f"{ram.percent}% used out of {round(ram.total/(1024**3))} GB"
            speak(f"RAM: {usage}", gui)
        except ImportError:
            speak("psutil library not installed. Cannot check system info.", gui)
        return

    if "copy" in cmd and "clipboard" in cmd:
        clip = re.search(r"copy\s+(.+)\s+to\s+clipboard", cmd)
        if clip:
            try:
                import pyperclip
                pyperclip.copy(clip.group(1))
                speak("Copied to clipboard", gui)
            except ImportError:
                speak("pyperclip library not installed.", gui)
        return

    if "clipboard" in cmd and ("paste" in cmd or "read" in cmd or "what" in cmd):
        try:
            import pyperclip
            t = pyperclip.paste()
            speak(f"Clipboard: {t[:80]}", gui)
        except ImportError:
            speak("pyperclip library not installed.", gui)
        return

    if "dark mode" in cmd or "light mode" in cmd:
        if "dark" in cmd:
            subprocess.run('powershell -Command "New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme -Value 0 -Force"', shell=True, capture_output=True)
            subprocess.run('powershell -Command "New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name SystemUsesLightTheme -Value 0 -Force"', shell=True, capture_output=True)
        else:
            subprocess.run('powershell -Command "New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme -Value 1 -Force"', shell=True, capture_output=True)
            subprocess.run('powershell -Command "New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name SystemUsesLightTheme -Value 1 -Force"', shell=True, capture_output=True)
        speak("Theme changed", gui)
        return

    type_match = re.search(r"^type\s+(.+)", cmd)
    if type_match and "pomodoro" not in cmd:
        text = type_match.group(1).strip()
        try:
            import keyboard
            keyboard.write(text + "\n")
        except ImportError:
            try:
                import pyperclip
                pyperclip.copy(text)
            except ImportError:
                speak("keyboard and pyperclip libraries not installed.", gui)
                return
        speak("Typed", gui)
        return

    if "pomodoro" in cmd or "focus" in cmd or "start pomodoro" in cmd:
        dur = 25
        pomo_match = re.search(r"(\d+)\s*min", cmd)
        if pomo_match:
            dur = int(pomo_match.group(1))
        speak(f"Pomodoro started for {dur} minutes", gui)

        def pomo():
            time.sleep(dur * 60)
            for _ in range(3):
                speak("Time for a break!", gui)
                time.sleep(2)
            speak("Break for 5 minutes", gui)
        threading.Thread(target=pomo, daemon=True).start()
        return

    if "wifi" in cmd or "bluetooth" in cmd:
        if "on" in cmd:
            if "wifi" in cmd:
                subprocess.run('powershell -Command "(Get-NetAdapter -Name \"Wi-Fi\").Name | Enable-NetAdapter"', shell=True, capture_output=True)
            if "bluetooth" in cmd:
                subprocess.run('powershell -Command "(Get-PnpDevice -Class Bluetooth).FriendlyName | Enable-PnpDevice"', shell=True, capture_output=True)
            speak("Enabled", gui)
        elif "off" in cmd:
            if "wifi" in cmd:
                subprocess.run('powershell -Command "(Get-NetAdapter -Name \"Wi-Fi\").Name | Disable-NetAdapter"', shell=True, capture_output=True)
            if "bluetooth" in cmd:
                subprocess.run('powershell -Command "(Get-PnpDevice -Class Bluetooth).FriendlyName | Disable-PnpDevice"', shell=True, capture_output=True)
            speak("Disabled", gui)
        return

    play_match = re.search(r"play\s+(.+)", cmd)
    if play_match and "open" not in cmd:
        song = play_match.group(1).strip()
        if song == "music":
            subprocess.Popen("start spotify", shell=True)
            speak("Opening Spotify", gui)
        else:
            speak(f"Searching {song}", gui)

            def play_song(song_name):
                try:
                    r = subprocess.run(
                        ['yt-dlp', '--flat-playlist', '--dump-json', '--no-warnings',
                         f'ytsearch1:{song_name}'],
                        capture_output=True, text=True, timeout=15
                    )
                    if r.stdout.strip():
                        data = json.loads(r.stdout.strip().split('\n')[0])
                        vid = data.get('id', '')
                        if vid:
                            subprocess.Popen(f'start https://www.youtube.com/watch?v={vid}', shell=True)
                            return
                except:
                    pass
                subprocess.Popen(f"start https://music.youtube.com/search?q={urllib.parse.quote(song_name)}", shell=True)
            threading.Thread(target=play_song, args=(song,), daemon=True).start()
        return

    note_match = re.search(r"(?:note this|take note|write note|save note)\s+(.+)", cmd)
    if note_match:
        note_text = note_match.group(1).strip()
        notes_path = os.path.join(DATA_FOLDER, "notes.md")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(notes_path, "a") as f:
            f.write(f"- [{timestamp}] {note_text}\n")
        speak("Note saved", gui)
        return

    if ("screenshot" in cmd and "show" not in cmd and "open" not in cmd) or "capture" in cmd:
        try:
            import PIL.ImageGrab
            img = PIL.ImageGrab.grab()
            fname = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img.save(os.path.join(SS_FOLDER, fname))
            speak("Screenshot saved", gui)
        except ImportError:
            speak("Pillow library not installed.", gui)
        except Exception as e:
            speak(f"Screenshot failed: {e}", gui)
        return

    if "remember" in cmd or "save that" in cmd or "keep that" in cmd:
        fact_match = re.search(r"(?:remember|save that|keep that)\s+(.+)", cmd)
        if fact_match:
            fact = fact_match.group(1).strip()
            memory.add(fact, "other")
            speak(f"Got it, I'll remember that {fact}", gui)
        elif "remember" in cmd and "what" not in cmd:
            fact = cmd.replace("remember", "").strip()
            if fact:
                memory.add(fact, "other")
                speak("I've added that to my memory.", gui)
        return

    if re.search(r"what do you know|what.*remember|recall|tell me about me|my memory|who am i", cmd):
        facts = memory.recall_all()
        speak(facts, gui)
        return

    forget_match = re.search(r"(?:forget|delete fact|remove fact)\s+(.+)", cmd)
    if forget_match:
        if memory.remove(forget_match.group(1)):
            speak("Forgotten", gui)
        else:
            speak("I don't have that saved", gui)
        return

    if "clear my memory" in cmd or "reset memory" in cmd or "wipe memory" in cmd:
        memory.clear()
        speak("Memory cleared", gui)
        return

    if not fuzzy_find(cmd, gui):
        from jarvis.llm import gen_llm
        threading.Thread(target=gen_llm, args=(cmd, gui), daemon=True).start()
