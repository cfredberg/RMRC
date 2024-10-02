import cv2
import socket
import pickle
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
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            exit("camera can't be opened")
        while True:
            ret, frame = cap.read()
            if ret:
                data = pickle.dumps(frame)
                message_size = struct.pack("L", len(data))  # Prefix each message with a fixed-size header
                conn.sendall(message_size + data)
            else:
                break
        cap.release()