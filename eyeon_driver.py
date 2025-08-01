import cv2
import mediapipe as mp
import time
import math
import serial
import threading
import pyttsx3

# ====================== Setup ======================

# Serial communication with ESP32
try:
    esp32 = serial.Serial('COM13', 9600)  # Update this COM port if needed
    print("✅ ESP32 Connected")
except:
    esp32 = None
    print("❌ ESP32 connection failed")

# Text-to-Speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)

def speak(text):
    threading.Thread(target=lambda: engine.say(text) or engine.runAndWait(), daemon=True).start()

# Mediapipe setup
mp_face = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
face_mesh = mp_face.FaceMesh(max_num_faces=1)
hands = mp_hands.Hands()

# Alert Control
alert_flags = {
    'drowsy': 0,
    'hand_to_ear': 0,
    'talking': 0,
    'left': 0,
    'right': 0
}
cooldown = 5  # seconds
eye_close_counter = 0
sleep_threshold = 15
look_start_time = None
look_direction = None

# Camera
cap = cv2.VideoCapture(0 , cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

# Utils
def get_distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def send_to_esp32(message):
    if esp32 and esp32.is_open:
        esp32.write((message + '\n').encode())
        print(f"📤 Sent to ESP32: {message}")

def trigger_alert(key, message, display_msg):
    current = time.time()
    if current - alert_flags[key] > cooldown:
        alert_flags[key] = current
        speak(message)
        send_to_esp32(display_msg)

# ====================== Main Loop ======================

while True:
    success, frame = cap.read()
    if not success:
        print("❌ Camera Error")
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_result = face_mesh.process(rgb)
    hand_result = hands.process(rgb)

    drowsy = False
    hand_to_ear = False
    talking = False
    looking_left = looking_right = False

    if face_result.multi_face_landmarks:
        face = face_result.multi_face_landmarks[0]

        # Eye Detection
        left_eye_top = face.landmark[159]
        left_eye_bottom = face.landmark[145]
        right_eye_top = face.landmark[386]
        right_eye_bottom = face.landmark[374]

        eye_gap = (get_distance(left_eye_top, left_eye_bottom) + get_distance(right_eye_top, right_eye_bottom)) / 2

        if eye_gap < 0.015:
            eye_close_counter += 1
            if eye_close_counter >= sleep_threshold:
                drowsy = True
        else:
            eye_close_counter = 0

        # Talking Detection
        mouth_gap = get_distance(face.landmark[13], face.landmark[14])
        if mouth_gap > 0.035:
            talking = True

        # Left/Right Looking Detection
        nose_x = face.landmark[1].x
        if nose_x < 0.45:
            if look_direction != 'left':
                look_direction = 'left'
                look_start_time = time.time()
            elif time.time() - look_start_time > 3:
                looking_left = True
        elif nose_x > 0.55:
            if look_direction != 'right':
                look_direction = 'right'
                look_start_time = time.time()
            elif time.time() - look_start_time > 3:
                looking_right = True
        else:
            look_direction = None
            look_start_time = None

        # Hand near ear (phone use)
        if hand_result.multi_hand_landmarks:
            for hand in hand_result.multi_hand_landmarks:
                wrist = hand.landmark[0]
                right_ear = face.landmark[234]
                if get_distance(wrist, right_ear) < 0.1:
                    hand_to_ear = True

    # ====================== Alerts ======================
    if drowsy:
        cv2.putText(frame, "DROWSINESS DETECTED", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        trigger_alert("drowsy", "Alert! Drowsiness detected.", "DROWSY DRIVER")

    if talking:
        cv2.putText(frame, "Talking Detected", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        trigger_alert("talking", "You're talking while driving!", "TALKING DRIVER")

    if hand_to_ear:
        cv2.putText(frame, "Phone Activity", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        trigger_alert("hand_to_ear", "Phone activity detected!", "PHONE USAGE")

    if looking_left:
        cv2.putText(frame, "Looking Left Too Long", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
        trigger_alert("left", "You're looking right too long!", "LEFT LOOKING")

    if looking_right:
        cv2.putText(frame, "Looking Right Too Long", (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
        trigger_alert("right", "You're looking left too long!", "RIGHT LOOKING")

    # Show video
    cv2.imshow("EyeOnDriver - Real-Time Monitoring", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
