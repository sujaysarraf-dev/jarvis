import re
import time
import threading
import requests
from rapidfuzz import fuzz, process
from jarvis.config import (
    OPENROUTER_URL, OPENROUTER_MODEL, OPENROUTER_API_KEY, COMMAND_MAP,
    OPENROUTER_TIMEOUT, OPENROUTER_FALLBACK_MODELS
)
from jarvis.memory import memory
from jarvis.speech import speak
from jarvis.utils import log_command, _run_ps, _is_useless_response, _clean_llm_response

_last_working_model = None
_last_working_lock = threading.Lock()

def _try_model(messages, model, max_tokens, temperature, timeout):
    try:
        r = requests.post(OPENROUTER_URL, json={
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }, headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }, timeout=timeout)
        if r.status_code == 429:
            return None, "rate_limit"
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        resp = r.json()
        if "error" in resp:
            msg = resp["error"].get("message", str(resp["error"]))
            if "rate" in msg.lower() or "429" in str(resp["error"]):
                return None, "rate_limit"
            return None, f"API: {msg[:80]}"
        msg = resp["choices"][0]["message"]
        content = msg.get("content") or msg.get("reasoning", "")
        if content and len(content.strip()) > 1:
            with _last_working_lock:
                global _last_working_model
                _last_working_model = model
            return content.strip(), None
        return None, "empty"
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.ConnectionError:
        return None, "connection"
    except Exception as e:
        return None, str(e)[:60]

def _or_chat(messages, max_tokens=120, temperature=0.1, timeout=None):
    if timeout is None:
        timeout = OPENROUTER_TIMEOUT
    with _last_working_lock:
        preferred = _last_working_model
    models_to_try = []
    if preferred and preferred in OPENROUTER_FALLBACK_MODELS:
        models_to_try.append(preferred)
    models_to_try.extend(m for m in OPENROUTER_FALLBACK_MODELS if m not in models_to_try)
    last_err = None
    for model in models_to_try:
        for attempt in range(3):
            res, err = _try_model(messages, model, max_tokens, temperature, timeout if attempt == 0 else timeout + 5)
            if err is None:
                return res, None
            if err == "rate_limit":
                time.sleep((attempt + 1) * 1.5)
                continue
            if err in ("timeout", "connection"):
                if attempt < 2:
                    time.sleep(1)
                    continue
                last_err = err
                break
            last_err = err
            break
    return None, last_err or "all_models_failed"

def _stream_chat(messages, gui, max_tokens=150, temperature=0.05, timeout=None):
    global _last_working_model
    if timeout is None:
        timeout = OPENROUTER_TIMEOUT
    with _last_working_lock:
        preferred = _last_working_model
    models_to_try = []
    if preferred and preferred in OPENROUTER_FALLBACK_MODELS:
        models_to_try.append(preferred)
    models_to_try.extend(m for m in OPENROUTER_FALLBACK_MODELS if m not in models_to_try)

    full = ""
    sent_buf = ""
    for model in models_to_try:
        for attempt in range(3):
            try:
                resp = requests.post(OPENROUTER_URL, json={
                    "model": model, "messages": messages,
                    "max_tokens": max_tokens, "temperature": temperature,
                    "stream": True,
                }, headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }, stream=True, timeout=timeout if attempt == 0 else timeout + 5)
                if resp.status_code == 429:
                    time.sleep((attempt + 1) * 1.5)
                    continue
                if resp.status_code != 200:
                    break
                with _last_working_lock:
                    _last_working_model = model

                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        decoded = line.decode("utf-8", errors="ignore")
                    except:
                        continue
                    if decoded.startswith("data: [DONE]"):
                        break
                    if decoded.startswith("data: "):
                        try:
                            data = json.loads(decoded[6:])
                            token = data["choices"][0]["delta"].get("content", "")
                        except:
                            continue
                        if not token:
                            continue
                        full += token
                        sent_buf += token
                        # Check if we have a POWERSHELL block
                        if "POWERSHELL" in full and "ENDPS" in full:
                            ps_match = re.search(r'POWERSHELL\s*\n(.*?)\nENDPS', full, re.DOTALL)
                            if ps_match:
                                ps_cmd = ps_match.group(1).strip()
                                from jarvis.config import FORBIDDEN_PS
                                if not FORBIDDEN_PS.search(ps_cmd):
                                    msg = re.sub(r'POWERSHELL\s*\n.*?\nENDPS', '', full, flags=re.DOTALL).strip()
                                    _run_ps(ps_cmd)
                                    if msg:
                                        speak(msg, gui)
                                    return full, None
                        # Speak complete sentences
                        for c in "!?.":
                            if c in sent_buf:
                                parts = re.split(r'(?<=[.!?])\s+', sent_buf)
                                if len(parts) > 1:
                                    for p in parts[:-1]:
                                        p = p.strip()
                                        if p:
                                            speak(p, gui)
                                    sent_buf = parts[-1]
                                break
                if sent_buf.strip():
                    speak(sent_buf.strip(), gui)
                return full, None
            except requests.exceptions.Timeout:
                if attempt < 2:
                    time.sleep(1)
                    continue
                break
            except requests.exceptions.ConnectionError:
                if attempt < 2:
                    time.sleep(1)
                    continue
                break
            except Exception as e:
                break
        break
    return full or None, "stream_failed"

