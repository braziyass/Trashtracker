import cv2
import time
import requests

# CONFIGURATION
ESP32_IP = "http://192.168.1.50" # À vérifier sur le moniteur série de l'ESP32
BIN_X, BIN_Y, BIN_W, BIN_H = 200, 150, 200, 200
FULL_BRIGHTNESS_THRESHOLD = 100
MOTION_THRESHOLD = 20
INTERVAL = 2 

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    exit("❌ Erreur : Caméra non détectée")

# Initialisation de la première frame pour éviter l'erreur absdiff
ret, first_frame = cap.read()
prev_roi = first_frame[BIN_Y:BIN_Y+BIN_H, BIN_X:BIN_X+BIN_W]
prev_gray = cv2.cvtColor(prev_roi, cv2.COLOR_BGR2GRAY)

last_send_time = 0

while True:
    ret, frame = cap.read()
    if not ret: break

    # Extraction et conversion de la ROI actuelle
    roi = frame[BIN_Y:BIN_Y+BIN_H, BIN_X:BIN_X+BIN_W]
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 1. Détection de remplissage
    brightness = gray_roi.mean()
    status = "FULL" if brightness < FULL_BRIGHTNESS_THRESHOLD else "OK"

    # 2. Détection de mouvement (Animal) - Correction de l'erreur absdiff
    diff = cv2.absdiff(prev_gray, gray_roi)
    motion = diff.mean()
    animal_detected = "true" if motion > MOTION_THRESHOLD else "false"
    
    # Mise à jour de la frame précédente pour la prochaine boucle
    prev_gray = gray_roi.copy()

    # 3. Envoi des données via HTTP POST
    now = time.time()
    if now - last_send_time > INTERVAL:
        try:
            payload = {"status": status, "animal": animal_detected}
            # Timeout de 1s pour ne pas bloquer le flux vidéo si l'ESP est déconnecté
            response = requests.post(f"{ESP32_IP}/update", json=payload, timeout=1)
            print(f"📤 Envoyé : {status} | Animal : {animal_detected} ({response.status_code})")
        except Exception as e:
            print(f"⚠️ Erreur de connexion ESP32 : L'adresse {ESP32_IP} est injoignable")
        
        last_send_time = now

    # VISUALISATION
    color = (0, 0, 255) if status == "FULL" else (0, 255, 0)
    cv2.rectangle(frame, (BIN_X, BIN_Y), (BIN_X+BIN_W, BIN_Y+BIN_H), color, 2)
    cv2.putText(frame, f"STATUS: {status}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imshow("Trash Tracker - Mode HTTP", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()