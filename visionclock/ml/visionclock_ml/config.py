import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"

DETECTOR_MODEL = MODELS_DIR / "face_detection_yunet_2023mar.onnx"
RECOGNIZER_MODEL = MODELS_DIR / "face_recognition_sface_2021dec.onnx"

EMBEDDINGS_FILE = DATA_DIR / "embeddings.json"
EVAL_DIR = DATA_DIR / "eval"

BACKEND_URL = os.getenv("VISIONCLOCK_URL", "http://localhost:8080")
CAMERA_INDEX = int(os.getenv("VISIONCLOCK_CAMERA", "0"))

DETECTOR_SCORE_THRESHOLD = 0.8

# Cosinus-likhet. SFace anbefaler 0.363. Høyere verdi gir strengere gjenkjenning.
MATCH_THRESHOLD = 0.363

# Liveness: tilfeldig hodebevegelse etter at ansiktet er gjenkjent.
LIVENESS_STEPS = 2
LIVENESS_STEP_TIMEOUT = 6.0
# Lavere enn MATCH_THRESHOLD fordi likheten faller når hodet er snudd.
LIVENESS_IDENTITY_FLOOR = 0.30
LIVENESS_YAW_DELTA = 0.20
LIVENESS_PITCH_DELTA = 0.12
# Sett til 1 hvis kameraet speilvender bildet og "venstre" føles omvendt.
LIVENESS_MIRROR = os.getenv("VISIONCLOCK_MIRROR", "0") == "1"

# Antall bilder på rad med samme treff før vi stempler.
CONFIRM_FRAMES = 5
COOLDOWN_SECONDS = 30
