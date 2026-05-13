import speech_recognition as sr
import subprocess
import threading
import tkinter as tk
from tkinter import font
import os
import sys
import datetime
import re
import time
import urllib.parse
import requests
import json
from rapidfuzz import fuzz, process

SPEAK_LOCK = threading.Lock()

try:
    import pygame
    pygame.mixer.init()
except:
    pass

try:
    from gtts import gTTS
    _HAVE_GTTS = True
except:
    _HAVE_GTTS = False

WAKE_WORD = "jarvis"
OLLAMA_URL = "http://localhost:11434/api/generate"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SS_FOLDER = os.path.join(BASE_DIR, "ss")
os.makedirs(SS_FOLDER, exist_ok=True)

COMMAND_MAP = {
    "calculator": "calc", "calc": "calc",
    "notepad": "notepad", "notes": "notepad",
    "browser": "start chrome", "web browser": "start chrome", "internet": "start chrome", "chrome": "start chrome",
    "edge": "start msedge", "microsoft edge": "start msedge",
    "firefox": "start firefox", "mozilla": "start firefox",
    "terminal": "start cmd", "command prompt": "start cmd", "cmd": "start cmd", "console": "start cmd", "powershell": "start powershell",
    "paint": "start mspaint", "ms paint": "start mspaint", "drawing": "start mspaint",
    "word": "start winword", "microsoft word": "start winword", "ms word": "start winword",
    "excel": "start excel", "microsoft excel": "start excel", "ms excel": "start excel",
    "powerpoint": "start powerpnt", "microsoft powerpoint": "start powerpnt", "slides": "start powerpnt",
    "spotify": "start spotify", "music player": "start spotify",
    "discord": "start discord", "vscode": "start code", "vs code": "start code", "visual studio code": "start code",
    "whatsapp": "start whatsapp", "telegram": "start telegram",
    "youtube": "start https://youtube.com",
    "maps": "start https://google.com/maps", "google maps": "start https://google.com/maps",
    "github": "start https://github.com", "gmail": "start https://gmail.com", "mail": "start https://gmail.com",
    "settings": "start ms-settings:", "control panel": "control",
    "task manager": "taskmgr", "taskmgr": "taskmgr",
    "file explorer": "explorer", "explorer": "explorer",
    "notepad++": "start notepad++", "calculator app": "calc",
}

