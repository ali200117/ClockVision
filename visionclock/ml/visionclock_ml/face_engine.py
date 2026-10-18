from dataclasses import dataclass

import cv2
import numpy as np

from . import config


@dataclass(frozen=True)
class Face:
    box: tuple[int, int, int, int]  # x, y, bredde, høyde
    score: float
    raw: np.ndarray  # raden fra detektoren: boks, 5 landemerker, score


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(normalize(a), normalize(b)))


class FaceEngine:
    """Detekterer ansikter (YuNet) og lager embeddings (SFace)."""

    def __init__(self) -> None:
        for model in (config.DETECTOR_MODEL, config.RECOGNIZER_MODEL):
            if not model.exists():
                raise FileNotFoundError(f"Mangler modellfil: {model}")
        self._detector = cv2.FaceDetectorYN.create(
            str(config.DETECTOR_MODEL), "", (320, 320),
            config.DETECTOR_SCORE_THRESHOLD, 0.3, 5000,
        )
        self._recognizer = cv2.FaceRecognizerSF.create(str(config.RECOGNIZER_MODEL), "")

    def detect(self, frame: np.ndarray) -> list[Face]:
        """Alle ansikter i bildet, største først."""
        height, width = frame.shape[:2]
        self._detector.setInputSize((width, height))
        _, rows = self._detector.detect(frame)
        if rows is None:
            return []
        faces = [
            Face(box=tuple(int(v) for v in row[:4]), score=float(row[14]), raw=row)
            for row in rows
        ]
        return sorted(faces, key=lambda f: f.box[2] * f.box[3], reverse=True)

    def embed(self, frame: np.ndarray, face: Face) -> np.ndarray:
        """Embedding med lengde 1 (128 tall) for ett ansikt."""
        aligned = self._recognizer.alignCrop(frame, face.raw)
        feature = self._recognizer.feature(aligned)
        return normalize(np.asarray(feature, dtype=np.float32).flatten())
