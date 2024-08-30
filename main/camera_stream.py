import cv2
import socket
import pickle
import time

HOST = ""
PORT = 8002

gst_str = "gst-launch-1.0 videotestsrc ! videoconvert ! appsink"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print("Connection established")
        print("sleeping")
        time.sleep(1)
        print("slept")
        cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
        while cap.isOpened():
            print("capture open")
            ret, frame = cap.read()
            if ret:
                print("have return")
                print(f"sending {frame}")
                frame = pickle.dumps(frame)
                s.sendall(frame)
            else:
                print("no return")
