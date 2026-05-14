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
_OWW_MODEL = None
_oww_thread = None
_oww_running = False
_oww_stream = None
_oww_pyaudio = None
INTERRUPT_EVENT = threading.Event()
try:
    from openwakeword.model import Model as _OWWModelClass
    _OWW_MODEL_CLASS = _OWWModelClass
    _HAVE_OWW = True
except Exception:
    _OWW_MODEL_CLASS = None
    _HAVE_OWW = False

_recognizer = sr.Recognizer()

_oww_init_lock = threading.Lock()

def _init_oww():
    global _OWW_MODEL
    if _OWW_MODEL is not None:
        return True
    with _oww_init_lock:
        if _OWW_MODEL is not None:
            return True
        try:
            _OWW_MODEL = _OWW_MODEL_CLASS(wakeword_models=["hey_jarvis"], inference_framework="onnx")
            return True
        except Exception as e:
            log_command(f"OpenWakeWord init failed: {e}")
            return False

def speak(text, gui, add_transcript=True):
    if not text:
        return
    # Pause wake word listener while speaking
    pause_oww()
    
    # Wait for any previous speech to finish
    with SPEAK_LOCK:
        gui.last_spoken = text[:200]
        if add_transcript:
            gui.add_transcript("Jarvis", text)
        
        gui.set_status("speaking", text[:100])
        speech_file = os.path.join(BASE_DIR, f"jarvis_speech_{int(time.time())}.mp3")
        spoken = False
        
        if _HAVE_GTTS and _HAVE_PYGAME:
            try:
                tts = gTTS(text=text, lang="en", tld="com", slow=False)
                tts.save(speech_file)
                pygame.mixer.music.load(speech_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    if INTERRUPT_EVENT.is_set():
                        pygame.mixer.music.stop()
                        INTERRUPT_EVENT.clear()
                        break
                    time.sleep(0.05)
                pygame.mixer.music.unload()
                spoken = True
            except Exception as e:
                log_command(f"Speech (gTTS) failed: {e}")
            finally:
                if os.path.exists(speech_file):
                    try: os.remove(speech_file)
                    except: pass
        
        if not spoken and not INTERRUPT_EVENT.is_set():
            try:
                import win32com.client
                sp = win32com.client.Dispatch("SAPI.SpVoice")
                sp.Speak(text, 0)
                spoken = True
            except: pass
            
        INTERRUPT_EVENT.clear()
        
        # Ensure we don't pick up our own tail end of speech
        time.sleep(0.4)
        WAKE_EVENT.clear()
    
    # Extra buffer for the microphone to settle
    time.sleep(0.4)
    WAKE_EVENT.clear()
    resume_oww()

def is_oww_available():
    return _HAVE_OWW

def start_oww_listener():
    global _oww_thread, _oww_running
    if not _HAVE_OWW or _oww_running:
        return
    if not _init_oww():
        return
    _oww_running = True
    _oww_thread = threading.Thread(target=_oww_listen_loop, daemon=True)
    _oww_thread.start()

_oww_paused = False

def pause_oww():
    global _oww_paused, _oww_stream
    _oww_paused = True
    time.sleep(0.05)
    if _oww_stream:
        try:
            _oww_stream.close()
        except:
            pass
        _oww_stream = None

def resume_oww():
    global _oww_paused
    _oww_paused = False

def _oww_listen_loop():
    global _oww_stream, _oww_pyaudio
    import pyaudio
    _oww_pyaudio = pyaudio.PyAudio()
    buf = []
    while True:
        try:
            if _oww_paused:
                time.sleep(0.1)
                buf = []
                continue
            if _oww_stream is None:
                _oww_stream = _oww_pyaudio.open(
                    format=pyaudio.paInt16, channels=1, rate=16000,
                    input=True, frames_per_buffer=1280
                )
            chunk = _oww_stream.read(1280, exception_on_overflow=False)
            buf.append(np.frombuffer(chunk, dtype=np.int16))
            if len(buf) < 5:
                time.sleep(0.005)
                continue
            audio = np.concatenate(buf)
            buf = []
            pred = _OWW_MODEL.predict(audio)
            if pred.get("hey_jarvis", 0) > 0.6:
                INTERRUPT_EVENT.set()
                WAKE_EVENT.set()
        except Exception:
            if _oww_stream:
                try:
                    _oww_stream.close()
                except:
                    pass
                _oww_stream = None
            buf = []
            time.sleep(0.2)

def listen_for_wake():
    # Wait for speech to finish if any
    with SPEAK_LOCK:
        pass
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

def capture_screen_b64():
    try:
        import PIL.ImageGrab, io, base64
        img = PIL.ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log_command(f"Screenshot capture failed: {e}")
        return None

def listen_for_cmd(gui, timeout=2):
    # Wait for speech to finish if any
    with SPEAK_LOCK:
        pass
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
