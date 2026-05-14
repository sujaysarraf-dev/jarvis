import os
import sys
import time
import threading
import tkinter as tk
from tkinter import font
import datetime
import subprocess
import math
import random
from jarvis.config import BASE_DIR, SS_FOLDER, STARTUP_FILE
from jarvis.speech import speak, listen_for_wake, listen_for_cmd, WAKE_EVENT, is_oww_available, start_oww_listener, pause_oww, resume_oww, SPEAK_LOCK
import jarvis.speech as speech_mod
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
        self._wave_rings = []
        self._wave_phase = 0
        self._particle_angles = [random.random() * math.pi * 2 for _ in range(8)]
        self._status_flash = 0

        self.size = 160
        self.glow_color = "#00d4ff"
        self.accent_color = "#0077ff"
        self.bg_color = "#0a0a0a"
        self.idle_color = "#2a2a3a"
        self.active_color = "#00d4ff"
        self.listening_color = "#00ffcc"
        self.processing_color = "#ff8800"
        self.speaking_color = "#0088ff"
        self.error_color = "#ff4444"

        self.x = self.root.winfo_screenwidth() - self.size - 40
        self.y = self.root.winfo_screenheight() - self.size - 120
        self.root.geometry(f"{self.size}x{self.size}+{self.x}+{self.y}")

        self.canvas = tk.Canvas(self.root, width=self.size, height=self.size, bg="black", highlightthickness=0)
        self.canvas.pack()

        cx, cy, S = self.size // 2, self.size // 2, self.size

        self.outer_glow = self.canvas.create_oval(3, 3, S-3, S-3, outline=self.idle_color, width=2, dash=(2, 6))
        self.outer_ring = self.canvas.create_oval(8, 8, S-8, S-8, outline=self.idle_color, width=4)
        self.mid_ring = self.canvas.create_oval(22, 22, S-22, S-22, outline=self.idle_color, width=2, dash=(3, 6))
        self.inner_ring = self.canvas.create_oval(40, 40, S-40, S-40, outline=self.idle_color, width=3)
        self.core_glow = self.canvas.create_oval(50, 50, S-50, S-50, fill="#0d1520", outline=self.active_color, width=2)

        self.core = self.canvas.create_oval(58, 58, S-58, S-58, fill="#0a0a0a", outline="")
        self.status_dot = self.canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill=self.idle_color, outline="")

        self.dashes = []
        for i in range(12):
            d = self.canvas.create_line(0, 0, 0, 0, fill=self.active_color, width=2)
            self.dashes.append(d)

        self.particles = []
        for i in range(8):
            p = self.canvas.create_oval(0, 0, 0, 0, fill=self.active_color, outline="")
            self.particles.append(p)

        self.wave_rings_canvas = []
        for _ in range(3):
            w = self.canvas.create_oval(cx, cy, cx, cy, outline=self.speaking_color, width=1, dash=(1, 4))
            self.wave_rings_canvas.append(w)

        self.canvas.tag_bind("all", "<ButtonPress-1>", self.start_drag)
        self.canvas.tag_bind("all", "<B1-Motion>", self.do_drag)
        self.canvas.tag_bind("all", "<ButtonRelease-1>", self.stop_drag)
        self.canvas.tag_bind(self.core_glow, "<Double-Button-1>", self.toggle_window)
        self.canvas.tag_bind(self.core_glow, "<Button-3>", self.show_context_menu)

        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#0d1117", fg="#c9d1d9",
            activebackground="#00d4ff", activeforeground="#000", borderwidth=0,
            font=("Segoe UI", 9))
        self.context_menu.add_command(label=" HUD Terminal ", command=self.show_info)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=" Hide ", command=self.hide)
        self.context_menu.add_command(label=" Shutdown ", command=self.close)

        self.root.after(16, self.update_animation)

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
                self.info_win.geometry(f"+{self.x - 350}+{self.y - 180}")

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

        ix = self.x - 350
        iy = self.y - 180
        self.info_win.geometry(f"340x500+{ix}+{iy}")

        main_frame = tk.Frame(self.info_win, bg="#0a0e17", highlightbackground="#00d4ff33", highlightthickness=1)
        main_frame.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(main_frame, bg="#0d1421")
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        header = tk.Frame(inner, bg="#0d1421")
        header.pack(fill=tk.X, padx=12, pady=(8, 2))

        tk.Label(header, text="JARVIS", bg="#0d1421", fg="#00d4ff",
            font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)

        self.clock_label = tk.Label(header, text="", bg="#0d1421", fg="#444466",
            font=("Segoe UI", 8))
        self.clock_label.pack(side=tk.RIGHT)

        sep = tk.Frame(inner, bg="#1a2640", height=1)
        sep.pack(fill=tk.X, padx=10, pady=2)

        btn_frame = tk.Frame(inner, bg="#0d1421")
        btn_frame.pack(fill=tk.X, padx=10, pady=(3, 0))
        tk.Button(btn_frame, text="×", command=self.toggle_window,
            bg="#0d1421", fg="#ff4444", bd=0, font=("Segoe UI", 10),
            activebackground="#1a1a2e", cursor="hand2").pack(side=tk.RIGHT)

        self.status_label = tk.Label(inner, text="STANDBY", bg="#0d1421", fg="#2a2a3a",
            font=("Segoe UI", 8, "bold"))
        self.status_label.pack(fill=tk.X, padx=12, pady=(0, 2))

        transcript_frame = tk.Frame(inner, bg="#060a12", highlightbackground="#00d4ff11", highlightthickness=1)
        transcript_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 8))

        self.transcript_box = tk.Text(transcript_frame, bg="#060a12", fg="#c9d1d9",
            font=("Segoe UI", 9), relief=tk.FLAT, borderwidth=0, highlightthickness=0,
            state=tk.DISABLED, wrap=tk.WORD, insertbackground="#00d4ff",
            padx=6, pady=6)
        self.transcript_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(transcript_frame, command=self.transcript_box.yview,
            bg="#060a12", troughcolor="#060a12", width=4, activebackground="#00d4ff")
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.transcript_box.config(yscrollcommand=scroll.set)

        self.transcript_box.tag_config("you", foreground="#ffffff")
        self.transcript_box.tag_config("jarvis", foreground="#00ffcc")
        self.transcript_box.tag_config("time", foreground="#333355")

        input_frame = tk.Frame(inner, bg="#0d1421")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(input_frame, textvariable=self.entry_var,
            bg="#060a12", fg="white", insertbackground="#00d4ff",
            font=("Segoe UI", 10), relief=tk.FLAT,
            highlightbackground="#0077ff44", highlightthickness=1)
        self.entry.pack(fill=tk.X, side=tk.LEFT, expand=True, ipady=4, padx=(0, 6))
        self.entry.bind("<Return>", self.submit_text)

        tk.Button(input_frame, text="↵", command=self.submit_text,
            bg="#00d4ff", fg="#000", font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, padx=12, cursor="hand2",
            activebackground="#33ddff").pack(side=tk.RIGHT)

        self._refresh_transcript()
        self.entry.focus()
        self.set_status(self.last_status)
        self._update_clock()

    def _update_clock(self):
        if self.info_win and self.info_win.winfo_exists():
            now = datetime.datetime.now().strftime("%H:%M")
            self.clock_label.config(text=now)
            self.root.after(10000, self._update_clock)

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
        log_command("Jarvis hidden")

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
        self._status_flash = 1.0
        self.root.after(0, self._update_gui_status, status, text)

    def _update_gui_status(self, status, text=""):
        colors = {
            "idle": self.idle_color, "wake": self.active_color, "listening": self.listening_color,
            "processing": self.processing_color, "speaking": self.speaking_color,
            "success": self.listening_color, "error": self.error_color,
            "looking": "#00FFFF"
        }
        color = colors.get(status, self.idle_color)

        self.canvas.itemconfig(self.outer_glow, outline=color)
        self.canvas.itemconfig(self.outer_ring, outline=color)
        self.canvas.itemconfig(self.mid_ring, outline=color)
        self.canvas.itemconfig(self.inner_ring, outline=color)
        self.canvas.itemconfig(self.core_glow, outline=color)
        self.canvas.itemconfig(self.status_dot, fill=color)
        for d in self.dashes:
            self.canvas.itemconfig(d, fill=color)
        for p in self.particles:
            self.canvas.itemconfig(p, fill=color)

        if self.info_win and self.info_win.winfo_exists():
            labels = {"idle": "STANDBY", "wake": "ACTIVE", "listening": "LISTENING",
                      "processing": "THINKING", "speaking": "SPEAKING", "success": "COMPLETE",
                      "error": "ERROR", "looking": "SCANNING"}
            self.status_label.config(text=labels.get(status, "READY"), fg=color)

    def update_animation(self):
        cx, cy, S = self.size // 2, self.size // 2, self.size
        self.rotation_angle = (self.rotation_angle + 2) % 360
        rad = math.radians(self.rotation_angle)

        status_speed_mult = {"idle": 0.5, "wake": 2.0, "listening": 2.5,
                            "processing": 3.0, "speaking": 1.5, "looking": 2.0}
        speed = status_speed_mult.get(self.last_status, 1.0)

        r_outer = S // 2 - 10
        r_inner = S // 2 - 18
        for i, dash in enumerate(self.dashes):
            angle = rad * speed + i * (math.pi * 2 / len(self.dashes))
            x1 = cx + math.cos(angle) * r_inner
            y1 = cy + math.sin(angle) * r_inner
            x2 = cx + math.cos(angle) * r_outer
            y2 = cy + math.sin(angle) * r_outer
            self.canvas.coords(dash, x1, y1, x2, y2)

        pulse_speeds = {"idle": 0.04, "wake": 0.12, "listening": 0.15,
                       "processing": 0.2, "speaking": 0.1, "looking": 0.12}
        pulse_rate = pulse_speeds.get(self.last_status, 0.06)
        self.pulse_phase = (self.pulse_phase + pulse_rate) % (math.pi * 2)
        pulse = math.sin(self.pulse_phase) * 0.5 + 0.5

        if self.last_status != "idle":
            self._status_flash = max(0, self._status_flash - 0.03)
            flash = 1.0 + self._status_flash * 6
        else:
            flash = 1.0 + pulse * 0.3

        color = self.canvas.itemcget(self.outer_ring, "outline")
        r, g, b = self._hex_to_rgb(color)
        r = min(255, int(r * flash))
        g = min(255, int(g * flash))
        b = min(255, int(b * flash))
        bright = self._rgb_to_hex(r, g, b)

        if self.last_status in ("processing", "listening", "speaking", "wake", "looking"):
            glow_offset = pulse * 5
            self.canvas.coords(self.outer_glow, 3 - glow_offset/3, 3 - glow_offset/3,
                              S - 3 + glow_offset/3, S - 3 + glow_offset/3)
            self.canvas.coords(self.inner_ring, 40 - glow_offset, 40 - glow_offset,
                              S - 40 + glow_offset, S - 40 + glow_offset)
            if self.last_status == "speaking":
                w = 4 + pulse * 4
            elif self.last_status == "processing":
                w = 3 + pulse * 2
            else:
                w = 3 + pulse
            self.canvas.itemconfig(self.outer_ring, width=max(2, int(w)))
            self.canvas.itemconfig(self.status_dot, fill=bright)
        else:
            self.canvas.itemconfig(self.outer_ring, width=3)
            self.canvas.itemconfig(self.status_dot, fill=self.idle_color)
            self.canvas.coords(self.outer_glow, 3, 3, S-3, S-3)
            self.canvas.coords(self.inner_ring, 40, 40, S-40, S-40)

        particle_orbit = S // 2 - 13
        for i, p in enumerate(self.particles):
            self._particle_angles[i] = (self._particle_angles[i] + (0.03 + i * 0.005) * speed) % (math.pi * 2)
            pa = self._particle_angles[i]
            px = cx + math.cos(pa) * (particle_orbit + pulse * (2 if i % 2 == 0 else -2))
            py = cy + math.sin(pa) * (particle_orbit + pulse * (2 if i % 2 == 0 else -2))
            psize = max(1, int(2 + pulse * (1.5 if i % 2 == 0 else 0.5)))
            self.canvas.coords(p, px - psize, py - psize, px + psize, py + psize)

        self._wave_phase = (self._wave_phase + 0.06) % (math.pi * 2)
        if self.last_status == "speaking":
            for i, w in enumerate(self.wave_rings_canvas):
                wp = (self._wave_phase + i * math.pi * 2 / 3) % (math.pi * 2)
                wsize = 5 + wp * 18
                alpha = max(0, 1.0 - wp / (math.pi * 2))
                wcolor = self._alpha_color(self.speaking_color, alpha)
                self.canvas.coords(w, cx - wsize, cy - wsize, cx + wsize, cy + wsize)
                self.canvas.itemconfig(w, outline=wcolor, width=max(1, int(alpha * 3)))
                self.canvas.tag_raise(w, self.core_glow)
        else:
            for w in self.wave_rings_canvas:
                self.canvas.coords(w, cx, cy, cx, cy)

        self.root.after(20, self.update_animation)

    def _hex_to_rgb(self, h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, r, g, b):
        return f"#{r:02x}{g:02x}{b:02x}"

    def _alpha_color(self, hex_color, alpha):
        r, g, b = self._hex_to_rgb(hex_color)
        bg_r, bg_g, bg_b = 10, 10, 10
        ar = int(bg_r + (r - bg_r) * alpha)
        ag = int(bg_g + (g - bg_g) * alpha)
        ab = int(bg_b + (b - bg_b) * alpha)
        return self._rgb_to_hex(ar, ag, ab)

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
            _, old, ts = self.transcript[self.streaming_idx]
            self.transcript[self.streaming_idx] = ("Jarvis", old + token, ts)
        self.root.after(0, self._refresh_transcript)

    def end_streaming(self):
        self.streaming_idx = None

    def _refresh_transcript(self):
        if hasattr(self, 'transcript_box') and self.info_win and self.info_win.winfo_exists():
            self.transcript_box.config(state=tk.NORMAL)
            self.transcript_box.delete("1.0", tk.END)
            for role, text, t in self.transcript[-20:]:
                tag = "you" if role == "You" else "jarvis"
                self.transcript_box.insert(tk.END, f" [{t}] ", "time")
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

    def set_startup(self, enable):
        try:
            if enable:
                script_path = os.path.abspath(os.path.join(BASE_DIR, "main.py"))
                pythonw = sys.executable.replace("python.exe", "pythonw.exe")
                with open(STARTUP_FILE, "w") as f:
                    f.write(f'@echo off\nstart "" "{pythonw}" "{script_path}" --listener\n')
            elif os.path.exists(STARTUP_FILE):
                os.remove(STARTUP_FILE)
        except Exception as e:
            log_command(f"Startup creation failed: {e}")

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