KNOWN_ACTIONS = [
    ("show desktop", lambda: subprocess.Popen(['powershell', '-Command', '(New-Object -ComObject Shell.Application).ToggleDesktop()']), ["show desktop", "minimize all windows", "show windows", "close all windows"]),
    ("lock", lambda: subprocess.Popen("rundll32.exe user32.dll,LockWorkStation"), ["lock", "lock pc", "lock computer", "lock screen"]),
    ("restart", lambda: subprocess.Popen("shutdown /r /t 0"), ["restart", "reboot", "restart pc", "restart computer"]),
    ("shutdown", lambda: subprocess.Popen("shutdown /s /t 0"), ["shutdown", "turn off", "power off", "shut down"]),
    ("sleep", lambda: subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"), ["sleep", "hibernate", "go to sleep"]),
    ("volume up", lambda: subprocess.run('powershell -Command "$s=(New-Object -ComObject WScript.Shell);for($i=0;$i -lt 10;$i++){$s.SendKeys([char]175);Start-Sleep -Milliseconds 50}"', shell=True), ["volume up", "louder", "increase volume", "turn up volume", "increase speaker volume"]),
    ("volume down", lambda: subprocess.run('powershell -Command "$s=(New-Object -ComObject WScript.Shell);for($i=0;$i -lt 10;$i++){$s.SendKeys([char]174);Start-Sleep -Milliseconds 50}"', shell=True), ["volume down", "quieter", "lower volume", "decrease volume", "turn down volume"]),
    ("unmute", lambda: subprocess.run('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]176)"', shell=True), ["unmute", "unmute volume", "unsilence", "unmute sound"]),
    ("mute", lambda: subprocess.run('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]176)"', shell=True), ["mute", "mute volume", "silence", "silent", "mute sound"]),
    ("open downloads", lambda: subprocess.Popen(['explorer', os.environ.get('USERPROFILE','') + '\\Downloads']), ["open downloads folder", "show downloads folder", "my downloads"]),
    ("open documents", lambda: subprocess.Popen(['explorer', os.environ.get('USERPROFILE','') + '\\Documents']), ["open documents folder", "show documents folder", "my documents"]),
    ("open desktop", lambda: subprocess.Popen(['explorer', os.environ.get('USERPROFILE','') + '\\Desktop']), ["open desktop folder", "show desktop folder"]),
    ("open screenshots", lambda: os.startfile(SS_FOLDER), ["open screenshots folder", "show screenshots folder"]),
]

class JarvisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True, "-transparentcolor", "black")
        self.configure_window()
        self.awake = False
        self.dragging = False
        self.drag_x = 0
        self.drag_y = 0

        self.size = 80
        self.x = self.root.winfo_screenwidth() - self.size - 30
        self.y = self.root.winfo_screenheight() - self.size - 80
        self.root.geometry(f"{self.size}x{self.size}+{self.x}+{self.y}")

        self.canvas = tk.Canvas(self.root, width=self.size, height=self.size, bg="black", highlightthickness=0)
        self.canvas.pack()

        self.bubble = self.canvas.create_oval(4, 4, self.size-4, self.size-4, fill="#333333", outline="#00d4ff", width=2)

        self.ring = self.canvas.create_oval(8, 8, self.size-8, self.size-8, outline="#00d4ff", width=0)

        self.status_dot = self.canvas.create_oval(self.size-22, self.size-22, self.size-10, self.size-10, fill="#888888", outline="")

        self.label = self.canvas.create_text(self.size//2, self.size//2, text="J", fill="white", font=font.Font(size=28, weight="bold"))

        self.canvas.tag_bind(self.bubble, "<ButtonPress-1>", self.start_drag)
        self.canvas.tag_bind(self.bubble, "<B1-Motion>", self.do_drag)
        self.canvas.tag_bind(self.bubble, "<ButtonRelease-1>", self.stop_drag)
        self.canvas.tag_bind(self.bubble, "<Double-Button-1>", self.toggle_window)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<Double-Button-1>", self.toggle_window)

        self.info_win = None
        self.last_status = "idle"
        self.transcript = []

        if not os.path.exists(STARTUP_FILE):
            self.set_startup(True)

        self.pulse_phase = 0
        self.root.after(100, self.update)

    def configure_window(self):
        try:
            self.root.wm_attributes("-transparentcolor", "black")
        except:
            pass

    def toggle_window(self, event=None):
        if self.info_win and self.info_win.winfo_exists():
            self.info_win.destroy()
            self.info_win = None
        else:
            self.show_info()

    def show_info(self):
        if self.info_win and self.info_win.winfo_exists():
            return
        self.info_win = tk.Toplevel(self.root)
        self.info_win.overrideredirect(True)
        self.info_win.attributes("-topmost", True)
        ix = self.x + self.size + 10
        iy = self.y - 150
        self.info_win.geometry(f"320x350+{ix}+{iy}")
        self.info_win.configure(bg="#1a1a2e")

        self.info_canvas = tk.Canvas(self.info_win, width=320, height=80, bg="#1a1a2e", highlightthickness=0)
        self.info_canvas.pack()
        self.info_canvas.create_rectangle(0, 0, 320, 80, fill="#1a1a2e", outline="#00d4ff", width=1)

        self.info_label = self.info_canvas.create_text(160, 20, text="Say 'Jarvis' to activate", fill="#ffaa00", font=font.Font(size=11))
        self.info_text = self.info_canvas.create_text(160, 45, text="", fill="white", width=300, font=font.Font(size=10))

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self.info_win, textvariable=self.entry_var, bg="#16213e", fg="white",
                              insertbackground="white", font=font.Font(size=10), relief=tk.FLAT)
        self.entry.pack(fill=tk.X, padx=8, pady=(5, 0))
        self.entry.bind("<Return>", self.submit_text)

        btn_frame = tk.Frame(self.info_win, bg="#1a1a2e")
        btn_frame.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(btn_frame, text="Send", command=self.submit_text, bg="#0f3460", fg="white",
                  activebackground="#1a5276", activeforeground="white", relief=tk.FLAT, cursor="hand2").pack(side=tk.RIGHT)
        tk.Label(btn_frame, text="Enter command:", bg="#1a1a2e", fg="#888", font=font.Font(size=8)).pack(side=tk.LEFT)

        self.check_startup(self.info_canvas)

        transcript_frame = tk.Frame(self.info_win, bg="#0d1b2a")
        transcript_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        tk.Label(transcript_frame, text="Transcript", bg="#0d1b2a", fg="#00d4ff",
                 font=font.Font(size=8), anchor=tk.W).pack(fill=tk.X)

        self.transcript_box = tk.Text(transcript_frame, height=8, bg="#0d1b2a", fg="#cccccc",
                                       font=font.Font(size=9), relief=tk.FLAT, borderwidth=0,
                                       highlightthickness=0, state=tk.DISABLED, wrap=tk.WORD)
        self.transcript_box.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.transcript_box, command=self.transcript_box.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.transcript_box.config(yscrollcommand=scrollbar.set)

        self.transcript_box.tag_config("you", foreground="#4fc3f7")
        self.transcript_box.tag_config("jarvis", foreground="#81c784")
        self.transcript_box.tag_config("time", foreground="#666666")

        self._refresh_transcript()

        self.info_win.bind("<Double-Button-1>", lambda e: self.toggle_window())
        self.entry.focus()

    def submit_text(self, event=None):
        text = self.entry_var.get().strip()
        if text:
            self.entry_var.set("")
            handle_cmd(text, self)
            self.info_win.lift()

    def check_startup(self, canvas=None):
        p = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'jarvis.bat')
        if canvas:
            txt = "On startup ✓" if os.path.exists(p) else "Startup: off"
            canvas.create_text(140, 85, text=txt, fill="#666", font=font.Font(size=7))

    def set_startup(self, enable):
        p = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'jarvis.bat')
        if enable:
            script_path = os.path.join(BASE_DIR, "main.py")
            with open(p, 'w') as f:
                f.write(f'@echo off\ncd /d "{BASE_DIR}"\nstart /b pythonw "{script_path}" --bg\n')
        elif os.path.exists(p):
            os.remove(p)

    def start_drag(self, event):
        self.dragging = True
        self.drag_x = event.x_root - self.x
        self.drag_y = event.y_root - self.y

    def do_drag(self, event):
        if self.dragging:
            self.x = event.x_root - self.drag_x
            self.y = event.y_root - self.drag_y
            self.root.geometry(f"+{self.x}+{self.y}")
            if self.info_win and self.info_win.winfo_exists():
                self.info_win.geometry(f"+{self.x+self.size+10}+{self.y-30}")

    def stop_drag(self, event):
        self.dragging = False

    def add_transcript(self, role, text):
        self.transcript.append((role, text, datetime.datetime.now().strftime("%H:%M")))
        if len(self.transcript) > 20:
            self.transcript = self.transcript[-20:]
        if self.info_win and self.info_win.winfo_exists() and hasattr(self, 'transcript_box'):
            self.root.after(0, self._refresh_transcript)

    def _refresh_transcript(self):
        if hasattr(self, 'transcript_box'):
            self.transcript_box.config(state=tk.NORMAL)
            self.transcript_box.delete("1.0", tk.END)
            for role, text, t in self.transcript[-10:]:
                tag = "you" if role == "You" else "jarvis"
                self.transcript_box.insert(tk.END, f"[{t}] ", "time")
                self.transcript_box.insert(tk.END, f"{role}: ", tag)
                self.transcript_box.insert(tk.END, f"{text}\n", "")
            self.transcript_box.config(state=tk.DISABLED)
            self.transcript_box.see(tk.END)

    def set_status(self, status, text=""):
        self.last_status = status
        self.root.after(0, self._update_gui, status, text)

    def _update_gui(self, status, text=""):
        colors = {
            "idle":"#444444","wake":"#ffaa00","listening":"#00ff00",
            "processing":"#ffaa00","speaking":"#00d4ff","success":"#00ff00","error":"#ff4444"
        }
        dots = {
            "idle":"#888888","wake":"#ffaa00","listening":"#00ff00",
            "processing":"#ffaa00","speaking":"#00d4ff","success":"#00ff00","error":"#ff4444"
        }
        labels = {"idle":"J","wake":"J","listening":"J","processing":"J","speaking":"J","success":"J","error":"J"}
        
        c = colors.get(status, "#444444")
        self.canvas.itemconfig(self.bubble, fill=c)
        self.canvas.itemconfig(self.ring, outline=c, width=0)
        self.canvas.itemconfig(self.status_dot, fill=dots.get(status, "#888888"))
        self.canvas.itemconfig(self.label, text=labels.get(status, "J"))
        
        if self.info_win and self.info_win.winfo_exists():
            ti = {"idle":"Say 'Jarvis' to activate","wake":"Activated!","listening":"Listening...",
                  "processing":"Processing...","speaking":"Speaking...","success":"Done","error":"Error"}
            if hasattr(self, 'info_canvas'):
                self.info_canvas.itemconfig(self.info_label, text=ti.get(status, ""), fill=colors.get(status, "#888888"))
                self.info_canvas.itemconfig(self.info_text, text=text if text else "")

    def pulse_animation(self):
        if self.last_status in ("processing", "listening"):
            self.pulse_phase = (self.pulse_phase + 1) % 20
            offset = abs(self.pulse_phase - 10) * 0.4
            size = self.size - 8 + offset
            self.canvas.coords(self.ring, 4-offset/2, 4-offset/2, self.size-4+offset/2, self.size-4+offset/2)
            self.canvas.itemconfig(self.ring, width=2)
        else:
            self.canvas.itemconfig(self.ring, width=0)

    def activate(self, has_cmd=False):
        self.awake = True
        self.set_status("wake")
        if not has_cmd:
            speak("I'm listening", self)
            time.sleep(0.5)

    def deactivate(self):
        self.awake = False
        self.set_status("idle")

    def close(self):
        self.running = False
        self.root.quit()

    def update(self):
        self.pulse_animation()
        self.root.update()
        self.root.after(50, self.update)

    def run(self):
        self.root.mainloop()

