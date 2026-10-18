"""Tar testbilder av en person til evalueringen (data/eval/<navn>/)."""
import argparse
import sys

import cv2

from visionclock_ml import camera, config
from visionclock_ml.face_engine import FaceEngine
from visionclock_ml.overlay import GREEN, RED, draw_face, draw_status

WINDOW = "VisionClock - ta testbilder"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--person", required=True, help="mappenavn, f.eks. ali eller venn1")
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()

    folder = config.EVAL_DIR / args.person
    folder.mkdir(parents=True, exist_ok=True)
    saved = len(list(folder.glob("*.jpg")))
    target = saved + args.count
    print(f"Lagrer i {folder}. SPACE = ta bilde, q = ferdig.")

    engine = FaceEngine()
    capture = camera.open_camera()
    try:
        while saved < target:
            frame = camera.read_frame(capture)
            faces = engine.detect(frame)
            one_face = len(faces) == 1

            display = frame.copy()
            for face in faces:
                draw_face(display, face, "", GREEN if one_face else RED)
            draw_status(display, f"{args.person}: {saved}/{target}   SPACE = ta bilde, q = ferdig")
            cv2.imshow(WINDOW, display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == 32 and one_face:
                saved += 1
                cv2.imwrite(str(folder / f"{saved:03d}.jpg"), frame)
                print(f"Lagret bilde {saved}")
    finally:
        capture.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
