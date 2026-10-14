# VisionClock: stegvis plan

Denne filen er arbeidsplanen. `README.md` forklarer hva prosjektet er, denne forklarer hva som skal gjøres og i hvilken rekkefølge.

**Regel for samarbeidet:** Jeg skriver all kode selv for å lære Java. Claude forklarer, spør, gir hint og leser koden min. Claude skriver ikke koden for meg.

**Slik bruker jeg filen:** Les "Hvor er jeg nå", gå til det neste steget som ikke er huket av, og hak av når Definition of done er oppfylt.

---

## Hvor er jeg nå

Status per 2026-10-14:

- Spring Boot 4.1.1, Java 21, Maven er satt opp. Dependencies: data-jpa, validation, webmvc, devtools, postgresql, og test-startere.
- `application.properties` setter profil `local`. Det finnes en `application-local.properties.example`, men den er tom.
- Alle klasser under `employee/` og `attendance/` er tomme skall. Ingenting har logikk ennå.
- Feil som må rettes i skallene, og som er med i steg 1 og 2:
  - `EmployeeRepository` er en `class`, men skal være et **interface**.
  - `AttendanceType` er en tom fil, men skal være en **enum**.
  - DTO-ene er `class`, men passer best som **records**.
  - `common/` (exception og config) finnes ikke ennå.
- Ingen database er koblet til, ingen tester er skrevet utover den genererte `VisionclockApplicationTests`.

**Neste steg: Steg 0, så Steg 1.**

---

## Oversikt over fasene

| Fase | Innhold | Språk |
|------|---------|-------|
| A. Backend uten ML | Steg 0 til 9 | Java |
| B. Kamera og ML | Steg 10 til 17 | Python, og Java for koblingen |

Fase A må fungere helt før fase B starter. Da kan jeg teste hele flyten med en falsk "gjenkjenner" som bare sender en employee-id.

---

# Fase A: Java-backend

## Steg 0: Miljø og database

**Mål:** Applikasjonen starter og snakker med PostgreSQL.

Gjøres:
1. Installer PostgreSQL lokalt, eller kjør den i Docker. Lag en database `visionclock` og en egen bruker (ikke bruk superbrukeren).
2. Fyll ut `application-local.properties.example` med nøklene som trengs (url, brukernavn, passord, `ddl-auto`, `show-sql`). Eksempelfilen skal ikke ha ekte passord.
3. Kopier eksempelfilen til `application-local.properties`. Sjekk at den nye filen står i `.gitignore`, slik at passordet aldri havner i git.
4. Start applikasjonen og les loggen. Du skal se at Hibernate kobler til uten feil.

Å lese om:
- Spring profiles (hvorfor `spring.profiles.active=local` finnes).
- `spring.jpa.hibernate.ddl-auto`: hva `none`, `validate`, `update` og `create-drop` gjør. Bruk `update` midlertidig nå, og bytt til Flyway i steg 8.
- `spring.datasource.*` og `spring.jpa.*`.

Definition of done: appen starter, ingen feil i loggen, `git status` viser ikke passordfilen.

---

## Steg 1: Employee-entiteten og repository

**Mål:** En `Employee` lagres og hentes fra databasen.

### 1.1 `Employee` (vanlig klasse med `@Entity`)

Felter:

| Felt | Type | Merknad |
|------|------|---------|
| `id` | `Long` | primærnøkkel, generert av databasen |
| `firstName` | `String` | ikke null |
| `lastName` | `String` | ikke null |
| `employeeNumber` | `String` | ikke null, **unik** |
| `active` | `boolean` | standard `true` |
| `createdAt` | `Instant` | settes når raden opprettes |

Å tenke over:
- Hvorfor `Instant` og ikke `LocalDateTime` for tidspunkt? (Svar: `Instant` er et absolutt tidspunkt uten tidssone, og passer for hendelser.)
- Hvorfor trenger JPA en tom konstruktør, og hvorfor bør den ikke være `public`?
- Hvorfor skal `equals`/`hashCode` på entiteter behandles med forsiktighet?
- Hvorfor `String` og ikke `int` for `employeeNumber`? (Ledende nuller, bokstaver.)
- Skal jeg bruke setters overalt, eller heller metoder med mening, som `deactivate()`? Prøv det siste.

### 1.2 `EmployeeRepository` (**interface**, ikke klasse)