def speak(text, gui):
    with SPEAK_LOCK:
        gui.add_transcript("Jarvis", text)
        gui.set_status("speaking", text)
        speech_file = os.path.join(BASE_DIR, "jarvis_speech.mp3")
        spoken = False
        if _HAVE_GTTS:
            try:
                tts = gTTS(text=text, lang="en", tld="com", slow=False)
                tts.save(speech_file)
                pygame.mixer.music.load(speech_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                pygame.mixer.music.unload()
                spoken = True
            except:
                pass
            finally:
                if os.path.exists(speech_file):
                    try: os.remove(speech_file)
                    except: pass
        if not spoken:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
            except:
                pass
        
        if gui.awake:
            gui.set_status("listening")

OLLAMA_MODEL = "llama3.2:1b"

MEMORY_FILE = os.path.join(BASE_DIR, "user_memory.json")

class MemoryStore:
    def __init__(self):
        self.facts = []
        self.lock = threading.Lock()
        self.load()

    def load(self):
        with self.lock:
            if os.path.exists(MEMORY_FILE):
                try:
                    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                        self.facts = json.load(f)
                except:
                    self.facts = []

    def save(self):
        with self.lock:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.facts, f, indent=2)

    def add(self, fact, category="other"):
        if not fact or len(fact) < 3:
            return
        fact_lower = fact.lower().strip()
        with self.lock:
            if any(f["fact"].lower() == fact_lower for f in self.facts):
                return
            self.facts.append({
                "fact": fact.strip(),
                "category": category,
                "timestamp": datetime.datetime.now().isoformat()
            })
        self.save()

    def remove(self, query):
        q = query.lower()
        with self.lock:
            before = len(self.facts)
            self.facts = [f for f in self.facts if q not in f["fact"].lower()]
            if len(self.facts) < before:
                changed = True
            else:
                changed = False
        
        if changed:
            self.save()
            return True
        return False

    def clear(self):
        with self.lock:
            self.facts = []
        self.save()

    def recall(self, query=None, limit=10):
        with self.lock:
            if not self.facts:
                return ""
            
            # If no query, just return recent facts
            if not query:
                recent = sorted(self.facts, key=lambda x: x["timestamp"], reverse=True)[:limit]
                return "\n".join(f"- {f['fact']}" for f in recent)
            
            # Simple keyword-based relevance search
            query_words = set(query.lower().split())
            scored_facts = []
            for f in self.facts:
                fact_lower = f["fact"].lower()
                score = sum(1 for word in query_words if word in fact_lower)
                if score > 0:
                    scored_facts.append((score, f))
            
            if scored_facts:
                # Sort by score descending, then by timestamp descending
                scored_facts.sort(key=lambda x: (x[0], x[1]["timestamp"]), reverse=True)
                results = [x[1] for x in scored_facts[:limit]]
            else:
                # Fallback to most recent
                results = sorted(self.facts, key=lambda x: x["timestamp"], reverse=True)[:limit]
                
            return "\n".join(f"- {f['fact']}" for f in results)

    def recall_all(self):
        with self.lock:
            if not self.facts:
                return "I don't have any specific memories about you yet."
            lines = [f"• {f['fact']}" for f in self.facts]
        return "Here is what I remember about you:\n" + "\n".join(lines)

