import cv2

# -------- Mapping helper --------
def map_range(value, in_min, in_max, out_min, out_max):
    # clamp value so it doesn’t go out of range
    value = max(min(value, in_max), in_min)
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

# -------- Setup --------
cap = cv2.VideoCapture(0)  # change index if wrong camera
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Servo ranges (tune later for your setup)
SERVO_X_MIN, SERVO_X_MAX = 10, 170
SERVO_Y_MIN, SERVO_Y_MAX = 10, 170

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1) 
    h, w, _ = frame.shape
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

    target_x, target_y = w // 2, h // 2  # default = center
    if len(faces) > 0:
        (x, y, fw, fh) = faces[0]  # first detected face
        target_x = x + fw // 2
        target_y = y + fh // 2
        # draw face box
        cv2.rectangle(frame, (x, y), (x + fw, y + fh), (0, 255, 0), 2)

    # Map pixel → servo angles
    servo_x = map_range(target_x, 0, w, SERVO_X_MIN, SERVO_X_MAX)
    servo_y = map_range(target_y, 0, h, SERVO_Y_MIN, SERVO_Y_MAX)

    # Map servo → "virtual eye" position on screen
    eye_x = map_range(servo_x, SERVO_X_MIN, SERVO_X_MAX, 100, w - 100)
    eye_y = map_range(servo_y, SERVO_Y_MIN, SERVO_Y_MAX, 100, h - 100)

    # Draw target (red) and simulated eye (blue)
    cv2.circle(frame, (target_x, target_y), 8, (0, 0, 255), -1)   # detected target
    cv2.circle(frame, (eye_x, eye_y), 20, (255, 0, 0), -1)        # virtual eye

    # Debug info
    cv2.putText(frame, f"ServoX={servo_x} ServoY={servo_y}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Animatronic Eye Simulation", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