Utvider `JpaRepository`. Du trenger ikke skrive implementasjon, Spring Data lager den.

Metoder jeg trenger utover de innebygde:
- finn en ansatt på `employeeNumber`
- sjekk om en `employeeNumber` allerede finnes
- (senere) list kun aktive ansatte

Å lese om: *Spring Data derived query methods* (metodenavn som `findBy...` og `existsBy...`), `Optional`.

### 1.3 Test

Skriv en `@DataJpaTest` som lagrer en ansatt og henter den igjen, og en som viser at duplikat `employeeNumber` feiler.

Definition of done: testene går, og jeg kan forklare hva `@Entity`, `@Id`, `@GeneratedValue` og `@Column` gjør.

---

## Steg 2: Attendance-modellen

**Mål:** Hver stempling lagres som en egen hendelse.

### 2.1 `AttendanceType` (**enum**)

Verdier: `CLOCK_IN`, `CLOCK_OUT`.

Å lese om: `@Enumerated(EnumType.STRING)`. Finn ut hvorfor `ORDINAL` er farlig (rekkefølgen i enumen blir lagret som tall, og endres den, blir gamle data feil).

### 2.2 `Attendance` (`@Entity`)

| Felt | Type | Merknad |
|------|------|---------|
| `id` | `Long` | primærnøkkel |
| `employee` | `Employee` | `@ManyToOne`, lazy |
| `type` | `AttendanceType` | lagres som tekst |
| `timestamp` | `Instant` | når stemplingen skjedde |

Å lese om:
- `@ManyToOne` og `@JoinColumn`.
- `FetchType.LAZY` kontra `EAGER`, og hva N+1-problemet er.
- Hvorfor jeg lagrer `employee` som relasjon og ikke bare en `Long employeeId`. Vurder begge, og skriv ned valget mitt her:

> Valg: _(fyll inn)_

### 2.3 `AttendanceRepository` (**interface**)

Metoder:
- siste hendelse for en ansatt (sortert synkende på `timestamp`, kun én)
- alle hendelser for en ansatt, nyeste først
- hendelser for en ansatt mellom to tidspunkter

Å lese om: `findFirstBy...OrderBy...Desc`, `Pageable`/`Page`, og når man heller skriver en `@Query` (JPQL).

### 2.4 Test

`@DataJpaTest`: lagre tre hendelser og verifiser at "siste hendelse"-metoden gir riktig.

Definition of done: testene går, tabellene ser riktige ut i databasen (sjekk med psql eller pgAdmin).

---

## Steg 3: DTO-er og validering

**Mål:** Controlleren eksponerer aldri entiteter direkte.

Hvorfor: entiteter er databasemodellen. Hvis de returneres rett ut, lekker interne felt, og API-et brekker når tabellen endres.

Skriv som **records** (Java 16+), fordi de er uforanderlige dataholdere:

| Record | Felter | Validering |
|--------|--------|-----------|
| `CreateEmployeeRequest` | firstName, lastName, employeeNumber | ikke blank på alle, maks lengde |
| `UpdateEmployeeRequest` | firstName, lastName | ikke blank |
| `EmployeeResponse` | id, firstName, lastName, employeeNumber, active, createdAt | ingen (kun ut) |
| `AttendanceResponse` | id, employeeId, type, timestamp | ingen (kun ut) |

Tillegg: en `ClockRequest`/lignende hvis jeg bestemmer at stempling tar en body (se steg 5).

Å lese om:
- Records i Java.
- Bean Validation (`jakarta.validation`): `@NotBlank`, `@Size`, `@Valid`. Merk `jakarta`, ikke `javax`.
- Statiske fabrikkmetoder, f.eks. `EmployeeResponse.from(Employee)`, for å konvertere entitet til DTO. Alternativet er et bibliotek som MapStruct. Gjør det for hånd først, siden det er poenget med å lære.

Definition of done: jeg har DTO-ene, og jeg kan forklare forskjellen på `@NotNull`, `@NotEmpty` og `@NotBlank`.

---

## Steg 4: EmployeeService og EmployeeController

**Mål:** CRUD for ansatte via REST.

### 4.1 `EmployeeService` (`@Service`)

All forretningslogikk bor her. Metoder:

