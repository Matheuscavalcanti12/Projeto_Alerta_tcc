import cv2
import time
import winsound
import threading

# --- SIRENE CONTÍNUA (RODA EM THREAD PARA NÃO TRAVAR) ---
alarm_active = False

def sirene_continua():
    global alarm_active
    while alarm_active:
        winsound.Beep(1800, 200)
        winsound.Beep(2200, 200)

# Classificadores
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Não foi possível acessar a câmera.")
    exit()

closed_start = None
EYE_CLOSED_THRESHOLD = 3  # segundos
flash = False  # controle da tela piscando

while True:
    ret, frame = camera.read()

    # Se der erro, mostra um frame preto pra não crashar
    frame_display = frame.copy() if ret else None

    if not ret:
        print("Erro ao capturar vídeo.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    eyes_detected = False

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=4)

        if len(eyes) > 0:
            eyes_detected = True

    if eyes_detected:
        closed_start = None
        if alarm_active:
            alarm_active = False
        frame_display = frame.copy()

    else:
        if closed_start is None:
            closed_start = time.time()
        else:
            elapsed = time.time() - closed_start

            if elapsed >= EYE_CLOSED_THRESHOLD:

                # Ativa sirene
                if not alarm_active:
                    alarm_active = True
                    threading.Thread(target=sirene_continua, daemon=True).start()

                # Pisca a tela em vermelho
                flash = not flash
                if flash:
                    frame_display = cv2.addWeighted(frame, 0.3,
                                                    (frame*0 + [0, 0, 255]).astype('uint8'),
                                                    0.7, 0)
                else:
                    frame_display = frame.copy()

                cv2.putText(frame_display, "OLHOS FECHADOS! ALERTA!!!",
                            (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 4)
            else:
                frame_display = frame.copy()

    cv2.imshow("Monitoramento dos Olhos - Q para sair", frame_display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

alarm_active = False
camera.release()
cv2.destroyAllWindows()
