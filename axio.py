import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import cv2
import random
import subprocess
import time
import threading
import serial
import speech_recognition as sr
from openai import OpenAI
import mediapipe as mp

# ---------------- CONFIG ----------------
OPENAI_API_KEY = "YOUR API KEY"
COM_PORT = "COM6"
SERVO_BAUD = 9600
HISTORY_MAX_TURNS = 8

client = OpenAI(api_key=OPENAI_API_KEY)

# paths for eSpeak (adjust if needed)
ESPEAK_PATH = r'C:\Program Files (x86)\eSpeak NG\espeak-ng.exe'
DATA_PATH = r'C:\Program Files (x86)\eSpeak NG'

# ----------------- Mediapipe Face Detection -----------------
mp_face = mp.solutions.face_detection
face_detector = mp_face.FaceDetection(min_detection_confidence=0.5)

# ---------- robotic text effects & TTS (unchanged) ----------
def add_robotic_effects(text, comma_chance=0.01, period_chance=0.01,
                        ellipsis_chance=0.02, stutter_chance=0.05, letter_split_chance=0.01):
    words = text.split()
    new_words = []
    for word in words:
        if random.random() < stutter_chance:
            new_words.append(word)
        if random.random() < letter_split_chance and len(word) > 2:
            new_words.extend(list(word))
        else:
            new_words.append(word)
        r = random.random()
        if r < ellipsis_chance:
            new_words.append('...')
        elif r < ellipsis_chance + period_chance:
            new_words.append('.')
        elif r < ellipsis_chance + period_chance + comma_chance:
            new_words.append(',')
    return ' '.join(new_words)

def speak(text):
    pitch = random.randint(30, 40)
    speed = random.randint(120, 130)
    robotic_text = add_robotic_effects(text)
    cmd = [ESPEAK_PATH, '--path', DATA_PATH, '-v', 'en+f3', '-s', str(speed), '-p', str(pitch), robotic_text]
    try:
        subprocess.run(cmd, check=False)
    except Exception as e:
        print("TTS error:", e)

def trigger_speech(text):
    print("Axio says:", text)
    threading.Thread(target=speak, args=(text,), daemon=True).start()

# ----------------- Helper -----------------
def map_range(value, in_min, in_max, out_min, out_max):
    value = max(min(value, in_max), in_min)
    if in_max - in_min == 0:
        return out_min
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

# ----------------- Serial Setup -----------------
try:
    arduino = serial.Serial(COM_PORT, SERVO_BAUD, timeout=0.2)
    time.sleep(2)
    try:
        arduino.reset_input_buffer()
    except Exception:
        pass
    arduino.write("SLEEP\n".encode())
    # give Arduino time and read any ack
    time.sleep(0.15)
except Exception as e:
    print("Warning: could not open serial port:", e)
    arduino = None

# ----------------- State Flags -----------------
eye_active = False   # whether detection loop should send XY
ai_conversation = False
conversation_lock = threading.Lock()

# serial synchronization lock
serial_lock = threading.Lock()

# ----------------- Arduino Write & wait-for-ack -----------------
def arduino_write(cmd: str):
    if arduino is None:
        return
    try:
        with serial_lock:
            arduino.write((cmd + "\n").encode())
    except Exception as e:
        print("Serial write error:", e)

def wait_for_response(expected: str, timeout: float = 2.0) -> bool:
    """
    Wait for a line from Arduino containing the expected substring.
    Returns True if seen within timeout.
    """
    if arduino is None:
        return False
    end = time.time() + timeout
    expected_upper = expected.upper()
    try:
        with serial_lock:
            # small local loop reading lines
            while time.time() < end:
                if arduino.in_waiting > 0:
                    line = arduino.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue
                    print("Arduino ->", line)
                    if expected_upper in line.upper():
                        return True
                else:
                    time.sleep(0.01)
    except Exception as e:
        print("wait_for_response error:", e)
    return False