| Metode | Gjør | Feiler hvis |
|--------|------|-------------|
| opprett ansatt | lagrer ny, `active = true` | `employeeNumber` finnes |
| hent én | finner på id | finnes ikke |
| hent alle | liste, evt. kun aktive | |
| oppdater | endrer navn | finnes ikke |
| deaktiver | setter `active = false` | finnes ikke |

Viktige valg:
- **Deaktiver, ikke slett.** Historikken i `Attendance` skal ikke bli ugyldig. Skriv ned hvorfor.
- `employeeNumber` kan ikke endres etter opprettelse. (Min beslutning, kan endres.)
- Bruk **constructor injection**, aldri `@Autowired` på felt. Finn ut hvorfor.
- `@Transactional`: hvilke metoder trenger den, og hvilke kan ha `readOnly = true`?

### 4.2 `EmployeeController` (`@RestController`)

Controlleren skal bare:
1. ta imot HTTP,
2. validere input (`@Valid`),
3. kalle servicen,
4. returnere riktig statuskode.

Ingen logikk her.

| Metode | Sti | Suksesskode |
|--------|-----|-------------|
| POST | `/api/employees` | 201 Created, med `Location`-header |
| GET | `/api/employees` | 200 |
| GET | `/api/employees/{id}` | 200 |
| PUT | `/api/employees/{id}` | 200 |
| POST | `/api/employees/{id}/deactivate` | 200 eller 204 |

Å lese om: `@RequestMapping`, `@PathVariable`, `@RequestBody`, `ResponseEntity`, `@ResponseStatus`, `ResponseEntity.created(...)`.

Valg å ta (skriv ned): bruke `PATCH` eller `POST .../deactivate`? `DELETE` som deaktiverer er forvirrende, så vurder det nøye.

### 4.3 Tester

- Service-test med **Mockito** (ingen database): opprett med duplikat gir feil.
- Controller-test med `@WebMvcTest` og `MockMvc`: riktig statuskode, validering gir 400.

Definition of done: jeg kan opprette, hente, oppdatere og deaktivere ansatte med Postman, Bruno eller `curl`.

---

## Steg 5: Stemplingslogikken (kjernen)

**Mål:** Backend bestemmer CLOCK_IN eller CLOCK_OUT selv.

### 5.1 Regelen

```text
Ingen tidligere hendelse   -> CLOCK_IN
Siste hendelse CLOCK_OUT   -> CLOCK_IN
Siste hendelse CLOCK_IN    -> CLOCK_OUT
```

Ytterligere regler:
- Ansatt finnes ikke -> feil.
- Ansatt er deaktivert -> feil, ingen stempling.

### 5.2 `AttendanceService`

Metoder:

| Metode | Gjør |
|--------|------|
| stempl | finn ansatt, valider aktiv, finn siste hendelse, lag ny av motsatt type, lagre, returner |
| nåværende status | er ansatten "inne" eller "ute"? |
| historikk | hendelser for en ansatt, evt. med datointervall |

Tips til design:
- Hold selve avgjørelsen ("hva blir neste type?") i en liten, ren metode som ikke rører databasen. Da kan den testes uten Spring.
- **Ikke kall `Instant.now()` direkte i servicen.** Injiser en `java.time.Clock` (definer den som en `@Bean` i `common/config/`). Da kan testene bruke en fast klokke.
- Vurder en enum `AttendanceStatus` (`CLOCKED_IN`, `CLOCKED_OUT`) for statusendepunktet. Husk å tenke på at status ikke er det samme som hendelsestype.

### 5.3 Samtidighet (les, ikke nødvendigvis løs med en gang)

Hva skjer hvis to stemplinger for samme ansatt kommer samtidig? Begge leser "siste = CLOCK_OUT" og begge lager CLOCK_IN. Les om:
- pessimistisk låsing (`@Lock(PESSIMISTIC_WRITE)` på ansatt-raden),
- optimistisk låsing (`@Version`),
- unike constraints i databasen.

Velg én løsning, skriv den ned her, og implementer den når grunnlaget fungerer:

> Valg: _(fyll inn)_

### 5.4 `AttendanceController`

| Metode | Sti | Gjør |
|--------|-----|------|
| POST | `/api/employees/{id}/clock` | stempler, returnerer `AttendanceResponse` |
| GET | `/api/employees/{id}/status` | nåværende status |
| GET | `/api/employees/{id}/attendance` | historikk, valgfritt `from` og `to` |

