import os
import sys
import time
import threading
import tkinter as tk
from tkinter import font
import datetime
import subprocess
import math
from jarvis.config import BASE_DIR, SS_FOLDER, STARTUP_FILE
from jarvis.speech import speak, listen_for_wake, listen_for_cmd, WAKE_EVENT, is_oww_available, start_oww_listener, pause_oww, resume_oww, SPEAK_LOCK
from jarvis.utils import log_command

class JarvisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "black")
        
        self.awake = False
        self.dragging = False
        self.drag_x = 0
        self.drag_y = 0
        self.running = True
        self.hidden = False
        self.pulse_phase = 0
        self.rotation_angle = 0
        self.last_status = "idle"
        self.transcript = []
        self.streaming_idx = None
        self.last_spoken = ""
        self.info_win = None

        # Design constants - Premium Theme
        self.size = 100
        self.glow_color = "#00d4ff"
        self.accent_color = "#0077ff"
        self.bg_color = "#0a0a0a"
        self.idle_color = "#444444"
        self.active_color = "#00d4ff"
        self.listening_color = "#00ffcc"
        self.processing_color = "#ffaa00"
        self.speaking_color = "#0077ff"
        self.error_color = "#ff4444"

        # Initial Position (Bottom Right)
        self.x = self.root.winfo_screenwidth() - self.size - 40
        self.y = self.root.winfo_screenheight() - self.size - 100
        self.root.geometry(f"{self.size}x{self.size}+{self.x}+{self.y}")

        self.canvas = tk.Canvas(self.root, width=self.size, height=self.size, bg="black", highlightthickness=0)
        self.canvas.pack()

        # Create layers for the "Arc Reactor" look
        self.outer_ring = self.canvas.create_oval(10, 10, self.size-10, self.size-10, outline=self.idle_color, width=2)
        self.inner_ring = self.canvas.create_oval(25, 25, self.size-25, self.size-25, outline=self.idle_color, width=1)
        
        # Decorative dashes for rotation
        self.dashes = []
        for i in range(8):
            dash = self.canvas.create_line(0, 0, 0, 0, fill=self.idle_color, width=3)
            self.dashes.append(dash)
        
        self.core = self.canvas.create_oval(35, 35, self.size-35, self.size-35, fill="#111111", outline=self.idle_color, width=2)
        self.status_dot = self.canvas.create_oval(self.size//2-5, self.size//2-5, self.size//2+5, self.size//2+5, fill=self.idle_color, outline="")
        
        # Event Bindings
        self.canvas.tag_bind(self.outer_ring, "<ButtonPress-1>", self.start_drag)
        self.canvas.tag_bind(self.outer_ring, "<B1-Motion>", self.do_drag)
        self.canvas.tag_bind(self.outer_ring, "<ButtonRelease-1>", self.stop_drag)
        self.canvas.tag_bind(self.core, "<Double-Button-1>", self.toggle_window)
        self.canvas.tag_bind(self.core, "<Button-3>", self.show_context_menu)
        
        # Context Menu
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#111111", fg="white", activebackground="#00d4ff", borderwidth=0)
        self.context_menu.add_command(label=" HUD Terminal ", command=self.show_info)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=" Hide Jarvis ", command=self.hide)
        self.context_menu.add_command(label=" Shutdown ", command=self.close)

        # Start Animation Loop
        self.root.after(50, self.update_animation)

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
                self.info_win.geometry(f"+{self.x - 330}+{self.y - 150}")

    def stop_drag(self, event):
        self.dragging = False

    def toggle_window(self, event=None):
        if self.info_win and self.info_win.winfo_exists():
            self.info_win.destroy()
            self.info_win = None
        else:
            self.show_info()

    def show_info(self):
        if self.info_win and self.info_win.winfo_exists():
            self.info_win.lift()
            return
            
        self.info_win = tk.Toplevel(self.root)
        self.info_win.overrideredirect(True)
        self.info_win.attributes("-topmost", True)
        self.info_win.attributes("-transparentcolor", "#000001")
        self.info_win.configure(bg="#000001")
        
        # Position HUD to the left of the bubble
        ix = self.x - 330
        iy = self.y - 150
        self.info_win.geometry(f"320x450+{ix}+{iy}")

        # HUD Frame with glass/tech effect
        main_frame = tk.Frame(self.info_win, bg="#0a0f1e", highlightbackground="#00d4ff", highlightthickness=1)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = tk.Frame(main_frame, bg="#0a0f1e")
        header.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(header, text="SYSTEM HUD v2.0", bg="#0a0f1e", fg="#00d4ff", font=("Consolas", 10, "bold")).pack(side=tk.LEFT)
        tk.Button(header, text="×", command=self.toggle_window, bg="#0a0f1e", fg="#ff4444", bd=0, font=("Consolas", 12, "bold"), activebackground="#1a1a2e").pack(side=tk.RIGHT)

        # Status Display
        self.status_label = tk.Label(main_frame, text="SYSTEM IDLE", bg="#0a0f1e", fg="#444444", font=("Consolas", 9))
        self.status_label.pack(fill=tk.X, padx=10)

        # Transcript Area
        transcript_frame = tk.Frame(main_frame, bg="#050a14")
        transcript_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.transcript_box = tk.Text(transcript_frame, bg="#050a14", fg="#00d4ff", font=("Consolas", 9),
                                      relief=tk.FLAT, borderwidth=0, highlightthickness=0,
                                      state=tk.DISABLED, wrap=tk.WORD, insertbackground="#00d4ff")
        self.transcript_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scroll = tk.Scrollbar(transcript_frame, command=self.transcript_box.yview, bg="#050a14", troughcolor="#050a14", width=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.transcript_box.config(yscrollcommand=scroll.set)

        self.transcript_box.tag_config("you", foreground="#ffffff")
        self.transcript_box.tag_config("jarvis", foreground="#00ffcc")
        self.transcript_box.tag_config("time", foreground="#444444")

        # Input Area
        input_frame = tk.Frame(main_frame, bg="#0a0f1e")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(input_frame, textvariable=self.entry_var, bg="#050a14", fg="white",
                              insertbackground="#00d4ff", font=("Consolas", 10), relief=tk.FLAT,
                              highlightbackground="#0077ff", highlightthickness=1)
        self.entry.pack(fill=tk.X, side=tk.LEFT, expand=True, ipady=3)
        self.entry.bind("<Return>", self.submit_text)
        
        tk.Button(input_frame, text="EXEC", command=self.submit_text, bg="#0077ff", fg="white",
                  font=("Consolas", 8, "bold"), relief=tk.FLAT, padx=10).pack(side=tk.RIGHT, padx=(5, 0))

        self._refresh_transcript()
        self.entry.focus()
        self.set_status(self.last_status)

    def submit_text(self, event=None):
        text = self.entry_var.get().strip()
        if text:
            self.entry_var.set("")
            from jarvis.commands import handle_cmd
            threading.Thread(target=handle_cmd, args=(text, self), daemon=True).start()

    def hide(self):
        if self.info_win and self.info_win.winfo_exists():
            self.info_win.withdraw()
        self.root.withdraw()
        self.hidden = True
        self.awake = False
        self.set_status("idle")
        log_command("Jarvis hidden (listening in background)")

    def show_gui_from_bg(self, should_activate=True):
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.hidden = False
        if self.info_win and self.info_win.winfo_exists():
            self.info_win.deiconify()
            self.info_win.lift()
        if should_activate:
            self.activate(has_cmd=False)

    def set_status(self, status, text=""):
        self.last_status = status
        self.root.after(0, self._update_gui_status, status, text)

    def _update_gui_status(self, status, text=""):
        colors = {
            "idle": self.idle_color, "wake": self.active_color, "listening": self.listening_color,
            "processing": self.processing_color, "speaking": self.speaking_color,
            "success": self.listening_color, "error": self.error_color
        }
        color = colors.get(status, self.idle_color)
        
        self.canvas.itemconfig(self.outer_ring, outline=color)
        self.canvas.itemconfig(self.inner_ring, outline=color)
        self.canvas.itemconfig(self.core, outline=color)
        self.canvas.itemconfig(self.status_dot, fill=color)
        for dash in self.dashes:
            self.canvas.itemconfig(dash, fill=color)
            
        if self.info_win and self.info_win.winfo_exists():
            ti = {"idle": "SYSTEM STANDBY", "wake": "SYSTEM ACTIVE", "listening": "LISTENING...",
                  "processing": "THINKING...", "speaking": "SPEAKING...", "success": "COMMAND COMPLETE", "error": "SYSTEM ERROR"}
            self.status_label.config(text=ti.get(status, "SYSTEM READY"), fg=color)

    def update_animation(self):
        # Rotation animation
        self.rotation_angle = (self.rotation_angle + 2) % 360
        rad = math.radians(self.rotation_angle)
        
        cx, cy = self.size // 2, self.size // 2
        r_outer = self.size // 2 - 15
        r_inner = self.size // 2 - 22
        
        for i, dash in enumerate(self.dashes):
            angle = rad + i * (math.pi * 2 / 8)
            x1 = cx + math.cos(angle) * r_inner
            y1 = cy + math.sin(angle) * r_inner
            x2 = cx + math.cos(angle) * r_outer
            y2 = cy + math.sin(angle) * r_outer
            self.canvas.coords(dash, x1, y1, x2, y2)

        # Pulse effect when active
        if self.last_status in ("processing", "listening", "speaking", "wake"):
            self.pulse_phase = (self.pulse_phase + 0.1) % (math.pi * 2)
            glow_offset = math.sin(self.pulse_phase) * 3
            self.canvas.coords(self.inner_ring, 25-glow_offset, 25-glow_offset, self.size-25+glow_offset, self.size-25+glow_offset)
            
            if self.last_status == "speaking":
                self.canvas.itemconfig(self.outer_ring, width=3 + math.sin(self.pulse_phase)*1)
            else:
                self.canvas.itemconfig(self.outer_ring, width=2)
        else:
            self.canvas.itemconfig(self.outer_ring, width=2)
            self.canvas.coords(self.inner_ring, 25, 25, self.size-25, self.size-25)

        self.root.after(30, self.update_animation)

    def add_transcript(self, role, text):
        if role == "Jarvis" and self.streaming_idx is not None:
            return
        self.transcript.append((role, text, datetime.datetime.now().strftime("%H:%M:%S")))
        if len(self.transcript) > 50:
            self.transcript = self.transcript[-50:]
        self.root.after(0, self._refresh_transcript)

    def update_streaming(self, token):
        if self.streaming_idx is None:
            self.transcript.append(("Jarvis", token, datetime.datetime.now().strftime("%H:%M:%S")))
            self.streaming_idx = len(self.transcript) - 1
        else:
            role, old, ts = self.transcript[self.streaming_idx]
            self.transcript[self.streaming_idx] = (role, old + token, ts)
        self.root.after(0, self._refresh_transcript)

    def end_streaming(self):
        self.streaming_idx = None

    def _refresh_transcript(self):
        if hasattr(self, 'transcript_box') and self.info_win and self.info_win.winfo_exists():
            self.transcript_box.config(state=tk.NORMAL)
            self.transcript_box.delete("1.0", tk.END)
            for role, text, t in self.transcript[-20:]:
                tag = "you" if role == "You" else "jarvis"
                self.transcript_box.insert(tk.END, f"[{t}] ", "time")
                self.transcript_box.insert(tk.END, f"{role}: ", tag)
                self.transcript_box.insert(tk.END, f"{text}\n\n", "")
            self.transcript_box.config(state=tk.DISABLED)
            self.transcript_box.see(tk.END)

    def activate(self, has_cmd=False):
        self.awake = True
        self.set_status("wake")
        if not has_cmd:
            speak("I'm listening", self)

    def deactivate(self):
        self.awake = False
        self.set_status("idle")

    def close(self):
        log_command("Jarvis shutting down")
        self.running = False
        self.root.destroy()
        sys.exit(0)

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def set_registry_startup(self, enable):
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enable:
                script_path = os.path.abspath(os.path.join(BASE_DIR, "main.py"))
                pythonw = sys.executable.replace("python.exe", "pythonw.exe")
                cmd = f'"{pythonw}" "{script_path}" --listener'
                winreg.SetValueEx(key, "JarvisListener", 0, winreg.REG_SZ, cmd)
            else:
                try: winreg.DeleteValue(key, "JarvisListener")
                except: pass
            winreg.CloseKey(key)
        except Exception as e:
            log_command(f"Registry startup failed: {e}")

    def run(self):
        self.root.mainloop()

def _listen_with_oww_pause(gui, timeout=2):
    pause_oww()
    time.sleep(0.2)
    cmd = listen_for_cmd(gui, timeout=timeout)
    resume_oww()
    return cmd

def main_loop(gui):
    time.sleep(1)
    idle_count = 0
    if is_oww_available():
        start_oww_listener()
    
    while gui.running:
        if WAKE_EVENT.is_set():
            WAKE_EVENT.clear()
            log_command("Wake word detected!")
            gui.root.after(0, lambda: gui.show_gui_from_bg(should_activate=False))
            gui.awake = True
            gui.set_status("wake")
            
            idle_count = 0
            # Quick check for immediate command
            cmd = _listen_with_oww_pause(gui, timeout=1)
            if not cmd:
                speak("I'm listening", gui)
                cmd = _listen_with_oww_pause(gui, timeout=4)
            
            if cmd:
                from jarvis.commands import handle_cmd
                handle_cmd(cmd, gui)
            continue

        if not gui.awake:
            if not is_oww_available():
                result = listen_for_wake()
                if result:
                    gui.activate(has_cmd=isinstance(result, str))
                    if isinstance(result, str):
                        from jarvis.commands import handle_cmd
                        handle_cmd(result, gui)
            time.sleep(0.1)
        else:
            cmd = _listen_with_oww_pause(gui, timeout=3)
            if cmd:
                from jarvis.commands import handle_cmd
                handle_cmd(cmd, gui)
                idle_count = 0
                gui.set_status("listening")
            else:
                idle_count += 1
                if idle_count > 10: # Stay awake for about 30 seconds of silence
                    gui.deactivate()
                    idle_count = 0
                else:
                    time.sleep(0.1)

def run_background_listener():
    from jarvis.speech import _HAVE_OWW, _init_oww
    log_command("Persistent Background Listener active")
    
    def is_jarvis_running():
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            s.connect(('127.0.0.1', 49152))
            s.close()
            return True
        except: return False

    if _HAVE_OWW and _init_oww():
        from jarvis.speech import _OWW_MODEL
        import pyaudio
        import numpy as np
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1280)
            while True:
                try:
                    chunk = stream.read(1280, exception_on_overflow=False)
                    audio = np.frombuffer(chunk, dtype=np.int16)
                    pred = _OWW_MODEL.predict(audio)
                    if pred.get("hey_jarvis", 0) > 0.6:
                        if not is_jarvis_running():
                            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
                            subprocess.Popen([pythonw, os.path.abspath(os.path.join(BASE_DIR, "main.py"))])
                        time.sleep(5)
                except: time.sleep(1)
        except Exception as e: log_command(f"BG Mic error: {e}")
        finally: p.terminate()

def main():
    import socket
    lock_port = 49152
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('127.0.0.1', lock_port))
        lock_socket.listen(5)
    except socket.error:
        # Send SHOW to existing instance
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(1)
            client.connect(('127.0.0.1', lock_port))
            client.sendall(b"SHOW")
            client.close()
        except: pass
        sys.exit(0)

    if "--listener" in sys.argv:
        run_background_listener()
        return

    os.makedirs(SS_FOLDER, exist_ok=True)
    gui = JarvisGUI()
    gui.set_registry_startup(True)
    
    def socket_server():
        while True:
            try:
                conn, addr = lock_socket.accept()
                with conn:
                    if b"SHOW" in conn.recv(1024):
                        gui.root.after(0, gui.show_gui_from_bg)
            except: time.sleep(1)
    
    threading.Thread(target=socket_server, daemon=True).start()
    threading.Thread(target=main_loop, args=(gui,), daemon=True).start()
    
    if "--bg" in sys.argv:
        gui.root.withdraw()
        gui.hidden = True
        
    gui.run()
