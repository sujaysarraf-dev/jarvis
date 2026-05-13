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
