import speech_recognition as sr
import subprocess
import threading
import tkinter as tk
from tkinter import font
import os
import sys
import datetime
import requests
import json
import re

WAKE_WORD = "jarvis"
OLLAMA_URL = "http://localhost:11434/api/generate"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SS_FOLDER = os.path.join(BASE_DIR, "ss")
os.makedirs(SS_FOLDER, exist_ok=True)

APPS = {
    "calculator": "calc", "notepad": "notepad", "browser": "start chrome",
    "chrome": "start chrome", "edge": "start msedge", "firefox": "start firefox",
    "explorer": "explorer", "terminal": "start cmd", "cmd": "start cmd",
    "paint": "start mspaint", "word": "start winword", "excel": "start excel",
    "powerpoint": "start powerpnt", "spotify": "start spotify", "discord": "start discord",
    "whatsapp": "start whatsapp", "telegram": "start telegram", "vscode": "start code",
    "youtube": "start https://youtube.com", "maps": "start https://google.com/maps",
    "github": "start https://github.com", "gmail": "start https://gmail.com",
    "settings": "start ms-settings:", "control panel": "control",
    "task manager": "taskmgr", "taskmgr": "taskmgr",
    "file explorer": "explorer", "notepad++": "start notepad++",
}

FAST = [
    (r"open ss\b|show ss|show screenshot|open screenshots", lambda: os.startfile(SS_FOLDER)),
    (r"show desktop", lambda: subprocess.Popen(['powershell', '-Command', '(New-Object -ComObject Shell.Application).ToggleDesktop()'])),
    (r"(lock|lock pc|lock computer)", lambda: subprocess.Popen("rundll32.exe user32.dll,LockWorkStation")),
    (r"restart|reboot", lambda: subprocess.Popen("shutdown /r /t 0")),
    (r"shutdown|turn off", lambda: subprocess.Popen("shutdown /s /t 0")),
    (r"sleep|hibernate", lambda: subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")),
    (r"volume up|louder|increase volume", lambda: subprocess.run('for /l %i in (1,1,10) do @start /b nircmd volup 65536', shell=True)),
    (r"volume down|quieter|lower|decrease volume", lambda: subprocess.run('for /l %i in (1,1,10) do @start /b nircmd voldown 65536', shell=True)),
    (r"mute|silence", lambda: subprocess.run("nircmd mutesysvolume 2", shell=True)),
    (r"unmute", lambda: subprocess.run("nircmd mutesysvolume 0", shell=True)),
    (r"open downloads", lambda: subprocess.Popen(['explorer', os.environ.get('USERPROFILE','') + '\\Downloads'])),
    (r"open documents", lambda: subprocess.Popen(['explorer', os.environ.get('USERPROFILE','') + '\\Documents'])),
    (r"open desktop", lambda: subprocess.Popen(['explorer', os.environ.get('USERPROFILE','') + '\\Desktop'])),
]

class JarvisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS")
        self.root.geometry("400x380")
        self.root.configure(bg="#1a1a2e")
        self.root.attributes("-topmost", True)
        
        self.awake = False
        
        title_font = font.Font(family="Helvetica", size=24, weight="bold")
        self.title_label = tk.Label(self.root, text="JARVIS", font=title_font, bg="#1a1a2e", fg="#00d4ff")
        self.title_label.pack(pady=20)

        self.status_label = tk.Label(self.root, text="Say 'Jarvis' to activate", font=("Helvetica", 12), bg="#1a1a2e", fg="#ffaa00")
        self.status_label.pack(pady=5)

        self.circle_canvas = tk.Canvas(self.root, width=100, height=100, bg="#1a1a2e", highlightthickness=0)
        self.circle_canvas.pack(pady=20)
        self.circle = self.circle_canvas.create_oval(10, 10, 90, 90, fill="#333333", outline="#00d4ff", width=2)

        self.text_label = tk.Label(self.root, text="", font=("Helvetica", 11), bg="#1a1a2e", fg="#ffffff", wraplength=350)
        self.text_label.pack(pady=10)

        self.startup_label = tk.Label(self.root, text="", font=("Helvetica", 9), bg="#1a1a2e", fg="#666666")
        self.startup_label.pack(pady=5)
        self.check_startup()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        if not os.path.exists(STARTUP_FILE):
            self.set_startup(True)

        self.root.after(100, self.update)

    def check_startup(self):
        p = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'jarvis.bat')
        if os.path.exists(p):
            self.startup_label.config(text="Running on startup ✓")
        else:
            self.startup_label.config(text="Not on startup")

    def set_startup(self, enable):
        p = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'jarvis.bat')
        if enable:
            with open(p, 'w') as f:
                f.write(f'@echo off\nstart /b python "{os.path.abspath(sys.argv[0])}"\n')
        elif os.path.exists(p):
            os.remove(p)
        self.check_startup()

    def set_status(self, status, text=""):
        colors = {
            "idle":"#333333","wake":"#ffaa00","listening":"#00ff00",
            "processing":"#ffaa00","speaking":"#00d4ff","success":"#00ff00","error":"#ff4444"
        }
        self.circle_canvas.itemconfig(self.circle, fill=colors.get(status, "#333333"))
        
        texts = {
            "idle":"Say 'Jarvis' to activate","wake":"Jarvis activated!",
            "listening":"Listening...","processing":"Processing...",
            "speaking":"Speaking...","success":"Done","error":"Error"
        }
        self.status_label.config(text=texts.get(status, ""), fg=colors.get(status, "#888888"))
        if text:
            self.text_label.config(text=text)

    def activate(self):
        self.awake = True
        self.set_status("wake")
        speak("I'm listening", self)

    def deactivate(self):
        self.awake = False
        self.set_status("idle")

    def on_close(self):
        self.root.quit()

    def update(self):
        self.root.update()
        self.root.after(50, self.update)

    def run(self):
        self.root.mainloop()

