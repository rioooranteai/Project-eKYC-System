import logging
from typing import Optional

from fastapi import HTTPException
from app.services.ocr_service import OCRService

logger = logging.getLogger(__name__)

_ocr_service: Optional[OCRService] = None


def set_services(
        ocr_scv: OCRService
) -> None:
    global _ocr_service

    _ocr_service = ocr_scv

    logger.info("=" * 60)
    logger.info("Dependencies registered:")
    logger.info(f"OCR Service: {_ocr_service is not None}")
    logger.info("=" * 60)


def get_ocr_service() -> OCRService:
    if _ocr_service is None:
        raise HTTPException(
            status_code=503,
            detail="OCR service not initialized. Server may still be starting up."
        )

    return _ocr_service


def cleanup_service() -> None:
    global _ocr_service

    logger.info("Cleaning up services...")

    _ocr_service = None

    logger.info("Services cleaned up")


def is_initialized() -> bool:
    return all([
        _ocr_service is not None
    ])
