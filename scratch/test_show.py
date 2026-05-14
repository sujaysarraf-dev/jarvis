import socket
import sys

port = 49152
try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', port))
    client.sendall(b"SHOW")
    client.close()
    print("Sent SHOW command.")
except Exception as e:
    print(f"Failed to send SHOW: {e}")
