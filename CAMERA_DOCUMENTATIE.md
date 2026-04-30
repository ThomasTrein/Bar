# KSA Bar — Camera & Opnames: Gedetailleerde Documentatie

> Dit document beschrijft exact wanneer de camera start en stopt, welke handelingen een opname triggeren, hoe bestanden worden opgeslagen en alle andere relevante details rond het opnamesysteem.

---

## Inhoudsopgave

1. [Technische basis](#1-technische-basis)
2. [Opname starten — alle triggers](#2-opname-starten--alle-triggers)
3. [Opname stoppen — alle triggers](#3-opname-stoppen--alle-triggers)
4. [Per modus gedetailleerd](#4-per-modus-gedetailleerd)
5. [Bestandsnaamgeving & mapstructuur](#5-bestandsnaamgeving--mapstructuur)
6. [Gedrag bij gelijktijdige opnames](#6-gedrag-bij-gelijktijdige-opnames)
7. [Opname op Raspberry Pi vs ontwikkel-PC](#7-opname-op-raspberry-pi-vs-ontwikkel-pc)
8. [Opnames raadplegen in het admin-paneel](#8-opnames-raadplegen-in-het-admin-paneel)
9. [Automatische opruiming](#9-automatische-opruiming)
10. [Logging](#10-logging)
11. [Configuratie-instellingen](#11-configuratie-instellingen)
12. [Bekende randgevallen](#12-bekende-randgevallen)

---

## 1. Technische basis

Het systeem gebruikt **ffmpeg** om beelden van de USB-webcam op te nemen in H.264-formaat (MP4).

**Hardware:**
- USB-webcam op `/dev/video0` (standaard)
- Resolutie: **1280 × 720** (720p)
- Framerate: **15 fps**

**Software:**
- `hardware/camera.py` beheert alle opnames
- Eén globale `Recording`-instantie actief tegelijk (`_active`)
- Thread-safe via een `threading.Lock`

**ffmpeg-commando (op Pi):**
```
ffmpeg -f v4l2 -video_size 1280x720 -framerate 15 -i /dev/video0
       -c:v libx264 -preset ultrafast -crf 28 -an -y <uitvoerbestand>
```
- `-preset ultrafast`: minimale CPU-belasting
- `-crf 28`: redelijke compressie, kleine bestanden
- `-an`: géén audio (microphone niet nodig)

---

## 2. Opname starten — alle triggers

De opname start **automatisch** bij de volgende handelingen:

### 2.1 Normale bestelling — eerste persoon selecteren

**Wanneer:** De gebruiker kiest zijn naam op het "Wie ben jij?" scherm van een bestelling.

**Code:** `routes/kiosk.py` — functie `bestelling_naam_post()`

**Voorwaarde:** De opname start enkel als er voor die bestelling (`ot`-token) nog geen `recording_path` is — herbezoek aan het naamscherm herstart de opname NIET.

```
Gebruiker kiest naam
    → recording_path nog niet in sessie?
        → start_recording("bestelling_<naam>")
        → pad opgeslagen in order['recording_path']
```

**Bestandsnaam voorbeeld:** `20251015_143022_bestelling_Thomas.mp4`

---

### 2.2 Baravond starten

**Wanneer:** Iemand klikt op "Baravond starten" en bevestigt met naam en begininventaris.

**Code:** `routes/kiosk.py` — functie `baravond_start()`

**Voorwaarde:** Altijd bij het starten van een baravond, geen sessie-check.

```
Admin klikt "Baravond starten" → naam + inventaris ingevuld → POST
    → start_recording("baravond")
    → pad opgeslagen in bar_evenings.video_path (database)
    → alle 3 deuren ontgrendeld
```

**Bestandsnaam voorbeeld:** `20251015_200000_baravond.mp4`

---

### 2.3 Aanvulmodus starten

**Wanneer:** Iemand klikt op "Aanvullen starten" en selecteert zijn naam.

**Code:** `routes/kiosk.py` — functie `aanvullen_start()`

**Voorwaarde:** Altijd bij het starten van de aanvulmodus.

```
Persoon kiest naam → POST aanvullen/start
    → start_recording("aanvullen")
    → pad opgeslagen in refill_sessions.video_path (database)
    → alle 3 deuren ontgrendeld
```

**Bestandsnaam voorbeeld:** `20251015_100500_aanvullen.mp4`

---

### 2.4 De Bond modus

**Wanneer:** Iemand klikt op "De Bond" op het kiosk-startscherm.

**Code:** `routes/kiosk.py` — functie `de_bond()`

**Voorwaarde:** Enkel als er in de huidige Bond-sessie nog geen `recording_path` zit (zodat het naamscherm herladen de opname niet herstart).

```
Klik "De Bond" op startscherm
    → bond_session['recording_path'] nog niet gezet?
        → start_recording("de_bond")
        → pad opgeslagen in sessie: bond_session['recording_path']
```

**Bestandsnaam voorbeeld:** `20251015_213000_de_bond.mp4`

---

## 3. Opname stoppen — alle triggers

### 3.1 Alle deuren terug vergrendeld (normale bestelling)

**Wanneer:** De `/api/deur-status` polling detecteert dat alle benodigde deuren terug vergrendeld zijn.

**Code:** `routes/api.py` — functie `deur_status()`

```
Poll detecteert alle_klaar = True
    → stop_recording()
    → sessie-order verwijderd
```

> ⚠️ Dit is de **normale** eindtrigger voor bestelling-opnames. De opname loopt dus door **totdat de deur terug dicht en vergrendeld is**, niet enkel tot wanneer de deur geopend is.

---

### 3.2 Timeout — deur nooit geopend

**Wanneer:** De timeout verstrijkt (standaard 120 seconden) zonder dat een deur geopend werd.

**Code:** `routes/kiosk.py` — `on_done()` callback in `bestelling_bevestigen()`

```
Alle deuren: timeout (opened = False)
    → bestelling geannuleerd (geannuleerd=1, deur_niet_geopend=1)
    → stock hersteld
    → deuren vergrendeld
    → poll detecteert alle_klaar → stop_recording()
```

> De opname stopt via dezelfde polling-weg als een normale bestelling. Het verschil zit enkel in het annuleren van de bestelling.

---

### 3.3 Bestelling annuleren op het wachtscherm

**Wanneer:** Gebruiker klikt op "Annuleren" terwijl de deuren ontgrendeld staan.

**Code:** `routes/kiosk.py` — functie `bestelling_annuleren()`

```
Klik "Annuleren"
    → stop_recording()  ← onmiddellijk
    → sessie verwijderd
    → redirect naar startscherm
```

---

### 3.4 Baravond stoppen

**Wanneer:** Iemand klikt op "Baravond stoppen" en bevestigt.

**Code:** `routes/kiosk.py` — functie `baravond_stop()`

```
Klik "Baravond stoppen" → naam stopper opgegeven → POST
    → stop_recording()
    → eindinventaris + verbruik opgeslagen in database
    → alle deuren worden NIET automatisch vergrendeld (al in beheer)
```

> Deuren worden tijdens baravond NIET automatisch vergrendeld na sluiting — de `unlock_all()` laat ze open totdat de baravond gestopt wordt.

---

### 3.5 Aanvulmodus stoppen

**Wanneer:** Iemand klikt op "Aanvullen stoppen".

**Code:** `routes/kiosk.py` — functie `aanvullen_stop()`

```
Klik "Aanvullen stoppen" → POST
    → stop_recording()
    → sessie verwijderd
```

---

### 3.6 Automatisch stoppen bij start nieuwe opname

**Wanneer:** Een nieuwe opname wordt gestart terwijl er al een actieve opname loopt.

**Code:** `hardware/camera.py` — functie `start_recording()`

```python
if _active and not _active.gestopt:
    _active.stop()   # vorige opname automatisch gestopt
```

Dit kan voorkomen bij **onverwacht gedrag** (bv. baravond starten terwijl een bestelling-opname loopt). De vorige opname wordt netjes afgesloten.

---

## 4. Per modus gedetailleerd

### Tijdlijn normale bestelling

```
[Startscherm]
      │
      ▼ Klik "Bestellen"
[Naam kiezen]
      │
      ▼ Persoon geselecteerd → ★ OPNAME START
[Producten kiezen]
      │  (opname loopt)
      ▼ Bevestig bestelling
[Wachtscherm — deuren ontgrendeld]
      │  (opname loopt, deuren staan open)
      ▼ Gebruiker opent deur → pakt product → sluit deur
[Deur vergrendeld → poll: alle_klaar] → ★ OPNAME STOPT
      │
      ▼ (5 sec countdown) → Startscherm
```

### Tijdlijn baravond

```
[Baravond-knop op startscherm]
      │
      ▼ Naam + begininventaris invullen → POST
★ OPNAME START → alle deuren ontgrendeld
[Startscherm met "Baravond actief" indicator]
      │  (opname loopt, deuren blijven open)
      │  ... avond verloopt ...
      ▼ Klik "Baravond stoppen" → stopper gekozen → POST
★ OPNAME STOPT → eindinventaris opgeslagen
[Startscherm normaal]
```

### Tijdlijn aanvullen

```
[Aanvullen-knop op startscherm]
      │
      ▼ Naam kiezen → POST
★ OPNAME START → alle deuren ontgrendeld
[Aanvulscherm — stock invoer]
      │  (opname loopt)
      ▼ Klik "Stoppen"
★ OPNAME STOPT → stock bijgewerkt in FIFO
[Startscherm normaal]
```

### Tijdlijn De Bond

```
[De Bond knop op startscherm]
      │
      ▼ Navigeer naar /de-bond
★ OPNAME START (enkel 1× per sessie)
[Naam kiezen]
      │
      ▼ Naam geselecteerd
[Producten + deuren kiezen]
      │
      ▼ Bestelling bevestigen
[Deuren ontgrendeld — wachtscherm]
      │  (opname van bond-sessie loopt nog steeds)
      ▼ Deuren dicht → alle_klaar
★ OPNAME STOPT (via poll)
```

---

## 5. Bestandsnaamgeving & mapstructuur

### Map

```
videos/
  └── YYYY/
        └── MM/
              └── DD/
                    └── <tijdstip>_<naam>.mp4
```

**Voorbeeld:**
```
videos/
  └── 2025/
        └── 10/
              └── 15/
                    ├── 20251015_143022_bestelling_Thomas.mp4
                    ├── 20251015_200000_baravond.mp4
                    └── 20251015_213000_de_bond.mp4
```

### Bestandsnaam formaat

```
<JJJJMMDD>_<UUMMSS>_<safe_naam>.mp4
```

- **safe_naam**: enkel letters, cijfers, `-` en `_` (speciale tekens worden verwijderd)
- Voorbeeld: `bestelling_Thomas`, `baravond`, `aanvullen`, `de_bond`

### Relatief pad (opgeslagen in database)

```
2025/10/15/20251015_143022_bestelling_Thomas.mp4
```

Dit pad wordt opgeslagen in:
- `orders.video_path`
- `bar_evenings.video_path`
- `refill_sessions.video_path`

---

## 6. Gedrag bij gelijktijdige opnames

Er kan maar **één opname tegelijk** actief zijn. Het systeem gebruikt een globale variabele `_active` beveiligd met een `threading.Lock`.

| Situatie | Gedrag |
|----------|--------|
| Bestelling start terwijl andere bestelling loopt | Eerste opname automatisch gestopt, nieuwe gestart |
| Baravond start terwijl bestelling loopt | Bestelling-opname gestopt, baravond-opname gestart |
| Aanvullen start terwijl baravond actief | **NIET MOGELIJK** — foutmelding: "Baravond is actief" |
| Baravond start terwijl aanvullen actief | **NIET MOGELIJK** — foutmelding: "Aanvulmodus is actief" |

> Het systeem **voorkomt actief** dat baravond en aanvulmodus gelijktijdig actief zijn. Twee simultane bestellingen (via `ot`-tokens) kunnen wel, maar starten elk hun eigen opname en stoppen de vorige.

---

## 7. Opname op Raspberry Pi vs ontwikkel-PC

| Aspect | Raspberry Pi | Ontwikkel-PC (Windows/Linux) |
|--------|-------------|------------------------------|
| ffmpeg-commando | Volledig uitgevoerd | Niet uitgevoerd |
| Bestand aangemaakt | Echte MP4 met videobeelden | Leeg `.mp4` bestand (0 bytes) |
| Webcam vereist | Ja (`/dev/video0`) | Nee |
| Log-bericht | `[REC] Opname gestart: ...` | `[STUB] Opname: ...` |
| `IS_RASPBERRY_PI` | `True` | `False` |

Dit maakt ontwikkeling en testen mogelijk zonder Pi of camera.

---

## 8. Opnames raadplegen in het admin-paneel

### Bestellingen
- Ga naar **Admin → Bestellingen**
- Kolom "Video" toont een "Bekijk"-knop als er een opname is
- Link: `/video/<pad>` serveert het bestand

### Baravonden
- Ga naar **Admin → Baravonden → Detail**
- Video-link zichtbaar per avond

### Aanvulsessies
- Momenteel enkel via de database-viewer of direct bestandspad

---

## 9. Automatische opruiming

Opnames ouder dan **40 dagen** worden automatisch verwijderd.

- **Instelling:** `video_bewaar_dagen` (standaard: `40`)
- **Functie:** `hardware/camera.py` → `cleanup_old_videos(bewaar_dagen)`
- **Hoe triggeren:** Manueel of via een geplande taak (cron)
- Na verwijdering worden ook **lege mappen** opgeruimd

```python
cleanup_old_videos(bewaar_dagen=40)
# Verwijdert bestanden ouder dan 40 dagen
# Verwijdert lege submappen in videos/
```

> ⚠️ De `video_bewaar_dagen`-instelling is aanpasbaar via **Admin → Instellingen**.

---

## 10. Logging

Elke start en stop van een opname wordt gelogd in de `logs`-tabel:

| Type | Beschrijving |
|------|-------------|
| `opname` | `Opname gestart: 2025/10/15/...mp4` |
| `opname` | `Opname gestopt: 2025/10/15/...mp4` |
| `systeem` | `Camera-fout: ffmpeg niet gevonden — opname niet mogelijk` |

Logs raadplegen: **Admin → Logs** — filter op type `opname`.

---

## 11. Configuratie-instellingen

Aanpasbaar in `config.py`:

| Instelling | Standaardwaarde | Beschrijving |
|-----------|----------------|-------------|
| `CAMERA_RESOLUTION` | `(1280, 720)` | Resolutie van de opname |
| `CAMERA_FPS` | `15` | Framerate (frames per seconde) |
| `CAMERA_DEVICE` | `0` | Webcam-apparaatnummer (`/dev/video0`) |
| `VIDEOS_DIR` | `./videos` | Map waar opnames worden opgeslagen |

Aanpasbaar via Admin → Instellingen:

| Instelling | Standaard | Beschrijving |
|-----------|-----------|-------------|
| `video_bewaar_dagen` | `40` | Hoeveel dagen opnames bewaard blijven |

---

## 12. Bekende randgevallen

| Situatie | Gedrag |
|----------|--------|
| ffmpeg crasht tijdens opname | Bestand corrupt/onvolledig — systeem merkt dit niet actief op |
| Pi verliest stroom tijdens opname | Bestand corrupt/afgekapt — MP4-container niet correct afgesloten |
| Webcam niet aangesloten | ffmpeg-fout gelogd, leeg bestand aangemaakt, systeem werkt verder |
| Webcam valt weg tijdens opname | ffmpeg-proces crasht, opname stopt, maar `_active` denkt nog steeds dat hij loopt tot `stop_recording()` expliciet aangeroepen wordt |
| Bestelling door timeout geannuleerd | Opname stopt pas via poll (`alle_klaar`) — niet via de annuleer-callback |
| Diskruimte vol | ffmpeg-fout, opname mislukt — geen foutmelding in UI |