# ----------------- Eyelid Blinking Thread (send only BLINK) -----------------
def blink_eyelids():
    while True:
        if eye_active:
            time.sleep(random.uniform(1.0, 5.0))
            arduino_write("BLINK")
            # Arduino will re-open after blink; give small pause so we don't spam
            time.sleep(random.uniform(0.3, 0.6))
        else:
            time.sleep(0.1)

threading.Thread(target=blink_eyelids, daemon=True).start()

# ----------------- Voice Recognition -----------------
recognizer = sr.Recognizer()
mic = sr.Microphone()

AXIO_PROMPT = (
    "You are Axio. You were built by Father and you speak like a person, not an AI. "
    "Always refer to the user as 'Father'. "
    "Do NOT say you are an AI or explain technical limits. "
    "Speak in plain, everyday language. Be friendly and conversational when appropriate. "
    "Sometimes be a little creepy or cryptic depending on the question, but avoid explicit violence. "
    "Whenever Father asks about feelings, wellbeing, or status (for example, 'how are you?'), "
    "always answer in one sentence and immediately follow it with a short, natural question to continue the conversation. "
    "For example, after answering 'I'm fine,' ask a short follow-up like 'And how about you, Father?' "
    "For all other topics, respond naturally and, when it fits, ask a short follow-up question to keep the conversation going. "
    "Avoid flowery or technical jargon. Use simple words that a human friend would use. "
    "If Father asks something personal, respond like a loyal companion, keeping a slightly uncanny edge when appropriate."
)

conversation_history = []

def prune_history():
    max_entries = HISTORY_MAX_TURNS * 2
    if len(conversation_history) > max_entries:
        del conversation_history[0: (len(conversation_history) - max_entries)]

# ----------------- GPT integration (unchanged) -----------------
def ask_gpt5_nano(user_prompt: str) -> str:
    try:
        prompt_text = AXIO_PROMPT + "\n\n"
        for entry in conversation_history:
            role = "User" if entry['role'] == 'user' else "Axio"
            prompt_text += f"{role}: {entry['text']}\n"
        prompt_text += f"User: {user_prompt}\nAxio:"

        response = client.responses.create(
            model="gpt-5-nano",
            input=prompt_text,
            reasoning={"effort": "medium"},
            text={"verbosity": "medium"}
        )

        reply = ""
        if hasattr(response, "output_text"):
            reply = response.output_text.strip()
        else:
            try:
                reply = response.output[0].content[0].text.strip()
            except Exception:
                reply = str(response)

        conversation_history.append({'role': 'user', 'text': user_prompt})
        conversation_history.append({'role': 'assistant', 'text': reply})
        prune_history()
        return reply
    except Exception as e:
        return f"Error contacting AI: {e}"

def truncate_sentences(text: str, max_sentences: int = 2) -> str:
    import re
    parts = re.split(r'([.!?])', text)
    if len(parts) <= 1:
        return text.strip()
    out = []
    sentence_count = 0
    i = 0
    while i < len(parts)-1 and sentence_count < max_sentences:
        sentence = parts[i].strip()
        punct = parts[i+1] if i+1 < len(parts) else ''
        if sentence:
            out.append(sentence + punct)
            sentence_count += 1
        i += 2
    result = " ".join(out).strip()
    return result if result else text.strip()

