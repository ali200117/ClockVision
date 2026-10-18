# VisionClock ML

Ansiktsgjenkjenning for VisionClock. Python-skriptene finner ansiktet i kameraet, lager en embedding (128 tall) med SFace, sammenligner med lagrede embeddings og kaller Java-backend for å stemple.

Detektor: YuNet. Embedding: SFace. Begge er ONNX-modeller som kjører i OpenCV på CPU.

## Oppsett (én gang)

Fra mappen `ml/`:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Modellfilene skal ligge i `ml/models/`:
- `face_detection_yunet_2023mar.onnx`
- `face_recognition_sface_2021dec.onnx`

Begge kommer fra `opencv/opencv_zoo` på GitHub. Mappene `models/`, `data/` og `.venv/` ligger i `.gitignore`.

## Bruk

Start backend først (`./mvnw spring-boot:run` i prosjektroten) og Postgres i Docker.

1. Opprett deg som ansatt og noter `id` fra svaret:

   ```powershell
   Invoke-RestMethod -Method Post -Uri http://localhost:8080/api/employees -ContentType application/json -Body '{"firstName":"Ali","lastName":"Al Kadri","employeeNumber":"A-001"}'
   ```

2. Registrer ansiktet ditt (SPACE tar bilde, q avbryter):

   ```powershell
   .venv\Scripts\python register.py --employee-id 1
   ```

3. Kjenn igjen og stempl (q avslutter). Bruk `--dry-run` for å teste uten å stemple:

   ```powershell
   .venv\Scripts\python recognize.py
   ```

## Liveness (hodebevegelse)

Etter at ansiktet er gjenkjent, får brukeren en tilfeldig utfordring, for eksempel "Snu hodet til VENSTRE", "Se OPP". Retningene er fra brukerens egen side. Stempling skjer først når alle bevegelsene er gjort i riktig rekkefølge innen tidsfristen, og samme ansatt er bekreftet i hele forløpet og igjen når hodet er tilbake i midten. Et stillestående bilde kan ikke snu seg.

Hodestillingen regnes ut fra de fem landemerkene til YuNet, som forhold mellom øyne, nese og munn.

- `--debug-pose` viser hvor mye hodet har beveget seg (yaw og pitch) mens du gjør utfordringen. Bruk det til å justere `LIVENESS_YAW_DELTA` og `LIVENESS_PITCH_DELTA` i `config.py`.
- `--steps 3` gir flere bevegelser. `--no-liveness` hopper over utfordringen.
- Føles venstre og høyre omvendt, sett miljøvariabelen `VISIONCLOCK_MIRROR=1`.

Begrensning: en video som snur seg i riktig rekkefølge kan lure en enkel utfordring. Tilfeldig rekkefølge og tidsfrist gjør det vanskeligere, men ikke umulig. Neste lag er en egen klassifikator for ekte mot skjerm eller utskrift.

## Måle kvaliteten

1. Ta testbilder av deg selv og minst én annen person (med samtykke):

   ```powershell
   .venv\Scripts\python capture.py --person ali --count 20
   .venv\Scripts\python capture.py --person venn1 --count 20
   ```

2. Kjør evalueringen. Den skriver FAR/FRR per terskel og lagrer `data/eval/report.png`:

   ```powershell
   .venv\Scripts\python evaluate.py
   ```

3. Juster `MATCH_THRESHOLD` i `visionclock_ml/config.py`, eller send `--threshold` til `recognize.py`.

## Filer

| Fil | Rolle |
|-----|-------|
| `visionclock_ml/face_engine.py` | detekterer ansikter og lager embeddings |
| `visionclock_ml/store.py` | lagrer og henter embeddings (`data/embeddings.json`), finner beste treff |
| `visionclock_ml/api_client.py` | snakker med Java-backend |
| `visionclock_ml/camera.py`, `overlay.py` | kamera og tegning i vinduet |
| `visionclock_ml/liveness.py` | tilfeldig hodeutfordring og hodestilling |
| `visionclock_ml/config.py` | terskel, cooldown, URL, liveness-innstillinger |
| `register.py`, `recognize.py` | registrering og gjenkjenning |
| `capture.py`, `evaluate.py` | testbilder og terskelmåling |

## Tester

```powershell
.venv\Scripts\python -m pytest
```

## Personvern

Ansiktsbilder og embeddings er biometriske data. Ikke legg dem i git, og bruk bare bilder av folk som har samtykket.
