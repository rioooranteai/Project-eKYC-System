from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)

CLASS_NAMES = {0: "id card", 1: "photo"}

MODEL_PATH = Path("model development/models/YOLO26/best_yolo26_5c0b9964.pt")


@dataclass
class YOLOBox:
    label: str
    x: float
    y: float
    w: float
    h: float
    score: float

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "x": round(self.x, 4),
            "y": round(self.y, 4),
            "w": round(self.w, 4),
            "h": round(self.h, 4),
            "score": round(self.score, 4),
        }

    def to_pixel(self, frame_w: int, frame_h: int) -> tuple[int, int, int, int]:
        x1 = int(self.x * frame_w)
        y1 = int(self.y * frame_h)
        x2 = int((self.x + self.w) * frame_w)
        y2 = int((self.y + self.h) * frame_h)
        return x1, y1, x2, y2


class YOLOService:
    def __init(
            self,
            model_path: str | Path = MODEL_PATH,
            confidence: float = 0.5,
            device: str = "cuda"
    ) -> None:

        self.confidence = confidence
        self.device = device
        self._model: Optional[YOLO] = None
        self.last_frame: Optional[np.ndarray] = None
        self.last_box: Optional[YOLOBox] = None
        self._load(model_path)

    def _load(self, model_path: str | Path) -> None:
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model YOLO tidak ditemukan: {path}")

        logger.info("Memuat model YOLO dari %s ...", path)
        t0 = time.perf_counter()

        self._model = YOLO(str(path))
        self._model.to(self.device)

        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        self._model.predict(dummy, verbose=False)

        logger.info("YOLO aktif | %.2fs | device=%s", time.perf_counter() - t0, self.device)

    def predict(self, frame: np.ndarray) -> list[YOLOBox]:
        if self._model is None:
            raise RuntimeError("Model YOLO belum diinisialisasi.")

        h, w = frame.shape[:2]

        results = self._model.predict(
            frame,
            conf=self.confidence,
            verbose=False,
            device=self.device
        )

        boxes: list[YOLOBox] = []

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id != 0:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                score = float(box.conf[0])

                boxes.append(YOLOBox(
                    label=CLASS_NAMES.get(cls_id, str(cls_id)),
                    x=x1 / w,
                    y=y1 / h,
                    w=(x2 - x1) / w,
                    h=(y2 - y1) / h,
                    score=score,
                ))

        boxes.sort(key=lambda b: b.score, reverse=True)
        return boxes[:1]

    def crop(self, frame: np.ndarray, box: YOLOBox, padding: float = 0.02) -> np.ndarray:
        """
        Crop frame berdasarkan YOLOBox + padding kecil.
        Return cropped BGR array siap masuk PaddleOCR.
        """
        h, w = frame.shape[:2]

        x1 = max(0, int((box.x - padding) * w))
        y1 = max(0, int((box.y - padding) * h))
        x2 = min(w, int((box.x + box.w + padding) * w))
        y2 = min(h, int((box.y + box.h + padding) * h))

        cropped = frame[y1:y2, x1:x2]

        if cropped.size == 0:
            logger.warning("Crop kosong, return frame asli.")
            return frame

        return cropped

    def store_frame(self, frame: np.ndarray) -> None:
        """Simpan frame terakhir untuk dipakai saat capture."""
        self.last_frame = frame.copy()

    def store_box(self, box: Optional["YOLOBox"]) -> None:
        """Simpan box terakhir hasil YOLO predict."""
        self.last_box = box