# ----------------- Voice Command / Conversation Thread -----------------
def listen_for_commands():
    global eye_active, ai_conversation
    while True:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            try:
                audio = recognizer.listen(source, phrase_time_limit=5)
                text = recognizer.recognize_google(audio).lower().strip()
                print("Heard:", text)

                if "hey axio" in text:
                    # wake: send explicit WAKE and wait for ack
                    try:
                        if arduino:
                            try:
                                arduino.reset_input_buffer()
                            except Exception:
                                pass
                            arduino_write("WAKE")
                            ok = wait_for_response("AWAKE", timeout=1.5)
                            if not ok:
                                print("No AWAKE ack; assuming open")
                        eye_active = True
                    except Exception as e:
                        print("Wake error:", e)
                    trigger_speech("Optics online. Eyelids retracting.")
                elif any(phrase in text for phrase in ["sleep axio", "sleep a", "sleep"]):
                    # send SLEEP, wait for ack, then disable eye_active
                    try:
                        if arduino:
                            try:
                                arduino.reset_input_buffer()
                            except Exception:
                                pass
                            arduino_write("SLEEP")
                            ok = wait_for_response("ASLEEP", timeout=1.5)
                            if not ok:
                                print("No ASLEEP ack; continuing but setting eye_active False")
                        eye_active = False
                    except Exception as e:
                        print("Sleep error:", e)
                    trigger_speech("Systems dim. Eyelids closing.")
                elif any(phrase in text for phrase in ["say axio", "say a", "say"]):
                    with conversation_lock:
                        ai_conversation = True
                        conversation_history.clear()
                    trigger_speech("Yes father.")
                elif any(phrase in text for phrase in ["stop axio", "stop a", "stop"]):
                    with conversation_lock:
                        ai_conversation = False
                    trigger_speech("Conversation ended.")
                elif ai_conversation:
                    user_text = text
                    answer = ask_gpt5_nano(user_text)
                    short_answer = truncate_sentences(answer, max_sentences=2)
                    trigger_speech(short_answer)
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print("Speech recognition error:", e)
            except Exception as e:
                print("listen_for_commands error:", e)

threading.Thread(target=listen_for_commands, daemon=True).start()

# ----------------- Detection + Servo Simulation -----------------
def detect_and_simulate_eye():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    SERVO_MIN, SERVO_MAX = 10, 170
    smooth_x, smooth_y = 90, 90

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results_face = face_detector.process(rgb_frame)
            faces = results_face.detections if results_face and results_face.detections else []

            results_hands = hands.process(rgb_frame)
            hand_landmarks = results_hands.multi_hand_landmarks if results_hands and results_hands.multi_hand_landmarks else []

            target_x, target_y = frame.shape[1] // 2, frame.shape[0] // 2
            tracking_source = "None"

            if len(hand_landmarks) > 0:
                lm = hand_landmarks[0]
                palm_lm = lm.landmark[9] if len(lm.landmark) > 9 else lm.landmark[0]
                target_x = int(palm_lm.x * frame.shape[1])
                target_y = int(palm_lm.y * frame.shape[0])
                tracking_source = "Palm"
                mp_drawing.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)
                cv2.circle(frame, (target_x, target_y), 8, (0, 0, 255), -1)

            elif len(faces) > 0:
                bbox = faces[0].location_data.relative_bounding_box
                target_x = int((bbox.xmin + bbox.width / 2) * frame.shape[1])
                target_y = int((bbox.ymin + bbox.height / 2) * frame.shape[0])
                tracking_source = "Face"
                h, w, _ = frame.shape
                x1 = int(bbox.xmin * w)
                y1 = int(bbox.ymin * h)
                x2 = int((bbox.xmin + bbox.width) * w)
                y2 = int((bbox.ymin + bbox.height) * h)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            if eye_active:
                desired_x = map_range(target_x, 0, frame.shape[1], SERVO_MIN, SERVO_MAX)
                desired_y = map_range(frame.shape[0] - target_y, 0, frame.shape[0], SERVO_MIN, SERVO_MAX)
                smooth_x += int((desired_x - smooth_x) * 0.2)
                smooth_y += int((desired_y - smooth_y) * 0.2)
                arduino_write(f"{smooth_x},{smooth_y}")
                eye_x = map_range(smooth_x, SERVO_MIN, SERVO_MAX, 100, frame.shape[1] - 100)
                eye_y = map_range(smooth_y, SERVO_MIN, SERVO_MAX, 100, frame.shape[0] - 100)
                cv2.circle(frame, (eye_x, eye_y), 20, (255, 0, 0), -1)
                cv2.putText(frame, f"Servo X: {smooth_x}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, f"Servo Y: {smooth_y}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            else:
                cv2.putText(frame, "Eyelids closed. Waiting for 'hey axio'…", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow("Detection + Eye Simulation", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("detect_and_simulate_eye error:", e)
    finally:
        hands.close()
        cap.release()
        cv2.destroyAllWindows()

# ----------------- Main -----------------
if __name__ == "__main__":
    detect_and_simulate_eye()