_always_on = False

def main_loop(gui):
    global _idle_counter, _always_on
    time.sleep(1)
    if is_oww_available():
        start_oww_listener()

    while gui.running:
        try:
            if WAKE_EVENT.is_set():
                WAKE_EVENT.clear()
                _idle_counter = 0
                _always_on = True
                log_command("Wake word detected!")
                gui.root.after(0, lambda: gui.show_gui_from_bg(should_activate=False))
                gui.awake = True
                gui.set_status("wake")

                cmd = _listen_with_oww_pause(gui, timeout=3)
                if not cmd:
                    speak("I'm listening", gui)
                    cmd = _listen_with_oww_pause(gui, timeout=8)

                if cmd:
                    from jarvis.commands import handle_cmd
                    handle_cmd(cmd, gui)
                continue

            if not gui.awake:
                if not _always_on:
                    _idle_counter += 1
                    if is_oww_available() and not speech_mod._oww_thread_alive:
                        start_oww_listener()
                    if not is_oww_available() or _idle_counter > 30:
                        _idle_counter = 0
                        result = listen_for_wake()
                        if result:
                            gui.activate(has_cmd=isinstance(result, str))
                            if isinstance(result, str):
                                from jarvis.commands import handle_cmd
                                handle_cmd(result, gui)
                time.sleep(0.1)
            else:
                cmd = _listen_with_oww_pause(gui, timeout=4)
                if cmd:
                    from jarvis.commands import handle_cmd
                    handle_cmd(cmd, gui)
                    gui.set_status("listening")
        except Exception as e:
            log_command(f"Main loop crash: {e}")
            time.sleep(2)


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

