import os
import sys
from jarvis.gui import JarvisGUI
from jarvis.config import STARTUP_FILE

print(f"Old startup file: {STARTUP_FILE}")
if os.path.exists(STARTUP_FILE):
    os.remove(STARTUP_FILE)
    print("Deleted old startup file.")

gui = JarvisGUI()
gui.set_startup(True)
print("New startup file created with --listener support.")
gui.root.destroy()
