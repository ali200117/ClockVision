"""Registrerer en ansatts ansikt: tar flere bilder og lagrer snittet av embeddingene."""
import argparse
import sys

import cv2
import numpy as np

from visionclock_ml import api_client, camera, config, store
from visionclock_ml.face_engine import FaceEngine, cosine_similarity
from visionclock_ml.overlay import GREEN, RED, draw_face, draw_status

WINDOW = "VisionClock - registrer"


def resolve_name(employee_id: int, name: str | None) -> str:
    if name:
        return name
    employee = api_client.get_employee(employee_id)
    return f"{employee['firstName']} {employee['lastName']}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--employee-id", type=int, help="id fra backend")
    target.add_argument("--other", metavar="NAVN",
                        help="registrer en ikke-ansatt som ligner en ansatt (f.eks. en bror). "
                             "Personen får aldri stemple, men tar treffet fra de ansatte.")
    parser.add_argument("--photos", type=int, default=8, help="antall bilder som tas")
    parser.add_argument("--name", help="hopp over backend-sjekk og bruk dette navnet")
    args = parser.parse_args()

    if args.other:
        name = args.other
        print(f"Registrerer {name} som ikke-ansatt. SPACE = ta bilde, q = avbryt.")
    else:
        try:
            name = resolve_name(args.employee_id, args.name)
        except api_client.BackendError as error:
            print(f"Kunne ikke hente ansatt {args.employee_id}: {error}")
            print("Start backend, eller bruk --name for å registrere uten backend.")
            return 1
        print(f"Registrerer {name} (id {args.employee_id}). SPACE = ta bilde, q = avbryt.")
    print("Tips: vri hodet litt mellom bildene, og varier avstand og lys.")

    engine = FaceEngine()
    capture = camera.open_camera()
    embeddings: list[np.ndarray] = []

    try:
        while len(embeddings) < args.photos:
            frame = camera.read_frame(capture)
            faces = engine.detect(frame)
            one_face = len(faces) == 1

            display = frame.copy()
            for face in faces:
                draw_face(display, face, "", GREEN if one_face else RED)
            draw_status(display, f"Bilder: {len(embeddings)}/{args.photos}   SPACE = ta bilde, q = avbryt")
            if not one_face:
                draw_status(display, "Trenger noyaktig ett ansikt i bildet", RED, line=1)
            cv2.imshow(WINDOW, display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Avbrutt. Ingenting er lagret.")
                return 1
            if key == 32 and one_face:
                embeddings.append(engine.embed(frame, faces[0]))
                print(f"Tok bilde {len(embeddings)}/{args.photos}")
    finally:
        capture.release()
        cv2.destroyAllWindows()

    mean = np.mean(embeddings, axis=0)
    lowest = min(cosine_similarity(e, mean) for e in embeddings)
    if lowest < config.MATCH_THRESHOLD:
        print(f"Advarsel: ett bilde ligner lite på de andre (likhet {lowest:.2f}). Vurder å registrere på nytt.")

    if args.other:
        store.save_other(name, embeddings)
    else:
        store.save_employee(args.employee_id, name, embeddings)
    print(f"Lagret {name} i {config.EMBEDDINGS_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
