## Dingen om toe te voegen
De logs:
Wanneer moet er gefilmd worden en hoelang?
- vanaf er op bestelling starten wordt geklikt dan moet er gefilmd worden tot dat alle sloten dicht zijn en de reed sensors dicht zijn.
- als er op bestelling starten wordt geklikt dan moet er gefilmd worden en ze gaan terug naar het homescreen via eender welke knop dan moet er niet meer gefilmd worden.
- 
---

## Te bespreken
- Wat moet er allemaal gefilmd worden en wat wordt er in de logs geschreven worden.
- Alle modussen en wanneer moet je je naam selecteren.
- Crasht er iets?
- Is er nog ergens data nodig die er niet in zit.
- Is er een link nodig?

---

# Analyse **KSA Bar app**

## 🎨 UX / UI

- **Snelbestelknop per persoon op home**
  Toon de 3-5 meest bestelde personen direct op het startscherm als grote knoppen. Probleem: te veel stappen voor een herhalende actie. *Zoals McDonald's kiosk "recent orders".*

- **Bestelling ruilknop zonder annuleren**
  Laat toe om tijdens een bestelling van persoon te wisselen zonder opnieuw te starten. Nu moet je annuleren en herbeginnen als je de verkeerde persoon kiest.

- **Visuele stockwaarschuwing op productkaart**
  Kleurovergang van groen → oranje → rood naarmate stock daalt. Nu is er enkel "NIET IN STOCK" maar geen vroege waarschuwing.

- **Bevestigingsscherm met tijdslimiet**
  Automatisch annuleren na 60 seconden inactiviteit op het bevestigingsscherm. Voorkomt half-afgeronde bestellingen die de frigo blokkeren.

- **Pincode per persoon (optioneel)**
  Laat personen een 4-cijferige PIN instellen i.p.v. hun foto te zoeken. Sneller voor vaste leden. *Zoals sportclubkassa's.*

---

## 📊 Beheer & Inzichten

- **Dashboard live stock-alerts**
  Push notificatie (of zichtbare badge) in admin als een product onder een instelbare drempelwaarde zakt. Oplossing: je merkt pas dat iets op is als het al te laat is.

- **Winst per baravond grafiek**
  Visualiseer omzet, kosten en winst per baravond over tijd als lijngrafiek. Nu zijn er enkel losse detailpagina's zonder trend.

- **Meest bestelde producten ranking**
  Top 10 producten per periode in het dashboard. Helpt bij inkoopbeslissingen.

- **Aanvulsessie vergelijking**
  Toon per aanvulsessie hoeveel er aangevuld werd vs. hoeveel er sindsdien verkocht werd. Detecteert discrepanties (diefstal/fouten).

- **Persoon-statistieken pagina**
  Per persoon: totaal besteld over tijd, favoriete product, gemiddeld per baravond. Handig voor bondsverantwoordelijken.

---

## 🔔 Engagement & Communicatie

- **Schuldherinnering export per persoon**
  Genereer een WhatsApp/email-tekst met openstaand saldo per lid, klaar om te kopiëren. Probleem: je moet nu manueel bedragen overnemen.

- **QR-code per persoon voor snelle scan**
  Elk lid heeft een unieke QR die je scant i.p.v. door een lijst te scrollen. *Zoals sportclubkassa's of Bpost-afhaalpunten.*

- **Baravond-samenvatting scherm**
  Na het afsluiten van een baravond: mooi overzichtsscherm met totale omzet, top product, winst — direct deelbaar als screenshot.

---

## ⚙️ Technische Verbeteringen

- **Offline-modus met sync**
  Bestellingen lokaal opslaan als de Raspberry Pi geen database-verbinding heeft, daarna automatisch syncen. Probleem: crash = verlies van data.

- **Automatische dagelijkse backup naar externe locatie**
  Nu is backup manueel. Automatisch backuppen naar een gedeelde map of USB-stick dagelijks.

- **Stock import via CSV**
  Bulk-update van stock na een grote inkoop via een CSV-upload i.p.v. product per product. Oplossing voor tijdrovende aanvulregistratie.

- **Productfoto compressie bij upload**
  Grote foto's vertragen de kiosk. Automatisch comprimeren naar max 200KB bij upload.

- **Audit trail voor stockwijzigingen**
  Log elke stockwijziging (aanvulling, bestelling, correctie) met tijdstip en persoon. Nu zijn sommige wijzigingen niet traceerbaar.

---

## 🔐 Veiligheid & Controle

- **Admin sessie-verlenging waarschuwing**
  30 seconden voor auto-logout een melding tonen: "Sessie verloopt — verleng?" i.p.v. stilletjes uitloggen midden in een actie.

- **Twee-factor voor gevoelige acties**
  Database leegmaken of wachtwoord wijzigen vereist een extra bevestiging (bv. huidige wachtwoord opnieuw). Nu is er enkel een tekstveld "LEEGMAKEN".

- **Rol-gebaseerde toegang**
  Onderscheid tussen "beheerder" (alles) en "barverantwoordelijke" (stock en baravond, geen financiën). Oplossing voor privacy bij gedeeld apparaat.

- **Video-opname statusindicator op kiosk**
  Duidelijke rode stip "● REC" zichtbaar tijdens opname zodat gebruikers weten dat de camera actief is. Juridisch en transparantieperspectief.

---

## 💡 Quick Wins (direct implementeerbaar)

- **Terug-knop op alle kiosk-pagina's** consequent op dezelfde positie
- **Zoekbalk in persoonsselectie** — voor grote ledenlijsten
- **"Opnieuw bestellen"** knop die de laatste bestelling van een persoon klaar zet
- **Deur-status badge op home** (🔒/🔓) zodat iemand ziet of een frigo nog open staat
- **Categorie-volgorde drag & drop** in admin i.p.v. een nummerveld