memory = MemoryStore()

FORBIDDEN_PS = re.compile(r'\b(Remove-Item|rm\b|del\b|Format-Volume|Clear-|Restart-Computer|Stop-Computer|Shutdown|Add-LocalGroupMember|Set-LocalUser|Disable-LocalUser)', re.I)

CREATE_NO_WINDOW = 0x08000000

def _run_ps(ps_cmd):
    subprocess.Popen(['powershell', '-NoProfile', '-Command', ps_cmd],
                     shell=False, creationflags=CREATE_NO_WINDOW)

USELESS_PATTERNS = re.compile(
    r'(i\'?m\s+jarvis|i am jarvis|your.*assistant|how can i help|'
    r'how may i help|nice to meet|hello there|hi there|'
    r'what can i do for you|is there anything|glad to help)',
    re.I
)

def _is_useless_response(text):
    stripped = re.sub(r'[^\w\s]', '', text).strip().lower()
    if len(stripped) < 15 and USELESS_PATTERNS.search(stripped):
        return True
    return False

PROMPT_ARTIFACTS = re.compile(r'(\[INST\]|\[/INST\]|Answer:|User:|###|\*\*)', re.I)

def _clean_llm_response(res):
    res = re.sub(r'<thought>.*?</thought>', '', res, flags=re.DOTALL)
    res = PROMPT_ARTIFACTS.sub('', res)
    res = res.strip().strip('"\'')
    return res

