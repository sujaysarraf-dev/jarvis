import re
import time
import threading
import requests
from jarvis.config import (
    ACTIVE_API_URL, ACTIVE_API_KEY, ACTIVE_MODEL,
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
        resp = requests.post(ACTIVE_API_URL, json={
            "model": model, "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature,
            "stream": False,
        }, headers={
            "Authorization": f"Bearer {ACTIVE_API_KEY}",
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
        if "choices" not in data or not data["choices"]:
            return None, f"API error: {data.get('error', {}).get('message', 'No choices in response')}"
        
        full = data["choices"][0].get("message", {}).get("content", "")
        if full is None:
            full = ""
    except Exception as e:
        return None, f"parse: {str(e)[:40]}"

    # PowerShell block detection (handles various closing tags)
    ps_pattern = re.compile(r'POWERSHELL\s*\n(.*?)(?:\nENDPS|\n</tool_call>|$)', re.DOTALL | re.I)
    ps_match = ps_pattern.search(full)
    
    if ps_match:
        ps_cmd = ps_match.group(1).strip()
        from jarvis.config import FORBIDDEN_PS
        if ps_cmd and not FORBIDDEN_PS.search(ps_cmd):
            _run_ps(ps_cmd)
            # Remove the PS block from the spoken response
            clean_msg = ps_pattern.sub('', full).strip()
            if not silent:
                if clean_msg:
                    speak(clean_msg, gui)
                else:
                    speak("Executing command.", gui)
            return full, None

    if full and not silent:
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
    elif silent and gui.streaming_idx is not None:
        gui.end_streaming()

    return full, None

def _stream_chat(messages, gui, max_tokens=150, temperature=0.05, timeout=None):
    if timeout is None:
        timeout = OPENROUTER_TIMEOUT
    
    with _last_working_lock:
        preferred = _last_working_model
    
    fallback_list = OPENROUTER_FALLBACK_MODELS if OPENROUTER_FALLBACK_MODELS is not None else [ACTIVE_MODEL]
    if ACTIVE_MODEL not in fallback_list:
        fallback_list.insert(0, ACTIVE_MODEL)
    
    models = []
    if preferred and preferred in fallback_list:
        models.append(preferred)
    
    models.extend(m for m in fallback_list if m not in models)
    
    for model in models:
        for attempt in range(3):
            try:
                res, err = _try_fetch(model, messages, max_tokens, temperature, timeout, gui)
                if err is None:
                    if res and len(res.strip()) > 0:
                        return res, None
                    # If response is empty, retry
                    log_command(f"LLM {model} returned empty response, retrying...")
                    continue
                
                log_command(f"LLM fail {model} attempt {attempt}: {err}")
                if "rate_limit" in str(err).lower():
                    time.sleep(2 * (attempt + 1))
                    continue
                if "timeout" in str(err).lower() or "connection" in str(err).lower():
                    time.sleep(1)
                    continue
                if "HTTP 5" in str(err):
                    time.sleep(2)
                    continue
                break # Other errors don't retry same model
            except Exception as e:
                log_command(f"LLM error {model}: {e}")
                break
        time.sleep(0.5)
    return None, "failed"

def extract_memory(user_cmd, llm_resp, gui):
    try:
        existing = memory.recall_all_formatted()
        res, err = _try_fetch(ACTIVE_MODEL, [
            {"role": "system", "content": "Extract personal facts about the user from this exchange. Be thorough. Format each as 'fact|category'. Categories: identity, preference, work, other. If nothing new, reply 'NONE'. DO NOT use any other words or tags."},
            {"role": "user", "content": f'User: "{user_cmd}"\nAssistant: "{llm_resp}"\n\nAlready known:\n{existing}\n\nNew facts to save:'}
        ], 80, 0, 8, gui, silent=True)
        
        if err or not res:
            return
            
        res_str = str(res)
        if "NONE" in res_str.upper():
            return
            
        for line in res_str.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                line = line[2:]
            line = line.strip()
            if "|" in line:
                parts = line.rsplit("|", 1)
                if len(parts) == 2:
                    fact, cat = parts
                    fact = fact.strip()
                    if fact and len(fact) > 5:
                        memory.add(fact, cat.strip())
    except Exception as e:
        log_command(f"Memory Extraction Error: {str(e)}")

_conversation_history = []
_MAX_HISTORY = 5

def gen_llm(cmd, gui):
    if not ACTIVE_API_KEY:
        speak("Please set your API key in the .env file.", gui)
        log_command("LLM: no API key configured")
        return
    try:
        user_context = memory.recall_all_formatted()
        sys_prompt = (
            "You are JARVIS, a Windows PC assistant that controls everything via PowerShell. Rules:\n"
            "1. For ANY system action, output:\n"
            "POWERSHELL\n<powershell command>\nENDPS\n<short confirmation>\n"
            "2. If no action is needed, answer in one concise sentence.\n"
            "3. NEVER explain reasoning. NEVER use XML tags. ALWAYS use ENDPS.\n\n"
            "PC Control Reference:\n"
            "- Open app: Start-Process <name>\n"
            "- Close app: taskkill /F /IM <process.exe> or Stop-Process -Name <name> -Force\n"
            "- Volume up: (New-Object -ComObject WScript.Shell).SendKeys([char]175)\n"
            "- Volume down: (New-Object -ComObject WScript.Shell).SendKeys([char]174)\n"
            "- Volume mute: (New-Object -ComObject WScript.Shell).SendKeys([char]173)\n"
            "- Brightness up/down: (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,<0-100>)\n"
            "- WiFi on: Enable-NetAdapter -Name \"Wi-Fi\"\n"
            "- WiFi off: Disable-NetAdapter -Name \"Wi-Fi\"\n"
            "- Bluetooth on: Enable-PnpDevice -InstanceId (Get-PnpDevice -Class Bluetooth).InstanceId\n"
            "- Bluetooth off: Disable-PnpDevice -InstanceId (Get-PnpDevice -Class Bluetooth).InstanceId\n"
            "- Dark mode: New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme -Value 0 -Force\n"
            "- Light mode: New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme -Value 1 -Force\n"
            "- Screenshot: Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{PRTSC}')\n"
            "- System info (RAM): Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory\n"
            "- System info (CPU): Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores\n"
            "- System info (disk): Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=3\" | Select-Object DeviceID,Size,FreeSpace\n"
            "- Battery: Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining\n"
            "- Open website: Start-Process \"https://<url>\"\n"
            "- Search web: Start-Process \"https://www.google.com/search?q=<query>\"\n"
            "- Clipboard copy: Set-Clipboard -Value \"<text>\"\n"
            "- Clipboard paste: Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('^V')\n"
            "- Type text: Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\"<text>\")\n"
            "- Calculator: <expression> | ForEach-Object { [math]::Evaluate($_).ToString() } \n"
            "- Play YouTube: Start-Process \"https://www.youtube.com/results?search_query=<query>\"\n"
            "- List processes: Get-Process | Select-Object Name,Id\n"
            "- Kill process: Stop-Process -Id <id> -Force\n"
            "- Create folder: New-Item -Path \"<path>\" -ItemType Directory -Force\n"
            "- Delete folder: Remove-Item -Path \"<path>\" -Recurse -Force\n"
            "- List files: Get-ChildItem -Path \"<path>\"\n\n"
            "For file/folder paths, only use paths the user explicitly mentions. Never guess.\n"
            "For non-PC questions, just answer directly without POWERSHELL.\n"
        )
        if user_context:
            sys_prompt += f"\n\nUser Context:\n{user_context}"

        messages = [{"role": "system", "content": sys_prompt}]
        for user_msg, asst_msg in _conversation_history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": asst_msg})
        messages.append({"role": "user", "content": cmd})

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

        if res:
            _conversation_history.append((cmd, res))
            if len(_conversation_history) > _MAX_HISTORY:
                _conversation_history.pop(0)

        if res and len(res) > 1 and "POWERSHELL" not in res.upper() and gui.streaming_idx is not None:
            gui.end_streaming()
    except Exception as e:
        log_command(f"LLM Error: {str(e)}")
        threading.Thread(target=speak, args=("I encountered an error connecting to my brain.", gui), daemon=True).start()
