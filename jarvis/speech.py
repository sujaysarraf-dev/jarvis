import os
import time
import threading
import speech_recognition as sr
from jarvis.config import BASE_DIR, WAKE_WORD
from jarvis.utils import log_command

SPEAK_LOCK = threading.Lock()

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

def speak(text, gui):
    with SPEAK_LOCK:
        gui.add_transcript("Jarvis", text)
        gui.set_status("speaking", text)
        speech_file = os.path.join(BASE_DIR, "jarvis_speech.mp3")
        spoken = False
        if _HAVE_GTTS and _HAVE_PYGAME:
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
                    try:
                        os.remove(speech_file)
                    except:
                        pass
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

def listen_for_cmd(gui, timeout=2):
    r = sr.Recognizer()
    try:
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src, duration=0.3)
            audio = r.listen(src, timeout=timeout, phrase_time_limit=4)
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