def _setup_hotkey(gui):
    try:
        import keyboard as kb
        kb.add_hotkey("ctrl+shift+j", lambda: gui.root.after(0, gui.show_gui_from_bg))
        log_command("Hotkey Ctrl+Shift+J registered")
    except Exception as e:
        log_command(f"Hotkey failed: {e}")

def main():
    import socket
    lock_port = 49152
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('127.0.0.1', lock_port))
        lock_socket.listen(5)
    except socket.error:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(1)
            client.connect(('127.0.0.1', lock_port))
            client.sendall(b"SHOW")
            client.close()
        except: pass
        sys.exit(0)

    def socket_server_generic():
        while True:
            try:
                conn, addr = lock_socket.accept()
                with conn:
                    data = conn.recv(1024)
                    if b"SHOW" in data:
                        if "--listener" in sys.argv:
                            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
                            subprocess.Popen([pythonw, os.path.abspath(os.path.join(BASE_DIR, "main.py"))])
                        else:
                            gui.root.after(0, gui.show_gui_from_bg)
            except: time.sleep(1)

    threading.Thread(target=socket_server_generic, daemon=True).start()

    if "--listener" in sys.argv:
        run_background_listener()
        return

    os.makedirs(SS_FOLDER, exist_ok=True)
    gui = JarvisGUI()
    _setup_hotkey(gui)
    gui.set_startup(True)
    gui.set_registry_startup(True)
    threading.Thread(target=main_loop, args=(gui,), daemon=True).start()

    if "--bg" in sys.argv:
        gui.root.withdraw()
        gui.hidden = True

    gui.run()
