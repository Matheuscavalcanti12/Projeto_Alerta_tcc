import cv2
import time
import winsound
import threading

# ================= CONFIG =================
EYE_CLOSED_THRESHOLD = 2
FRAME_SKIP = 3
RESIZE_SCALE = 0.6

alarm_active = False

# ================= SIRENE =================
def sirene():
    global alarm_active
    while alarm_active:
        winsound.Beep(1800, 200)
        winsound.Beep(2200, 200)

# ================= CLASSIFICADORES =================
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
eye_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml"
)

# ================= AUTO DETECÇÃO DE CÂMERA =================
camera = None
camera_index = None

for i in [1, 0]:  # tenta webcam externa primeiro
    cam = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # CAP_DSHOW acelera no Windows
    if cam.isOpened():
        camera = cam
        camera_index = i
        print(f"Câmera ativa: índice {i}")
        break

if camera is None:
    print("Nenhuma câmera encontrada.")
    exit()

# ================= VARIÁVEIS =================
closed_start = None
frame_count = 0
eyes_detected = True

# ================= LOOP =================
while True:
    ret, frame = camera.read()
    if not ret:
        print("Erro ao capturar vídeo.")
        break

    frame_count += 1

    # Reduz resolução
    small_frame = cv2.resize(frame, None, fx=RESIZE_SCALE, fy=RESIZE_SCALE)
    gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

    # Detecta apenas a cada FRAME_SKIP frames
    if frame_count % FRAME_SKIP == 0:
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5
        )

        eyes_detected = False

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(
                roi_gray,
                scaleFactor=1.2,
                minNeighbors=5
            )

            if len(eyes) > 0:
                eyes_detected = True
                break

    # ================= LÓGICA DE ALERTA =================
    if eyes_detected:
        closed_start = None
        alarm_active = False

    else:
        if closed_start is None:
            closed_start = time.time()

        elif time.time() - closed_start >= EYE_CLOSED_THRESHOLD:
            if not alarm_active:
                alarm_active = True
                threading.Thread(target=sirene, daemon=True).start()

            cv2.putText(
                frame,
                "ALERTA SONO!",
                (50, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 0, 255),
                3
            )

    cv2.imshow(
        f"Alerta de Sono (Camera {camera_index}) - Q para sair",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ================= FINALIZAÇÃO =================
alarm_active = False
camera.release()
cv2.destroyAllWindows()
