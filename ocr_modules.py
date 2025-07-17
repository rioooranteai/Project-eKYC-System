import numpy as np
import re
import easyocr

from PIL import Image
from paddleocr import PaddleOCR, draw_ocr

def paddle_read_license(image):
    try:
        ocr = PaddleOCR(use_angle_cls=False, lang='en', use_gpu=True)
        
        result = ocr.ocr(image, cls=True)
        
        if result and result[0]:
            for line in result[0]:
                if line and len(line) > 1:
                    text, confidence = line[1]
                    
                    cleaned_text = re.sub(r'[^0-9]', '', text)
                    
                    if re.match(r'^\d{16}$', cleaned_text):
                        logger.info(f"PaddleOCR found license: {cleaned_text} (confidence: {confidence:.2f})")
                        return cleaned_text
                        
    except Exception as e:
        logger.error(f"PaddleOCR error: {str(e)}")
    
    return None

def easyocr_read_license(image):
    try: 
        reader = easyocr.Reader(['en'], gpu=True)

        results = reader.readtext(image, allowlist='0123456789')
        
        for (bbox, text, confidence) in results:
       
            cleaned_text = re.sub(r'[^0-9]', '', text)
            
            if re.match(r'^\d{16}$', cleaned_text) and confidence > 0.5:
                logger.info(f"EasyOCR found license: {cleaned_text} (confidence: {confidence:.2f})")
                return cleaned_text
                
    except Exception as e:
        logger.error(f"EasyOCR error: {str(e)}")
    
    return None
