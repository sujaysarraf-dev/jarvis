import re
import threading
from rapidfuzz import fuzz
from jarvis.config import VISION_PATTERNS
from jarvis.memory import memory
from jarvis.speech import speak
from jarvis.utils import log_command

def handle_cmd(cmd, gui):
    cmd = cmd.lower().strip()
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

    from jarvis.llm import gen_llm
    threading.Thread(target=gen_llm, args=(cmd, gui), daemon=True).start()
