import cv2
import numpy as np
import os
import datetime
from ultralytics import YOLO
from OCR import paddle_read_license

yolo = YOLO('best (1).pt')

capture = cv2.VideoCapture(0)
capture.set(3, 1920)
capture.set(4, 720)

def getColours(cls_num):
    base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    color_index = cls_num % len(base_colors)
    increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
    color = [base_colors[color_index][i] + increments[color_index][i] *
    (cls_num // len(base_colors)) % 256 for i in range(3)]
    return tuple(color)

if not os.path.exists("Foto"):
    os.makedirs("Foto")

while True:
    ret, frame = capture.read()
    if not ret:
        continue

    results = yolo.track(frame, stream=True)

    for result in results:

        class_names = result.names

        for box in result.boxes:

            if box.conf[0] >= 0.9:

                [x1, y1, x2, y2] = box.xyxy[0]

                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                cls = int(box.cls[0])

                class_name = class_names[cls]

                colour = getColours(cls)

                id_card_crop = frame[y1:y2, x1:x2]

                id_card_crop_gray = cv2.cvtColor(id_card_crop, cv2.COLOR_BGR2GRAY)

                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"Foto/id_card_{timestamp}.png"

                cv2.imwrite(filename, id_card_crop_gray)

                nik = paddle_read_license(id_card_crop_gray)

                cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)


                cv2.putText(frame, f'NIK-{nik} {box.conf[0]:.2f}', (x1, y1),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, colour, 2)


        cv2.imshow('frame', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

capture.release()
cv2.destroyAllWindows()