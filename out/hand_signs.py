import cv2
import mediapipe as mp
import numpy as np
import urllib.request
import os

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(OUT_DIR, "hand_landmarker.task")
if not os.path.exists(model_path):
    print("Downloading hand landmarker model...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
        model_path
    )
    print("Downloaded.")

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

_landmarker = None

def get_landmarker():
    global _landmarker
    if _landmarker is None:
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        )
        _landmarker = HandLandmarker.create_from_options(options)
    return _landmarker

def finger_state(lm):
    return [
        lm[4].x < lm[3].x,
        lm[8].y < lm[6].y,
        lm[12].y < lm[10].y,
        lm[16].y < lm[14].y,
        lm[20].y < lm[18].y,
    ]

def detect_gesture(up, lm):
    t, i, m, r, p = up
    if all(up):
        return "PALM"
    if not any(up):
        return "FIST"
    if t and not any(up[1:]):
        return "THUMBS_UP"
    if not t and i and not any(up[2:]):
        return "POINT"
    if not t and i and m and not r and not p:
        if abs(lm[8].y - lm[12].y) < 0.03:
            return "PEACE"
    if not t and i and m and r and not p:
        return "THREE"
    if not t and not i and not m and not r and p:
        return "PINKY"
    if not t and i and not m and not r and p:
        return "ROCK"
    if t and i and not any(up[2:4]) and p:
        return "SPIDER"
    if np.linalg.norm(np.array([lm[4].x, lm[4].y]) - np.array([lm[8].x, lm[8].y])) < 0.04:
        return "OK"
    c = sum(up)
    return ["ONE", "TWO", "THREE", "FOUR", "FIVE"][c-1] if 1 <= c <= 5 else None

CONNECTIONS = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),
               (10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17)]

def run():
    landmarker = get_landmarker()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No camera detected.")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    print("Hand + Face Detector — ESC to quit")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_img)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        for (fx, fy, fw, fh) in faces:
            cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), (0, 255, 0), 2)
            cv2.putText(frame, "FACE", (fx, fy-10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)

        if result.hand_landmarks:
            for hl in result.hand_landmarks:
                pts = [(int(l.x * w), int(l.y * h)) for l in hl]
                for a, b in CONNECTIONS:
                    cv2.line(frame, pts[a], pts[b], (50, 150, 255), 2)
                for pt in pts:
                    cv2.circle(frame, pt, 5, (0, 255, 0), -1)

                up = finger_state(hl)
                gesture = detect_gesture(up, hl)

                if gesture:
                    cv2.putText(frame, gesture, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                                1.3, (0, 255, 0), 3)

        cv2.putText(frame, "ESC exit", (w-120, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (100, 100, 100), 1)
        cv2.imshow("Hand Signs", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()

if __name__ == "__main__":
    run()
