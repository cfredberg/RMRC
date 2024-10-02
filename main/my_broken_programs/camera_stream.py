import cv2
import socket
import pickle
import time
import struct

HOST = ""
PORT = 8000

gst_str = "gst-launch-1.0 videotestsrc ! videoconvert ! appsink"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print("Connection established")
        # cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            exit("camera can't be opened")
        while True:
            print("capture open")
            ret, frame = cap.read()
            if ret:
                print("have return")
                frame = pickle.dumps(frame)
                print(f"sending {frame}")
                counter = 1
                for i in range(0, len(frame), 1024):
                    data = frame[i : i + 1024]
                    print(f"Data #{counter}: {data}")
                    s.sendall(data)
                    counter += 1
            else:
                print("no return")
        cap.release()
