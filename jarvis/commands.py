import re
import threading
import subprocess
from rapidfuzz import fuzz
from jarvis.config import VISION_PATTERNS, COMMAND_MAP, CLOSE_MAP, PREFIXES, FUZZY_SCORE, CREATE_NO_WINDOW
from jarvis.memory import memory
from jarvis.speech import speak
from jarvis.utils import log_command

def _fuzzy_find(cmd):
    parts = cmd.split()
    for i, word in enumerate(parts):
        if word in PREFIXES:
            remainder = " ".join(parts[i+1:])
            log_command(f"  prefix match: [{word}] remainder=[{remainder}]")
            if remainder in COMMAND_MAP:
                return COMMAND_MAP[remainder]
            scores = sorted(
                ((k, fuzz.WRatio(remainder, k)) for k in COMMAND_MAP),
                key=lambda x: x[1], reverse=True
            )
            if scores and scores[0][1] >= FUZZY_SCORE:
                log_command(f"  fuzzy app: [{scores[0][0]}] score={scores[0][1]}")
                return COMMAND_MAP[scores[0][0]]
            return None
    if cmd in COMMAND_MAP:
        log_command(f"  exact match: [{COMMAND_MAP[cmd]}] via [{cmd}]")
        return COMMAND_MAP[cmd]
    scores = sorted(
        ((k, fuzz.WRatio(cmd, k)) for k in COMMAND_MAP),
        key=lambda x: x[1], reverse=True
    )
    if scores and scores[0][1] >= FUZZY_SCORE:
        log_command(f"  fuzzy match: [{scores[0][0]}] score={scores[0][1]}")
        return COMMAND_MAP[scores[0][0]]
    return None

def _fuzzy_find_close(cmd):
    for phrase, proc in CLOSE_MAP.items():
        if phrase in cmd:
            log_command(f"  close match: [{phrase}] -> [{proc}]")
            return proc
    scores = sorted(
        ((k, fuzz.WRatio(cmd, k)) for k in CLOSE_MAP),
        key=lambda x: x[1], reverse=True
    )
    if scores and scores[0][1] >= FUZZY_SCORE:
        log_command(f"  close fuzzy: [{scores[0][0]}] score={scores[0][1]}")
        return CLOSE_MAP[scores[0][0]]
    return None

def handle_cmd(cmd, gui):
    cmd = cmd.lower().strip()
    if not cmd:
        return
    # Strip wake word if present (e.g. "jarvis open calc" -> "open calc")
    for w in ["jarvis", "hey jarvis", "hey jar"]:
        if cmd.startswith(w):
            cmd = cmd[len(w):].strip()
        elif cmd.endswith(w):
            cmd = cmd[:-len(w)].strip()
        if not cmd:
            return

    echo_phrases = ["i am listen", "i am listening", "listening", "i'm listening", "system ready", "i am awake"]
    if cmd in echo_phrases:
        log_command(f"Echo filter: exact match for [{cmd}]")
        return

    if gui.last_spoken:
        ratio = fuzz.partial_ratio(cmd, gui.last_spoken.lower())
        if ratio > 80:
            log_command(f"Echo guard: skipped (fuzz={ratio:.0f}%): [{cmd}] vs [{gui.last_spoken[:50]}]")
            return

    gui.add_transcript("You", cmd)
    gui.set_status("processing", f"Accepted: {cmd}")
    log_command(cmd)

    if re.search(r"\b(?:bye\s+jarvis|bye\s+jar|exit\s+jarvis|goodbye|goodbye\s+jarvis|close\s+jarvis)\b", cmd):
        speak("Always a pleasure. Shutting down systems now.", gui)
        gui.close()
        return

    if re.search(r'\b(?:deactivate|go to sleep|standby)\b', cmd) and len(cmd.split()) < 4:
        speak("Entering standby mode.", gui)
        gui.deactivate()
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

    if VISION_PATTERNS.search(cmd):
        from jarvis.llm import ask_vision
        threading.Thread(target=ask_vision, args=(cmd, gui), daemon=True).start()
        return

    # Open/close via hardcoded maps (reliable)
    if any(cmd.startswith(p) for p in PREFIXES) or cmd in COMMAND_MAP:
        app = _fuzzy_find(cmd)
        if app:
            log_command(f"Opening: {app}")
            subprocess.Popen(app, shell=True, creationflags=CREATE_NO_WINDOW)
            speak("Opening.", gui)
            return

    if re.search(r'\b(?:close|kill|shut)\b', cmd) or cmd.startswith("x "):
        proc = _fuzzy_find_close(cmd)
        if proc:
            log_command(f"Closing: {proc}")
            r = subprocess.run(['powershell', '-NoProfile',
                                f'Stop-Process -Name {proc} -Force -ErrorAction Stop'],
                              shell=False, creationflags=CREATE_NO_WINDOW, timeout=10,
                              capture_output=True, text=True)
            if r.returncode == 0:
                speak("Closed.", gui)
            else:
                log_command(f"Close failed: {r.stderr.strip()}")
                speak(f"Could not close {cmd.replace('close','').replace('kill','').strip()}", gui)
            return

    from jarvis.llm import gen_llm
    threading.Thread(target=gen_llm, args=(cmd, gui), daemon=True).start()
