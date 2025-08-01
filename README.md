# EyeOnDriver – ADAR 1.0 🚘🧠  
**Advanced Driver & Road Safety System**

---

## 📌 Overview

**EyeOnDriver (ADAR 1.0)** is an intelligent, real-time driver monitoring system designed to enhance road safety using **AI-powered computer vision** and **IoT hardware integration**. Built with **Python (OpenCV & MediaPipe)** and **ESP32 microcontroller**, this system proactively detects unsafe driver behaviors and environmental conditions, preventing accidents through early alerts and control actions.

It is designed to be low-cost, open-source, and scalable for deployment in personal vehicles, commercial fleets, and public transport—especially across developing regions.

---

## ⚙️ Core Features

| Feature                         | Description                                                                 |
|---------------------------------|-----------------------------------------------------------------------------|
| 👁️ Drowsiness Detection         | Detects closed eyes via Eye Aspect Ratio (EAR) using face landmarks.        |
| 📱 Phone Usage Detection        | Identifies hand-to-ear gesture or downward gaze using MediaPipe landmarks. |
| 🗣️ Talking Detection            | Tracks continuous mouth motion to flag phone conversation or distraction.  |
| 🧑 Facial Recognition           | Only authorized drivers can start/operate the vehicle.                      |
| 🧾 Aadhaar Age Verification     | Prototype simulation checks for 18+ eligibility to drive.                  |
| 🍷 Alcohol Detection (MQ-3)     | ESP32 + gas sensor prevents ignition if alcohol is detected.               |
| 🔊 Voice Alerts (TTS)           | Speaks real-time warnings via text-to-speech.                              |
| 🧠 ESP32 Integration            | Communicates with Python via serial to display messages, trigger buzzers.  |
| 🆘 SOS Feature (Planned)        | Auto-alert + location tracking for emergencies (future scope).             |

---

## 🧠 Technologies Used

- **Python**: OpenCV, MediaPipe, pyttsx3, serial
- **Hardware**: ESP32, MQ-3 sensor, 16x2 LCD (I2C), buzzer, LEDs
- **Tools**: Arduino IDE, VS Code, Fritzing (for circuits)
- **Future Additions**: Firebase/ThingsBoard dashboard, GPS + GSM integration

---

## 🛠️ System Architecture

```text
[ Laptop Camera ]
       ↓
[ Python + OpenCV ]
       ↓
[ Detection Logic ]
       ↓
[ Serial Communication ]
       ↓
[ ESP32 Board ]
   ↓          ↓          ↓
[Buzzer]  [LCD Display] [Relay Lock]

EyeOnDriver/
├── README.md
├── requirements.txt
├── /python_code
│   └── driver_monitor.py
├── /esp32_code
│   └── esp32_driver_alert.ino
├── /images
│   └── demo_setup.jpg
├── /circuit_diagrams
│   └── wiring_schematic.pdf
├── /docs
│   └── project_description.pdf
└── /videos
    └── demo_clip.mp4
