from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as webrtc_router, get_webrtc_service
from core.dependencies import set_services, cleanup_services, is_initialized
from services.ocr_service import OCRService
from services.yolo_service import YOLOService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

MODEL_PATH = "model development/models/YOLO26/best_yolo26_5c0b9964.pt"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Veriface eKYC System starting...")
    logger.info("=" * 60)

    # Load semua service saat startup
    yolo_service = YOLOService(model_path=MODEL_PATH, device="cuda")
    ocr_service = OCRService(min_confidence=0.65)

    set_services(ocr_scv=ocr_service, yolo_scv=yolo_service)

    logger.info("Semua service siap. Server online.")
    logger.info("=" * 60)

    yield

    # Cleanup saat shutdown
    logger.info("Server shutting down...")
    await get_webrtc_service().close_all()
    cleanup_services()
    logger.info("Shutdown selesai.")


app = FastAPI(
    title="Veriface eKYC API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webrtc_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "initialized": is_initialized(),
    }
