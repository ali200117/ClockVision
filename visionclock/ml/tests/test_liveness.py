import random

import numpy as np

from visionclock_ml.liveness import (
    Direction,
    HeadPose,
    LivenessChallenge,
    Status,
    head_pose,
)

FRONT = HeadPose(yaw=0.0, pitch=0.60)


def landmarks(nose_x_offset: float = 0.0, nose_y: float = 160.0) -> np.ndarray:
    """YuNet-rad: boks, høyre øye, venstre øye, nese, høyre munnvik, venstre munnvik, score."""
    row = np.zeros(15, dtype=np.float32)
    row[4:6] = (100, 100)
    row[6:8] = (160, 100)
    row[8:10] = (130 + nose_x_offset, nose_y)
    row[10:12] = (110, 190)
    row[12:14] = (150, 190)
    row[14] = 0.99
    return row


def pose(yaw: float, pitch: float = 0.60) -> HeadPose:
    return HeadPose(yaw, pitch)


def calibrated(steps, **settings) -> LivenessChallenge:
    challenge = LivenessChallenge(steps, calibration_frames=3, **settings)
    for i in range(3):
        challenge.update(FRONT, now=float(i) * 0.1)
    assert challenge.status is Status.WAITING
    return challenge


def test_head_pose_is_neutral_for_frontal_face():
    result = head_pose(landmarks(nose_x_offset=0, nose_y=160))
    assert abs(result.yaw) < 1e-6


def test_nose_to_the_right_gives_positive_yaw():
    assert head_pose(landmarks(nose_x_offset=20)).yaw > 0.3
    assert head_pose(landmarks(nose_x_offset=-20)).yaw < -0.3


def test_mirror_flips_yaw_sign():
    normal = head_pose(landmarks(nose_x_offset=20))
    mirrored = head_pose(landmarks(nose_x_offset=20), mirror=True)
    assert mirrored.yaw == -normal.yaw


def test_nose_closer_to_eyes_means_looking_up():
    assert head_pose(landmarks(nose_y=140)).pitch < head_pose(landmarks(nose_y=165)).pitch


def rotate(row: np.ndarray, degrees: float, center=(130.0, 140.0)) -> np.ndarray:
    """Roterer alle landemerkene, som et bilde som vippes sidelengs."""
    angle = np.radians(degrees)
    matrix = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    rotated = row.copy()
    for i in range(4, 14, 2):
        rotated[i:i + 2] = matrix @ (row[i:i + 2] - center) + center
    return rotated


def test_tilting_a_photo_sideways_does_not_look_like_a_head_turn():
    frontal = head_pose(landmarks())
    for degrees in (-30, -15, 15, 30):
        tilted = head_pose(rotate(landmarks(), degrees))
        assert abs(tilted.yaw - frontal.yaw) < 0.02
        assert abs(tilted.pitch - frontal.pitch) < 0.02


def test_real_head_turn_still_detected_when_head_is_tilted():
    turned = head_pose(rotate(landmarks(nose_x_offset=20), 15))
    assert turned.yaw > 0.3


def test_degenerate_landmarks_give_none():
    row = landmarks()
    row[6:8] = row[4:6]
    assert head_pose(row) is None


def test_random_challenge_never_repeats_direction_back_to_back():
    for seed in range(50):
        challenge = LivenessChallenge.random(4, rng=random.Random(seed))
        pairs = zip(challenge.steps, challenge.steps[1:])
        assert all(a != b for a, b in pairs)


def test_random_challenges_differ_between_seeds():
    sequences = {tuple(LivenessChallenge.random(3, rng=random.Random(s)).steps) for s in range(30)}
    assert len(sequences) > 5


def test_calibration_waits_for_enough_steady_frames():
    challenge = LivenessChallenge([Direction.LEFT], calibration_frames=3)
    challenge.update(FRONT, now=0.0)
    challenge.update(FRONT, now=0.1)
    assert challenge.status is Status.CALIBRATING
    challenge.update(FRONT, now=0.2)
    assert challenge.status is Status.WAITING


def test_calibration_restarts_if_head_is_moving():
    challenge = LivenessChallenge([Direction.LEFT], calibration_frames=3)
    for yaw in (0.0, 0.3, 0.0):
        challenge.update(pose(yaw), now=0.0)
    assert challenge.status is Status.CALIBRATING


def test_single_step_passes_after_turn_and_return():
    challenge = calibrated([Direction.LEFT])
    challenge.update(pose(0.3), now=1.0)
    assert challenge.status is Status.RETURNING
    challenge.update(pose(0.02), now=2.0)
    assert challenge.status is Status.PASSED


def test_wrong_direction_does_not_pass():
    challenge = calibrated([Direction.LEFT])
    challenge.update(pose(-0.4), now=1.0)
    assert challenge.status is Status.WAITING


def test_must_return_to_center_before_next_step():
    challenge = calibrated([Direction.LEFT, Direction.RIGHT])
    challenge.update(pose(0.3), now=1.0)
    challenge.update(pose(0.3), now=1.5)
    assert challenge.status is Status.RETURNING
    challenge.update(pose(0.0), now=2.0)
    assert challenge.status is Status.WAITING
    assert challenge.current is Direction.RIGHT


def test_steps_must_happen_in_the_given_order():
    challenge = calibrated([Direction.LEFT, Direction.RIGHT])
    challenge.update(pose(-0.4), now=1.0)
    assert challenge.status is Status.WAITING
    assert challenge.current is Direction.LEFT


def test_up_and_down_use_pitch():
    up = calibrated([Direction.UP])
    up.update(pose(0.0, 0.60 - 0.2), now=1.0)
    assert up.status is Status.RETURNING

    down = calibrated([Direction.DOWN])
    down.update(pose(0.0, 0.60 + 0.2), now=1.0)
    assert down.status is Status.RETURNING


def test_timeout_fails_the_challenge():
    challenge = calibrated([Direction.LEFT], step_timeout=5.0)
    challenge.update(FRONT, now=10.0)
    assert challenge.status is Status.FAILED


def test_failed_and_passed_are_final():
    challenge = calibrated([Direction.LEFT], step_timeout=1.0)
    challenge.update(FRONT, now=10.0)
    challenge.update(pose(0.3), now=10.1)
    assert challenge.status is Status.FAILED


def test_missing_face_does_not_advance():
    challenge = calibrated([Direction.LEFT])
    challenge.update(None, now=1.0)
    assert challenge.status is Status.WAITING
