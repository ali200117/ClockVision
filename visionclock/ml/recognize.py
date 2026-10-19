"""Kjenner igjen ansikter fra kameraet og stempler ansatte via Java-backend.

Flyt: ansiktet gjenkjennes -> tilfeldig hodeutfordring (liveness) -> samme person bekreftes -> stempling.
"""
import argparse
import sys
import time

import cv2

from visionclock_ml import api_client, camera, config, liveness, store
from visionclock_ml.face_engine import FaceEngine
from visionclock_ml.liveness import LivenessChallenge, Status
from visionclock_ml.overlay import BLACK, GREEN, RED, draw_face, draw_status

WINDOW = "VisionClock - gjenkjenning"
RETRY_AFTER_FAILURE_SECONDS = 5
MESSAGE_SECONDS = 4
FACE_LOST_SECONDS = 1.5
CALIBRATION_TIMEOUT_SECONDS = 8.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=float, default=config.MATCH_THRESHOLD)
    parser.add_argument("--cooldown", type=float, default=config.COOLDOWN_SECONDS)
    parser.add_argument("--confirm-frames", type=int, default=config.CONFIRM_FRAMES)
    parser.add_argument("--identity-floor", type=float, default=config.LIVENESS_IDENTITY_FLOOR,
                        help="laveste likhet under utfordringen, mens hodet er snudd")
    parser.add_argument("--steps", type=int, default=config.LIVENESS_STEPS,
                        help="antall hodebevegelser i utfordringen")
    parser.add_argument("--step-timeout", type=float, default=config.LIVENESS_STEP_TIMEOUT,
                        help="sekunder per hodebevegelse")
    parser.add_argument("--no-liveness", action="store_true", help="hopp over utfordringen")
    parser.add_argument("--debug-pose", action="store_true", help="vis hodestilling på skjermen")
    parser.add_argument("--dry-run", action="store_true", help="ikke kall backend, bare vis treff")
    args = parser.parse_args()

    registered = store.load()
    if not registered:
        print("Ingen registrerte ansikter. Kjør register.py først.")
        return 1
    employees = sum(1 for person in registered if person.employee_id is not None)
    print(f"{employees} ansatt(e) og {len(registered) - employees} distraktor(er). "
          f"Terskel {args.threshold}. q = avslutt.")

    engine = FaceEngine()
    capture = camera.open_camera()

    candidate: int | None = None
    streak = 0
    next_allowed: dict[int, float] = {}
    message = ""
    message_until = 0.0

    challenge: LivenessChallenge | None = None
    owner_id: int | None = None
    owner_name = ""
    last_face_seen = 0.0
    challenge_started = 0.0

    def show(text: str, now: float) -> None:
        nonlocal message, message_until
        message = text
        message_until = now + MESSAGE_SECONDS
        print(text)

    def stamp(employee_id: int, name: str, now: float) -> None:
        if args.dry_run:
            next_allowed[employee_id] = now + args.cooldown
            show(f"{name}: bestatt (dry-run)", now)
            return
        try:
            result = api_client.clock(employee_id)
            next_allowed[employee_id] = now + args.cooldown
            show(f"{name}: {result['type']}", now)
        except api_client.BackendError as error:
            next_allowed[employee_id] = now + RETRY_AFTER_FAILURE_SECONDS
            show("Feil mot backend, se terminal", now)
            print(error)

    try:
        while True:
            frame = camera.read_frame(capture)
            faces = engine.detect(frame)
            now = time.monotonic()
            display = frame.copy()

            face = faces[0] if faces else None
            match = store.best_match(engine.embed(frame, face), registered) if face else None
            strong = match is not None and match.score >= args.threshold
            recognized = strong and match.is_employee

            if face is not None:
                if recognized:
                    draw_face(display, face, f"{match.name} {match.score:.2f}", GREEN)
                elif strong:
                    draw_face(display, face, f"avvist: ligner {match.name} {match.score:.2f}", RED)
                else:
                    score = f" {match.score:.2f}" if match else ""
                    draw_face(display, face, f"ukjent{score}", RED)

            if challenge is not None:
                failure = None
                pose = None
                if face is None:
                    if now - last_face_seen > FACE_LOST_SECONDS:
                        failure = "Mistet ansiktet under utfordringen"
                else:
                    last_face_seen = now
                    pose = liveness.head_pose(face.raw, config.LIVENESS_MIRROR)
                    if match is None or match.employee_id != owner_id or match.score < args.identity_floor:
                        failure = "Ikke samme person under utfordringen"

                status = challenge.update(pose, now) if failure is None else Status.FAILED
                if status is Status.FAILED and failure is None:
                    failure = "Tidsfristen gikk ut"
                elif failure is None and status is Status.CALIBRATING \
                        and now - challenge_started > CALIBRATION_TIMEOUT_SECONDS:
                    failure = "Hodet var ikke i ro, prov igjen"

                if failure is not None:
                    next_allowed[owner_id] = now + RETRY_AFTER_FAILURE_SECONDS
                    show(failure, now)
                    challenge = None
                elif status is Status.PASSED:
                    if recognized and match.employee_id == owner_id:
                        stamp(owner_id, owner_name, now)
                    else:
                        next_allowed[owner_id] = now + RETRY_AFTER_FAILURE_SECONDS
                        show("Identitet ikke bekreftet etter utfordringen", now)
                    challenge = None
                else:
                    draw_status(display, f"{challenge.prompt()}  ({challenge.seconds_left(now):.0f}s)", BLACK)
                    if args.debug_pose and challenge.last_delta:
                        d_yaw, d_pitch = challenge.last_delta
                        draw_status(display, f"yaw {d_yaw:+.2f}  pitch {d_pitch:+.2f}", BLACK, line=1)
                    cv2.imshow(WINDOW, display)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                    continue

            if recognized:
                streak = streak + 1 if candidate == match.employee_id else 1
                candidate = match.employee_id
            else:
                candidate, streak = None, 0

            if recognized and streak >= args.confirm_frames and now >= next_allowed.get(candidate, 0.0):
                streak = 0
                if args.no_liveness:
                    stamp(candidate, match.name, now)
                else:
                    challenge = LivenessChallenge.random(
                        args.steps,
                        step_timeout=args.step_timeout,
                        yaw_delta=config.LIVENESS_YAW_DELTA,
                        pitch_delta=config.LIVENESS_PITCH_DELTA,
                    )
                    owner_id, owner_name = candidate, match.name
                    last_face_seen = challenge_started = now
                    print(f"Utfordring for {owner_name}: "
                          + ", ".join(step.value for step in challenge.steps))

            if now < message_until:
                draw_status(display, message, BLACK)
            else:
                draw_status(display, "q = avslutt", BLACK)

            cv2.imshow(WINDOW, display)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
