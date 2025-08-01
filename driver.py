import cv2
import mediapipe as mp
import time
import math
import pyttsx3
import threading 
import serial
import time

# Serial Communication Setup
SERIAL_PORT = 'COM13'  # Change this to match your ESP32's port
BAUD_RATE = 9600

try:
    esp32 = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to ESP32 on {SERIAL_PORT}")
except Exception as e:
    print(f"Failed to connect to ESP32: {e}")
    esp32 = None

def send_to_esp32(alert_message):
    if esp32 and esp32.is_open:
        try:
            # Add newline to ensure ESP32 receives complete message
            message = alert_message + "\n"
            esp32.write(message.encode())
            esp32.flush()  # Ensure the message is sent
            print(f"Sent to ESP32: {alert_message}")
            
            # Wait for confirmation (with timeout}
            start_time = time.time()
            while time.time() - start_time < 2:  # 2 second timeout
                if esp32.in_waiting:
                    response = esp32.readline().decode().strip()
                    if response.startswith("ALERT_DISPLAYED:"):
                        print("ESP32 confirmed alert display")
                        return True
            print("No confirmation received from ESP32")
        except Exception as e:
            print(f"Error sending to ESP32: {e}")
    return False

# Initialize Mediapipe
mp_face = mp.solutions.face_mesh

face_mesh = mp_face.FaceMesh(max_num_faces=1)
hands = mp_hands.Hands()

# Alert timing
last_alert_time = {
    'drowsy': 0,
    'looking_down': 0,
    'hand_to_ear': 0,
    'talking': 0,
    'looking_left': 0,
    'looking_right': 0
}
alert_cooldown = 5  # seconds

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def get_distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

while True:
    success, frame = cap.read()
    if not success:
        print("Failed to capture frame")
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_result = face_mesh.process(frame_rgb)
    hand_result = hands.process(frame_rgb)

    current_time = time.time()
    
    if face_result.multi_face_landmarks:
        face = face_result.multi_face_landmarks[0]
        
        # Drowsiness detection
        left_eye_top = face.landmark[159]
        left_eye_bottom = face.landmark[145]
        right_eye_top = face.landmark[386]
        right_eye_bottom = face.landmark[374]
        
        eye_distance = (get_distance(left_eye_top, left_eye_bottom) + 
                       get_distance(right_eye_top, right_eye_bottom)) / 2
                       
        if eye_distance < 0.013 and current_time - last_alert_time['drowsy'] > alert_cooldown:
            alert = "DROWSY"
            cv2.putText(frame, "DROWSINESS DETECTED", (30, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            send_to_esp32(alert)
            last_alert_time['drowsy'] = current_time

        # Looking down detection
        nose_y = face.landmark[1].y
        chin_y = face.landmark[152].y
        if (chin_y - nose_y) > 0.07 and current_time - last_alert_time['looking_down'] > alert_cooldown:
            alert = "Looking Down"
            cv2.putText(frame, "LOOKING DOWN", (30, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            send_to_esp32(alert)
            last_alert_time['looking_down'] = current_time

        # Looking left/right detection
        nose_x = face.landmark[1].x
        if nose_x < 0.45 and current_time - last_alert_time['looking_left'] > alert_cooldown:
            alert = "Looking Left"
            cv2.putText(frame, "LOOKING LEFT", (30, 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            send_to_esp32(alert)
            last_alert_time['looking_left'] = current_time
        elif nose_x > 0.55 and current_time - last_alert_time['looking_right'] > alert_cooldown:
            alert = "Looking Right"
            cv2.putText(frame, "LOOKING RIGHT", (30, 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            send_to_esp32(alert)
            last_alert_time['looking_right'] = current_time

    # Phone usage detection
    if hand_result.multi_hand_landmarks and face_result.multi_face_landmarks:
        for hand in hand_result.multi_hand_landmarks:
            wrist = hand.landmark[0]
            if face.landmark[234]:  # Right ear landmark
                right_ear = face.landmark[234]
                if (get_distance(wrist, right_ear) < 0.1 and 
                    current_time - last_alert_time['hand_to_ear'] > alert_cooldown):
                    alert = "Phone Usage"
                    cv2.putText(frame, "PHONE DETECTED", (30, 160),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    send_to_esp32(alert)
                    last_alert_time['hand_to_ear'] = current_time

    cv2.imshow("Driver Monitoring", frame)
    
    # Check for ESP32 responses
    if esp32 and esp32.in_waiting:
        response = esp32.readline().decode().strip()
        print(f"ESP32 says: {response}")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if esp32:
    esp32.close()