def gen_llm(cmd, gui):
    try:
        context = memory.recall(cmd, limit=3)
        ctx_line = f" (context: {context})" if context else ""
        prompt = (
            "### Instruction: You are a Windows PC assistant.\n"
            "If a task can be done with PowerShell, output:\n"
            'POWERSHELL\n<powershell command>\nENDPS\n<confirmation>\n\n'
            "Otherwise answer in 1 short sentence.\n\n"
            "Examples:\n"
            '- open calculator -> POWERSHELL\nStart-Process calc\nENDPS\nDone\n'
            '- close notepad -> POWERSHELL\nGet-Process notepad | Stop-Process -Force\nENDPS\nClosed\n\n'
            f"User: {cmd}{ctx_line}\n"
            "### Response:"
        )

        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_ctx": 512, "num_predict": 120, "temperature": 0.1,
                        "stop": ["\n###", "User:", "\n\n\n"]}
        }, timeout=30)

        if r.status_code != 200:
            speak("My brain returned an error.", gui)
            log_command(f"LLM HTTP {r.status_code}: {r.text[:100]}")
            return

        res = r.json().get("response", "").strip()
        res = _clean_llm_response(res)
        if not res or len(res) < 2:
            speak("Sorry, I didn't understand.", gui)
            return

        log_command(f"LLM: [{cmd}] -> [{res[:100]}]")

        ps_match = re.search(r'POWERSHELL\s*\n(.*?)\nENDPS', res, re.DOTALL)
        if ps_match:
            ps_cmd = ps_match.group(1).strip()
            if FORBIDDEN_PS.search(ps_cmd):
                speak("That action is not allowed for safety.", gui)
            else:
                try:
                    _run_ps(ps_cmd)
                    msg = re.sub(r'POWERSHELL\s*\n.*?\nENDPS', '', res, flags=re.DOTALL).strip()
                    speak(msg if msg else "Done", gui)
                except Exception as e:
                    speak(f"Failed: {e}", gui)
            threading.Thread(target=extract_memory, args=(cmd, res, gui), daemon=True).start()
            return

        if _is_useless_response(res):
            speak("Sorry, I didn't understand that.", gui)
            log_command(f"LLM: filtered useless response: [{res[:50]}]")
            return

        if len(res) > 1:
            matched = process.extractOne(res.lower(), list(COMMAND_MAP.keys()), scorer=fuzz.token_set_ratio, score_cutoff=85)
            if matched:
                subprocess.Popen(COMMAND_MAP[matched[0]], shell=True)
                speak(f"Opening {matched[0]}", gui)
            else:
                speak(res, gui)

        threading.Thread(target=extract_memory, args=(cmd, res, gui), daemon=True).start()
    except Exception as e:
        log_command(f"LLM Error: {str(e)}")
        speak("I encountered an error connecting to my brain.", gui)