Å lese om: `@RequestParam`, `@DateTimeFormat` / ISO-8601, `Pageable` som parameter.

### 5.5 Tester

Dette er den viktigste testsuiten i fasen. Dekk minst:
- første stempling gir CLOCK_IN
- to stemplinger gir CLOCK_IN, så CLOCK_OUT
- tre stemplinger gir CLOCK_IN, CLOCK_OUT, CLOCK_IN
- deaktivert ansatt avvises
- ukjent ansatt avvises
- fast klokke gir forventet `timestamp`

Definition of done: all logikken ligger i servicen, testene er grønne, og controlleren er tynn.

---

## Steg 6: Feilhåndtering

**Mål:** API-et gir ryddige feilsvar i stedet for stacktraces.

Opprett i `common/exception/`:

| Klasse | Type | Brukes når | HTTP |
|--------|------|------------|------|
| `EmployeeNotFoundException` | `RuntimeException` | id finnes ikke | 404 |
| `DuplicateEmployeeNumberException` | `RuntimeException` | nummer er tatt | 409 |
| `EmployeeInactiveException` | `RuntimeException` | stempling av deaktivert | 409 eller 422 |
| `GlobalExceptionHandler` | `@RestControllerAdvice` | oversetter unntak til svar | |

Å lese om:
- Checked kontra unchecked exceptions i Java. Hvorfor bruker Spring-prosjekter helst unchecked?
- `@ExceptionHandler`, `@RestControllerAdvice`.
- `ProblemDetail` (RFC 7807 / 9457), som Spring har innebygd støtte for.
- `MethodArgumentNotValidException`: hva Spring kaster når `@Valid` feiler, og hvordan gjøre den om til en liste med feltfeil.

Definition of done: alle feiltilfellene fra steg 4 og 5 gir riktig statuskode og en JSON-body som beskriver feilen.

---

## Steg 7: Integrasjonstester med ekte database

**Mål:** Teste hele kjeden mot en ekte PostgreSQL, ikke en falsk.

Å lese om og vurdere å legge til (nytt i `pom.xml`):
- **Testcontainers** (starter en PostgreSQL i Docker under testen). Krever Docker.
- Spring Boots støtte for dette (`@ServiceConnection`).
- `@SpringBootTest` med `MockMvc` eller `TestRestTemplate`/`RestTestClient`.

Skriv en ende-til-ende-test: opprett ansatt, stempl to ganger, hent historikk, sjekk status.

Merk: Spring Boot 4 har delt opp startere og testmoduler (`spring-boot-starter-*-test`). Mange nettguider er skrevet for Boot 3, så sjekk alltid offisiell dokumentasjon for 4.x når noe ikke stemmer.

Definition of done: `./mvnw verify` går grønt fra ren tilstand.

---

## Steg 8: Databasemigrasjoner og opprydding

**Mål:** Schemaet styres av kode jeg kontrollerer.

1. Legg til **Flyway**. Skriv `V1__create_employee.sql` og `V2__create_attendance.sql` for hånd, med primærnøkler, fremmednøkler, `UNIQUE` på `employee_number` og en indeks på `(employee_id, timestamp)`.
2. Sett `ddl-auto=validate`, slik at Hibernate sjekker at entitetene matcher schemaet i stedet for å endre det.
3. Konfigurer logging (nivåer, skru av `show-sql` utenom debugging).
4. Gjennomgå: ingen ubrukte klasser, `package-info` eller kommentarer er ikke nødvendig, men navn skal være konsekvente.

Å lese om: Flyway-navnekonvensjon, hvorfor man aldri redigerer en migrasjon som allerede er kjørt, indekser og `EXPLAIN`.

Definition of done: tom database -> start appen -> alle tabeller opprettes av Flyway, og `validate` klager ikke.

---

## Steg 9: API-dokumentasjon og klargjøring for ML

**Mål:** En stabil kontrakt som ML-delen kan bruke.

1. Legg til **springdoc-openapi** for automatisk Swagger UI. Se på dokumentasjonen først.
2. Skriv API-oversikten inn i `README.md`.
3. Bestem hvordan en annen tjeneste (Python) skal kalle stemplingen. Anbefaling: gjenbruk `POST /api/employees/{id}/clock`, og legg til en enkel API-nøkkel i en header senere (steg 16).
4. Legg til et `recognition`-skall i Java (se steg 15), men ikke noe mer.

