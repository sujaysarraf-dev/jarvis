import os
import time
import warnings
import threading
import numpy as np
import speech_recognition as sr
from jarvis.config import BASE_DIR, WAKE_WORD
from jarvis.utils import log_command

SPEAK_LOCK = threading.Lock()
WAKE_EVENT = threading.Event()
MIC_LOCK = threading.Lock()

warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

try:
    import pygame
    pygame.mixer.init()
    _HAVE_PYGAME = True
except:
    _HAVE_PYGAME = False

try:
    from gtts import gTTS
    _HAVE_GTTS = True
except:
    _HAVE_GTTS = False

_HAVE_OWW = False
_oww_model = None
_oww_thread = None
_oww_running = False
_oww_pyaudio = None
_oww_stream = None
try:
    from openwakeword.model import Model
    _OWW_MODEL = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
    _HAVE_OWW = True
except Exception:
    log_command("OpenWakeWord not available, falling back to cloud STT")

_recognizer = sr.Recognizer()

def speak(text, gui, add_transcript=True):
    if not text:
        return
    with SPEAK_LOCK:
        if add_transcript:
            gui.add_transcript("Jarvis", text[:200])
        gui.set_status("speaking", text[:100])
        speech_file = os.path.join(BASE_DIR, "jarvis_speech.mp3")
        spoken = False
        if _HAVE_GTTS and _HAVE_PYGAME:
            gtts_ok = [False]
            def do_gtts():
                try:
                    tts = gTTS(text=text, lang="en", tld="com", slow=False)
                    tts.save(speech_file)
                    gtts_ok[0] = True
                except:
                    pass
            t = threading.Thread(target=do_gtts, daemon=True)
            t.start()
            t.join(8)
            if gtts_ok[0]:
                try:
                    pygame.mixer.music.load(speech_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    pygame.mixer.music.unload()
                    spoken = True
                except:
                    pass
            if os.path.exists(speech_file):
                try:
                    os.remove(speech_file)
                except:
                    pass
        if not spoken:
            try:
                import win32com.client
                sp = win32com.client.Dispatch("SAPI.SpVoice")
                sp.Speak(text, 0)
            except:
                pass
        if gui.awake:
            gui.set_status("listening")

def is_oww_available():
    return _HAVE_OWW

def start_oww_listener():
    global _oww_thread, _oww_running
    if not _HAVE_OWW or _oww_running:
        return
    _oww_running = True
    _oww_thread = threading.Thread(target=_oww_listen_loop, daemon=True)
    _oww_thread.start()

def stop_oww_listener():
    global _oww_running, _oww_stream, _oww_pyaudio
    _oww_running = False
    if _oww_stream:
        try:
            _oww_stream.close()
        except:
            pass
        _oww_stream = None
    if _oww_pyaudio:
        try:
            _oww_pyaudio.terminate()
        except:
            pass
        _oww_pyaudio = None

def restart_oww_listener():
    stop_oww_listener()
    time.sleep(0.3)
    start_oww_listener()

def _oww_listen_loop():
    global _oww_stream, _oww_pyaudio
    import pyaudio
    try:
        _oww_pyaudio = pyaudio.PyAudio()
        _oww_stream = _oww_pyaudio.open(
            format=pyaudio.paInt16, channels=1, rate=16000,
            input=True, frames_per_buffer=1280,
            stream_callback=None
        )
        _oww_stream.start_stream()
        while _oww_running:
            try:
                chunk = _oww_stream.read(1280, exception_on_overflow=False)
                audio = np.frombuffer(chunk, dtype=np.int16)
                pred = _OWW_MODEL.predict(audio)
                if pred.get("hey_jarvis", 0) > 0.5:
                    WAKE_EVENT.set()
            except:
                time.sleep(0.01)
    except:
        pass
    finally:
        if _oww_stream:
            try:
                _oww_stream.close()
            except:
                pass
            _oww_stream = None
        if _oww_pyaudio:
            try:
                _oww_pyaudio.terminate()
            except:
                pass
            _oww_pyaudio = None

def listen_for_wake():
    try:
        with sr.Microphone() as src:
            _recognizer.adjust_for_ambient_noise(src, duration=0.3)
            audio = _recognizer.listen(src, timeout=3, phrase_time_limit=5)
        text = _recognizer.recognize_google(audio)
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

def listen_for_cmd(gui, timeout=2):
    try:
        with sr.Microphone() as src:
            _recognizer.adjust_for_ambient_noise(src, duration=0.3)
            audio = _recognizer.listen(src, timeout=timeout, phrase_time_limit=4)
        text = _recognizer.recognize_google(audio)
        if text:
            return text.lower()
        return None
    except sr.RequestError:
        log_command("Speech recognition: network error")
        return None
    except sr.WaitTimeoutError:
        return None
    except:
        return None
