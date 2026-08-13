import cv2

for i in range(2):  # only 0 and 1 found
    print(f"🔍 Testing camera index {i}")
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"❌ Could not open camera {i}")
        continue

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    ret, frame = cap.read()
    if ret:
        cv2.imshow(f"Camera {i}", frame)
        print("Press any key to close this window...")
        cv2.waitKey(0)
    else:
        print(f"❌ No frame from camera {i}")
    cap.release()
    cv2.destroyAllWindows()