---

## 📹 Video-opnames

De app filmt via een USB-webcam (ffmpeg, v4l2) bij de volgende gebeurtenissen:

| Gebeurtenis | Opname start | Opname stopt |
|---|---|---|
| **Bestelling** | Klik op "Bestelling starten" | Alle sloten gesloten + reed-sensors dicht |
| **Baravond** | Activatie baravond | Deactivatie baravond |
| **Aanvulmodus** | Start aanvulsessie | Einde aanvulsessie |
| **De Bond** | Start De Bond-transactie | Einde transactie |

**Technische details:**
- Resolutie: 1280×720px — Framerate: 15 FPS — Codec: H.264 (libx264)
- Opslaglocatie: `/videos/JJJJ/MM/DD/tijdstip_naam.mp4`
- Bewaarperiode: 40 dagen (configureerbaar via instellingen)
- Op niet-Raspberry Pi systemen: stub-modus (leeg bestand, geen echte opname)

---

## 📋 Logging

Alle significante gebeurtenissen worden opgeslagen in de SQLite-database (`ksa_bar.db`, tabel `logs`). Er zijn geen log-levels (geen INFO/WARNING/ERROR) — enkel categorieën.

| Type | Wat wordt gelogd |
|---|---|
| `systeem` | Opstart van de applicatie, aanmaken van een nieuw persoon |
| `admin` | Inloggen/uitloggen, producten/personen beheren (incl. oud→nieuw waarden voor naam/prijs/velden), instellingen wijzigen (incl. welke instelling en oud→nieuw waarde) |
| `bestelling` | Plaatsen en annuleren van bestellingen (incl. persoonsnaam bij annulering) |
| `deur` | Deur ontgrendeld/vergrendeld, inclusief timeout-status per deur — nu ook voor De Bond-bestellingen |
| `baravond` | Start en stop van een baravond (incl. naam van de activerende persoon) |
| `aanvulling` | Start en stop van een aanvulsessie |
| `betaling` | Betalingen en rekening-afsluitingen (incl. bedrag) |
| `stock` | Winkelaankopen en stock-teruggaves (De Bond) |

**Velden per log-entry:** tijdstip, type, beschrijving, person_id, referentie_id, referentie_type  
**Bewaarperiode logs:** onbeperkt (geen automatische opruiming)

| Type | Wat wordt gelogd |
|---|---|
| `opname` | Start en stop van elke video-opname (incl. bestandspad) |
| `kiosk` | Persoon geselecteerd voor een bestelling |
| `systeem` | Opstart, nieuw persoon aangemaakt, hardware-status (ffmpeg, GPIO), De Bond niet gevonden |

---

## 🧪 Test Rapport

Volledig getest op 29/04/2026. Alle 47+ routes getest (kiosk, admin, API).

### 🔴 CRASH

**`GET /admin/bestellingen/<niet-bestaand-id>` → 500 Internal Server Error**

In `routes/admin.py` is er geen null-check in `bestelling_detail`:
```python
def bestelling_detail(oid):
    order = query("SELECT * FROM orders WHERE id=?", (oid,), one=True)
    # ❌ order kan None zijn — template crasht op order.id, order.tijdstip etc.
    return render_template('admin/order_detail.html', order=order, ...)
```
Als je via de URL een niet-bestaand bestelling-ID invult, krijg je een harde 500-fout.

---

### 🟠 SECURITY PROBLEEM

**Hardware API-routes zijn bereikbaar zonder authenticatie**

De volgende endpoints vereisen **geen login**:
- `POST /api/hardware-test/deur/1/unlock`
- `POST /api/hardware-test/deur/1/lock`
- `POST /api/hardware-test/deur/1/simulate-open`
- `POST /api/hardware-test/deur/1/simulate-close`
- (idem voor deur 2 en 3)

Iedereen die het IP-adres kent kan de koelkastdeuren ontgrendelen zonder wachtwoord.

---

### 🟡 FUNCTIONELE BUGS

**1. "Actief" checkbox bij nieuw product heeft geen effect**

In `templates/admin/products.html` staat een checkbox "Actief" bij het aanmaken van een nieuw product. In `routes/admin.py` wordt dit veld echter nergens uitgelezen bij `product_nieuw()` — het product wordt altijd als actief aangemaakt, ook als de checkbox uitgevinkt staat.

**2. Wachtpagina loopt vast als product geen deur gekoppeld heeft**

Als een product geen deur gekoppeld heeft, is `deuren_nodig = []`. De `/api/deur-status` berekent dan:
```python
alle_klaar = bool([]) and all(...)  # = altijd False
```
De wachtpagina blijft eindeloos pollen en de gebruiker zit vast zonder terugknop.

---

### ℹ️ OPMERKINGEN

- **Admin wachtwoord** in de database staat op `admin`. De standaard config (`config.py`) stelt `admin123` in als standaard, maar omdat de database al bestaat wordt die standaard niet meer toegepast. Dit kan verwarrend zijn bij een nieuwe installatie.
- **`GET /bestelling/wachten`** heeft geen sessiecheck — als je er direct naartoe navigeert zonder actieve bestelling, laadt de pagina leeg zonder foutmelding.

---

### ✅ Alles wat wél correct werkt

Kiosk (home, naam, producten, overzicht, wachten, baravond, aanvullen, De Bond, winkelaankoop, stock), alle admin-pagina's (dashboard, producten, categorieën, personen, bestellingen, rekening, baravond, winst, logs, database viewer, hardware test, instellingen, backup), Excel/PDF-export, FIFO stock engine, hardware stub-modus, login/logout flow.
