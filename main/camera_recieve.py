import cv2
import pickle
import socket
import struct

HOST = "127.0.0.1"
PORT = 8000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    data = b""
    payload_size = struct.calcsize("L")
    while True:
        while len(data) < payload_size:
            packet = s.recv(4 * 1024)  # Adjust the buffer size as needed
            if not packet:
                break
            data += packet
        packed_msg_size = data[:payload_size]
        # this next line is in case we've already recieved more than just the
        # header (and since we initially recieve 4 * 1024 bytes, we definitely
        #  recieve more than just the header)
        data = data[payload_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]
        while len(data) < msg_size:
            data += s.recv(4 * 1024)
        frame_data = data[:msg_size]
        # This is again in case we recieved more than just the frame we want
        # and it is actually super smart cause then any data we get for the
        # next frame/header can be used for it later
        data = data[msg_size:]
        frame = pickle.loads(frame_data)
        cv2.imshow("Camera Footage Via Gstreamer", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    s.close()