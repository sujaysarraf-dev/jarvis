import os
import time
import warnings
import threading
import speech_recognition as sr
from jarvis.config import BASE_DIR, WAKE_WORD
from jarvis.utils import log_command

SPEAK_LOCK = threading.Lock()

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

_recognizer = sr.Recognizer()

_tts_engine = None

def _get_tts():
    global _tts_engine
    if _tts_engine is None:
        try:
            import pyttsx3
            _tts_engine = pyttsx3.init()
            _tts_engine.setProperty("rate", 180)
        except:
            pass
    return _tts_engine

def speak(text, gui):
    if not text:
        return
    with SPEAK_LOCK:
        gui.add_transcript("Jarvis", text[:200])
        gui.set_status("speaking", text[:100])
        engine = _get_tts()
        spoken = False
        if engine:
            try:
                engine.say(text)
                engine.runAndWait()
                spoken = True
            except:
                pass
        if not spoken and _HAVE_GTTS and _HAVE_PYGAME:
            speech_file = os.path.join(BASE_DIR, "jarvis_speech.mp3")
            try:
                tts = gTTS(text=text, lang="en", tld="com", slow=False)
                tts.save(speech_file)
                pygame.mixer.music.load(speech_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                pygame.mixer.music.unload()
            except:
                pass
            finally:
                if os.path.exists(speech_file):
                    try:
                        os.remove(speech_file)
                    except:
                        pass
        if gui.awake:
            gui.set_status("listening")

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
