"""Liveness: tilfeldig utfordring med hodebevegelse, målt ut fra YuNets fem landemerker.

Hodestillingen er et forhold mellom landemerkene, ikke en vinkel i grader. Utfordringen måler
endring fra en baseline tatt når personen ser rett frem.

Retninger er fra brukerens egen side. Når brukeren snur hodet til sin venstre side, flytter
nesen seg mot høyre i det ikke-speilvendte kamerabildet, og yaw blir positiv.
"""
import math
import random
from dataclasses import dataclass
from enum import Enum

import numpy as np


class Direction(Enum):
    LEFT = "venstre"
    RIGHT = "hoyre"
    UP = "opp"
    DOWN = "ned"


PROMPTS = {
    Direction.LEFT: "Snu hodet til VENSTRE (din venstre)",
    Direction.RIGHT: "Snu hodet til HOYRE (din hoyre)",
    Direction.UP: "Se OPP",
    Direction.DOWN: "Se NED",
}


class Status(Enum):
    CALIBRATING = "kalibrerer"
    WAITING = "venter"
    RETURNING = "tilbake"
    PASSED = "bestatt"
    FAILED = "feilet"


@dataclass(frozen=True)
class HeadPose:
    yaw: float    # positiv = nesen mot høyre i bildet (brukerens venstre)
    pitch: float  # lavere = nesen nærmere øynene (ser opp), høyere = ser ned


def head_pose(raw: np.ndarray, mirror: bool = False) -> HeadPose | None:
    """Hodestilling fra raden fra YuNet: boks, 5 landemerker (øyne, nese, munnvik), score."""
    right_eye, left_eye = raw[4:6], raw[6:8]
    nose = raw[8:10]
    mouth = (raw[10:12] + raw[12:14]) / 2

    eye_mid = (right_eye + left_eye) / 2
    eye_distance = math.dist(right_eye, left_eye)
    face_height = float(mouth[1] - eye_mid[1])
    if eye_distance <= 0 or face_height <= 0:
        return None

    yaw = float(nose[0] - eye_mid[0]) / eye_distance
    pitch = float(nose[1] - eye_mid[1]) / face_height
    return HeadPose(-yaw if mirror else yaw, pitch)


class LivenessChallenge:
    """Tilfeldig rekkefølge av hodebevegelser. Hver må gjøres innen tidsfristen, med retur til midten imellom."""

    def __init__(self, steps: list[Direction], *, step_timeout: float = 6.0,
                 calibration_frames: int = 5, yaw_delta: float = 0.20,
                 pitch_delta: float = 0.12, return_yaw: float = 0.10,
                 return_pitch: float = 0.06, max_calibration_spread: float = 0.08) -> None:
        if not steps:
            raise ValueError("Trenger minst ett steg.")
        self.steps = steps
        self.step_timeout = step_timeout
        self.calibration_frames = calibration_frames
        self.yaw_delta = yaw_delta
        self.pitch_delta = pitch_delta
        self.return_yaw = return_yaw
        self.return_pitch = return_pitch
        self.max_calibration_spread = max_calibration_spread

        self.status = Status.CALIBRATING
        self.index = 0
        self._baseline: HeadPose | None = None
        self._calibration: list[HeadPose] = []
        self._deadline = 0.0
        self.last_delta: tuple[float, float] | None = None

    @classmethod
    def random(cls, count: int, rng: random.Random | None = None, **settings) -> "LivenessChallenge":
        """Tilfeldige retninger uten at samme retning kommer to ganger på rad."""
        rng = rng or random.SystemRandom()
        steps: list[Direction] = []
        for _ in range(count):
            options = [d for d in Direction if not steps or d != steps[-1]]
            steps.append(rng.choice(options))
        return cls(steps, **settings)

    @property
    def current(self) -> Direction | None:
        if self.status in (Status.WAITING, Status.RETURNING) and self.index < len(self.steps):
            return self.steps[self.index]
        return None

    def prompt(self) -> str:
        if self.status is Status.CALIBRATING:
            return "Se rett frem"
        if self.status is Status.WAITING:
            return f"{self.index + 1}/{len(self.steps)}: {PROMPTS[self.steps[self.index]]}"
        if self.status is Status.RETURNING:
            return "Tilbake til midten"
        return self.status.value

    def seconds_left(self, now: float) -> float:
        return max(0.0, self._deadline - now)

    def update(self, pose: HeadPose | None, now: float) -> Status:
        if self.status in (Status.PASSED, Status.FAILED):
            return self.status

        if self.status is Status.CALIBRATING:
            self._calibrate(pose, now)
            return self.status

        if now > self._deadline:
            self.status = Status.FAILED
            return self.status
        if pose is None:
            return self.status

        delta_yaw = pose.yaw - self._baseline.yaw
        delta_pitch = pose.pitch - self._baseline.pitch
        self.last_delta = (delta_yaw, delta_pitch)

        if self.status is Status.WAITING:
            if self._reached(self.steps[self.index], delta_yaw, delta_pitch):
                self.status = Status.RETURNING
                self._deadline = now + self.step_timeout
        elif abs(delta_yaw) < self.return_yaw and abs(delta_pitch) < self.return_pitch:
            self.index += 1
            if self.index >= len(self.steps):
                self.status = Status.PASSED
            else:
                self.status = Status.WAITING
                self._deadline = now + self.step_timeout
        return self.status

    def _calibrate(self, pose: HeadPose | None, now: float) -> None:
        if pose is None:
            self._calibration.clear()
            return
        self._calibration.append(pose)
        if len(self._calibration) < self.calibration_frames:
            return

        yaws = [p.yaw for p in self._calibration]
        pitches = [p.pitch for p in self._calibration]
        if max(yaws) - min(yaws) > self.max_calibration_spread or \
                max(pitches) - min(pitches) > self.max_calibration_spread:
            self._calibration.clear()
            return
        self._baseline = HeadPose(float(np.mean(yaws)), float(np.mean(pitches)))
        self.status = Status.WAITING
        self._deadline = now + self.step_timeout

    def _reached(self, direction: Direction, delta_yaw: float, delta_pitch: float) -> bool:
        if direction is Direction.LEFT:
            return delta_yaw >= self.yaw_delta
        if direction is Direction.RIGHT:
            return delta_yaw <= -self.yaw_delta
        if direction is Direction.UP:
            return delta_pitch <= -self.pitch_delta
        return delta_pitch >= self.pitch_delta
