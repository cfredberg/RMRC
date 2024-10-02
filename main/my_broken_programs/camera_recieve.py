import cv2
import pickle
import socket
import time

HOST = "127.0.0.1"
PORT = 8000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        frame = b''
        while True:
            data = s.recv(1024)
            if not data:
                break
            else:
                frame += data
        print(frame)
        if frame != b'':
            frame = pickle.loads(frame)
            cv2.imshow("Camera Footage Via Gstreamer", frame)