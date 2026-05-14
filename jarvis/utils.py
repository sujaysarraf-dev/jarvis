import os
import re
import time
import datetime
import subprocess
from jarvis.config import CREATE_NO_WINDOW, HISTORY_FILE, BASE_DIR, FORBIDDEN_PS

_MAX_LOG_LINES = 2000

def _trim_log():
    try:
        if os.path.exists(HISTORY_FILE) and os.path.getsize(HISTORY_FILE) > 2 * 1024 * 1024:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines[-_MAX_LOG_LINES:])
    except:
        pass

_trim_log()

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
    try:
        if os.path.getsize(HISTORY_FILE) > 2 * 1024 * 1024:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines[-_MAX_LOG_LINES:])
    except:
        pass

def _run_ps(ps_cmd):
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', ps_cmd],
                          shell=False, creationflags=CREATE_NO_WINDOW,
                          capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            err = r.stderr.strip()[:200] if r.stderr.strip() else f"exit code {r.returncode}"
            log_command(f"PS fail: {err} | cmd: {ps_cmd[:100]}")
            if _needs_admin(err):
                log_command("Retrying PS command elevated...")
                return _run_ps_elevated(ps_cmd)
            return False, err
        out = r.stdout.strip()[:200] if r.stdout.strip() else ""
        return True, out
    except subprocess.TimeoutExpired:
        log_command(f"PS timeout: {ps_cmd[:100]}")
        return False, "timeout"
    except Exception as e:
        log_command(f"PS error: {e} | cmd: {ps_cmd[:100]}")
        return False, str(e)[:100]

def _needs_admin(err):
    kw = ['permission', 'denied', 'generic failure', 'admin', 'elevated',
          'access denied', 'privilege', 'unauthorized']
    return any(k in err.lower() for k in kw)

def _run_ps_elevated(ps_cmd):
    import tempfile, os, time
    stamp = str(int(time.time()))
    tmp = tempfile.gettempdir()
    script = os.path.join(tmp, f"jarvis_elevated_{stamp}.ps1")
    outf = os.path.join(tmp, f"jarvis_out_{stamp}.txt")
    try:
        with open(script, "w") as f:
            f.write(f'Try {{ {ps_cmd} }} Catch {{ $__e = $_; \"ERR: $__e\" }} | Out-File -FilePath \"{outf}\" -Encoding UTF8\n')
        ps_code = f'Start-Process powershell -Verb RunAs -ArgumentList \'-NoProfile -File "{script}"\' -WindowStyle Hidden -Wait'
        subprocess.run(['powershell', '-NoProfile', '-Command', ps_code],
                      shell=False, creationflags=CREATE_NO_WINDOW, timeout=60)
        for _ in range(30):
            if os.path.exists(outf):
                break
            time.sleep(0.5)
        if os.path.exists(outf):
            with open(outf, 'r', encoding='utf-8') as f:
                result = f.read().strip()
            os.remove(outf)
            return True, result[:200] if result else ""
        return False, "elevated command failed"
    except Exception as e:
        return False, f"elevate error: {str(e)[:60]}"
    finally:
        for f in [script, outf]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass

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
