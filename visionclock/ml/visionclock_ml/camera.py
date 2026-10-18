import cv2

from . import config


def open_camera(index: int = config.CAMERA_INDEX) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not capture.isOpened():
        raise RuntimeError(
            f"Fant ikke kameraet med indeks {index}. "
            "Sjekk at ingen andre programmer bruker det, eller sett VISIONCLOCK_CAMERA."
        )
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return capture


def read_frame(capture: cv2.VideoCapture):
    ok, frame = capture.read()
    if not ok:
        raise RuntimeError("Kunne ikke lese bilde fra kameraet.")
    return frame
