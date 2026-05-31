# KSA Bar — Camera & Opnames: Gedetailleerde Documentatie

> Dit document beschrijft exact wanneer de camera start en stopt, welke handelingen een opname triggeren, hoe bestanden worden opgeslagen en alle andere relevante details rond het opnamesysteem.

---

## Inhoudsopgave

0. [Camera opzetten — stap voor stap](#0-camera-opzetten--stap-voor-stap)
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

## 0. Camera opzetten — stap voor stap

> Dit gedeelte leidt je van een lege Raspberry Pi naar een werkende camera-opname. Elke stap bouwt voort op de vorige. Lees altijd de **foutmeldingen** helemaal voor je iets probeert op te lossen.

---

### Stap 0.1 — Benodigdheden controleren

Controleer dat je het volgende hebt voordat je begint:

| Wat | Waarom |
|-----|--------|
| Raspberry Pi 4 met Ubuntu | Het systeem werkt alleen op Linux |
| USB-webcam | Elke standaard UVC-webcam werkt |
| KSA Bar project geïnstalleerd | Zie `RASPBERRY_PI_INSTALLATIE.md` |
| Internetverbinding (tijdelijk) | Voor installeren van ffmpeg |

---

### Stap 0.2 — ffmpeg installeren

De camera-module gebruikt **ffmpeg** om video op te nemen. Dit moet apart worden geïnstalleerd.

**Open een terminal op de Pi en typ:**

```bash
sudo apt update
sudo apt install -y ffmpeg
```

> `sudo apt update` haalt de laatste lijst van beschikbare programma's op.  
> `sudo apt install -y ffmpeg` installeert ffmpeg automatisch (`-y` bevestigt alle vragen).

**Controleer of het gelukt is:**

```bash
ffmpeg -version
```

Je moet iets zien als:
```
ffmpeg version 6.x.x Copyright (c) ...
```

✅ **Gelukt:** je ziet een versienummer  
❌ **Mislukt:** zie [Fout A](#fout-a--ffmpeg-niet-gevonden)

---

### Stap 0.3 — Webcam aansluiten

1. Steek de USB-webcam in een **USB 3.0 poort** van de Pi (blauwe poort)
2. Wacht 5 seconden
3. Controleer of de Pi de webcam herkent:

```bash
ls /dev/video*
```

Je moet zien:
```
/dev/video0
```

(Soms ook `/dev/video1`, `/dev/video2` — dat is normaal, de eerste (`video0`) is jouw webcam)

✅ **Gelukt:** `/dev/video0` verschijnt in de lijst  
❌ **Mislukt:** zie [Fout B](#fout-b--devvideo0-bestaat-niet)

---

### Stap 0.4 — Webcam testen met ffmpeg

Controleer of ffmpeg de webcam kan aanspreken door een testfoto te maken:

```bash
ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 /tmp/test.jpg -y
```

**Wat dit doet:** Maakt één foto (`-frames:v 1`) van de webcam en slaat die op als `/tmp/test.jpg`.

**Controleer of de foto er is:**

```bash
ls -lh /tmp/test.jpg
```

Je moet een bestand zien met een grootte groter dan 0 bytes, bijv.:
```
-rw-r--r-- 1 ubuntu ubuntu 45K mei 31 19:00 /tmp/test.jpg
```

✅ **Gelukt:** bestandsgrootte > 0 bytes  
❌ **Mislukt - "0 bytes":** zie [Fout C](#fout-c--testfoto-is-0-bytes)  
❌ **Mislukt - foutmelding in terminal:** zie [Fout D](#fout-d--ffmpeg-geeft-een-foutmelding-bij-de-webcam)

---

### Stap 0.5 — Controleer welke resolutie de webcam ondersteunt

Niet elke webcam ondersteunt 1280×720. Controleer dit:

```bash
sudo apt install -y v4l-utils
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

Je ziet een lijst van ondersteunde formaten. Zoek naar regels met `Size`:

```
[0]: 'MJPG' (Motion-JPEG, compressed)
    Size: Discrete 1280x720
        Interval: Discrete 0.067s (15.000 fps)
    Size: Discrete 640x480
        Interval: Discrete 0.033s (30.000 fps)
```

- Als `1280x720` met `15 fps` in de lijst staat → geen aanpassing nodig ✅
- Als `1280x720` er **niet** in staat → zie [Stap 0.5a](#stap-05a--resolutie-aanpassen)

#### Stap 0.5a — Resolutie aanpassen

Open het configuratiebestand:

```bash
nano ~/ksa-bar/config.py
```

Pas de resolutie aan naar een waarde die jouw webcam wél ondersteunt:

```python
CAMERA_RESOLUTION = (640, 480)   # pas aan naar wat jouw webcam ondersteunt
CAMERA_FPS = 30                  # pas framerate ook aan indien nodig
```

Sla op met `Ctrl+O`, dan `Enter`, dan `Ctrl+X`.

---

### Stap 0.6 — Controleer of de webcam niet op een ander nummer staat

Als je meerdere video-apparaten hebt (bijv. `/dev/video0`, `/dev/video1`, `/dev/video2`), moet je controleren welke de echte webcam is:

```bash
v4l2-ctl --list-devices
```

Voorbeeld uitvoer:
```
USB 2.0 Camera: USB 2.0 Camera (usb-...-1.4):
    /dev/video0
    /dev/video2

bcm2835-isp (platform:bcm2835-isp):
    /dev/video13
    /dev/video14
```

De eerste groep (met de naam van jouw webcam) is de juiste. Gebruik het **eerste** apparaat uit die groep.

Als jouw webcam op `/dev/video2` staat (niet `/dev/video0`), pas dan `config.py` aan:

```bash
nano ~/ksa-bar/config.py
```

```python
CAMERA_DEVICE = 2   # verander 0 naar het juiste nummer
```

---

### Stap 0.7 — Permissies instellen voor de webcam

Soms heeft de gebruiker geen toegang tot `/dev/video0`. Controleer dit:

```bash
ls -l /dev/video0
```

Je ziet zoiets als:
```
crw-rw----+ 1 root video 81, 0 mei 31 19:00 /dev/video0
```

De groep `video` heeft toegang. Voeg jouw gebruiker toe aan die groep:

```bash
sudo usermod -aG video $USER
```

**Daarna uitloggen en opnieuw inloggen** (of de Pi herstarten) zodat de groepswijziging van kracht wordt:

```bash
sudo reboot
```

Na herstart: herhaal Stap 0.4 om te controleren dat het nu werkt.

---

### Stap 0.8 — Een echte testopname maken

Maak nu een opname van 5 seconden om te controleren dat alles werkt:

```bash
ffmpeg -f v4l2 -video_size 1280x720 -framerate 15 -i /dev/video0 \
       -c:v libx264 -preset ultrafast -crf 28 -an -t 5 -y /tmp/test.mp4
```

**Uitleg:**
- `-t 5` → opname duurt 5 seconden
- `-c:v libx264` → H.264 videocompressie (zelfde als het echte systeem)
- `-preset ultrafast` → minimale CPU-belasting
- `-crf 28` → kwaliteitsinstelling (lager = hogere kwaliteit, groter bestand)
- `-an` → geen audio

**Controleer het resultaat:**

```bash
ls -lh /tmp/test.mp4
```

Het bestand moet groter dan 0 bytes zijn (bijv. 500KB–2MB voor 5 seconden).

✅ **Gelukt:** bestand heeft inhoud  
❌ **Mislukt:** zie [Fout D](#fout-d--ffmpeg-geeft-een-foutmelding-bij-de-webcam)

---

### Stap 0.9 — Map voor opnames controleren

Het systeem slaat opnames op in de `videos/` map in het project. Controleer dat die map bestaat en schrijfbaar is:

```bash
ls -ld ~/ksa-bar/videos/
```

Als de map niet bestaat:

```bash
mkdir -p ~/ksa-bar/videos
```

Controleer dat de gebruiker er in mag schrijven:

```bash
touch ~/ksa-bar/videos/test.txt && echo "OK" && rm ~/ksa-bar/videos/test.txt
```

Je moet `OK` zien. Als je een foutmelding krijgt over permissies:

```bash
sudo chown -R $USER:$USER ~/ksa-bar/videos/
```

---

### Stap 0.10 — Camera testen via de app zelf

Start de app en controleer of de camera werkt via de hardware-testpagina:

```bash
cd ~/ksa-bar
source venv/bin/activate
python app.py
```

Open een browser en ga naar:
```
http://localhost:5000/admin/hardware-test
```

Log in als admin en gebruik de camera-knoppen op de testpagina. Controleer daarna:

```bash
ls -lh ~/ksa-bar/videos/
```

Je moet een map met de huidige datum zien, met een MP4-bestand erin.

✅ **Gelukt:** MP4 aanwezig en groter dan 0 bytes  
❌ **Mislukt:** zie [Fout E](#fout-e--app-maakt-lege-mp4-bestanden-aan)

---

### Stap 0.11 — Controleer de logs in de app

Na een opname: ga naar **Admin → Logs** en filter op type `opname`.

Je moet regels zien zoals:
```
opname | Opname gestart: 2025/10/15/20251015_143022_bestelling_Thomas.mp4
opname | Opname gestopt: 2025/10/15/20251015_143022_bestelling_Thomas.mp4
```

Als je in de logs `Camera-fout: ffmpeg niet gevonden` ziet → zie [Fout A](#fout-a--ffmpeg-niet-gevonden).

---

## Foutmeldingen en oplossingen

---

### Fout A — ffmpeg niet gevonden

**Symptoom:**
```
[WARN] ffmpeg niet gevonden
```
of
```
bash: ffmpeg: command not found
```

**Oorzaak:** ffmpeg is niet geïnstalleerd.

**Oplossing:**

```bash
sudo apt update
sudo apt install -y ffmpeg
ffmpeg -version   # controleer
```

Als `apt install` mislukt door geen internetverbinding:

```bash
# Controleer verbinding
ping -c 3 8.8.8.8

# Als geen verbinding, probeer via ethernet ipv wifi
# of schakel wifi opnieuw in:
nmcli radio wifi off
nmcli radio wifi on
```

---

### Fout B — /dev/video0 bestaat niet

**Symptoom:**
```
ls: cannot access '/dev/video*': No such file or directory
```

**Oorzaak:** De Pi herkent de webcam niet.

**Stap 1:** Controleer of de webcam fysiek aangesloten is.

**Stap 2:** Probeer een andere USB-poort (bij voorkeur de blauwe USB 3.0-poorten).

**Stap 3:** Controleer of de Pi de webcam ziet in de USB-apparatenlijst:

```bash
lsusb
```

Zoek naar een regel met de naam van jouw webcam (bijv. `Logitech`, `Microsoft`, `USB Camera`):
```
Bus 001 Device 003: ID 046d:0825 Logitech, Inc. Webcam C270
```

Als de webcam **niet** in `lsusb` staat → is de webcam defect of niet compatibel.

**Stap 4:** Als de webcam wel in `lsusb` staat maar niet in `/dev/video*`:

```bash
# Herlaad de USB-videostuurprogramma's
sudo modprobe uvcvideo
ls /dev/video*
```

**Stap 5:** Herstart de Pi:

```bash
sudo reboot
```

---

### Fout C — Testfoto is 0 bytes

**Symptoom:** `/tmp/test.jpg` bestaat maar is leeg (0 bytes).

**Oorzaak:** ffmpeg kon geen beeld van de webcam lezen.

**Stap 1:** Controleer of de webcam al in gebruik is door een ander programma:

```bash
sudo lsof /dev/video0
```

Als er een programma in de lijst staat, stop dat dan eerst.

**Stap 2:** Probeer met expliciete invoerparameters:

```bash
ffmpeg -f v4l2 -video_size 640x480 -framerate 30 -i /dev/video0 -frames:v 1 /tmp/test2.jpg -y
```

**Stap 3:** Controleer de permissies (zie [Stap 0.7](#stap-07--permissies-instellen-voor-de-webcam)).

---

### Fout D — ffmpeg geeft een foutmelding bij de webcam

**Symptoom:** ffmpeg toont een foutmelding in de terminal.

#### "Invalid argument" of "VIDIOC_S_FMT"

De webcam ondersteunt de gevraagde resolutie of framerate niet.

```bash
# Bekijk wat jouw webcam ondersteunt
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

Pas daarna `config.py` aan met een ondersteunde resolutie (zie [Stap 0.5a](#stap-05a--resolutie-aanpassen)).

#### "Device or resource busy"

De webcam is al in gebruik door een ander programma.

```bash
# Zoek welk programma de webcam gebruikt
sudo lsof /dev/video0

# Stop het proces (vervang <PID> door het getal uit de vorige uitvoer)
sudo kill <PID>
```

Als de camera-module van de app nog draait, herstart de app.

#### "No such file or directory: /dev/video0"

De webcam staat op een ander apparaatnummer. Zie [Stap 0.6](#stap-06--controleer-of-de-webcam-niet-op-een-ander-nummer-staat).

#### "Permission denied"

Je hebt geen toegang tot `/dev/video0`. Zie [Stap 0.7](#stap-07--permissies-instellen-voor-de-webcam).

#### "Unknown encoder 'libx264'"

ffmpeg is geïnstalleerd maar zonder H.264 ondersteuning.

```bash
# Verwijder en herinstalleer met volledige ondersteuning
sudo apt remove ffmpeg
sudo apt install -y ffmpeg
```

Als dat niet helpt, installeer de volledige versie:

```bash
sudo apt install -y ffmpeg libx264-dev
```

---

### Fout E — App maakt lege MP4-bestanden aan

**Symptoom:** Er worden MP4-bestanden aangemaakt in `videos/`, maar ze zijn 0 bytes groot.

**Oorzaak 1:** De app draait niet op een Raspberry Pi (`IS_RASPBERRY_PI = False`).

Controleer:
```bash
cat /proc/device-tree/model
```
Als je `Raspberry Pi 4` ziet → Pi wordt herkend.  
Als je een fout krijgt → de app denkt dat het geen Pi is en gebruikt stub-modus.

Dit kan ook optreden als het bestand `/proc/device-tree/model` niet bestaat:
```bash
ls /proc/device-tree/model
```

Als het niet bestaat:
```bash
sudo apt install -y device-tree-compiler
sudo reboot
```

**Oorzaak 2:** ffmpeg is niet gevonden. Controleer de logs (**Admin → Logs**, type `systeem`).

**Oorzaak 3:** ffmpeg crasht onmiddellijk. Controleer via de terminal:

```bash
cd ~/ksa-bar
source venv/bin/activate
python -c "
from hardware.camera import start_recording, stop_recording
import time
rec = start_recording('test')
time.sleep(3)
stop_recording()
print('Klaar')
"
```

Bekijk de uitvoer — je moet `[REC] Opname gestart:` en `[REC] Opname gestopt:` zien.

---

### Fout F — Opnames worden aangemaakt maar zijn corrupt

**Symptoom:** MP4-bestanden zijn aanwezig maar kunnen niet worden afgespeeld.

**Oorzaak 1:** De Pi verloor stroom tijdens een opname (MP4-container niet afgesloten).

**Oplossing:** Herstel het bestand:
```bash
# Installeer mp4frag als dat beschikbaar is, of gebruik ffmpeg:
ffmpeg -i corrupt_bestand.mp4 -c copy hersteld.mp4
```

**Oorzaak 2:** Schijfruimte vol tijdens opname.

Controleer beschikbare ruimte:
```bash
df -h ~/ksa-bar/videos/
```

Als de schijf vol is:
```bash
# Verwijder handmatig oude opnames
find ~/ksa-bar/videos/ -name "*.mp4" -mtime +30 -delete

# Of pas de bewaarperiode aan via Admin → Instellingen → video_bewaar_dagen
```

---

### Fout G — Opname stopt niet

**Symptoom:** De app denkt dat een opname bezig is, maar ffmpeg is al gestopt.

Herstart de Flask-app:
```bash
sudo systemctl restart ksa-bar
```

Of als je handmatig draait, stop de app met `Ctrl+C` en start opnieuw.

---

### Fout H — Geen video te zien in het admin-paneel

**Symptoom:** Er is een MP4-bestand in `videos/`, maar de knop "Bekijk" verschijnt niet.

**Oorzaak 1:** Het pad in de database klopt niet.

Controleer via **Admin → Database** → tabel `orders` → kolom `video_path`. Het pad moet eruitzien als:
```
2025/10/15/20251015_143022_bestelling_Thomas.mp4
```

**Oorzaak 2:** Het bestand bestaat wel maar staat op de verkeerde locatie.

```bash
# Controleer of het bestand echt bestaat
ls ~/ksa-bar/videos/2025/10/15/
```

---

## Snelle probleemdiagnose — beslisboom

```
Camera werkt niet?
│
├── Bestaat /dev/video0?
│   ├── Nee → Fout B (webcam niet herkend)
│   └── Ja  →
│
├── ffmpeg geïnstalleerd? (ffmpeg -version)
│   ├── Nee → Fout A (ffmpeg installeren)
│   └── Ja  →
│
├── Testfoto maken gelukt? (Stap 0.4)
│   ├── Nee: "Permission denied" → Fout D / Stap 0.7
│   ├── Nee: "Invalid argument"  → Fout D / resolutie aanpassen
│   ├── Nee: "Device busy"       → Fout D / ander programma stoppen
│   └── Ja  →
│
├── Testopname (5 sec) gelukt? (Stap 0.8)
│   ├── Nee → Fout D
│   └── Ja  →
│
├── App maakt lege bestanden?
│   └── Ja → Fout E (IS_RASPBERRY_PI check / ffmpeg crash)
│
└── Opnames corrupt?
    └── Ja → Fout F (stroom / schijfruimte)
```

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
