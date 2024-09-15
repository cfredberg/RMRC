import cv2
import pickle
import socket
import time

HOST = "127.0.0.1"
PORT = 8002

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("sleeping")
    time.sleep(1)
    print("slept")
    while True:
        frame = b''
        data = b'1'
        while data != b'':
            data = s.recv(1024)
            frame += data
        print(frame)
        frame = pickle.loads(frame)
        cv2.imshow("Camera Footage Via Gstreamer", frame)