Definition of done: Swagger UI viser alle endepunktene, og jeg kan gå gjennom flyten uten å åpne koden.

**Her er fase A ferdig.** Commit og tagg, f.eks. `v0.1-backend`.

---

# Fase B: Kamera og maskinlæring

Her er målet å forstå, ikke å bygge det beste systemet. Jeg trener min egen modell i stedet for å bruke en ferdig tjeneste. Python er et nytt språk i prosjektet, men konseptene er det viktige.

## Arkitektur for fase B

```text
Kamera -> Python-tjeneste -> (identifisert employeeId) -> Java-backend -> PostgreSQL
              |
              +-- detektor -> justering -> modell -> sammenligning mot lagrede ansikter
```

Ansvarsdeling:
- **Python:** alt som har med bilder og modell å gjøre. Svarer på "hvem er dette?".
- **Java:** alt som har med ansatte, regler og lagring å gjøre. Bestemmer CLOCK_IN/OUT.
- Modellen vet ingenting om stempling, og Java vet ingenting om bilder.

Dette skillet er viktig. Det betyr at jeg kan bytte modell uten å røre Java.

## Steg 10: Python-miljø og grunnleggende bildebehandling

**Mål:** Komfortabel med verktøyene før jeg trener noe.

Gjøres:
1. Lag mappen `ml/` i repoet (eller et eget repo). Lag et virtuelt miljø (`venv`) og en `requirements.txt`.
2. Installer **NumPy**, **OpenCV** (`opencv-python`), **PyTorch**, **matplotlib**.
3. Skriv små skript: les et bilde, vis det, gjør det grått, endre størrelse, åpne webkameraet og vis strømmen.

Å lese om:
- NumPy-arrays og `shape`. Et bilde er en 3D-array (høyde, bredde, kanaler).
- OpenCV bruker **BGR**-rekkefølge, ikke RGB. Dette er en klassisk feilkilde.
- Hva en piksel er, normalisering (0-255 til 0-1).

Definition of done: jeg kan vise webkameraet i et vindu og lagre et bilde.

## Steg 11: Datainnsamling

**Mål:** Et eget datasett.

Gjøres:
1. Skriv et skript som tar bilder fra kameraet og lagrer dem i `data/raw/<employeeNumber>/`.
2. Samle minst 50 til 100 bilder per person, med variasjon: vinkel, lys, avstand, brille/ikke brille.
3. Ha også en mappe med "ukjente" ansikter (kolleger/venner som ikke er registrert), som trengs for å teste avvisning.
4. Hold bildene utenfor git (`.gitignore`). Se også personvernmerknaden nederst.

Å lese om: hvorfor variasjon i data er viktigere enn mengde, bias i datasett.

Definition of done: en mappestruktur med bilder jeg kan beskrive (antall per person, forskjellen i forhold).

## Steg 12: Ansiktsdeteksjon og forbehandling

**Mål:** Fra råbilde til et jevnt, beskåret ansiktsbilde.

Pipeline per bilde:
1. **Detekter** ansiktet. Start med OpenCVs Haar cascade eller DNN-detektor. (Å bygge en detektor selv er et eget stort prosjekt, så bruk en ferdig her og skriv det ned som et bevisst valg.)
2. **Beskjær** ansiktet.
3. **Juster** (valgfritt, men løfter kvaliteten): roter slik at øynene ligger vannrett.
4. **Skaler** til fast størrelse, f.eks. 112x112 eller 160x160.
5. **Normaliser** pikselverdier.
6. Lagre til `data/processed/`.

Å lese om: Haar cascades kontra CNN-baserte detektorer, aspect ratio, hvorfor alle bilder må ha lik størrelse, data augmentation (flipp, lysendring, små rotasjoner).

Definition of done: `data/processed/` inneholder bare ansiktsbilder av lik størrelse, og jeg har sett over dem manuelt.

## Steg 13: Første modell, klassifikasjon (læringsfasen)

**Mål:** Trene et CNN og forstå treningsløkken.

Start enkelt: en **klassifikator** som gir "person A, B, C eller ukjent".

