import numpy as np

from visionclock_ml import store
from visionclock_ml.face_engine import normalize


def vector(*values):
    return normalize(np.array(values, dtype=np.float32))


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "embeddings.json"
    store.save_employee(1, "Ali Test", [vector(1, 0, 0), vector(0.9, 0.1, 0)], path)

    loaded = store.load(path)

    assert len(loaded) == 1
    assert loaded[0].employee_id == 1
    assert loaded[0].name == "Ali Test"
    assert abs(float(np.linalg.norm(loaded[0].embedding)) - 1.0) < 1e-5


def test_load_missing_file_gives_empty_list(tmp_path):
    assert store.load(tmp_path / "missing.json") == []


def test_saving_same_employee_replaces_old_embedding(tmp_path):
    path = tmp_path / "embeddings.json"
    store.save_employee(1, "Ali", [vector(1, 0, 0)], path)
    store.save_employee(1, "Ali", [vector(0, 1, 0)], path)

    loaded = store.load(path)

    assert len(loaded) == 1
    assert loaded[0].embedding[1] > 0.99


def test_best_match_picks_most_similar_person(tmp_path):
    path = tmp_path / "embeddings.json"
    store.save_employee(1, "Ali", [vector(1, 0, 0)], path)
    store.save_employee(2, "Kari", [vector(0, 1, 0)], path)

    match = store.best_match(vector(0.1, 0.95, 0), store.load(path))

    assert match.employee_id == 2
    assert match.score > 0.9


def test_best_match_without_registered_people_is_none():
    assert store.best_match(vector(1, 0, 0), []) is None


def test_other_person_is_not_an_employee(tmp_path):
    path = tmp_path / "embeddings.json"
    store.save_other("bror", [vector(0, 1, 0)], path)

    loaded = store.load(path)

    assert loaded[0].employee_id is None
    assert loaded[0].name == "bror"


def test_lookalike_other_takes_the_match_from_employee(tmp_path):
    path = tmp_path / "embeddings.json"
    store.save_employee(1, "Ali", [vector(1, 0.2, 0)], path)
    store.save_other("bror", [vector(1, 0.6, 0)], path)

    match = store.best_match(vector(1, 0.55, 0), store.load(path))

    assert match.name == "bror"
    assert not match.is_employee
