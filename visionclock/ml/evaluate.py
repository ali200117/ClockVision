"""Måler hvor godt terskelen skiller en person fra andre, slik det skjer i recognize.py.

Leser bilder fra data/eval/<person>/*.jpg (lag dem med capture.py). For hver person:
  - malen er snittet av noen få bilder, akkurat som ved registrering med register.py
  - de resterende bildene av personen er "egne" forsøk (skal godtas)
  - alle bilder av de andre personene er "fremmede" forsøk (skal avvises)

  FRR: andel egne forsøk som avvises (ansatt blir ikke gjenkjent)
  FAR: andel fremmede forsøk som godtas (fremmed blir gjenkjent som ansatt)
"""
import argparse
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import cv2

from visionclock_ml import config
from visionclock_ml.face_engine import FaceEngine, normalize

IMAGE_PATTERNS = ("*.jpg", "*.jpeg", "*.png")
MAX_FAR_FOR_SUGGESTION = 0.01
SAFETY_MARGIN = 0.05


def collect_embeddings(engine: FaceEngine) -> dict[str, list[np.ndarray]]:
    people: dict[str, list[np.ndarray]] = {}
    if not config.EVAL_DIR.exists():
        return people
    for folder in sorted(p for p in config.EVAL_DIR.iterdir() if p.is_dir()):
        embeddings = []
        for pattern in IMAGE_PATTERNS:
            for path in sorted(folder.glob(pattern)):
                frame = cv2.imread(str(path))
                faces = engine.detect(frame) if frame is not None else []
                if not faces:
                    print(f"Ingen ansikt i {path}, hoppet over")
                    continue
                embeddings.append(engine.embed(frame, faces[0]))
        if embeddings:
            people[folder.name] = embeddings
            print(f"{folder.name}: {len(embeddings)} bilder")
    return people


def split_template(embeddings: list[np.ndarray], template_size: int):
    """Velger malbildene jevnt fordelt, og returnerer (mal, resten)."""
    picked = set(np.linspace(0, len(embeddings) - 1, template_size).round().astype(int))
    template = normalize(np.mean([embeddings[i] for i in sorted(picked)], axis=0))
    rest = [e for i, e in enumerate(embeddings) if i not in picked]
    return template, rest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-size", type=int, default=8,
                        help="antall bilder i malen, som --photos i register.py")
    args = parser.parse_args()

    engine = FaceEngine()
    people = collect_embeddings(engine)
    needed = args.template_size + 2
    eligible = {name: e for name, e in people.items() if len(e) >= needed}
    if len(people) < 2 or not eligible:
        print(f"Trenger minst to personer, og minst én med {needed} bilder eller flere. Bruk capture.py.")
        return 1

    templates, genuine_by_person = {}, {}
    for name, embeddings in eligible.items():
        template, rest = split_template(embeddings, args.template_size)
        templates[name] = template
        genuine_by_person[name] = np.array([float(np.dot(template, e)) for e in rest])

    genuine = np.concatenate(list(genuine_by_person.values()))
    impostor_by_pair: dict[tuple[str, str], np.ndarray] = {}
    for owner, template in templates.items():
        for other, embeddings in people.items():
            if other != owner:
                impostor_by_pair[(owner, other)] = np.array([float(np.dot(template, e)) for e in embeddings])
    impostor = np.concatenate(list(impostor_by_pair.values()))

    print(f"\nMal = snitt av {args.template_size} bilder. "
          f"{len(genuine)} egne forsøk, {len(impostor)} fremmede forsøk.")

    print("\nEgne forsøk (lavest/snitt) per person:")
    for name, scores in genuine_by_person.items():
        print(f"  {name:10s} lavest {scores.min():.2f}   snitt {scores.mean():.2f}")

    print("\nFremmede mot mal (høyest/snitt). Høyeste tall er det som teller:")
    for (owner, other), scores in sorted(impostor_by_pair.items()):
        print(f"  mal {owner:10s} mot {other:10s} høyest {scores.max():.2f}   snitt {scores.mean():.2f}")

    thresholds = np.linspace(0.0, 1.0, 201)
    frr = np.array([(genuine < t).mean() for t in thresholds])
    far = np.array([(impostor >= t).mean() for t in thresholds])

    print("\nterskel    FAR     FRR")
    for t in np.arange(0.30, 0.85, 0.05):
        i = int(round(t * 200))
        print(f"{thresholds[i]:.2f}     {far[i]:6.1%}  {frr[i]:6.1%}")

    eer_index = int(np.argmin(np.abs(far - frr)))
    print(f"\nEER (FAR = FRR) ved terskel {thresholds[eer_index]:.3f}, rundt {far[eer_index]:.1%}")

    allowed = np.where(far <= MAX_FAR_FOR_SUGGESTION)[0]
    if len(allowed):
        pick = int(allowed[0])
        print(f"Laveste terskel med FAR <= {MAX_FAR_FOR_SUGGESTION:.0%}: {thresholds[pick]:.3f} (FRR {frr[pick]:.1%})")

    safe = impostor.max() + SAFETY_MARGIN
    print(f"Høyeste fremmed-score: {impostor.max():.2f}. Med margin {SAFETY_MARGIN}: terskel {safe:.2f} "
          f"(FRR {(genuine < safe).mean():.1%})")
    print(f"Laveste egen-score: {genuine.min():.2f}")
    print(f"Terskelen i config.py nå: {config.MATCH_THRESHOLD}")

    figure, (left, right) = plt.subplots(1, 2, figsize=(11, 4))
    left.hist(genuine, bins=30, alpha=0.7, label="egne")
    left.hist(impostor, bins=30, alpha=0.7, label="fremmede")
    left.axvline(config.MATCH_THRESHOLD, color="k", linestyle="--", label="terskel")
    left.set_xlabel("cosinus-likhet mot mal")
    left.legend()
    right.plot(thresholds, far, label="FAR")
    right.plot(thresholds, frr, label="FRR")
    right.axvline(config.MATCH_THRESHOLD, color="k", linestyle="--")
    right.set_xlabel("terskel")
    right.legend()
    report = config.EVAL_DIR / "report.png"
    figure.tight_layout()
    figure.savefig(report)
    print(f"Plott lagret i {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
