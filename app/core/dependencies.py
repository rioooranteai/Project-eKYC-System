import logging
from typing import Optional

from app.services.ocr_service import OCRService
from app.services.yolo_service import YOLOService
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_ocr_service: Optional[OCRService] = None
_yolo_service: Optional[YOLOService] = None


def set_services(
        ocr_scv: OCRService,
        yolo_svc: YOLOService
) -> None:
    global _ocr_service, _yolo_service

    _ocr_service = ocr_scv
    _yolo_service = yolo_svc

    logger.info("=" * 60)
    logger.info("Dependencies registered:")
    logger.info("  OCR  Service : %s", _ocr_service is not None)
    logger.info("  YOLO Service : %s", _yolo_service is not None)
    logger.info("=" * 60)


def get_ocr_service() -> OCRService:
    if _ocr_service is None:
        raise HTTPException(
            status_code=503,
            detail="OCR service not initialized. Server may still be starting up."
        )

    return _ocr_service


def get_yolo_service() -> YOLOService:
    if _yolo_service is None:
        raise HTTPException(
            status_code=503,
            detail="OCR service not initialized. Server still be starting up."
        )


def cleanup_service() -> None:
    global _ocr_service, _yolo_service

    logger.info("Membersihkan semua service...")
    _ocr_service = None
    _yolo_service = None
    logger.info("Semua service dibersihkan.")


def is_initialized() -> bool:
    return all([
        _ocr_service is not None,
        _yolo_service is not None,
    ])