Bygg i PyTorch:
- `Dataset` og `DataLoader`: egen klasse som laster bildene.
- Deling i **trening / validering / test** (f.eks. 70/15/15). Splitt på *bilder fra ulike økter*, ikke tilfeldig, ellers lekker nesten like bilder mellom settene.
- Modell: et lite CNN (noen få `Conv2d`, `ReLU`, `MaxPool2d`, så `Linear`).
- Tapsfunksjon: `CrossEntropyLoss`.
- Optimalisator: `Adam`.
- Treningsløkke: forward, loss, `backward()`, `step()`, `zero_grad()`.
- Plott tap og nøyaktighet per epoke for trening og validering.

Begreper å forstå (huk av når jeg kan forklare dem med egne ord):
- [ ] Convolution og filtre
- [ ] Aktiveringsfunksjon
- [ ] Loss-funksjon
- [ ] Backpropagation og gradienter
- [ ] Læringsrate
- [ ] Epoke kontra batch
- [ ] Overfitting og hvordan jeg ser det i kurvene
- [ ] Regularisering (dropout, weight decay, augmentation)

Ærlig begrensning: en ren klassifikator må trenes om hver gang en ny ansatt registreres, fordi utgangslaget har fast antall klasser. Det er derfor steg 14 finnes.

Definition of done: modellen får høy nøyaktighet på valideringssettet, og jeg ser og forklarer hva som skjer hvis jeg trener for lenge.

## Steg 14: Embeddings (den ekte løsningen)

**Mål:** En modell som lager en "fingeravtrykkvektor" av et ansikt, slik at nye ansatte kan legges til uten ny trening.

Ide:
- Modellen mapper et ansiktsbilde til en vektor, f.eks. 128 eller 512 tall (en **embedding**).
- Samme person gir vektorer som ligger nære hverandre. Ulike personer ligger langt unna.
- Ved registrering lagrer jeg en eller flere embeddings per ansatt (f.eks. snittet).
- Ved gjenkjenning beregner jeg embeddingen for ansiktet i kameraet og finner nærmeste lagrede.

Å lese om:
- **Triplet loss** (anker, positiv, negativ) og **contrastive loss**. Evt. ArcFace/CosFace som en senere forbedring.
- Avstandsmål: euklidsk avstand kontra **cosinuslikhet**. Normalisering av embeddings (L2).
- Hvordan man velger gode treningspar/trillinger (*hard negative mining*).
- Transfer learning: å starte fra en forhåndstrent CNN (f.eks. ResNet) i stedet for tom modell. Skriv ned som et valg om jeg gjør det, siden det er et kompromiss mellom læring og resultat.

Dataproblem: med bare noen få personer blir en embedding-modell dårlig. Vurder å forhåndstrene på et offentlig ansiktsdatasett, og så finjustere på mine egne.

Definition of done: jeg kan beregne en embedding for to bilder og vise at avstanden er liten for samme person og stor for ulike personer.

## Steg 15: Gjenkjenning, terskel og "ukjent"

**Mål:** Et svar som er riktig også når personen ikke er registrert.

Logikk:
1. Beregn embedding for ansiktet i kamera.
2. Sammenlign mot alle registrerte ansatte.
3. Er den nærmeste avstanden under **terskelen** -> returner den ansattes id og en konfidens. Ellers -> returner "ukjent".

Evaluering (dette er den viktigste læringen i hele prosjektet):
- **FAR** (false accept rate): hvor ofte en fremmed godtas som en ansatt.
- **FRR** (false reject rate): hvor ofte en ansatt avvises.
- Endre terskelen og plott avveiningen (ROC-kurve). Velg terskel ut fra hva som er verst: å stemple feil person er verre enn å måtte prøve igjen.
- Test mot de "ukjente" ansiktene fra steg 11.

Definition of done: en tabell/plott med FAR og FRR for ulike terskler, og en begrunnet valgt terskel.

## Steg 16: Koble Python og Java

**Mål:** Kameraet stempler en ekte ansatt.

### Python-siden
- En liten HTTP-tjeneste (**FastAPI** er et godt valg) med et endepunkt som tar imot et bilde og svarer med `{employeeId, confidence}` eller "ukjent". Alternativt kjører Python-skriptet selv kameraløkken og kaller Java direkte.
- Bestem: skal Python kalle Java (anbefalt, enklest), eller Java kalle Python?

