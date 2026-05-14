import os, time, ctypes
from gtts import gTTS

tts = gTTS(text="Testing MCI audio playback on Windows", lang="en", tld="com", slow=False)
tts.save("scratch/test_mci.mp3")

path = os.path.abspath("scratch/test_mci.mp3")
res = ctypes.windll.winmm.mciSendStringW(f'open "{path}" alias speech', None, 0, 0)
print(f"Open result: {res}")
if res == 0:
    res = ctypes.windll.winmm.mciSendStringW("play speech wait", None, 0, 0)
    print(f"Play result: {res}")
    ctypes.windll.winmm.mciSendStringW("close speech", None, 0, 0)
print("Done")
os.remove("scratch/test_mci.mp3")
