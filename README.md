## Dingen om toe te voegen
- Je moet ook een bak bier op de bond kunnen zetten.

- Bij baravonden hoeft "Baravond #4" niet te staan. Enkel de naam van de baravond die je zelf kiest moet daar staan.

---

## Te bespreken
- Wat moet er allemaal gefilmd worden en wat wordt er in de logs geschreven worden.
- Alle modussen en wanneer moet je je naam selecteren.
- Crasht er iets?
- Is er nog ergens data nodig die er niet in zit.
- Is er een link nodig?

---

## Dingen die zijn aangepast:

- De bak bestellen optie in het hamburger menu moet weg. Je kan enkel een bak bestellen als je een bestelling start. De functie bak bestellen moet bij het product staan. Onder of naast de knop die al bestaat. De locatie mag je zelf kiezen wat het beste is.

- Als je een nieuwe winkel aankoop wil registeren dan zijn de namen en initiaal onderlijnd. Ik wil niet dat ze onderlijnd zijn.

- Voor iemand iets op de bond kan plaatsen moet deze ook eerst een naam selecteren. Er moet ook gefilmd worden.

- Als ik al ben ingelogd als admin en ik ga terug naar het admin paneel dan wil ik niet dat ik nog eens mijn wachtwoord moet invullen.

- De instelling prijzen tonen op kiosk die werkt niet. Als hij eerst op ja staat en je zet hem op nee en je slaat op dan staan de prijzen er nog steeds.

- In het admin paneel moet je naar alles kunnen doorklikken.

- In de rekening tab moet je al de bestelde items kunnen zien, hun totaal. Je moet ook al de bestellingen kunnen zien van die persoon. Je moet ook het winst/verlies zien dat je op die persoon hebt gemaakt.

- Als je de aanvul modus stopt moet je ook weten wie hem stopt in de logs.

- Als je in productbeheer filtert op de categorieën gebeurt er niks. Als je op een categorie klikt dan mag je enkel nog maar producten zien van die categorie.

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
