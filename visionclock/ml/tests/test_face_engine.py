import numpy as np
import pytest

from visionclock_ml import config
from visionclock_ml.face_engine import Face, FaceEngine, cosine_similarity

pytestmark = pytest.mark.skipif(
    not config.DETECTOR_MODEL.exists() or not config.RECOGNIZER_MODEL.exists(),
    reason="modellfilene ligger ikke i ml/models",
)


def test_detect_finds_no_face_in_noise():
    engine = FaceEngine()
    noise = np.random.default_rng(0).integers(0, 255, (480, 640, 3), dtype=np.uint8)

    assert engine.detect(noise) == []


def test_embedding_has_128_values_and_unit_length():
    engine = FaceEngine()
    image = np.random.default_rng(1).integers(0, 255, (480, 640, 3), dtype=np.uint8)
    row = np.array([200, 100, 150, 180, 240, 160, 300, 160, 270, 200, 245, 240, 295, 240, 0.99],
                   dtype=np.float32)

    embedding = engine.embed(image, Face((200, 100, 150, 180), 0.99, row))

    assert embedding.shape == (128,)
    assert abs(float(np.linalg.norm(embedding)) - 1.0) < 1e-5
    assert cosine_similarity(embedding, embedding) == pytest.approx(1.0, abs=1e-5)
