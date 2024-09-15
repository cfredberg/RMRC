import cv2
gstreamer_str = "videotestsrc ! video/x-raw,framerate=30/1 ! videoconvert ! appsink"

# cap = cv2.VideoCapture(gstreamer_str, cv2.CAP_GSTREAMER)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    exit("camera can't be opened")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    print("Frame captured")
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()