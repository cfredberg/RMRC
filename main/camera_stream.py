import cv2

gst_str = "gst-launch-1.0 device=/dev/video0 ! videoconvert ! autovideosink"

cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

while cap.isOpened():
    