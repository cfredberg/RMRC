import cv2
gstreamer_str = "sudo gst-launch-1.0 rtspsrc location=rtsp://192.168.1.5:8080/h264_ulaw.sdp latency=100 ! queue ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! videoscale ! video/x-raw,width=640,height=480,format=BGR ! appsink drop=1"

cap = cv2.VideoCapture(gstreamer_str, cv2.CAP_GSTREAMER)

while(cap.isOpened()):
    ret, frame = cap.read()
    if ret:
        cv2.imshow("Input via Gstreamer", frame)
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
        else:
            break
cap.release()
cv2.destroyAllWindows()