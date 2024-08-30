import cv2
import pickle
import socket
import time

HOST = "127.0.0.1"
PORT = 8002

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("sleeping")
    time.sleep(2)
    print("slept")
    while True:
        frame = s.recv(10000000)
        if not frame:
            print(f"recieved frame {frame}")
            frame = pickle.loads(frame)
            cv2.imshow("Camera Footage Via Gstreamer", frame)