def speak(text, gui):
    gui.set_status("speaking", text)
    try:
        from gtts import gTTS
        import pygame
        import time
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

def gen_llm(cmd, gui):
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": "phi4",
            "prompt": f"""You are JARVIS voice assistant. User said: "{cmd}"
If it's a question or calculation, reply with just the ANSWER (short, 1 sentence).
If it's a command to do something, reply with the Windows CMD command to execute (start with CMD:).
Otherwise reply "NONE".

Example 1: "what is 2+2" -> 4
Example 2: "open calculator" -> CMD:calc
Example 3: "what's the weather" -> NONE
Example 4: "play music" -> CMD:start spotify

Your response:""",
            "stream": False,
            "options": {"num_ctx": 512, "num_predict": 50, "temperature": 0}
        }, timeout=25)
        res = r.json().get("response","").strip()
        if not res or res == "NONE":
            speak("I don't know how to do that", gui)
        elif res.startswith("CMD:"):
            subprocess.run(res[4:].strip(), shell=True, capture_output=True)
            speak("Done", gui)
        else:
            gui.set_status("success", res)
            speak(res, gui)
    except Exception as e:
        speak("LLM error", gui)

def handle_cmd(cmd, gui):
    cmd = cmd.lower().strip()
    gui.set_status("processing", f"You said: {cmd}")

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

    for pattern, action in FAST:
        if re.search(pattern, cmd):
            try:
                action()
                speak("Done", gui)
            except Exception as e:
                speak("Failed", gui)
            return

    for name, run_cmd in APPS.items():
        if f"open {name}" in cmd or name in cmd.split():
            subprocess.Popen(run_cmd, shell=True)
            speak(f"Opening {name}", gui)
            return

    play_match = re.search(r"play\s+(.+)", cmd)
    if play_match and "open" not in cmd:
        song = play_match.group(1).strip()
        if song == "music":
            subprocess.Popen("start spotify", shell=True)
            speak("Opening Spotify", gui)
        else:
            import urllib.parse
            query = urllib.parse.quote(song)
            subprocess.Popen(f"start https://music.youtube.com/search?q={query}", shell=True)
            speak(f"Playing {song}", gui)
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

    threading.Thread(target=gen_llm, args=(cmd, gui), daemon=True).start()

def listen_for_wake():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src, duration=0.3)
            audio = r.listen(src, timeout=3, phrase_time_limit=3)
        text = r.recognize_google(audio)
        if text and WAKE_WORD in text.lower():
            return True
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
    import time
    time.sleep(1)
    while True:
        if not gui.awake:
            if listen_for_wake():
                gui.activate()
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