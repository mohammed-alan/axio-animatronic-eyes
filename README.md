# Axio – Animatronic Eye with Voice and AI


https://github.com/user-attachments/assets/969f4634-7d05-4f24-bbf0-409ac9c5c5e4


**Axio** is an interactive animatronic eye that combines Arduino-controlled servos, computer vision, speech recognition, and AI conversation powered by OpenAI.  
It can track faces or hands, blink, sleep, and hold conversations with the user through a robotic voice.

---

## Features

### Eye Movement Tracking
- Tracks a face or hand (via **MediaPipe** + **OpenCV**).
- Smooth servo movement for lifelike motion.

### Eyelid Control
- Blinks randomly when awake.
- Closes fully when in "sleep mode".

### Voice Activation & Commands
- **"hey axio"** → wake up.
- **"sleep axio" / "sleep"** → close eyes, stop tracking.
- **"say axio" / "say"** → enter conversation mode.
- **"stop axio" / "stop"** → end conversation mode.

### Conversational AI
- Integrated with **OpenAI (gpt-5-nano)** for natural, character-driven responses.
- Axio speaks using **eSpeak NG** with randomized robotic effects.

### Arduino Communication
- Serial link (default: **COM6 @ 9600 baud**).
- Commands: **SLEEP**, **WAKE**, **BLINK**, or **X,Y** servo positions.

---

## Requirements

### Hardware

![20250920_114914](https://github.com/user-attachments/assets/3bb53519-81a7-4abd-98a8-5c21647273bb)
![20250920_111146](https://github.com/user-attachments/assets/5775a4d6-384b-425b-add1-6f668d2b4514)


- **Arduino** (tested on Uno/Nano compatible)
- **6x Servo motors**  
  - 4 for eyelids  
  - 2 for horizontal/vertical eye rotation
- **Webcam** (for face/hand tracking)
- **Microphone** (for voice commands)

### Software
- **Python 3.9+**
- Required Python packages:  
  ```bash
  pip install opencv-python mediapipe speechrecognition pyserial openai

---

## Setup

### Arduino
1. Upload the provided `Arduino.ino` code to your board.
2. Connect servos to the defined pins:  
   - **Eyelids:** pins 6, 7, 9, 11  
   - **Eye X/Y:** pins 5, 3
3. Open the serial monitor (**9600 baud**) to verify **AWAKE / ASLEEP** acknowledgements.

### Python
1. Replace `OPENAI_API_KEY` in `axio.py` with your OpenAI API key.
2. Update `COM_PORT` if your Arduino is not on **COM6**.
3. Confirm the correct **eSpeak NG** installation paths:  
   - `ESPEAK_PATH` → main installation folder  
   - `DATA_PATH` → `espeak-data` folder inside installation
4. Install required Python packages if not already done:  
   ```bash
   pip install opencv-python mediapipe speechrecognition pyserial openai

5. Open a terminal in the project folder.

6. Run the Python script:

```bash 
python axio.py
```

7. A window will open showing webcam input and simulated eye movement.

8. Speak commands like “hey axio” to interact with the animatronic eye.

### AI Conversation Mode
- After saying "say axio", Axio will respond to your voice with natural, character-driven replies.
- Keeps a conversation history (max 8 turns) for context.
- Responses are truncated to 2 sentences for clarity.
- Personality: loyal, slightly uncanny, friendly, refers to user as "Father".

### Notes & Troubleshooting
- Ensure the correct **COM_PORT** and baud rate (9600) for Arduino communication.
- If the Python script cannot find the Arduino, it will continue in simulation mode.
- Blinking occurs randomly when awake; eyelids remain closed in sleep mode.
- Webcam must be available for tracking; otherwise, only servo simulation is active.

### License
MIT License – free to use and modify for personal or research projects.