### Java-siden
Ny pakke `recognition/`:

| Klasse | Type | Rolle |
|--------|------|-------|
| `RecognitionResult` | record | utfallet: ansatt-id eller ukjent, pluss konfidens |
| `FaceRecognizer` | **interface** | kontrakten: "gitt data, hvem er dette?" |
| `PythonFaceRecognizer` | klasse | ekte implementasjon som kaller Python-tjenesten |
| `FakeFaceRecognizer` | klasse | brukes i tester og fase A |
| `RecognitionController` | `@RestController` | tar imot et gjenkjenningsresultat og kaller `AttendanceService` |

Hvorfor et interface: da kan resten av Java-koden ikke se forskjell på ekte og falsk gjenkjenner, og jeg kan teste uten kamera. Dette er et godt eksempel på "program mot interface".

Å lese om: `RestClient` (Springs moderne HTTP-klient), timeouts, hva som skjer hvis Python-tjenesten er nede, enkel API-nøkkel i header.

Ekstra regler å bestemme:
- Minimum konfidens før stempling godtas.
- **Cooldown:** ikke la samme person stemple igjen innen f.eks. 30 sekunder (ellers stempler man inn og ut rett etter hverandre mens man står i bildet).

Definition of done: jeg står foran kameraet og får en CLOCK_IN i databasen, og står jeg der igjen etter cooldown, får jeg CLOCK_OUT.

## Steg 17: Registrering av ansikt og siste forbedringer

**Mål:** Hele livssyklusen.

- Registreringsflyt: opprett ansatt (Java) -> ta bilder (Python) -> beregn embedding(er) -> lagre dem. Bestem hvor embeddings bor: i Python (fil) eller i PostgreSQL (f.eks. som `bytea`/array i en egen tabell, eller `pgvector`). Skriv ned valget.
- Slett embeddings når en ansatt slettes eller ber om det.
- Vurder **liveness** (at det ikke er et bilde av en person som holdes opp). Les om hvorfor det er et reelt sikkerhetshull, selv om jeg ikke bygger det.
- Skriv ferdig dokumentasjon og begrensninger i `README.md`.

---

# Oversikt over klassene og hvem som snakker med hvem

```text
HTTP-forespørsel
      |
      v
Controller        tar imot, validerer, returnerer statuskode. Ingen logikk.
      |   (snakker med DTO-er)
      v
Service           forretningslogikk, @Transactional. Her bor reglene.
      |   (snakker med entiteter)
      v
Repository        interface. Spring Data lager implementasjonen.
      |
      v
Entity            @Entity. Speiler databasetabellen.
      |
      v
PostgreSQL
```

Regler:
- Controller kjenner **Service** og **DTO-er**. Den kjenner aldri Repository eller Entity.
- Service kjenner **Repository** og **Entity**, og tar inn/ut det controlleren trenger.
- Repository kjenner bare **Entity**.
- DTO-er og entiteter blandes aldri: konvertering skjer på ett sted.
- `AttendanceService` kan bruke `EmployeeRepository` (eller `EmployeeService`). Bestem hvilket, og skriv ned hvorfor.

| Element | Java-type | Hvorfor |
|---------|-----------|---------|
| `Employee`, `Attendance` | klasse med `@Entity` | JPA trenger veranderlige objekter |
| `AttendanceType`, `AttendanceStatus` | **enum** | fast sett av verdier |
| `EmployeeRepository`, `AttendanceRepository` | **interface** | Spring genererer implementasjonen |
| `...Request`, `...Response` | **record** | uforanderlige dataholdere |
| `EmployeeService`, `AttendanceService` | klasse med `@Service` | logikk |
| `...Controller` | klasse med `@RestController` | HTTP |
| `...Exception` | klasse som arver `RuntimeException` | feil |
| `GlobalExceptionHandler` | klasse med `@RestControllerAdvice` | feil til svar |
| `FaceRecognizer` | **interface** | bytt ekte/falsk implementasjon |
| `Clock` | bean i `common/config` | testbar tid |

## Pakkestruktur (mål)

