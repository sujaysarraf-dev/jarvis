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
import requests
import json
from rapidfuzz import fuzz, process

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
    ("volume up", lambda: subprocess.run('for /l %i in (1,1,10) do @start /b nircmd volup 65536', shell=True), ["volume up", "louder", "increase volume", "turn up volume", "increase speaker volume"]),
    ("volume down", lambda: subprocess.run('for /l %i in (1,1,10) do @start /b nircmd voldown 65536', shell=True), ["volume down", "quieter", "lower volume", "decrease volume", "turn down volume"]),
    ("unmute", lambda: subprocess.run("nircmd mutesysvolume 0", shell=True), ["unmute", "unmute volume", "unsilence", "unmute sound"]),
    ("mute", lambda: subprocess.run("nircmd mutesysvolume 2", shell=True), ["mute", "mute volume", "silence", "silent", "mute sound"]),
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
        iy = self.y - 30
        self.info_win.geometry(f"280x210+{ix}+{iy}")
        self.info_win.configure(bg="#1a1a2e")

        self.info_canvas = tk.Canvas(self.info_win, width=280, height=100, bg="#1a1a2e", highlightthickness=0)
        self.info_canvas.pack()
        self.info_canvas.create_rectangle(0, 0, 280, 100, fill="#1a1a2e", outline="#00d4ff", width=1)

        self.info_label = self.info_canvas.create_text(140, 25, text="Say 'Jarvis' to activate", fill="#ffaa00", font=font.Font(size=11))
        self.info_text = self.info_canvas.create_text(140, 55, text="", fill="white", width=260, font=font.Font(size=10))

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
            with open(p, 'w') as f:
                f.write(f'@echo off\nstart /b python "{os.path.abspath(sys.argv[0])}"\n')
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

    def set_status(self, status, text=""):
        self.last_status = status
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

    def on_close(self):
        self.root.quit()

    def update(self):
        self.pulse_animation()
        self.root.update()
        self.root.after(50, self.update)

    def run(self):
        self.root.mainloop()

def speak(text, gui):
    gui.set_status("speaking", text)
    try:
        from gtts import gTTS
        import pygame
        tts = gTTS(text=text, lang="en", tld="com", slow=False)
        tts.save("jarvis_speech.mp3")
        pygame.mixer.init()
        pygame.mixer.music.load("jarvis_speech.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.quit()
        if os.path.exists("jarvis_speech.mp3"):
            os.remove("jarvis_speech.mp3")
    except:
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

def gen_llm(cmd, gui):
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": f"Name the app/program for: {cmd}. Reply 1 word only.",
            "stream": False,
            "options": {"num_ctx": 64, "num_predict": 5, "temperature": 0}
        }, timeout=15)
        res = r.json().get("response", "").strip().lower().strip("`'\".,!?:; ")
        log_command(f"LLM: [{cmd}] -> [{res}]")
        if res and len(res) > 1 and "sorry" not in res:
            matched = process.extractOne(res, list(COMMAND_MAP.keys()), scorer=fuzz.token_set_ratio, score_cutoff=70)
            if matched:
                subprocess.Popen(COMMAND_MAP[matched[0]], shell=True)
                speak(f"Opening {matched[0]}", gui)
            else:
                try:
                    subprocess.Popen(f"start {res}", shell=True)
                    speak(f"Opening {res}", gui)
                except:
                    speak(f"Trying {res}", gui)
        else:
            speak("I don't know", gui)
    except:
        speak("I don't know", gui)

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

def handle_cmd(cmd, gui):
    cmd = cmd.lower().strip()
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
    if "stop" in cmd or "sleep" in cmd or "bye" in cmd or "go to sleep" in cmd or "deactivate" in cmd:
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
        import psutil
        ram = psutil.virtual_memory()
        usage = f"{ram.percent}% used out of {round(ram.total/(1024**3))} GB"
        speak(f"RAM: {usage}", gui)
        return

    if "copy" in cmd and "clipboard" in cmd:
        clip = re.search(r"copy\s+(.+)\s+to\s+clipboard", cmd)
        if clip:
            import pyperclip
            pyperclip.copy(clip.group(1))
            speak("Copied to clipboard", gui)
        return

    if "clipboard" in cmd and ("paste" in cmd or "read" in cmd or "what" in cmd):
        import pyperclip
        t = pyperclip.paste()
        speak(f"Clipboard: {t[:80]}", gui)
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
        except:
            import pyperclip
            pyperclip.copy(text)
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
                        import json
                        data = json.loads(r.stdout.strip().split('\n')[0])
                        vid = data.get('id', '')
                        if vid:
                            subprocess.Popen(f'start https://www.youtube.com/watch?v={vid}', shell=True)
                            return
                except:
                    pass
                import urllib.parse
                subprocess.Popen(f"start https://music.youtube.com/search?q={urllib.parse.quote(song_name)}", shell=True)
            threading.Thread(target=play_song, args=(song,), daemon=True).start()
        return

    note_match = re.search(r"(?:note this|take note|write note|save note|remember)\s+(.+)", cmd)
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
        except:
            speak("Screenshot failed", gui)
        return

    if not fuzzy_find(cmd, gui):
        threading.Thread(target=gen_llm, args=(cmd, gui), daemon=True).start()

def listen_for_wake():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src, duration=0.3)
            audio = r.listen(src, timeout=3, phrase_time_limit=3)
        text = r.recognize_google(audio)
        if text and WAKE_WORD in text.lower():
            idx = text.lower().index(WAKE_WORD) + len(WAKE_WORD)
            after = text[idx:].strip()
            return after if after else True
    except:
        pass
    return False

def listen_for_cmd(gui):
    gui.set_status("listening")
    r = sr.Recognizer()
    try:
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src, duration=0.5)
            audio = r.listen(src, timeout=5)
        text = r.recognize_google(audio)
        return text.lower() if text else None
    except:
        return None

STARTUP_FILE = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'jarvis.bat')

def main_loop(gui):
    time.sleep(1)
    while True:
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

def main():
    gui = JarvisGUI()
    threading.Thread(target=main_loop, args=(gui,), daemon=True).start()
    gui.run()

if __name__ == "__main__":
    main()