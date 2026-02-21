from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

import numpy as np
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.dependencies import get_ocr_service
from app.services.webrtc_service import WebRTCService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webrtc", tags=["WebRTC"])


_webrtc_service: Optional[WebRTCService] = None

def get_webrtc_service() -> WebRTCService:
    global _webrtc_service
    if _webrtc_service is None:
        _webrtc_service = WebRTCService()
    return _webrtc_service


class ConnectionManager:
    """Kelola semua WebSocket aktif untuk broadcast notifikasi."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.info("WebSocket terhubung. Total: %d", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.remove(ws)
        logger.info("WebSocket terputus. Total: %d", len(self._connections))

    async def send(self, ws: WebSocket, message: dict) -> None:
        await ws.send_json(message)

    async def broadcast(self, message: dict) -> None:
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


# ─── Schema ───────────────────────────────────────────────────────────────────

class OfferRequest(BaseModel):
    sdp:  str
    type: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/offer")
async def offer(payload: OfferRequest) -> dict:
    """
    Terima SDP offer dari browser, return SDP answer.
    Setiap frame yang masuk akan broadcast notifikasi via WebSocket.
    """
    service     = get_webrtc_service()
    frame_count = 0

    def on_frame(frame_ndarray) -> None:
        nonlocal frame_count
        frame_count += 1

        import asyncio
        asyncio.ensure_future(
            manager.broadcast({
                "event":       "frame_received",
                "frame_index": frame_count,
                "message":     f"Frame #{frame_count} berhasil ditangkap oleh server.",
            })
        )

    try:
        answer = await service.handle_offer(
            sdp=payload.sdp,
            type_=payload.type,
            on_frame=on_frame,
        )
        return answer

    except Exception as e:
        logger.error("Gagal handle offer: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/notify")
async def notify(ws: WebSocket) -> None:
    """
    WebSocket endpoint untuk FE subscribe notifikasi frame.
    FE connect ke sini sebelum memulai WebRTC offer.
    """
    await manager.connect(ws)
    try:
        await ws.send_json({"event": "connected", "message": "Siap menerima notifikasi."})
        while True:
            await ws.receive_text()  # keep-alive, terima ping dari FE
    except WebSocketDisconnect:
        manager.disconnect(ws)