```text
com.visionclock
├── VisionclockApplication
├── employee/
│   ├── Employee, EmployeeRepository, EmployeeService, EmployeeController
│   └── dto/  CreateEmployeeRequest, UpdateEmployeeRequest, EmployeeResponse
├── attendance/
│   ├── Attendance, AttendanceType, AttendanceStatus
│   ├── AttendanceRepository, AttendanceService, AttendanceController
│   └── dto/  AttendanceResponse
├── recognition/            (fase B)
│   └── FaceRecognizer, PythonFaceRecognizer, FakeFaceRecognizer, RecognitionResult, RecognitionController
└── common/
    ├── exception/  *Exception, GlobalExceptionHandler
    └── config/     ClockConfig
```

---

# Bibliotek og temaer å lese om

| Tema | Når | Hva jeg trenger å forstå |
|------|-----|--------------------------|
| Spring Boot (auto-config, profiles) | Steg 0 | hvorfor så lite konfigurasjon trengs |
| Dependency injection / IoC | Steg 4 | hva en bean er, constructor injection |
| Spring Data JPA | Steg 1, 2 | derived queries, `JpaRepository`, `Optional` |
| Hibernate / JPA-annotasjoner | Steg 1, 2 | `@Entity`, `@ManyToOne`, lazy loading |
| Bean Validation | Steg 3 | `@Valid`, `@NotBlank` |
| Spring MVC | Steg 4, 5 | `@RestController`, `ResponseEntity` |
| Transaksjoner | Steg 4, 5 | `@Transactional`, isolasjon, låsing |
| `java.time` | Steg 1, 5 | `Instant`, `Clock`, tidssoner |
| Records og enums | Steg 2, 3 | uforanderlighet |
| JUnit 5, Mockito, MockMvc | Steg 1, 4 | enhetstest kontra integrasjonstest |
| Testcontainers | Steg 7 | ekte DB i test |
| Flyway | Steg 8 | versjonerte migrasjoner |
| springdoc-openapi | Steg 9 | API-dokumentasjon |
| NumPy, OpenCV | Steg 10 til 12 | bilder som arrays |
| PyTorch | Steg 13, 14 | tensorer, autograd, treningsløkke |
| FastAPI | Steg 16 | HTTP fra Python |
| `RestClient` | Steg 16 | Java kaller Python |

Lombok bevisst **utelatt** i begynnelsen: jeg lærer mer av å skrive konstruktører, getters og `equals` selv, og records dekker mye av behovet.

---

# Beslutninger jeg må ta underveis

Fyll ut når jeg har bestemt meg:

| Spørsmål | Steg | Valg |
|----------|------|------|
| Relasjon eller bare `employeeId` i `Attendance`? | 2 | |
| Deaktiver via PATCH eller POST `/deactivate`? | 4 | |
| Hvilken låsestrategi for samtidige stemplinger? | 5 | |
| Hvor bor embeddings? | 17 | |
| Forhåndstrent modell eller helt fra scratch? | 14 | |
| Hvem kaller hvem, Python eller Java? | 16 | |
| Terskel for gjenkjenning | 15 | |

---

# Personvern

Ansiktsdata er biometriske data, og er en særlig kategori av personopplysninger etter GDPR. Dette er et læringsprosjekt, men gode vaner koster ikke noe:

- Bruk kun bilder av folk som har sagt ja.
- Hold bilder og embeddings utenfor git.
- Lagre ikke mer enn nødvendig, og kunne slette alt om en person.
- Hvis dette noen gang skal brukes på ekte ansatte, trengs rettslig grunnlag og en vurdering av personvernkonsekvenser.

---

# Hurtigsjekkliste

- [ ] Steg 0: Miljø og database
- [ ] Steg 1: Employee og repository
- [ ] Steg 2: Attendance-modellen
- [ ] Steg 3: DTO-er og validering
- [ ] Steg 4: EmployeeService og EmployeeController
- [ ] Steg 5: Stemplingslogikken
- [ ] Steg 6: Feilhåndtering
- [ ] Steg 7: Integrasjonstester
- [ ] Steg 8: Flyway og opprydding
- [ ] Steg 9: Swagger og klargjøring
- [ ] Steg 10: Python og bildebehandling
- [ ] Steg 11: Datainnsamling
- [ ] Steg 12: Deteksjon og forbehandling
- [ ] Steg 13: Første CNN-klassifikator
- [ ] Steg 14: Embeddings
- [ ] Steg 15: Terskel og "ukjent"
- [ ] Steg 16: Python og Java kobles sammen
- [ ] Steg 17: Registrering og finpuss