def extract_memory(user_cmd, llm_resp, gui):
    try:
        existing = memory.recall_all_formatted()
        res, err = _or_chat([
            {"role": "system", "content": "Extract personal facts about the user from this exchange. Be thorough — capture name, job, hobbies, preferences, location, etc. Format each as 'fact|category'. Categories: identity, preference, work, other. If nothing new, reply 'NONE'."},
            {"role": "user", "content": f'User: "{user_cmd}"\nAssistant: "{llm_resp}"\n\nAlready known:\n{existing}\n\nNew facts to save:'}
        ], max_tokens=80, temperature=0, timeout=10)

        if err or not res:
            return

        if "NONE" in res.upper():
            return

        new_facts = []
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
                    new_facts.append(fact)

        if new_facts:
            log_command(f"Memory Updated: {len(new_facts)} facts added.")
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
            if err == "stream_failed":
                res, err = _or_chat(messages, max_tokens=150, temperature=0.05)
                if err:
                    speak("Sorry, I couldn't get an answer right now. Please try again.", gui)
                    return
                if not res or len(res) < 2:
                    speak("Sorry, I didn't understand.", gui)
                    return
                res = _clean_llm_response(res)
                if not res or len(res) < 2:
                    speak("Sorry, I didn't understand.", gui)
                    return
                ps_match = re.search(r'POWERSHELL\s*\n(.*?)\nENDPS', res, re.DOTALL)
                if ps_match:
                    ps_cmd = ps_match.group(1).strip()
                    from jarvis.config import FORBIDDEN_PS
                    if FORBIDDEN_PS.search(ps_cmd):
                        speak("That action is not allowed for safety.", gui)
                    else:
                        try:
                            _run_ps(ps_cmd)
                            msg = re.sub(r'POWERSHELL\s*\n.*?\nENDPS', '', res, flags=re.DOTALL).strip()
                            speak(msg if msg else "Done", gui)
                        except Exception as e:
                            speak(f"Failed: {e}", gui)
                    return
                log_command(f"LLM: [{cmd}] -> [{res[:100]}]")
                if _is_useless_response(res):
                    speak("Sorry, I didn't understand that.", gui)
                    return
                if len(res) > 1:
                    matched = process.extractOne(res.lower(), list(COMMAND_MAP.keys()), scorer=fuzz.token_set_ratio, score_cutoff=85)
                    if matched:
                        import subprocess
                        subprocess.Popen(COMMAND_MAP[matched[0]], shell=True)
                        speak(f"Opening {matched[0]}", gui)
                    else:
                        speak(res, gui)
                threading.Thread(target=extract_memory, args=(cmd, res, gui), daemon=True).start()
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
        speak("I encountered an error connecting to my brain.", gui)
