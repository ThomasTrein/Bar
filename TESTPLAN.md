# KSA Bar — Testplan

> Dit document beschrijft alle scenario's en losse testen die uitgevoerd moeten worden om het volledige systeem (Raspberry Pi, sloten, reed contacten, camera, software) te valideren vóór productie.

---

## Inhoudsopgave

1. [Hardware testen — losse componenten](#1-hardware-testen--losse-componenten)
2. [Bestelling — normale flow](#2-bestelling--normale-flow)
3. [Bestelling — randgevallen & foutscenarios](#3-bestelling--randgevallen--foutscenarios)
4. [Deuren & sloten — specifieke scenarios](#4-deuren--sloten--specifieke-scenarios)
5. [Baravond modus](#5-baravond-modus)
6. [Aanvulmodus (stock bijvullen)](#6-aanvulmodus-stock-bijvullen)
7. [De Bond modus](#7-de-bond-modus)
8. [Productbeperkingen & globally locked](#8-productbeperkingen--globally-locked)
9. [Admin-paneel](#9-admin-paneel)
10. [Camera & opnames](#10-camera--opnames)
11. [Systeem & Raspberry Pi](#11-systeem--raspberry-pi)
12. [Database & backups](#12-database--backups)

---

## 1. Hardware testen — losse componenten

### 1.1 Solenoid relays (sloten)

| # | Test | Verwacht resultaat |
|---|------|--------------------|
| H1 | Verbind relay module met Pi — zet spanning op | Relay klikt, slot springt open |
| H2 | Stuur GPIO-pin `RELAY_PINS[1]` (BCM 17) HIGH via hardware-testpagina | Deur 1 ontgrendelt |
| H3 | Stuur GPIO-pin `RELAY_PINS[2]` (BCM 27) HIGH | Deur 2 ontgrendelt |
| H4 | Stuur GPIO-pin `RELAY_PINS[3]` (BCM 22) HIGH | Deur 3 ontgrendelt |
| H5 | Zet pin LOW | Slot vergrendelt terug |
| H6 | Test alle 3 sloten tegelijk ontgrendeld | Alle 3 open tegelijk |
| H7 | Test `RELAY_ACTIVE_HIGH = False` als relay actief-laag is | Stel in config.py in en hertest |

### 1.2 Reed contacten (deursensors)

| # | Test | Verwacht resultaat |
|---|------|--------------------|
| R1 | Reed contact deur 1 (BCM 5) — open deur | Sensor detecteert "open" (`is_pressed = True`) |
| R2 | Reed contact deur 1 — sluit deur | Sensor detecteert "gesloten" (`is_pressed = False`) |
| R3 | Herhaal voor deur 2 (BCM 6) en deur 3 (BCM 13) | Zelfde resultaat |
| R4 | Controleer bounce_time (50 ms) — snel open/dicht | Geen valse detecties |
| R5 | Reed contact simulatie via hardware-testpagina (`simulate-open`, `simulate-close`) | Statuswijziging zichtbaar in API-respons |
| R6 | Controleer of `/api/deur-status` de correcte status weergeeft | JSON toont `open: true/false` per deur |

### 1.3 GPIO pinout verificatie

| # | Test | Verwacht resultaat |
|---|------|--------------------|
| G1 | Controleer `config.py`: `RELAY_PINS = {1:17, 2:27, 3:22}` | Klopt met de bedrading |
| G2 | Controleer `config.py`: `REED_PINS = {1:5, 2:6, 3:13}` | Klopt met de bedrading |
| G3 | Voer `IS_RASPBERRY_PI` check uit (`/proc/device-tree/model` bestaat) | `True` op de Pi, `False` op PC |

---

## 2. Bestelling — normale flow

| # | Scenario | Stappen | Verwacht resultaat |
|---|----------|---------|-------------------|
| B1 | Eén persoon, één product | Kies persoon → kies product → bevestig | Deur ontgrendelt, na sluiting vergrendelt, bestelling aangerekend |
| B2 | Eén persoon, meerdere producten | Voeg 2+ producten toe | Beide deuren (indien anders) ontgrendeld, alles aangerekend |
| B3 | Meerdere personen in 1 bestelling | Persoon 1 kiest product, voeg persoon 2 toe, persoon 2 kiest product | Elk item correct gekoppeld aan juiste persoon in `order_items` |
| B4 | Product met bak-grootte | Kies product met bakbestelling | Bak correct verwerkt, stock daalt met bak-grootte |
| B5 | Stock daalt correct | Controleer stock vóór en na bestelling | Stock verminderd met het juiste aantal |
| B6 | Rekening klopt | Ga naar admin → Rekening | Totaalbedrag correct opgeteld |
| B7 | Video opgeslagen | Na bestelling → admin → bestellingen | Video-link zichtbaar en speelbaar |

---

## 3. Bestelling — randgevallen & foutscenarios

| # | Scenario | Stappen | Verwacht resultaat |
|---|----------|---------|-------------------|
| E1 | **Deur nooit geopend (timeout)** | Bevestig bestelling → doe GEEN deur open → wacht tot timeout | Bestelling geannuleerd, bedrag NIET aangerekend, stock hersteld, badge "Deuren nooit geopend" in admin |
| E2 | **Één deur geopend, andere niet** | 2 deuren nodig — open slechts 1 deur | Enkel de geopende deur telt; de andere krijgt timeout maar bestelling gaat door (deels geopend) |
| E3 | **Bestelling annuleren vóór bevestiging** | Klik "Annuleren" op overzichtspagina | Bestelling verwijderd, geen items aangerekend, geen deur ontgrendeld |
| E4 | **Bestelling annuleren op wachtscherm** | Klik "Annuleren" tijdens wachten | Opname gestopt, bestelling gemarkeerd als geannuleerd, geen bedrag aangerekend |
| E5 | **Product zonder deur gekoppeld** | Bestelling met product zonder `product_doors` | Bestelling direct klaar (geen deur nodig), onmiddellijk aangerekend |
| E6 | **Stock is 0** | Probeer product te bestellen met stock 0 | Product niet bestelbaar OF stock gaat negatief (afhankelijk van implementatie) |
| E7 | **Persoon niet actief** | Deactiveer persoon — probeer te bestellen | Persoon niet zichtbaar in lijst |
| E8 | **Dubbele bestelling zelfde persoon** | Twee bestellingen tegelijk (2 browser-tabs) | Beide afzonderlijk verwerkt met eigen `ot`-token |

---

## 4. Deuren & sloten — specifieke scenarios

| # | Scenario | Verwacht resultaat |
|---|----------|--------------------|
| D1 | Deur handmatig opengetrokken vóór ontgrendeling | Reed-contact detecteert dit, geen vergrendeling actief |
| D2 | Ontgrendel deur → open deur → sluit deur → wacht | Slot vergrendelt automatisch na sluiting |
| D3 | Auto-lock: product koppelt aan 2 deuren — open 1 | De andere deur vergrendelt automatisch (niet meer nodig) |
| D4 | Timeout-timer loopt af (standaard 120 sec) | Slot vergrendelt na timeout, log "Deur X timeout" |
| D5 | Alle 3 deuren tegelijk ontgrendeld (baravond/aanvullen) | Alle 3 sloten open, reed contacten actief |
| D6 | Reed contact-kabel losgetrokken | Sensor geeft continue "open" of "gesloten" — controleer gedrag |
| D7 | Relay geeft geen respons | Log bevat foutmelding; slot blijft vergrendeld |
| D8 | Deur open tijdens vergrendelen | Slot mag niet vergrendelen als deur open is (mechanische bescherming) |

---

## 5. Baravond modus

| # | Scenario | Verwacht resultaat |
|---|----------|-------------------|
| BA1 | Baravond starten | Kies naam, vul begininventaris in → alle deuren ontgrendeld, opname gestart |
| BA2 | Opname tijdens baravond | Opname-bestand aangemaakt in `videos/` |
| BA3 | Baravond stoppen | Kies stopper-naam → deuren vergrendeld, opname gestopt, eindinventaris opgeslagen |
| BA4 | Verbruik berekend | `eind_inventaris - start_inventaris` correct berekend en opgeslagen |
| BA5 | Aanvulmodus starten terwijl baravond actief | Foutmelding: "Baravond is actief" |
| BA6 | Baravond bekijken in admin | Video en inventaris zichtbaar in baravond-detail |
| BA7 | Meerdere baravonden na elkaar | Elke avond apart opgeslagen met correcte tijdstip |

---

## 6. Aanvulmodus (stock bijvullen)

| # | Scenario | Verwacht resultaat |
|---|----------|-------------------|
| AV1 | Aanvulmodus starten | Kies persoon → alle deuren ontgrendeld, opname gestart |
| AV2 | Stock toevoegen via FIFO | Nieuwe batch aangemaakt in `fifo_batches`, stock omhoog |
| AV3 | Aanvulmodus stoppen | Deuren vergrendeld, opname gestopt |
| AV4 | Baravond starten terwijl aanvulmodus actief | Foutmelding: "Aanvulmodus is actief" |
| AV5 | Aankoopprijs correct opgeslagen per batch | Controleer `fifo_batches` in database-viewer |

---

## 7. De Bond modus

| # | Scenario | Verwacht resultaat |
|---|----------|-------------------|
| BO1 | Klik "De Bond" op startscherm | Opname gestart, naamkeuze getoond |
| BO2 | Kies naam | Productoverzicht met deuren getoond |
| BO3 | Kies producten en bevestig | Deuren ontgrendeld per product, bestelling opgeslagen als type `bond` |
| BO4 | Terugzetten van producten | Kies producten die teruggelegd worden → stock hersteld via `return_to_oldest_fifo` |
| BO5 | Opname gestopt na bestelling | Opname-bestand aangemaakt en opgeslagen |

---

## 8. Productbeperkingen & globally locked

| # | Scenario | Verwacht resultaat |
|---|----------|-------------------|
| P1 | Product instellen als "Geblokkeerd voor iedereen" bij aanmaken | Alle bestaande personen krijgen product in `person_blocked_products` |
| P2 | Nieuw persoon aanmaken na globally locked product | Nieuwe persoon krijgt het product automatisch geblokkeerd |
| P3 | Globally locked in bewerkscherm aanzetten (0→1) | Alle personen krijgen direct blokkade toegevoegd |
| P4 | Globally locked in bewerkscherm uitzetten (1→0) | Alle blokkades voor dat product verwijderd |
| P5 | Uitzondering aanmaken voor 1 persoon | Ga naar Beperkingen van die persoon → zet vinkje UIT voor het globally locked product → opslaan |
| P6 | Controleer kiosk — persoon met uitzondering | Persoon kan het product bestellen, anderen niet |
| P7 | Hele categorie blokkeren voor persoon | Alle producten uit die categorie niet bestelbaar |
| P8 | Product geblokkeerd via categorie EN apart — combinatie | Product blijft geblokkeerd |

---

## 9. Admin-paneel

| # | Scenario | Verwacht resultaat |
|---|----------|-------------------|
| A1 | Inloggen met juist wachtwoord | Dashboard geladen |
| A2 | Inloggen met fout wachtwoord | Foutmelding, geen toegang |
| A3 | Automatische uitlog na inactiviteit (standaard 10 min) | Redirect naar kiosk-startscherm |
| A4 | Product aanmaken, bewerken, verwijderen | Correct zichtbaar in kiosk daarna |
| A5 | Persoon aanmaken, bewerken, deactiveren | Deactiveren = niet meer zichtbaar op kiosk |
| A6 | Categorie aanmaken, bewerken, verwijderen | Volgorde klopt in kiosk |
| A7 | Bestelling annuleren vanuit admin | `geannuleerd=1`, bedrag afgetrokken van rekening |
| A8 | Rekening bekijken per persoon | Correcte totalen gebaseerd op order_items |
| A9 | Winst berekening | Verkoopprijs - aankoopprijs (FIFO) klopt |
| A10 | Database-viewer | Correcte tabel-inhoud weergegeven |
| A11 | Instellingen wijzigen (timeout, wachtwoord, ...) | Instellingen onmiddellijk actief |
| A12 | Hardware-testpagina — manueel slot ontgrendelen | Slot reageert |
| A13 | Hardware-testpagina — reed-contact simuleren | Status zichtbaar in UI |

---

## 10. Camera & opnames

| # | Scenario | Verwacht resultaat |
|---|----------|-------------------|
| C1 | USB-webcam aangesloten op `/dev/video0` | `ffmpeg` kan signaal lezen |
| C2 | Opname gestart bij eerste persoon kiezen in bestelling | MP4-bestand aangemaakt in `videos/YYYY/MM/DD/` |
| C3 | Opname gestopt na deuren dicht | Bestand correct afgesloten, afspeelbaar |
| C4 | Opname gestopt bij annuleren | Bestand aangemaakt maar korte opname |
| C5 | Opname bij baravond start/stop | Apart bestand per baravond |
| C6 | Opname bij aanvulmodus start/stop | Apart bestand per aanvulsessie |
| C7 | Opname bij De Bond | Apart bestand |
| C8 | Twee opnames tegelijk proberen starten | Vorige opname automatisch gestopt, nieuwe gestart |
| C9 | ffmpeg niet geïnstalleerd | Logt fout, stub-bestand aangemaakt, systeem crasht niet |
| C10 | Video meer dan 40 dagen oud | Automatisch verwijderd bij cleanup |
| C11 | Video bekijken via admin | Link werkt, video speelt af |
| C12 | Opname op development-PC (geen Pi) | Leeg stub-MP4 aangemaakt, geen crash |

---

## 11. Systeem & Raspberry Pi

| # | Scenario | Verwacht resultaat |
|---|----------|-------------------|
| S1 | Pi opstart na stroom onderbreking | App start automatisch via systemd-service |
| S2 | Chromium opent automatisch in kiosk-modus | Browser gaat direct naar `http://localhost:5000` |
| S3 | App bereikbaar via netwerk (`http://<pi-ip>:5000`) | Admin-paneel toegankelijk van andere PC |
| S4 | Dagelijkse herstart om 06:30 | Cron-job herstart de Pi, app herstart automatisch |
| S5 | Pi crasht tijdens bestelling | Na herstart: bestelling was gecommit maar deuren vergrendeld → controleer status |
| S6 | SD-kaart vol | Applicatie logt fout, opnames mislukken, rest werkt nog |
| S7 | Hoge CPU-belasting (opname + 3 deuren actief) | Systeem reageert nog steeds, geen timeouts |
| S8 | Temperatuur Pi controleren | Onder 80°C bij normale werking |
| S9 | Touchscreen responsief | Alle knoppen correct bedienbaar met vinger |
| S10 | Screensaver timeout (standaard 2 min) | Kiosk keert terug naar startscherm na inactiviteit |

---

## 12. Database & backups

| # | Scenario | Verwacht resultaat |
|---|----------|-------------------|
| DB1 | Database-bestand `ksa_bar.db` aanwezig | Bestand bestaat op correcte locatie |
| DB2 | `init_db()` uitvoeren op bestaande database | Geen dataverlies door `ALTER TABLE IF NOT EXISTS` |
| DB3 | Automatische backup aangemaakt | Bestand in `backups/` met timestamp |
| DB4 | Backup herstellen | Database vervangen en app herstart → data intact |
| DB5 | Foreign keys ON | Verwijderen persoon → cascade naar `person_blocked_products` |
| DB6 | WAL-mode actief | Geen corruptie bij gelijktijdige lees/schrijf-operaties |

---

## Checklist voor productie-oplevering

- [ ] Alle hardware-testen (H1–H7, R1–R6, G1–G3) geslaagd
- [ ] Normale bestelling (B1–B7) werkt correct
- [ ] Timeout/annuleer (E1–E8) correct afgehandeld
- [ ] Globally locked producten (P1–P8) correct
- [ ] Baravond, aanvullen, De Bond werken end-to-end
- [ ] Camera opnames aangemaakt en afspeelbaar
- [ ] Admin-paneel volledig functioneel
- [ ] Pi herstart en auto-start getest
- [ ] Backup aanwezig en herstelbaar
