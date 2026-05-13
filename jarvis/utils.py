import os
import re
import datetime
import subprocess
from jarvis.config import CREATE_NO_WINDOW, HISTORY_FILE, BASE_DIR, FORBIDDEN_PS

USELESS_PATTERNS = re.compile(
    r'(i\'?m\s+jarvis|i am jarvis|your.*assistant|how can i help|'
    r'how may i help|nice to meet|hello there|hi there|'
    r'what can i do for you|is there anything|glad to help)',
    re.I
)

PROMPT_ARTIFACTS = re.compile(r'(\[INST\]|\[/INST\]|Answer:|User:|###|\*\*)', re.I)

REASONING_SENTENCES = re.compile(
    r'^(?:the user|given the|let me|i think|i\'?ll|okay,?|hmm|'
    r'looking at|based on|i understand|the most likely|'
    r'in this context|as (?:an?|a )|first,?|here\'?s|'
    r'let\'?s break|i need to|i should|i can|i will|'
    r'i have to|i\'?m going|my response|keep it|'
    r'we need|we should|we must|we have to|we can|we will|'
    r'according to|probably|maybe |perhaps |it seems|'
    r'it looks|it appears|the (?:user|person|question|example|answer|context)|'
    r'that\'?s (?:ambiguous|a question|not clear)|'
    r'their interaction|just (?:a|the|answer|concise)|'
    r'so (?:i|we|the|let|to|that)|'
    r'i (?:need to|should|can (?:also|just)|will (?:now|keep)|'
    r'have to|want to|am going|was going))',
    re.I
)

def log_command(cmd, status="executed"):
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {cmd} -> {status}\n")
    except:
        pass

def _run_ps(ps_cmd):
    subprocess.Popen(['powershell', '-NoProfile', '-Command', ps_cmd],
                     shell=False, creationflags=CREATE_NO_WINDOW)

def _is_useless_response(text):
    stripped = re.sub(r'[^\w\s]', '', text).strip().lower()
    if len(stripped) < 15 and USELESS_PATTERNS.search(stripped):
        return True
    return False

def _clean_llm_response(res):
    res = re.sub(r'<thought>.*?</thought>', '', res, flags=re.DOTALL)
    res = PROMPT_ARTIFACTS.sub('', res)
    res = res.strip().strip('"\'')

    sentences = re.split(r'(?<=[.!?])["\']?\s+', res)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]

    clean = []
    for s in sentences:
        if REASONING_SENTENCES.match(s):
            continue
        clean.append(s)

    if not clean:
        clean = sentences[-1:] if sentences else [""]

    res = ' '.join(clean).strip()
    if len(res) > 300:
        res = res[:300].rsplit('. ', 1)[0] + '.'
    return res
