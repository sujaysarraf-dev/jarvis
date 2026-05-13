import os
import re
import subprocess

WAKE_WORD = "jarvis"
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "openrouter/free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_TIMEOUT = 8
OPENROUTER_FALLBACK_MODELS = [
    "openrouter/free",
    "gryphe/mythomax-l2-13b:free",
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS_FOLDER = os.path.join(BASE_DIR, "ss")
DATA_FOLDER = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(DATA_FOLDER, "command_history.txt")
MEMORY_FILE = os.path.join(DATA_FOLDER, "user_memory.json")

os.makedirs(SS_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
STARTUP_FILE = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'jarvis.bat')

COMMAND_MAP = {
    "calculator": "calc", "calc": "calc",
    "notepad": "notepad", "notes": "notepad",
    "browser": "start chrome", "web browser": "start chrome", "internet": "start chrome", "chrome": "start chrome",
    "edge": "start msedge", "microsoft edge": "start msedge",
    "firefox": "start firefox", "mozilla": "start firefox",
    "terminal": "start cmd", "command prompt": "start cmd", "cmd": "start cmd", "console": "start cmd", "powershell": "start powershell",
    "paint": "start mspaint", "ms paint": "start mspaint", "drawing": "start mspaint",
    "word": "start winword", "microsoft word": "start winword", "ms word": "start winword",
    "excel": "start excel", "microsoft excel": "start excel", "ms excel": "start excel",
    "powerpoint": "start powerpnt", "microsoft powerpoint": "start powerpnt", "slides": "start powerpnt",
    "spotify": "start spotify", "music player": "start spotify",
    "discord": "start discord", "vscode": "start code", "vs code": "start code", "visual studio code": "start code",
    "whatsapp": "start whatsapp", "telegram": "start telegram",
    "youtube": "start https://youtube.com",
    "maps": "start https://google.com/maps", "google maps": "start https://google.com/maps",
    "github": "start https://github.com", "gmail": "start https://gmail.com", "mail": "start https://gmail.com",
    "settings": "start ms-settings:", "control panel": "control",
    "task manager": "taskmgr", "taskmgr": "taskmgr",
    "file explorer": "explorer", "explorer": "explorer",
    "notepad++": "start notepad++", "calculator app": "calc",
}

KNOWN_ACTIONS = [
    ("show desktop", lambda: subprocess.Popen(['powershell', '-Command', '(New-Object -ComObject Shell.Application).ToggleDesktop()']), ["show desktop", "minimize all windows", "show windows", "close all windows"]),
    ("lock", lambda: subprocess.Popen("rundll32.exe user32.dll,LockWorkStation"), ["lock", "lock pc", "lock computer", "lock screen"]),
    ("restart", lambda: subprocess.Popen("shutdown /r /t 0"), ["restart", "reboot", "restart pc", "restart computer"]),
    ("shutdown", lambda: subprocess.Popen("shutdown /s /t 0"), ["shutdown", "turn off", "power off", "shut down"]),
    ("sleep", lambda: subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"), ["sleep", "hibernate", "go to sleep"]),
    ("volume up", lambda: subprocess.run('powershell -Command "$s=(New-Object -ComObject WScript.Shell);for($i=0;$i -lt 10;$i++){$s.SendKeys([char]175);Start-Sleep -Milliseconds 50}"', shell=True), ["volume up", "louder", "increase volume", "turn up volume", "increase speaker volume"]),
    ("volume down", lambda: subprocess.run('powershell -Command "$s=(New-Object -ComObject WScript.Shell);for($i=0;$i -lt 10;$i++){$s.SendKeys([char]174);Start-Sleep -Milliseconds 50}"', shell=True), ["volume down", "quieter", "lower volume", "decrease volume", "turn down volume"]),
    ("unmute", lambda: subprocess.run('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]176)"', shell=True), ["unmute", "unmute volume", "unsilence", "unmute sound"]),
    ("mute", lambda: subprocess.run('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]176)"', shell=True), ["mute", "mute volume", "silence", "silent", "mute sound"]),
    ("open downloads", lambda: subprocess.Popen(['explorer', os.environ.get('USERPROFILE','') + '\\Downloads']), ["open downloads folder", "show downloads folder", "my downloads"]),
    ("open documents", lambda: subprocess.Popen(['explorer', os.environ.get('USERPROFILE','') + '\\Documents']), ["open documents folder", "show documents folder", "my documents"]),
    ("open desktop", lambda: subprocess.Popen(['explorer', os.environ.get('USERPROFILE','') + '\\Desktop']), ["open desktop folder", "show desktop folder"]),
    ("open screenshots", lambda: os.startfile(SS_FOLDER), ["open screenshots folder", "show screenshots folder"]),
]

FORBIDDEN_PS = re.compile(r'\b(Remove-Item|rm\b|del\b|Format-Volume|Clear-|Restart-Computer|Stop-Computer|Shutdown|Add-LocalGroupMember|Set-LocalUser|Disable-LocalUser)', re.I)

CREATE_NO_WINDOW = 0x08000000

PREFIXES = ("open ", "launch ", "start ", "run ", "switch to ")
FUZZY_SCORE = 75
