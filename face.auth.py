import cv2
import face_recognition
import os
import numpy as np
import pyttsx3
import time
import threading

# === Initialize Text-to-Speech Engine ===
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Adjust as needed

last_spoken = {"Access granted": 0, "Access denied": 0}
cooldown = 3  # seconds

def speak_alert_async(message):
    def speak():
        engine.say(message)
        engine.runAndWait()
    now = time.time()
    if now - last_spoken[message] > cooldown:
        last_spoken[message] = now
        threading.Thread(target=speak).start()

# === Load Authorized Faces ===
path = 'authorized_faces'
images = []
classnames = []

if not os.path.exists(path):
    print(f"[ERROR] Folder '{path}' not found.")
    exit()

print("[INFO] Loading authorized face images...")

for filename in os.listdir(path):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        img_path = os.path.join(path, filename)
        img = cv2.imread(img_path)
        if img is not None:
            images.append(img)
            classnames.append(os.path.splitext(filename)[0].upper())

if not images:
    print("[ERROR] No images found in authorized_faces folder.")
    exit()

# === Encode Faces ===
def encode_faces(images):
    encoded_list = []
    for img in images:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img_rgb)
        if encodings:
            encoded_list.append(encodings[0])
        else:
            encoded_list.append(None)
    return encoded_list

print("[INFO] Encoding faces...")
known_encodings = encode_faces(images)

# Filter
filtered_encodings = []
filtered_names = []
for encoding, name in zip(known_encodings, classnames):
    if encoding is not None:
        filtered_encodings.append(encoding)
        filtered_names.append(name)
    else:
        print(f"[WARNING] No face found in image for '{name}', skipping.")

if not filtered_encodings:
    print("[ERROR] No valid face encodings found.")
    exit()

print(f"[INFO] Encoded {len(filtered_encodings)} faces.")

# === Webcam Setup ===
cap = cv2.VideoCapture(0 , cv2.CAP_DSHOW)
if not cap.isOpened():
    print("[ERROR] Webcam not available.")
    exit()

frame_count = 0
process_every_n_frames = 5
tolerance = 0.5

print("[INFO] Starting face recognition. Press 'q' to quit.")

face_locations = []
face_labels = []

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Frame grab failed.")
        break

    # Resize to 1/8 for faster processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.125, fy=0.125)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    if frame_count % process_every_n_frames == 0:
        face_locations = face_recognition.face_locations(rgb_small, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        face_labels = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(filtered_encodings, face_encoding, tolerance=tolerance)
            face_distances = face_recognition.face_distance(filtered_encodings, face_encoding)

            if face_distances.any():
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = filtered_names[best_match_index]
                    face_labels.append((name, (0, 255, 0)))
                else:
                    face_labels.append(("UNKNOWN", (0, 0, 255)))
            else:
                face_labels.append(("UNKNOWN", (0, 0, 255)))

    # Draw boxes
    access_granted = False
    for (top, right, bottom, left), (name, color) in zip(face_locations, face_labels):
        top *= 8
        right *= 8
        bottom *= 8
        left *= 8
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        if name != "UNKNOWN":
            access_granted = True

    # Show access message + speak
    if access_granted:
        cv2.putText(frame, "ACCESS GRANTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        speak_alert_async("Access granted")
    else:
        cv2.putText(frame, "ACCESS DENIED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        speak_alert_async("Access denied")

    cv2.imshow("Face Unlock System", frame)
    frame_count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
print("[INFO] System stopped.")
