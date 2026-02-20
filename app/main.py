from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import get_webrtc_service, router as webrtc_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting...")
    yield
    logger.info("Server shutting down — menutup semua peer connection...")
    await get_webrtc_service().close_all()


app = FastAPI(title="WebRTC + FastAPI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ganti dengan domain FE di production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webrtc_router)


@app.get("/health")
def health():
    return {"status": "ok"}