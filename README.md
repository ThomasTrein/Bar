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
