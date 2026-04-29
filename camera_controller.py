import cv2
import time
import paho.mqtt.publish as publish

# =========================
# MQTT CONFIGURATION
# =========================
BROKER = "broker.hivemq.com"
TOPIC_STATUS = "city/bin/1/status"
TOPIC_ALERT = "city/bin/1/alert"

# =========================
# CAMERA INITIALIZATION
# =========================
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

print("✅ Camera started")

# =========================
# BIN ROI (adjust if needed)
# =========================
BIN_X = 200
BIN_Y = 150
BIN_W = 200
BIN_H = 200

# =========================
# THRESHOLDS
# =========================
FULL_BRIGHTNESS_THRESHOLD = 100
MOTION_THRESHOLD = 20
MQTT_INTERVAL = 2  # seconds

last_mqtt_time = 0

# =========================
# INITIAL FRAME (for motion)
# =========================
ret, prev_frame = cap.read()
if not ret:
    print("❌ Cannot read initial frame")
    exit()

prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

# =========================
# MAIN LOOP
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # ----- ROI -----
    roi = frame[BIN_Y:BIN_Y + BIN_H, BIN_X:BIN_X + BIN_W]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # ----- FULL / OK detection -----
    brightness = gray.mean()
    status = "FULL" if brightness < FULL_BRIGHTNESS_THRESHOLD else "OK"

    # ----- ANIMAL detection (motion) -----
    prev_roi = prev_gray[BIN_Y:BIN_Y + BIN_H, BIN_X:BIN_X + BIN_W]
    diff = cv2.absdiff(prev_roi, gray)
    motion = diff.mean()
    animal_detected = motion > MOTION_THRESHOLD

    # ----- MQTT send -----
    now = time.time()
    if now - last_mqtt_time > MQTT_INTERVAL:
        publish.single(TOPIC_STATUS, status, hostname=BROKER)
        print("📤 MQTT STATUS ->", status)

        if animal_detected:
            publish.single(TOPIC_ALERT, "ANIMAL", hostname=BROKER)
            print("🚨 MQTT ALERT -> ANIMAL")

        last_mqtt_time = now

    # ----- Visualization -----
    color = (0, 0, 255) if status == "FULL" else (0, 255, 0)

    cv2.rectangle(
        frame,
        (BIN_X, BIN_Y),
        (BIN_X + BIN_W, BIN_Y + BIN_H),
        color,
        2
    )

    cv2.putText(
        frame,
        f"STATUS: {status}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        color,
        2
    )

    cv2.putText(
        frame,
        f"Brightness: {int(brightness)}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Motion: {int(motion)}",
        (20, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    cv2.imshow("Smart Trash Bin Vision", frame)

    prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# =========================
# CLEANUP
# =========================
cap.release()
cv2.destroyAllWindows()
print("✅ Vision system stopped")