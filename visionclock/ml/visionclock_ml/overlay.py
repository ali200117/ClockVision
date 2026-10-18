import cv2

GREEN = (0, 200, 0)
RED = (0, 0, 220)
YELLOW = (0, 200, 220)


def draw_face(frame, face, label: str, color) -> None:
    x, y, w, h = face.box
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    cv2.putText(frame, label, (x, max(y - 8, 18)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def draw_status(frame, text: str, color=YELLOW, line: int = 0) -> None:
    cv2.putText(frame, text, (10, 25 + 25 * line), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
