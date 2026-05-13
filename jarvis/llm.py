import re
import time
import json
import threading
import requests
from rapidfuzz import fuzz, process
from jarvis.config import (
    OPENROUTER_URL, OPENROUTER_MODEL, OPENROUTER_API_KEY, COMMAND_MAP,
    OPENROUTER_TIMEOUT, OPENROUTER_FALLBACK_MODELS
)
from jarvis.memory import memory
from jarvis.speech import speak
from jarvis.utils import log_command, _run_ps

_last_working_model = None
_last_working_lock = threading.Lock()

def _try_fetch(model, messages, max_tokens, temperature, timeout, gui, silent=False):
    global _last_working_model
    try:
        resp = requests.post(OPENROUTER_URL, json={
            "model": model, "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature,
            "stream": False,
        }, headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }, timeout=timeout)
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.ConnectionError:
        return None, "connection"
    except Exception as e:
        return None, str(e)[:60]
    if resp.status_code == 429:
        return None, "rate_limit"
    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code}"
    with _last_working_lock:
        _last_working_model = model

    try:
        data = resp.json()
        full = data["choices"][0]["message"]["content"]
    except Exception as e:
        return None, f"parse: {str(e)[:40]}"

    if "POWERSHELL" in full and "ENDPS" in full:
        ps_match = re.search(r'POWERSHELL\s*\n(.*?)\nENDPS', full, re.DOTALL)
        if ps_match:
            ps_cmd = ps_match.group(1).strip()
            from jarvis.config import FORBIDDEN_PS
            if not FORBIDDEN_PS.search(ps_cmd):
                _run_ps(ps_cmd)
                msg = re.sub(r'POWERSHELL\s*\n.*?\nENDPS', '', full, flags=re.DOTALL).strip()
                if msg:
                    speak(msg, gui)
                return full, None

    if not silent:
        def animate_transcript():
            words = re.split(r'(\s+)', full)
            for w in words:
                gui.update_streaming(w)
                time.sleep(0.02)
            gui.end_streaming()
        threading.Thread(target=animate_transcript, daemon=True).start()

        sentences = re.split(r'(?<=[.!?])\s+', full)
        for s in sentences:
            s = s.strip()
            if s:
                speak(s, gui, add_transcript=False)
    else:
        if gui.streaming_idx is not None:
            gui.end_streaming()

    return full, None

def _stream_chat(messages, gui, max_tokens=150, temperature=0.05, timeout=None):
    if timeout is None:
        timeout = OPENROUTER_TIMEOUT
    with _last_working_lock:
        preferred = _last_working_model
    models = []
    if preferred and preferred in OPENROUTER_FALLBACK_MODELS:
        models.append(preferred)
    models.extend(m for m in OPENROUTER_FALLBACK_MODELS if m not in models)
    for model in models:
        for attempt in range(3):
            try:
                res, err = _try_fetch(model, messages, max_tokens, temperature, timeout, gui)
                if err is None:
                    return res, None
                log_command(f"LLM fail {model} attempt {attempt}: {err}")
                if err == "rate_limit":
                    time.sleep(2 * (attempt + 1))
                    continue
                if err in ("timeout", "connection"):
                    time.sleep(1)
                    continue
                if err.startswith("HTTP 5"):
                    time.sleep(2)
                    continue
                break
            except Exception as e:
                log_command(f"LLM error {model}: {e}")
                break
        time.sleep(1)
    return None, "failed"

def extract_memory(user_cmd, llm_resp, gui):
    try:
        existing = memory.recall_all_formatted()
        res, err = _try_fetch("openrouter/free", [
            {"role": "system", "content": "Extract personal facts about the user from this exchange. Be thorough. Format each as 'fact|category'. Categories: identity, preference, work, other. If nothing new, reply 'NONE'."},
            {"role": "user", "content": f'User: "{user_cmd}"\nAssistant: "{llm_resp}"\n\nAlready known:\n{existing}\n\nNew facts to save:'}
        ], 80, 0, 8, gui, silent=True)
        if err or not res:
            return
        if "NONE" in res.upper():
            return
        for line in res.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                line = line[2:]
            line = line.strip()
            if "|" in line:
                fact, cat = line.rsplit("|", 1)
                fact = fact.strip()
                if fact and len(fact) > 5:
                    memory.add(fact, cat.strip())
    except Exception as e:
        log_command(f"Memory Extraction Error: {str(e)}")

def gen_llm(cmd, gui):
    if not OPENROUTER_API_KEY:
        speak("Please set your OpenRouter API key in the .env file.", gui)
        log_command("LLM: no API key configured")
        return
    try:
        user_context = memory.recall_all_formatted()
        sys_prompt = (
            "You are a concise Windows PC assistant. Rules:\n"
            "1. For computer actions, output:\n"
            'POWERSHELL\n<powershell command>\nENDPS\n<confirmation>\n'
            "2. For questions, answer in 1 sentence. NO extra thinking.\n"
            "3. NEVER output reasoning, analysis, or numbered options.\n"
            "4. NEVER say you are Jarvis.\n"
            "5. Respond directly with the answer only.\n"
            "6. Use the user's personal context to personalize your response.\n\n"
            "Examples:\n"
            'open calculator -> POWERSHELL\nStart-Process calc\nENDPS\nDone\n'
            'close notepad -> POWERSHELL\nGet-Process notepad | Stop-Process -Force\nENDPS\nClosed\n'
            'what is unity -> Unity is a game engine for building 2D and 3D games.\n'
        )
        if user_context:
            sys_prompt += f"\n\nPersonal context about the user:\n{user_context}"

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": cmd}
        ]

        res, err = _stream_chat(messages, gui)

        if err:
            log_command(f"LLM Error: {err} | cmd: {cmd[:50]}")
            if err == "rate_limit":
                msg = "I'm getting too many requests. Please wait a moment and try again."
            elif err == "timeout":
                msg = "I'm having trouble getting a response right now. Please try again."
            elif err == "no_api_key":
                msg = "Please set your OpenRouter API key in the .env file."
            elif err == "failed":
                msg = "My brain is having trouble connecting. You can try again or ask something simple."
            else:
                msg = "I couldn't get an answer right now. Please try again."
            threading.Thread(target=speak, args=(msg, gui), daemon=True).start()
            return

        log_command(f"LLM: [{cmd}] -> [{res[:100]}]")

        if len(res) > 1:
            matched = process.extractOne(res.lower(), list(COMMAND_MAP.keys()), scorer=fuzz.token_set_ratio, score_cutoff=85)
            if matched:
                import subprocess
                subprocess.Popen(COMMAND_MAP[matched[0]], shell=True)
                speak(f"Opening {matched[0]}", gui)

        threading.Thread(target=extract_memory, args=(cmd, res, gui), daemon=True).start()
    except Exception as e:
        log_command(f"LLM Error: {str(e)}")
        threading.Thread(target=speak, args=("I encountered an error connecting to my brain.", gui), daemon=True).start()