def extract_memory(user_cmd, llm_resp, gui):
    try:
        prompt = f"""Analyze this interaction and identify any NEW personal facts, preferences, or details the user shared.
User: "{user_cmd}"
Assistant: "{llm_resp}"

Rules:
1. Only extract long-term useful facts (e.g., interests, names, habits).
2. Format as 'fact|category'. Categories: identity, preference, work, other.
3. If no new facts, reply 'NONE'.
4. Be concise. Do not repeat existing known facts.

User Memory for context:
{memory.recall(limit=20)}

Reply with facts only:"""

        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_ctx": 512, "num_predict": 60, "temperature": 0}
        }, timeout=15)
        
        res = r.json().get("response", "").strip()
        if res and "NONE" not in res.upper():
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
                # We could potentially notify the user, but ChatGPT does it subtly.
                # Maybe a small dot or something in GUI? 
                # For now, let's just log it.
    except Exception as e:
        log_command(f"Memory Extraction Error: {str(e)}")

def fuzzy_find(cmd, gui):
    cmd_lower = cmd.lower().strip()
    log_command(f"fuzzy_find input: [{cmd_lower}]")
    
    PREFIXES = ("open ", "launch ", "start ", "run ", "switch to ")
    SCORE = 75
    
    all_exact = []
    for name, action, phrases in KNOWN_ACTIONS:
        for phrase in phrases:
            all_exact.append((len(phrase), phrase, name, action))
    all_exact.sort(key=lambda x: -x[0])
    for length, phrase, name, action in all_exact:
        if phrase in cmd_lower:
            log_command(f"  exact match: [{name}] via [{phrase}]")
            try: action()
            except: pass
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
            result = process.extractOne(remainder, list(COMMAND_MAP.keys()), scorer=fuzz.token_sort_ratio, score_cutoff=SCORE)
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
            try: action()
            except: pass
            speak("Done", gui)
            return True
    
    result = process.extractOne(cmd_lower, list(COMMAND_MAP.keys()), scorer=fuzz.token_sort_ratio, score_cutoff=SCORE)
    if result:
        log_command(f"  fuzzy whole-cmd: [{result[0]}] score={result[1]}")
        subprocess.Popen(COMMAND_MAP[result[0]], shell=True)
        speak(f"Opening {result[0]}", gui)
        return True
    
    log_command(f"  NO MATCH for: [{cmd_lower}]")
    return False

HISTORY_FILE = os.path.join(BASE_DIR, "command_history.txt")

def log_command(cmd, status="executed"):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {cmd} -> {status}\n")

