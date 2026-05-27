# Netwerk Handleiding — KSA Bar op Raspberry Pi

## Kan ik de website bereiken via mijn gsm-hotspot?

**Ja, dat kan!** Als de Raspberry Pi verbonden is met de hotspot van jouw gsm, dan zitten zowel de Pi als jouw gsm op hetzelfde lokale netwerk. Je kan de website dan gewoon bereiken via het IP-adres van de Pi.

---

## Stap-voor-stap: Raspberry Pi verbinden met gsm-hotspot

### Stap 1 — Zet hotspot aan op je gsm
- **Android**: Instellingen → Netwerk → Hotspot & Tethering → Wifi-hotspot aanzetten
- **iPhone**: Instellingen → Persoonlijke hotspot → aanzetten

Onthoud de naam (SSID) en het wachtwoord van jouw hotspot.

### Stap 2 — Verbind de Raspberry Pi met de hotspot
Dit doe je het makkelijkst via de terminal op de Pi:

```bash
sudo nmcli dev wifi connect "NAAM_VAN_JE_HOTSPOT" password "JE_WACHTWOORD"
```

Of via de grafische omgeving (als je een scherm hebt): klik op het wifi-icoontje rechtsboven en selecteer jouw hotspot.

### Stap 3 — Zoek het IP-adres van de Pi
Open een terminal op de Raspberry Pi en typ:

```bash
hostname -I
```

Je krijgt iets te zien zoals: `192.168.43.152 ...`

Het **eerste adres** is het IP-adres dat je nodig hebt.

### Stap 4 — Open de website op je gsm of laptop
Zorg dat je gsm/laptop ook verbonden is met **dezelfde hotspot**. Open dan een browser en ga naar:

```
http://192.168.43.152:5000
```

(Vervang `192.168.43.152` door het IP-adres dat je in stap 3 vond.)

De website van de KSA Bar zou nu zichtbaar moeten zijn!

---

## Controleer of Flask bereikbaar is van buitenaf

De Flask-app moet draaien op `0.0.0.0` (niet alleen `127.0.0.1`). Controleer dit in `app.py`:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Als er staat `host='127.0.0.1'`, verander dit naar `host='0.0.0.0'`. Anders is de app enkel bereikbaar van de Pi zelf.

---

## Tijdzone instellen op de Raspberry Pi

Om zeker te zijn dat de tijden in de app kloppen, stel je de tijdzone in op de Pi:

```bash
sudo timedatectl set-timezone Europe/Brussels
```

Controleer nadien:

```bash
timedatectl
```

Je zou `Time zone: Europe/Brussels` moeten zien.

---

## Problemen oplossen

| Probleem | Oplossing |
|----------|-----------|
| Website niet bereikbaar | Controleer of Pi én gsm op **dezelfde** hotspot zitten |
| IP-adres verandert telkens | Stel een **vast IP** in via `nmcli` of in de hotspot-instellingen |
| Flask start niet op 0.0.0.0 | Pas `app.py` aan (zie hierboven) |
| Pagina laadt niet | Controleer of de Flask-app draait: `ps aux \| grep python` |

---

## Vast IP instellen (optioneel maar handig)

Als je wil dat de Pi altijd hetzelfde IP-adres heeft op jouw hotspot:

```bash
# Bekijk de verbinding
nmcli connection show

# Stel een vast IP in (pas de namen en adressen aan)
sudo nmcli connection modify "NAAM_VAN_JE_HOTSPOT" \
  ipv4.addresses "192.168.43.50/24" \
  ipv4.gateway "192.168.43.1" \
  ipv4.method manual

sudo nmcli connection up "NAAM_VAN_JE_HOTSPOT"
```

Kies een adres dat nog vrij is op jouw hotspot (typisch `192.168.43.x` voor Android, `172.20.10.x` voor iPhone).
