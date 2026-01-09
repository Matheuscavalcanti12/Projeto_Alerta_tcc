import cv2
import time
import winsound
import threading

# ================== CONTROLE DA SIRENE ==================
alarm_active = False

def sirene_continua():
    global alarm_active
    while alarm_active:
        winsound.Beep(1800, 200)
        winsound.Beep(2200, 200)

# ================== CLASSIFICADORES ==================
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
eye_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml"
)

# ================== SELEÇÃO AUTOMÁTICA DE CÂMERA ==================
camera = None
camera_index = None

for i in [1, 0]:  # tenta externa primeiro, depois interna
    cam = cv2.VideoCapture(i)
    if cam.isOpened():
        camera = cam
        camera_index = i
        print(f"Câmera ativa: índice {i}")
        break

if camera is None:
    print("Nenhuma câmera encontrada.")
    exit()

# ================== CONTROLE DE OLHOS ==================
closed_start = None
EYE_CLOSED_THRESHOLD = 3  # segundos
flash = False

# ================== LOOP PRINCIPAL ==================
while True:
    ret, frame = camera.read()

    if not ret:
        print("Erro ao capturar vídeo.")
        break

    frame_display = frame.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5
    )

    eyes_detected = False

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        eyes = eye_cascade.detectMultiScale(
            roi_gray, scaleFactor=1.1, minNeighbors=4
        )

        if len(eyes) > 0:
            eyes_detected = True

    # ================== LÓGICA DE ALERTA ==================
    if eyes_detected:
        closed_start = None
        if alarm_active:
            alarm_active = False

    else:
        if closed_start is None:
            closed_start = time.time()
        else:
            elapsed = time.time() - closed_start

            if elapsed >= EYE_CLOSED_THRESHOLD:

                if not alarm_active:
                    alarm_active = True
                    threading.Thread(
                        target=sirene_continua, daemon=True
                    ).start()

                flash = not flash
                if flash:
                    red_frame = frame.copy()
                    red_frame[:] = (0, 0, 255)
                    frame_display = cv2.addWeighted(
                        frame, 0.3, red_frame, 0.7, 0
                    )

                cv2.putText(
                    frame_display,
                    "OLHOS FECHADOS! ALERTA!!!",
                    (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.4,
                    (0, 0, 255),
                    4
                )

    # ================== EXIBIÇÃO ==================
    cv2.imshow(
        f"Monitoramento dos Olhos (Camera {camera_index}) - Q para sair",
        frame_display
    )

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ================== FINALIZAÇÃO ==================
alarm_active = False
camera.release()
cv2.destroyAllWindows()
