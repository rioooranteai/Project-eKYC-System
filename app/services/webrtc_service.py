from __future__ import annotations

import asyncio
import logging
from typing import Callable

import numpy as np
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole
from av import VideoFrame

logger = logging.getLogger(__name__)


class VideoFrameTrack(MediaStreamTrack):
    """
    Wrapper track yang intercept setiap frame video masuk,
    lalu trigger callback ke layer atas (router).
    """

    kind = "video"

    def __init__(
            self,
            track: MediaStreamTrack,
            on_frame: Callable[[np.ndarray], None],
    ) -> None:
        super().__init__()
        self._track = track
        self._on_frame = on_frame

    async def recv(self) -> VideoFrame:
        frame = await self._track.recv()

        img = frame.to_ndarray(format="bgr24")
        self._on_frame(img)

        return frame


class WebRTCService:

    def __init__(self) -> None:
        self._peer_connections: set[RTCPeerConnection] = set()

    async def handle_offer(
            self,
            sdp: str,
            type_: str,
            on_frame: Callable[[np.ndarray], None],
    ) -> dict:
        """
        Terima SDP offer dari FE, buat answer, dan setup pipeline frame.

        Args:
            sdp:      SDP string dari browser.
            type_:    Tipe SDP ("offer").
            on_frame: Callback dipanggil setiap frame diterima.

        Returns:
            Dict berisi sdp dan type answer untuk dikirim balik ke FE.
        """
        pc = RTCPeerConnection()
        self._peer_connections.add(pc)

        sink = MediaBlackhole()

        @pc.on("track")
        async def on_track(track: MediaStreamTrack) -> None:
            if track.kind != "video":
                await sink.addTrack(track)
                return

            wrapped = VideoFrameTrack(track, on_frame)
            await sink.addTrack(wrapped)
            logger.info("Video track diterima dari peer.")

        @pc.on("connectionstatechange")
        async def on_state() -> None:
            logger.info("WebRTC state: %s", pc.connectionState)
            if pc.connectionState in ("failed", "closed", "disconnected"):
                await self._cleanup(pc)

        await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type=type_))
        await sink.start()

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type,
        }

    async def _cleanup(self, pc: RTCPeerConnection) -> None:
        await pc.close()
        self._peer_connections.discard(pc)
        logger.info("Peer connection ditutup dan dibersihkan.")

    async def close_all(self) -> None:
        """Tutup semua peer connection — dipanggil saat shutdown."""
        await asyncio.gather(*[pc.close() for pc in self._peer_connections])
        self._peer_connections.clear()
