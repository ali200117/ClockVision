import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import config
from .face_engine import cosine_similarity, normalize

OTHER_PREFIX = "other:"


@dataclass(frozen=True)
class Registered:
    """En registrert person. employee_id er None for ikke-ansatte (distraktorer)."""
    employee_id: int | None
    name: str
    embedding: np.ndarray


@dataclass(frozen=True)
class Match:
    employee_id: int | None
    name: str
    score: float

    @property
    def is_employee(self) -> bool:
        return self.employee_id is not None


def load(path: Path = config.EMBEDDINGS_FILE) -> list[Registered]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        Registered(
            None if key.startswith(OTHER_PREFIX) else int(key),
            entry["name"],
            np.array(entry["embedding"], dtype=np.float32),
        )
        for key, entry in raw.items()
    ]


def _write(key: str, name: str, embeddings: list[np.ndarray], path: Path) -> None:
    if not embeddings:
        raise ValueError("Trenger minst én embedding.")
    mean = normalize(np.mean(embeddings, axis=0))

    raw = {}
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
    raw[key] = {"name": name, "embedding": [float(v) for v in mean]}

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(raw, indent=2), encoding="utf-8")


def save_employee(employee_id: int, name: str, embeddings: list[np.ndarray],
                  path: Path = config.EMBEDDINGS_FILE) -> None:
    """Lagrer snittet av flere embeddings for en ansatt, og erstatter en eventuell gammel."""
    _write(str(employee_id), name, embeddings, path)


def save_other(name: str, embeddings: list[np.ndarray],
               path: Path = config.EMBEDDINGS_FILE) -> None:
    """Lagrer en ikke-ansatt som ligner en ansatt. Den får aldri stemple, men tar treffet fra de ansatte."""
    _write(OTHER_PREFIX + name, name, embeddings, path)


def best_match(embedding: np.ndarray, registered: list[Registered]) -> Match | None:
    """Den registrerte personen som ligner mest, uansett om den er god nok."""
    best = None
    for person in registered:
        score = cosine_similarity(embedding, person.embedding)
        if best is None or score > best.score:
            best = Match(person.employee_id, person.name, score)
    return best