def main_loop(gui):
    time.sleep(1)
    # Loop runs while the GUI is marked as running
    while gui.running:
        if not gui.awake:
            result = listen_for_wake()
            if result:
                gui.activate(has_cmd=isinstance(result, str))
            if isinstance(result, str):
                handle_cmd(result, gui)
        else:
            cmd = listen_for_cmd(gui)
            if cmd:
                handle_cmd(cmd, gui)
            else:
                gui.set_status("idle")

def handle_cmd(cmd, gui):
    cmd = cmd.lower().strip()
    gui.add_transcript("You", cmd)
    gui.set_status("processing", f"You said: {cmd}")
    log_command(cmd)

    if "time" in cmd:
        t = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {t}", gui)
        return
    if "date" in cmd or "today" in cmd or "day" in cmd:
        d = datetime.datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {d}", gui)
        return
    if re.search(r"\bbye\s+jarvis\b", cmd):
        speak("Goodbye", gui)
        gui.close()
        return
    if re.search(r'\b(?:deactivate|go to sleep)\b', cmd):
        speak("Going to sleep", gui)
        gui.deactivate()
        return
    if re.search(r'\b(?:stop|sleep|bye)\b', cmd) and not re.search(r'\b(?:stopwatch|stop the music|stop playing|stopwatch|stopped|stopping|storage|sleeping)\b', cmd):
        speak("Going to sleep", gui)
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
        todo_path = os.path.join(BASE_DIR, "todo.txt")
        with open(todo_path, "a") as f:
            f.write(f"- {datetime.datetime.now().strftime('%m/%d')}: {text}\n")
        speak("Reminder saved", gui)
        return

    site = re.search(r"(?:open|go to|launch)\s+(\w+\.\w+)", cmd)
    if site:
        subprocess.Popen(f"start https://{site.group(1)}", shell=True)
        speak(f"Opening {site.group(1)}", gui)
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
        notes_path = os.path.join(BASE_DIR, "notes.md")
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
                speak(f"I've added that to my memory.", gui)
        return

    if re.search(r"what do you know|what.*remember|recall|tell me about me|my memory|who am i", cmd):
        facts = memory.recall_all()
        speak(facts, gui)
        return

    forget_match = re.search(r"(?:forget|delete|remove)\s+(.+)", cmd)
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
        threading.Thread(target=gen_llm, args=(cmd, gui), daemon=True).start()

def listen_for_wake():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src, duration=0.3)
            audio = r.listen(src, timeout=3, phrase_time_limit=5)
        text = r.recognize_google(audio)
        if text and WAKE_WORD in text.lower():
            idx = text.lower().index(WAKE_WORD) + len(WAKE_WORD)
            after = text[idx:].strip()
            return after if after else True
    except sr.RequestError:
        log_command("Wake word: network error")
    except sr.WaitTimeoutError:
        pass
    except:
        pass
    return False

def listen_for_cmd(gui):
    gui.set_status("listening")
    r = sr.Recognizer()
    try:
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src, duration=0.5)
            audio = r.listen(src, timeout=5, phrase_time_limit=5)
        text = r.recognize_google(audio)
        if text:
            return text.lower()
        return None
    except sr.RequestError:
        log_command("Speech recognition: network error")
        speak("Network error with speech recognition.", gui)
        return None
    except sr.WaitTimeoutError:
        return None
    except:
        return None

STARTUP_FILE = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'jarvis.bat')



def run_background_listener():
    log_command("Background listener started")
    while True:
        try:
            r = sr.Recognizer()
            with sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.5)
                audio = r.listen(src, timeout=5, phrase_time_limit=5)
            text = r.recognize_google(audio).lower()
            if WAKE_WORD in text:
                log_command("Wake word detected in background, launching GUI")
                subprocess.Popen(['pythonw', os.path.abspath(__file__)])
                time.sleep(5)
        except Exception:
            time.sleep(1)

def main():
    if "--bg" in sys.argv:
        run_background_listener()
    else:
        gui = JarvisGUI()
        gui.running = True
        threading.Thread(target=main_loop, args=(gui,), daemon=True).start()
        gui.run()

if __name__ == "__main__":
    main()