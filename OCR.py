import numpy as np
import re
from PIL import Image
from paddleocr import PaddleOCR, draw_ocr

def paddle_read_license(image):
    ocr = PaddleOCR(use_angle_cls=False, lang='en', use_gpu=True)

    try:
        result = ocr.ocr(image, cls=True)

        for line in result:

            for word in line:
                text, confidence = word[1]

                if re.match(r'^\d{16}$', text):
                   return text
    except:
        return "Error"