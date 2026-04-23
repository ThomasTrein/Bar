# KSA Bar Systeem — Installatie op Raspberry Pi 4

> **Voor wie is deze handleiding?**  
> Voor iemand die nog nooit eerder met een Raspberry Pi heeft gewerkt. Elke stap wordt uitgelegd, inclusief *waarom* je het doet. Er zijn ook alternatieve methodes voor wanneer iets niet werkt.

---

## Inhoudsopgave

1. [Wat heb je nodig?](#1-wat-heb-je-nodig)
2. [Hoe werkt dit systeem?](#2-hoe-werkt-dit-systeem)
3. [Ubuntu installeren op de SD-kaart](#3-ubuntu-installeren-op-de-sd-kaart)
4. [Eerste keer opstarten](#4-eerste-keer-opstarten)
5. [Internetverbinding instellen](#5-internetverbinding-instellen)
6. [Systeem updaten](#6-systeem-updaten)
7. [Projectbestanden kopiëren via USB-stick](#7-projectbestanden-kopiëren-via-usb-stick)
8. [Python en de app installeren](#8-python-en-de-app-installeren)
9. [GPIO bedrading aansluiten en instellen](#9-gpio-bedrading-aansluiten-en-instellen)
10. [USB webcam instellen](#10-usb-webcam-instellen)
11. [De app handmatig testen](#11-de-app-handmatig-testen)
12. [Automatisch opstarten bij het aanzetten van de Pi](#12-automatisch-opstarten-bij-het-aanzetten-van-de-pi)
13. [Chromium kiosk-modus instellen](#13-chromium-kiosk-modus-instellen)
14. [Dagelijkse automatische herstart](#14-dagelijkse-automatische-herstart)
15. [Automatische database backups](#15-automatische-database-backups)
16. [Probleemoplossing](#16-probleemoplossing)

---

## 1. Wat heb je nodig?

### Hardware
| Onderdeel | Aanbeveling |
|---|---|
| Raspberry Pi 4 | Model B, minimaal 4 GB RAM |
| SD-kaart | Minimaal **32 GB**, klasse 10 of A1/A2 (snellere kaart = sneller systeem) |
| SD-kaartlezer | Om de SD-kaart te beschrijven vanuit je Windows-pc |
| HDMI touchscreen | Met HDMI-kabel en stroomkabel |
| USB-C stroomadapter | Officieel Raspberry Pi voeding (5V / 3A). Goedkope laders zorgen voor problemen! |
| Ethernetkabel | Tijdelijk tijdens installatie, voor internet |
| USB-stick | Voor het kopiëren van de bestanden |
| USB webcam | Voor de video-opnames |
| USB toetsenbord + muis | Alleen nodig tijdens de installatie |
| 3× solenoid relay module | Voor de frigo-sloten |
| 3× reed contact / deurmagneetsensor | Om te detecteren of een deur open is |
| Jumperwires (DuPont kabels) | Om de GPIO-pinnen te verbinden |

### Software (op je Windows-pc installeren voor je begint)
- **Raspberry Pi Imager** — gratis programma om Ubuntu op de SD-kaart te zetten  
  Download: [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/)

---

## 2. Hoe werkt dit systeem?

Het KSA Bar systeem is een **webapplicatie** gebouwd in Python (Flask). Dat betekent:
- De Raspberry Pi draait als een mini-server
- De kiosk-interface is een **webbrowser** (Chromium) die de lokale website opent
- De admin-pagina is bereikbaar via `http://localhost:5000/admin`
- De database is een enkel bestand (`ksa_bar.db`) — eenvoudig en betrouwbaar
- Via de GPIO-pinnen worden de frigo-sloten (solenoids) aangestuurd
- Een USB-webcam neemt video op bij elke bestelling

**Volgorde van opstarten (automatisch):**
1. Pi start op → Ubuntu laadt
2. Systemd service start de Flask-app
3. GNOME desktop laadt
4. Chromium opent automatisch in kiosk-modus op `http://localhost:5000`

---

## 3. Ubuntu installeren op de SD-kaart

> **Waarom Ubuntu?** Ubuntu is een populaire, goed ondersteunde Linux-distributie. De Desktop-versie bevat al een grafische omgeving zodat de browser automatisch kan opstarten.

### Stap 1: SD-kaart formatteren en Ubuntu installeren

1. Steek de SD-kaart in je **Windows-pc** (via de SD-kaartlezer)
2. Open **Raspberry Pi Imager**
3. Klik op **"CHOOSE DEVICE"** → selecteer **Raspberry Pi 4**
4. Klik op **"CHOOSE OS"** → scroll naar **"Other general-purpose OS"** → **Ubuntu** → **Ubuntu Desktop 24.04 LTS (64-bit)**
5. Klik op **"CHOOSE STORAGE"** → selecteer je SD-kaart  
   ⚠️ **Let op:** alles op de SD-kaart wordt gewist!
6. Klik op **"NEXT"**
7. Er verschijnt een vraag *"Would you like to apply OS customisation settings?"*  
   Klik op **"EDIT SETTINGS"** en stel het volgende in:
   - **Hostname:** `ksa-bar` (de naam van de Pi op het netwerk)
   - **Username:** `ksa`
   - **Password:** kies een wachtwoord dat je onthoudt (bijv. `ksa2024`)
   - Laat WiFi leeg (je gebruikt ethernet)
   - **Locale settings:** Timezone `Europe/Brussels`, Keyboard layout `be`
8. Klik op **"SAVE"** → **"YES"** → **"YES"**
9. Wacht tot het schrijven en verifiëren klaar is (5–15 minuten)
10. Verwijder de SD-kaart veilig uit je pc

### Als het niet werkt — alternatieve methode
Als Raspberry Pi Imager vastloopt of een fout geeft:
1. Download de Ubuntu 24.04 Desktop image rechtstreeks: [https://ubuntu.com/download/raspberry-pi](https://ubuntu.com/download/raspberry-pi)
2. Download **balenaEtcher**: [https://etcher.balena.io/](https://etcher.balena.io/)
3. Open balenaEtcher → selecteer het gedownloade `.img.xz` bestand → selecteer de SD-kaart → Flash

---

## 4. Eerste keer opstarten

1. Steek de SD-kaart in de Raspberry Pi (gleuf aan de onderkant)
2. Sluit de **HDMI-kabel** aan op de Pi en het scherm
3. Sluit het **toetsenbord en de muis** aan
4. Sluit de **ethernetkabel** aan op de Pi en op een router/modem met internet
5. Sluit als **laatste** de USB-C stroomkabel aan → de Pi start automatisch op

> De eerste opstart duurt langer dan normaal (2–5 minuten). Ubuntu wordt voorbereid.

### Ubuntu installatie wizard
Na het opstarten verschijnt een installatiewizard:
1. Kies taal: **Nederlands** (of English als je dat makkelijker vindt)
2. Klik door de stappen: kies tijdzone **Brussel**, toetsenbordindeling **Belgisch**
3. Maak een gebruiker aan:
   - Naam: `ksa`
   - Wachtwoord: `ksa2024` (of wat je zelf kiest — onthoud dit!)
4. Wacht tot de installatie klaar is en de Pi herstart

### Automatisch inloggen instellen
Omdat dit een kiosk is (niemand hoeft in te loggen), stel je automatisch inloggen in:

1. Klik linksboven op het **grid-icoontje** (apps) → zoek **"Instellingen"**
2. Ga naar **Gebruikers**
3. Klik rechtsboven op **"Ontgrendelen"** → voer je wachtwoord in
4. Zet **"Automatisch aanmelden"** aan
5. Herstart de Pi om te bevestigen dat het werkt:
   ```
   sudo reboot
   ```

---

## 5. Internetverbinding instellen

> **Waarom?** Je hebt internet nodig om software te installeren (Python-pakketten, ffmpeg, etc.). Na de installatie hoef je de ethernetkabel niet meer te gebruiken.

### Controleren of internet werkt

Open een **terminal**:
- Klik rechtsboven op het datum/tijd → of rechtsklik op het bureaublad → **"Open Terminal"**
- Als dat niet werkt: druk op de toetsen `Ctrl + Alt + T`

Typ in de terminal:
```bash
ping -c 4 google.com
```

Als je regels ziet zoals `64 bytes from ...` → internet werkt ✅  
Als je `Network unreachable` ziet → zie hieronder

### Als internet niet werkt

**Methode 1:** Via de netwerkinstellingen
1. Klik op het netwerk-icoontje rechtsboven in de balk
2. Klik op **"Bekabeld netwerk"** → zorg dat het aan staat

**Methode 2:** Via terminal
```bash
# Bekijk alle netwerkinterfaces
ip link show

# Activeer de ethernet interface (usually eth0 or enp2s0 of enXXXXXXXX)
sudo ip link set eth0 up

# Vraag een IP-adres op
sudo dhclient eth0
```

**Methode 3:** NetworkManager herstarten
```bash
sudo systemctl restart NetworkManager
```

---

## 6. Systeem updaten

> **Waarom?** Een vers geïnstalleerd systeem heeft altijd updates klaarstaan. Dit zorgt voor betere stabiliteit en veiligheid.

```bash
sudo apt update && sudo apt upgrade -y
```

Dit kan 5–20 minuten duren. Wacht tot het klaar is.

Als er gevraagd wordt om te herstarten:
```bash
sudo reboot
```

### Benodigde extra software installeren

```bash
# Python tools
sudo apt install -y python3-pip python3-venv python3-full

# ffmpeg voor video-opnames
sudo apt install -y ffmpeg

# GPIO libraries voor Ubuntu op Raspberry Pi
sudo apt install -y python3-gpiozero python3-lgpio

# Git (handig voor later)
sudo apt install -y git

# Extra tools
sudo apt install -y curl wget nano
```

> **Wat zijn dit?**
> - `python3-venv` — maakt een afgeschermde Python-omgeving (venv) zodat pakketten niet door elkaar lopen
> - `ffmpeg` — programma dat de webcam-opnames maakt
> - `python3-gpiozero` — Python library om GPIO-pinnen aan te sturen
> - `python3-lgpio` — de backend die gpiozero gebruikt op Ubuntu

### GPIO-rechten instellen

De gebruiker `ksa` moet toestemming hebben om de GPIO-pinnen te gebruiken:
```bash
sudo usermod -aG gpio ksa
sudo usermod -aG dialout ksa
sudo usermod -aG video ksa
```

Na dit commando **moet je uitloggen en opnieuw inloggen** (of rebooten):
```bash
sudo reboot
```

---

## 7. Projectbestanden kopiëren via USB-stick

### Op je Windows-pc: bestanden op de USB-stick zetten

1. Steek de USB-stick in je Windows-pc
2. Kopieer de volledige projectmap (de map met `app.py`, `config.py`, etc.) naar de USB-stick
3. Noem de map op de USB-stick: `ksa-bar`
4. Werp de USB-stick veilig uit

### Op de Raspberry Pi: bestanden kopiëren

1. Steek de USB-stick in de Raspberry Pi
2. Open een terminal (`Ctrl + Alt + T`)
3. Zoek waar de USB-stick verschenen is:
   ```bash
   ls /media/ksa/
   ```
   Je ziet een naam zoals `/media/ksa/USB_STICK` of `/media/ksa/KINGSTON` (de naam van je stick)

4. Kopieer de bestanden naar je thuismap:
   ```bash
   cp -r /media/ksa/*/ksa-bar ~/ksa-bar
   ```
   
   > Als dit niet werkt, vervang `*` door de exacte naam van je stick, bijv.:
   > ```bash
   > cp -r /media/ksa/KINGSTON/ksa-bar ~/ksa-bar
   > ```

5. Controleer of de bestanden goed zijn overgekomen:
   ```bash
   ls ~/ksa-bar
   ```
   Je moet zien: `app.py`, `config.py`, `requirements.txt`, `routes/`, `database/`, etc.

### Als de USB-stick niet automatisch verschijnt

**Methode 1:** Handmatig mounten
```bash
# Zoek de naam van de USB-stick
lsblk

# Je ziet zoiets als sda1 — mount het
sudo mkdir -p /mnt/usb
sudo mount /dev/sda1 /mnt/usb

# Kopieer de bestanden
cp -r /mnt/usb/ksa-bar ~/ksa-bar

# Daarna ontkoppelen
sudo umount /mnt/usb
```

**Methode 2:** Via de bestandsbeheerder
1. Klik op het **bestandsbeheerder**-icoontje in de zijbalk
2. De USB-stick verschijnt links in de lijst
3. Sleep de `ksa-bar` map naar je thuismap

---

## 8. Python en de app installeren

### Virtuele omgeving aanmaken

> **Waarom een virtuele omgeving (venv)?** Dit is een afgeschermde Python-installatie alleen voor dit project. Zo raken de Python-pakketten van de app niet verward met de systeempackages van Ubuntu.

```bash
# Ga naar de projectmap
cd ~/ksa-bar

# Maak een virtuele omgeving aan
python3 -m venv venv

# Activeer de virtuele omgeving
source venv/bin/activate
```

Je ziet nu `(venv)` voor je terminalprompt — dit betekent dat de venv actief is.

### Pakketten installeren

```bash
# Zorg dat pip up-to-date is
pip install --upgrade pip

# Installeer de basis-pakketten
pip install flask>=3.0.0 Pillow>=10.0.0 openpyxl>=3.1.0 reportlab>=4.0.0

# Installeer de GPIO-pakketten (specifiek voor Raspberry Pi)
pip install gpiozero RPi.GPIO
```

### Als een pakket niet installeert

**Fout: `error: externally-managed-environment`**
```bash
# Dit betekent dat Ubuntu het beheer van pip blokkeert.
# Gebruik --break-system-packages ALLEEN binnen de venv:
pip install --break-system-packages flask Pillow openpyxl reportlab gpiozero RPi.GPIO
```

**Fout: `RPi.GPIO` installeert niet**  
RPi.GPIO kan op sommige Ubuntu-versies problemen geven. Gebruik dan alleen gpiozero (de code ondersteunt dit):
```bash
pip install gpiozero lgpio
```

**Controleer of alles goed geïnstalleerd is:**
```bash
pip list | grep -E "Flask|Pillow|openpyxl|reportlab|gpiozero"
```

---

## 9. GPIO bedrading aansluiten en instellen

> **Wat is GPIO?** De Raspberry Pi heeft een rij van 40 pinnen aan de zijkant. Via deze pinnen kun je elektrische apparaten (zoals sloten en sensoren) aansturen. GPIO staat voor "General Purpose Input/Output".

### GPIO-pinout diagram

```
                    Raspberry Pi 4 — GPIO pinnen (BCM nummering)
                    
    [3.3V] [ 1][ 2] [5V   ]
    [SDA ] [ 3][ 4] [5V   ]
    [SCL ] [ 5][ 6] [GND  ]
    [  4 ] [ 7][ 8] [TX   ]
    [GND ] [ 9][10] [RX   ]
    [ 17 ] [11][12] [18   ]   ← RELAY 1 (frigo 1)
    [ 27 ] [13][14] [GND  ]   ← RELAY 2 (frigo 2)
    [ 22 ] [15][16] [23   ]   ← RELAY 3 (frigo 3)
    [3.3V] [17][18] [24   ]
    [MOSI] [19][20] [GND  ]
    [MISO] [21][22] [25   ]
    [SCLK] [23][24] [CE0  ]
    [GND ] [25][26] [CE1  ]
    [  5 ] [29][30] [GND  ]   ← REED 1 (deur 1)
    [  6 ] [31][32] [12   ]   ← REED 2 (deur 2)
    [ 13 ] [33][34] [GND  ]   ← REED 3 (deur 3)
    [ 19 ] [35][36] [16   ]
    [ 26 ] [37][38] [20   ]
    [GND ] [39][40] [21   ]
```

> 💡 **Tip:** Zoek online naar "Raspberry Pi 4 GPIO pinout" voor een kleurrijke afbeelding.  
> Handige website: [https://pinout.xyz/](https://pinout.xyz/)

### Standaard bedrading (uit `config.py`)

| Component | BCM Pin | Fysieke Pin |
|---|---|---|
| Relay frigo 1 | BCM 17 | Pin 11 |
| Relay frigo 2 | BCM 27 | Pin 13 |
| Relay frigo 3 | BCM 22 | Pin 15 |
| Reed contact frigo 1 | BCM 5 | Pin 29 |
| Reed contact frigo 2 | BCM 6 | Pin 31 |
| Reed contact frigo 3 | BCM 13 | Pin 33 |

### Relays aansluiten

Een relay-module heeft meestal 3 aansluitingen aan de GPIO-kant:
- **VCC** → verbind met **3.3V of 5V** van de Pi (pin 1 of pin 2)
- **GND** → verbind met **GND** van de Pi (bijv. pin 6, 9, 14, etc.)
- **IN** → verbind met de **BCM-pin** (bijv. pin 11 voor relay 1)

⚠️ **Let op:** Controleer of je relay-module **actief-hoog** (HIGH = aan) of **actief-laag** (LOW = aan) is.  
- Actief-hoog: `RELAY_ACTIVE_HIGH = True` (standaard in de code)
- Actief-laag: zet `RELAY_ACTIVE_HIGH = False` in `config.py`

### Reed contacten aansluiten

Een reed contact heeft 2 draden:
- Draad 1 → verbind met de **BCM-pin** (bijv. pin 29 voor reed 1)
- Draad 2 → verbind met **GND** van de Pi

De code gebruikt interne pull-up weerstand (`pull_up=True`), dus je hebt geen externe weerstand nodig.

### GPIO-pinnen aanpassen in `config.py`

Als jouw bedrading anders is dan de standaard, pas je `config.py` aan:

```bash
nano ~/ksa-bar/config.py
```

Zoek deze regels en pas de nummers aan naar jouw bedrading:
```python
# GPIO pins (BCM nummering)
RELAY_PINS = {1: 17, 2: 27, 3: 22}   # frigo 1, 2, 3
REED_PINS  = {1: 5,  2: 6,  3: 13}   # frigo 1, 2, 3
RELAY_ACTIVE_HIGH = True              # False als relay actief-laag is
```

Sla op: `Ctrl + O` → Enter → `Ctrl + X`

> **BCM vs BOARD nummering:** De code gebruikt BCM-nummering. Dit zijn de getallen op het schema hierboven (bijv. BCM 17, BCM 27). Niet de fysieke pinnummers (1 t/m 40).

---

## 10. USB webcam instellen

1. Sluit de USB-webcam aan op een USB-poort van de Pi
2. Controleer of de Pi de webcam ziet:
   ```bash
   ls /dev/video*
   ```
   Je ziet `/dev/video0` (en soms `/dev/video1`, `/dev/video2` etc.)

3. Test of de webcam werkt:
   ```bash
   ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 /tmp/test.jpg
   ```
   Als er een bestand `/tmp/test.jpg` aangemaakt wordt → webcam werkt ✅

### Als de webcam niet op `/dev/video0` staat

Controleer welk apparaatnummer jouw webcam heeft:
```bash
v4l2-ctl --list-devices
```

Als je webcam bijv. op `/dev/video2` staat, pas dan `config.py` aan:
```python
CAMERA_DEVICE = 2  # verander van 0 naar 2
```

### Als ffmpeg de webcam niet herkent

```bash
# Installeer extra tools
sudo apt install -y v4l-utils

# Bekijk welke formaten de webcam ondersteunt
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

Soms moet je de resolutie aanpassen als de webcam `1280x720` niet ondersteunt. Pas in `config.py` aan:
```python
CAMERA_RESOLUTION = (640, 480)   # lagere resolutie als 1280x720 niet werkt
CAMERA_FPS = 15
```

---

## 11. De app handmatig testen

> **Waarom eerst handmatig testen?** Zodat je eventuele fouten kunt zien voordat je alles automatisch laat draaien.

```bash
# Ga naar de projectmap
cd ~/ksa-bar

# Activeer de virtuele omgeving
source venv/bin/activate

# Start de app
python app.py
```

Je moet zien:
```
[OK] Database geinitialiseerd.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://[::]:5000
```

Open nu **Chromium** (zoek in de apps) en ga naar:
```
http://localhost:5000
```

Je moet de kiosk-interface zien.

### De app stoppen
Druk in de terminal op `Ctrl + C`

### Als de app een fout geeft

**Fout: `ModuleNotFoundError: No module named 'flask'`**
```bash
# De venv is niet geactiveerd, of de installatie is mislukt
source venv/bin/activate
pip install flask
```

**Fout: `Address already in use`**
```bash
# Poort 5000 is al in gebruik, zoek welk proces dat is
sudo lsof -i :5000

# Stop dat proces (vervang 1234 door het PID uit de vorige uitvoer)
kill -9 1234
```

**Fout: `PermissionError` bij GPIO**
```bash
# Controleer of de gebruiker in de gpio-groep zit
groups ksa

# Als gpio er niet bij staat:
sudo usermod -aG gpio ksa
# Dan uitloggen en opnieuw inloggen, of:
sudo reboot
```

---

## 12. Automatisch opstarten bij het aanzetten van de Pi

> **Waarom systemd?** Systemd is het systeem dat Ubuntu gebruikt om programma's te starten en te beheren. Door een "service" aan te maken, start de Flask-app automatisch op bij het opstarten van de Pi, ook als er iets misgaat (de app herstart zichzelf automatisch).

### Service-bestand aanmaken

```bash
sudo nano /etc/systemd/system/ksa-bar.service
```

Kopieer de volgende inhoud (pas de paden aan als je een andere gebruikersnaam hebt dan `ksa`):

```ini
[Unit]
Description=KSA Bar Systeem
# Wacht tot het systeem volledig opgestart is
After=network.target multi-user.target

[Service]
Type=simple
# Gebruiker die de app draait
User=ksa
Group=ksa
# Map waar app.py staat
WorkingDirectory=/home/ksa/ksa-bar
# Commando om de app te starten
ExecStart=/home/ksa/ksa-bar/venv/bin/python app.py
# Automatisch herstarten als de app crasht
Restart=always
RestartSec=5
# Omgevingsvariabelen
Environment=PYTHONUNBUFFERED=1

[Install]
# Start bij het opstarten van het systeem
WantedBy=multi-user.target
```

Sla op: `Ctrl + O` → Enter → `Ctrl + X`

### Service activeren

```bash
# Systemd opnieuw laden zodat de nieuwe service herkend wordt
sudo systemctl daemon-reload

# De service automatisch laten starten bij opstarten
sudo systemctl enable ksa-bar

# De service nu starten (zonder te rebooten)
sudo systemctl start ksa-bar

# Controleer of de service draait
sudo systemctl status ksa-bar
```

Je moet zien: `Active: active (running)`

### Service beheren

```bash
# Status bekijken
sudo systemctl status ksa-bar

# Service stoppen
sudo systemctl stop ksa-bar

# Service herstarten
sudo systemctl restart ksa-bar

# Logs bekijken (wat de app uitprint)
sudo journalctl -u ksa-bar -f

# Laatste 50 regels logs
sudo journalctl -u ksa-bar -n 50
```

### Als de service niet start

```bash
# Bekijk de foutmeldingen
sudo journalctl -u ksa-bar -n 100 --no-pager
```

Veel voorkomende problemen:
- **Fout: `venv/bin/python not found`** → de venv bestaat niet op het opgegeven pad
  ```bash
  ls /home/ksa/ksa-bar/venv/bin/python
  # Als dit niet bestaat:
  cd /home/ksa/ksa-bar
  python3 -m venv venv
  source venv/bin/activate
  pip install flask Pillow openpyxl reportlab gpiozero RPi.GPIO
  ```
- **Fout: `Permission denied`** → bestandsrechten aanpassen
  ```bash
  sudo chown -R ksa:ksa /home/ksa/ksa-bar
  ```

---

## 13. Chromium kiosk-modus instellen

> **Wat is kiosk-modus?** Chromium opent in volledig scherm zonder adresbalk, tabbladen of knoppen. De gebruiker ziet alleen de KSA Bar interface. Dit is bedoeld voor gebruik als een "apparaat" (kiosk), niet als gewone computer.

### Wacht-script aanmaken

De browser moet wachten tot de Flask-app gestart is. Daarvoor maken we een wacht-script:

```bash
nano ~/ksa-bar/start_kiosk.sh
```

Inhoud:
```bash
#!/bin/bash

# Wacht tot de Flask-app bereikbaar is (max 60 seconden)
echo "Wachten op KSA Bar app..."
for i in $(seq 1 60); do
    if curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "App bereikbaar, browser starten..."
        break
    fi
    sleep 1
done

# Schermbeveiliging uitschakelen (anders gaat het scherm op zwart)
xset s off
xset s noblank
xset -dpms

# Chromium starten in kiosk-modus
chromium-browser \
    --kiosk \
    --app=http://localhost:5000 \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --no-first-run \
    --start-maximized
```

Sla op: `Ctrl + O` → Enter → `Ctrl + X`

Maak het bestand uitvoerbaar:
```bash
chmod +x ~/ksa-bar/start_kiosk.sh
```

### Autostart instellen in GNOME

```bash
# Maak de autostart-map aan als die niet bestaat
mkdir -p ~/.config/autostart

# Maak een autostart-bestand aan
nano ~/.config/autostart/ksa-kiosk.desktop
```

Inhoud:
```ini
[Desktop Entry]
Type=Application
Name=KSA Bar Kiosk
Comment=Start KSA Bar kiosk browser
Exec=/home/ksa/ksa-bar/start_kiosk.sh
X-GNOME-Autostart-enabled=true
```

Sla op: `Ctrl + O` → Enter → `Ctrl + X`

### Test de kiosk-modus

```bash
# Herstart de Pi
sudo reboot
```

Na het herstarten moet de Pi automatisch:
1. Inloggen als `ksa`
2. De Flask-app starten (via systemd)
3. Chromium openen in volledig scherm op `http://localhost:5000`

### Kiosk-modus verlaten

Als je tijdens gebruik het scherm wilt verlaten:
- Druk op `Alt + F4` om Chromium te sluiten
- Of druk op `Ctrl + Alt + T` om een terminal te openen

### Als de browser niet automatisch start

**Methode 1:** Controleer het autostart-bestand
```bash
cat ~/.config/autostart/ksa-kiosk.desktop
```

**Methode 2:** Handmatig testen
```bash
bash ~/ksa-bar/start_kiosk.sh
```

**Methode 3:** GNOME Tweaks gebruiken
```bash
sudo apt install gnome-tweaks
# Open Tweaks → Startup Applications
```

**Methode 4:** Als `chromium-browser` niet gevonden wordt
```bash
# Controleer de naam van Chromium
which chromium
which chromium-browser

# Installeer Chromium als het er niet is
sudo apt install chromium-browser
# of
sudo snap install chromium
```
Als de snap-versie geïnstalleerd is, gebruik dan `chromium` in plaats van `chromium-browser` in het script.

---

## 14. Dagelijkse automatische herstart

> **Waarom een dagelijkse herstart?** De Pi draait 24/7. Door elke nacht te herstarten, wordt het geheugen geleegd, worden updates verwerkt en blijft het systeem stabiel. De code heeft al een instelling `pi_reboot_tijd: '06:30'` — hier geven we dat ook echt uitvoer.

### Crontab instellen

```bash
# Open de crontab-editor (als root, want alleen root kan de Pi herstarten)
sudo crontab -e
```

Als er gevraagd wordt welke editor je wilt: kies **1** (nano)

Voeg deze regel toe aan het einde van het bestand:
```
# Dagelijkse herstart om 06:30
30 6 * * * /sbin/reboot
```

> **Uitleg van de tijdnotatie:** `30 6 * * *` betekent: minuut 30, uur 6, elke dag, elke maand, elke dag van de week → dus om 06:30 elke dag.

Sla op: `Ctrl + O` → Enter → `Ctrl + X`

### Controleer of de crontab goed is
```bash
sudo crontab -l
```

Je moet de lijn `30 6 * * * /sbin/reboot` zien.

### Andere herstartijden instellen

| Tijd | Crontab-regel |
|---|---|
| 06:30 | `30 6 * * * /sbin/reboot` |
| 03:00 | `0 3 * * * /sbin/reboot` |
| 02:30 | `30 2 * * * /sbin/reboot` |

---

## 15. Automatische database backups

> **Waarom backups?** De database (`ksa_bar.db`) bevat alle bestellingen, personen en instellingen. Als het SD-kaartje crasht zonder backup, ben je alles kwijt. De code maakt automatisch timestamped backups in de `backups/` map en bewaart de laatste 7 kopieën.

### Backup-script aanmaken

```bash
nano ~/ksa-bar/backup.sh
```

Inhoud:
```bash
#!/bin/bash
cd /home/ksa/ksa-bar
/home/ksa/ksa-bar/venv/bin/python -c "
from services.backup import backup_database
pad = backup_database()
print(f'Backup gemaakt: {pad}')
"
```

Sla op en maak uitvoerbaar:
```bash
chmod +x ~/ksa-bar/backup.sh
```

### Backup testen

```bash
bash ~/ksa-bar/backup.sh
```

Je moet zien: `[BACKUP] Backup: /home/ksa/ksa-bar/backups/ksa_bar_XXXXXXXX_XXXXXX.db`

Controleer:
```bash
ls ~/ksa-bar/backups/
```

### Automatische backup via crontab

```bash
crontab -e
```

Voeg toe (backup elke dag om 05:00, vóór de herstart):
```
# Dagelijkse database backup om 05:00
0 5 * * * /home/ksa/ksa-bar/backup.sh >> /home/ksa/ksa-bar/backup.log 2>&1
```

### Backups kopiëren naar USB-stick

Als je een backup wilt opslaan op een USB-stick:
```bash
# Steek USB-stick in
ls /media/ksa/

# Kopieer alle backups (vervang NAAM door de naam van je stick)
cp ~/ksa-bar/backups/*.db /media/ksa/NAAM/

# Of kopieer alleen de nieuwste backup
ls -t ~/ksa-bar/backups/ | head -1 | xargs -I{} cp ~/ksa-bar/backups/{} /media/ksa/NAAM/
```

---

## 16. Probleemoplossing

### De app start niet op

```bash
# Bekijk de logs van de systemd service
sudo journalctl -u ksa-bar -n 100 --no-pager

# Probeer handmatig te starten om de fout te zien
cd ~/ksa-bar
source venv/bin/activate
python app.py
```

---

### Het scherm gaat op zwart / screensaver

```bash
# Voeg dit toe aan het begin van start_kiosk.sh (staat er al in):
xset s off
xset s noblank
xset -dpms

# Als dit niet werkt, schakel de GNOME screensaver uit:
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.session idle-delay 0
```

---

### GPIO werkt niet

```bash
# Controleer of de gpio-groep bestaat
cat /etc/group | grep gpio

# Controleer of de gebruiker in de groep zit
groups ksa

# Als de groep gpio niet bestaat, maak hem aan:
sudo groupadd gpio

# Voeg rechten toe via udev-regels
echo 'SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"' | sudo tee /etc/udev/rules.d/99-gpio.rules
sudo udevadm control --reload-rules

# Voeg gebruiker toe aan groep
sudo usermod -aG gpio ksa

# Herstart
sudo reboot
```

**Alternatief: gpiozero met lgpio backend**
```bash
source ~/ksa-bar/venv/bin/activate
pip install lgpio gpiozero
```

---

### Webcam geeft geen beeld

```bash
# Controleer of de webcam herkend wordt
lsusb

# Controleer de videodevices
ls /dev/video*

# Test een opname van 5 seconden
ffmpeg -f v4l2 -i /dev/video0 -t 5 /tmp/test.mp4

# Als video0 bezet is door iets anders, probeer video2:
ffmpeg -f v4l2 -i /dev/video2 -t 5 /tmp/test.mp4
```

---

### "Port already in use" — poort 5000 bezet

```bash
# Zoek welk proces poort 5000 gebruikt
sudo ss -lptn 'sport = :5000'

# Of:
sudo lsof -i :5000

# Stop het proces (vervang PID door het gevonden getal)
sudo kill -9 PID
```

---

### Pi start op maar de kiosk-browser verschijnt niet

```bash
# Controleer of de systemd service draait
sudo systemctl status ksa-bar

# Controleer het autostart-bestand
cat ~/.config/autostart/ksa-kiosk.desktop

# Controleer of het script uitvoerbaar is
ls -la ~/ksa-bar/start_kiosk.sh

# Start het script handmatig
bash ~/ksa-bar/start_kiosk.sh
```

---

### Na een update werkt de app niet meer

```bash
cd ~/ksa-bar
source venv/bin/activate

# Herinstalleer alle pakketten
pip install --force-reinstall flask Pillow openpyxl reportlab gpiozero

# Herstart de service
sudo systemctl restart ksa-bar
```

---

### De database is beschadigd

```bash
# Controleer de database
sqlite3 ~/ksa-bar/ksa_bar.db "PRAGMA integrity_check;"

# Herstel vanuit een backup (pas de datum aan)
ls ~/ksa-bar/backups/
cp ~/ksa-bar/backups/ksa_bar_XXXXXXXX_XXXXXX.db ~/ksa-bar/ksa_bar.db

# Herstart de app
sudo systemctl restart ksa-bar
```

---

### Vrije schijfruimte controleren

```bash
df -h /

# Bekijk hoeveel ruimte de videos innemen
du -sh ~/ksa-bar/videos/

# Verwijder videos ouder dan 40 dagen handmatig
find ~/ksa-bar/videos/ -name "*.mp4" -mtime +40 -delete
```

---

### Volledig overzicht van nuttige commando's

| Commando | Wat het doet |
|---|---|
| `sudo systemctl status ksa-bar` | Status van de app-service |
| `sudo systemctl restart ksa-bar` | App herstarten |
| `sudo journalctl -u ksa-bar -f` | Live logs bekijken |
| `sudo reboot` | Pi herstarten |
| `sudo shutdown now` | Pi veilig uitzetten |
| `df -h` | Schijfruimte bekijken |
| `free -h` | RAM-gebruik bekijken |
| `top` | CPU/RAM live bekijken (stop met `q`) |
| `ip addr` | IP-adressen bekijken |
| `ls /dev/video*` | Beschikbare webcams |

---

## Samenvatting van de bestandslocaties

| Wat | Locatie op de Pi |
|---|---|
| Projectmap | `/home/ksa/ksa-bar/` |
| Database | `/home/ksa/ksa-bar/ksa_bar.db` |
| Backups | `/home/ksa/ksa-bar/backups/` |
| Video-opnames | `/home/ksa/ksa-bar/videos/` |
| Configuratie | `/home/ksa/ksa-bar/config.py` |
| Systemd service | `/etc/systemd/system/ksa-bar.service` |
| Autostart browser | `/home/ksa/.config/autostart/ksa-kiosk.desktop` |
| Kiosk-script | `/home/ksa/ksa-bar/start_kiosk.sh` |
| Backup-script | `/home/ksa/ksa-bar/backup.sh` |
| Backup log | `/home/ksa/ksa-bar/backup.log` |

---

*Installatiehandleiding voor KSA Bar Systeem — Raspberry Pi 4 met Ubuntu Desktop 24.04 LTS*
