import pyaudio
p = pyaudio.PyAudio()
print(f"Default input device: {p.get_default_input_device_info()}")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"Device {i}: {info['name']} (Inputs: {info['maxInputChannels']})")
p.terminate()
