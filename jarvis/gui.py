import os
import sys
import time
import threading
import tkinter as tk
from tkinter import font
import datetime
import subprocess
from jarvis.config import BASE_DIR, SS_FOLDER, STARTUP_FILE
from jarvis.speech import speak, listen_for_wake, listen_for_cmd
from jarvis.utils import log_command

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
        self.running = True

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
            from jarvis.commands import handle_cmd
            threading.Thread(target=handle_cmd, args=(text, self), daemon=True).start()
            self.info_win.lift()

    def check_startup(self, canvas=None):
        p = STARTUP_FILE
        if canvas:
            txt = "On startup ✓" if os.path.exists(p) else "Startup: off"
            canvas.create_text(140, 85, text=txt, fill="#666", font=font.Font(size=7))

    def set_startup(self, enable):
        if enable:
            script_path = os.path.join(BASE_DIR, "main.py")
            env_file = os.path.join(BASE_DIR, ".env")
            with open(STARTUP_FILE, 'w') as f:
                f.write(f'@echo off\ncd /d "{BASE_DIR}"\n')
                if os.path.exists(env_file):
                    with open(env_file) as ef:
                        for line in ef:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                f.write(f'set {line}\n')
                f.write(f'start /b pythonw "{script_path}" --bg\n')
        elif os.path.exists(STARTUP_FILE):
            os.remove(STARTUP_FILE)

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
        self.transcript.append((role, text, datetime.datetime.now().strftime("%H:%M:%S")))
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
            "idle": "#444444", "wake": "#ffaa00", "listening": "#00ff00",
            "processing": "#ffaa00", "speaking": "#00d4ff", "success": "#00ff00", "error": "#ff4444"
        }
        dots = {
            "idle": "#888888", "wake": "#ffaa00", "listening": "#00ff00",
            "processing": "#ffaa00", "speaking": "#00d4ff", "success": "#00ff00", "error": "#ff4444"
        }
        labels = {"idle": "J", "wake": "J", "listening": "J", "processing": "J", "speaking": "J", "success": "J", "error": "J"}

        c = colors.get(status, "#444444")
        self.canvas.itemconfig(self.bubble, fill=c)
        self.canvas.itemconfig(self.ring, outline=c, width=0)
        self.canvas.itemconfig(self.status_dot, fill=dots.get(status, "#888888"))
        self.canvas.itemconfig(self.label, text=labels.get(status, "J"))

        if self.info_win and self.info_win.winfo_exists():
            ti = {"idle": "Say 'Jarvis' to activate", "wake": "Activated!", "listening": "Listening...",
                  "processing": "Processing...", "speaking": "Speaking...", "success": "Done", "error": "Error"}
            if hasattr(self, 'info_canvas'):
                self.info_canvas.itemconfig(self.info_label, text=ti.get(status, ""), fill=colors.get(status, "#888888"))
                self.info_canvas.itemconfig(self.info_text, text=text if text else "")

    def pulse_animation(self):
        if self.last_status in ("processing", "listening"):
            self.pulse_phase = (self.pulse_phase + 1) % 20
            offset = abs(self.pulse_phase - 10) * 0.4
            size = self.size - 8 + offset
            self.canvas.coords(self.ring, 4 - offset / 2, 4 - offset / 2, self.size - 4 + offset / 2, self.size - 4 + offset / 2)
            self.canvas.itemconfig(self.ring, width=2)
        else:
            self.canvas.itemconfig(self.ring, width=0)

    def activate(self, has_cmd=False):
        self.awake = True
        self.set_status("wake")
        if not has_cmd:
            speak("I'm listening", self)

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

def main_loop(gui):
    time.sleep(1)
    wake_timeout = 0
    while gui.running:
        if not gui.awake:
            result = listen_for_wake()
            if result:
                gui.activate(has_cmd=isinstance(result, str))
            if isinstance(result, str):
                from jarvis.commands import handle_cmd
                handle_cmd(result, gui)
        else:
            cmd = listen_for_cmd(gui, timeout=2)
            if cmd:
                from jarvis.commands import handle_cmd
                handle_cmd(cmd, gui)
                wake_timeout = 0
                gui.set_status("listening")
            else:
                wake_timeout += 1
                if wake_timeout > 25:
                    gui.deactivate()
                elif wake_timeout > 15:
                    gui.set_status("listening" if wake_timeout % 2 == 0 else "idle")

def run_background_listener():
    import speech_recognition as sr
    from jarvis.config import WAKE_WORD
    from jarvis.speech import _recognizer
    log_command("Background listener started")
    while True:
        try:
            with sr.Microphone() as src:
                _recognizer.adjust_for_ambient_noise(src, duration=0.5)
                audio = _recognizer.listen(src, timeout=5, phrase_time_limit=5)
            text = _recognizer.recognize_google(audio).lower()
            if WAKE_WORD in text:
                log_command("Wake word detected in background, launching GUI")
                subprocess.Popen(['pythonw', os.path.abspath(os.path.join(BASE_DIR, "main.py"))])
                time.sleep(5)
        except Exception:
            time.sleep(1)

def main():
    os.makedirs(SS_FOLDER, exist_ok=True)
    if "--bg" in sys.argv:
        run_background_listener()
    else:
        gui = JarvisGUI()
        threading.Thread(target=main_loop, args=(gui,), daemon=True).start()
        gui.run()
