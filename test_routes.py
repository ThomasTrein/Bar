import requests
import json

s = requests.Session()
issues = []
ok = []

def check(label, r, expected_status=200, error_keywords=None):
    if error_keywords is None:
        error_keywords = ['Internal Server Error', 'Traceback', 'AttributeError', 'KeyError',
                          'OperationalError', 'ProgrammingError', 'TypeError', 'NameError',
                          'ImportError', 'ValueError', 'Exception', '500', 'werkzeug']
    status_ok = r.status_code == expected_status
    content = r.text if hasattr(r, 'text') else ''
    found_errors = [kw for kw in error_keywords if kw in content]
    
    if not status_ok:
        issues.append(f"[STATUS] {label}: expected {expected_status}, got {r.status_code} | URL: {r.url}")
    elif found_errors:
        issues.append(f"[ERROR_IN_PAGE] {label}: found keywords {found_errors} | URL: {r.url}")
        # print snippet
        for kw in found_errors:
            idx = content.find(kw)
            snippet = content[max(0, idx-50):idx+200].replace('\n', ' ')
            print(f"  Snippet for '{kw}': ...{snippet}...")
    else:
        ok.append(f"[OK] {label}: {r.status_code}")

# ── Admin login ──────────────────────────────────────────────────────────────
print("=== ADMIN LOGIN ===")
r = s.get('http://localhost:5000/admin/login')
check("GET /admin/login", r)

r = s.post('http://localhost:5000/admin/login', data={'wachtwoord': 'admin123'}, allow_redirects=True)
if 'login' in r.url.lower():
    issues.append("[AUTH] POST /admin/login: still on login page after submit – auth may have failed")
else:
    ok.append(f"[OK] POST /admin/login: redirected to {r.url}")

# ── Kiosk GET routes ──────────────────────────────────────────────────────────
print("=== KIOSK GET ROUTES ===")
kiosk_routes = [
    '/',
    '/bestelling/naam',
    '/bestelling/extra-persoon',
    '/bestelling/producten',
    '/bestelling/overzicht',
    '/bestelling/wachten',
    '/stock',
    '/baravond',
    '/aanvullen',
    '/de-bond',
    '/de-bond/naam',
    '/de-bond/producten',
    '/de-bond/terugzetten',
    '/winkelaankoop',
    '/bak-bestellen',
]
for route in kiosk_routes:
    r = s.get(f'http://localhost:5000{route}', allow_redirects=True)
    check(f"GET {route}", r)

# ── API Routes ─────────────────────────────────────────────────────────────────
print("=== API ROUTES ===")
r = s.get('http://localhost:5000/api/deur-status')
check("GET /api/deur-status", r, error_keywords=['Traceback', 'Internal Server Error', 'AttributeError'])
try:
    j = r.json()
    ok.append(f"[OK] /api/deur-status JSON: {j}")
except Exception as e:
    issues.append(f"[JSON] /api/deur-status: not valid JSON – {e}")

r = s.get('http://localhost:5000/api/personen/zoeken?q=a', allow_redirects=True)
check("GET /api/personen/zoeken?q=a", r, error_keywords=['Traceback', 'Internal Server Error'])
person_id = None
try:
    data = r.json()
    ok.append(f"[OK] /api/personen/zoeken returned {len(data)} results")
    if data:
        person_id = data[0].get('id') or data[0].get('persoon_id')
        ok.append(f"  First person id: {person_id}, data: {data[0]}")
except Exception as e:
    issues.append(f"[JSON] /api/personen/zoeken: not valid JSON – {e} | body: {r.text[:200]}")

r = s.get('http://localhost:5000/api/personen/zoeken?q=test', allow_redirects=True)
check("GET /api/personen/zoeken?q=test", r, error_keywords=['Traceback', 'Internal Server Error'])

r = s.post('http://localhost:5000/api/bestelling/item-verwijderen',
           json={'product_id': 1, 'bestelling_id': 1},
           headers={'Content-Type': 'application/json'})
check("POST /api/bestelling/item-verwijderen", r,
      expected_status=r.status_code,  # accept whatever
      error_keywords=['Traceback', 'Internal Server Error', 'AttributeError'])
try:
    j = r.json()
    ok.append(f"[OK] /api/bestelling/item-verwijderen JSON: {j}")
except Exception as e:
    if r.status_code >= 500:
        issues.append(f"[ERROR] /api/bestelling/item-verwijderen: status {r.status_code}")
    else:
        ok.append(f"[OK] /api/bestelling/item-verwijderen: {r.status_code}")

for action in ['unlock', 'lock', 'simulate-open', 'simulate-close']:
    r = s.post(f'http://localhost:5000/api/hardware-test/deur/1/{action}')
    check(f"POST /api/hardware-test/deur/1/{action}", r,
          expected_status=r.status_code,
          error_keywords=['Traceback', 'Internal Server Error'])
    try:
        j = r.json()
        ok.append(f"[OK] /api/hardware-test/deur/1/{action}: {r.status_code} → {j}")
    except:
        if r.status_code >= 500:
            issues.append(f"[ERROR] /api/hardware-test/deur/1/{action}: status {r.status_code}")
        else:
            ok.append(f"[OK] /api/hardware-test/deur/1/{action}: {r.status_code} (non-JSON)")

# ── Admin GET routes ───────────────────────────────────────────────────────────
print("=== ADMIN GET ROUTES ===")
admin_routes = [
    '/admin/',
    '/admin/producten',
    '/admin/personen',
    '/admin/bestellingen',
    '/admin/rekening',
    '/admin/baravond',
    '/admin/winst',
    '/admin/logs',
    '/admin/database',
    '/admin/hardware-test',
    '/admin/instellingen',
]
for route in admin_routes:
    r = s.get(f'http://localhost:5000{route}', allow_redirects=True)
    check(f"GET {route}", r)

# ── Admin extra checks ─────────────────────────────────────────────────────────
print("=== ADMIN EXTRA CHECKS ===")
r = s.get('http://localhost:5000/admin/rekening/export?formaat=excel&datum_van=2024-01-01&datum_tot=2024-12-31', allow_redirects=True)
if r.status_code == 200:
    ct = r.headers.get('Content-Type', '')
    if 'excel' in ct or 'spreadsheet' in ct or 'octet' in ct or len(r.content) > 100:
        ok.append(f"[OK] Excel export: {r.status_code}, Content-Type: {ct}, size: {len(r.content)} bytes")
    else:
        issues.append(f"[WARN] Excel export: 200 but Content-Type is '{ct}', size {len(r.content)} bytes – may not be real Excel")
        if 'Internal Server Error' in r.text or 'Traceback' in r.text:
            issues.append(f"[ERROR] Excel export: error in response body")
else:
    issues.append(f"[STATUS] Excel export: expected 200, got {r.status_code}")

r = s.get('http://localhost:5000/admin/rekening/export?formaat=pdf&datum_van=2024-01-01&datum_tot=2024-12-31', allow_redirects=True)
if r.status_code == 200:
    ct = r.headers.get('Content-Type', '')
    if 'pdf' in ct or r.content[:4] == b'%PDF':
        ok.append(f"[OK] PDF export: {r.status_code}, Content-Type: {ct}")
    else:
        issues.append(f"[WARN] PDF export: 200 but Content-Type is '{ct}', size {len(r.content)} – may not be real PDF")
        if 'Internal Server Error' in r.text or 'Traceback' in r.text:
            issues.append(f"[ERROR] PDF export: error in response body")
else:
    issues.append(f"[STATUS] PDF export: expected 200, got {r.status_code}")

r = s.get('http://localhost:5000/admin/bestellingen/999', allow_redirects=True)
if r.status_code in (404, 200):
    if r.status_code == 404:
        ok.append("[OK] /admin/bestellingen/999: 404 (proper not-found)")
    elif 'Internal Server Error' in r.text or 'Traceback' in r.text:
        issues.append("[ERROR] /admin/bestellingen/999: 200 but contains error traceback")
    else:
        ok.append("[OK] /admin/bestellingen/999: 200 (handled gracefully)")
else:
    issues.append(f"[STATUS] /admin/bestellingen/999: got {r.status_code}")

r = s.get('http://localhost:5000/admin/database?tabel=products', allow_redirects=True)
check("GET /admin/database?tabel=products", r)

r = s.get('http://localhost:5000/admin/database?tabel=nonexistent', allow_redirects=True)
if r.status_code == 200 and ('Internal Server Error' not in r.text) and ('Traceback' not in r.text):
    ok.append("[OK] /admin/database?tabel=nonexistent: handled gracefully")
elif r.status_code == 400:
    ok.append("[OK] /admin/database?tabel=nonexistent: 400 (proper bad-request)")
else:
    issues.append(f"[WARN] /admin/database?tabel=nonexistent: status {r.status_code} – check if error shown")
    if 'Traceback' in r.text or 'Internal Server Error' in r.text:
        issues.append("[ERROR] /admin/database?tabel=nonexistent: unhandled exception in response")

# ── Admin POST routes ──────────────────────────────────────────────────────────
print("=== ADMIN POST FORM SUBMISSIONS ===")

# Create product
r = s.post('http://localhost:5000/admin/producten/nieuw',
           data={'naam': 'TestProduct', 'prijs': '1.50', 'categorie_id': '', 'btw': '21', 'beschikbaar': '1'},
           allow_redirects=True)
if r.status_code in (200, 302):
    if 'Traceback' in r.text or 'Internal Server Error' in r.text:
        issues.append(f"[ERROR] POST /admin/producten/nieuw: error in response")
    else:
        ok.append(f"[OK] POST /admin/producten/nieuw: {r.status_code}")
else:
    issues.append(f"[STATUS] POST /admin/producten/nieuw: got {r.status_code}")

# Create category
r = s.post('http://localhost:5000/admin/categorieen/nieuw',
           data={'naam': 'TestCategorie'},
           allow_redirects=True)
if r.status_code in (200, 302):
    if 'Traceback' in r.text or 'Internal Server Error' in r.text:
        issues.append(f"[ERROR] POST /admin/categorieen/nieuw: error in response")
    else:
        ok.append(f"[OK] POST /admin/categorieen/nieuw: {r.status_code}")
else:
    issues.append(f"[STATUS] POST /admin/categorieen/nieuw: got {r.status_code}")

# Create person
r = s.post('http://localhost:5000/admin/personen/nieuw',
           data={'voornaam': 'TestPersoon', 'achternaam': 'Test'},
           allow_redirects=True)
if r.status_code in (200, 302):
    if 'Traceback' in r.text or 'Internal Server Error' in r.text:
        issues.append(f"[ERROR] POST /admin/personen/nieuw: error in response")
    else:
        ok.append(f"[OK] POST /admin/personen/nieuw: {r.status_code}")
else:
    issues.append(f"[STATUS] POST /admin/personen/nieuw: got {r.status_code}")

# Save settings
r = s.post('http://localhost:5000/admin/instellingen',
           data={'bar_naam': 'KSA Bar Test', 'btw_percentage': '21'},
           allow_redirects=True)
if r.status_code in (200, 302):
    if 'Traceback' in r.text or 'Internal Server Error' in r.text:
        issues.append(f"[ERROR] POST /admin/instellingen: error in response")
    else:
        ok.append(f"[OK] POST /admin/instellingen: {r.status_code}")
else:
    issues.append(f"[STATUS] POST /admin/instellingen: got {r.status_code}")

# POST /bestelling/naam with person_id
if person_id:
    r = s.post('http://localhost:5000/bestelling/naam',
               data={'persoon_id': person_id},
               allow_redirects=True)
    if r.status_code in (200, 302):
        if 'Traceback' in r.text or 'Internal Server Error' in r.text:
            issues.append(f"[ERROR] POST /bestelling/naam (person_id={person_id}): error in response")
        else:
            ok.append(f"[OK] POST /bestelling/naam: {r.status_code}")
    else:
        issues.append(f"[STATUS] POST /bestelling/naam: got {r.status_code}")
else:
    issues.append("[SKIP] POST /bestelling/naam: no person_id available")

# ── Logout ────────────────────────────────────────────────────────────────────
r = s.get('http://localhost:5000/admin/logout', allow_redirects=True)
if r.status_code == 200 and ('login' in r.url.lower() or 'login' in r.text.lower()):
    ok.append("[OK] GET /admin/logout: redirected to login")
elif r.status_code in (200, 302):
    ok.append(f"[OK] GET /admin/logout: {r.status_code}")
else:
    issues.append(f"[STATUS] GET /admin/logout: {r.status_code}")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print(f"RESULTS: {len(ok)} OK, {len(issues)} ISSUES")
print("="*70)

print(f"\n✅ OK ({len(ok)}):")
for o in ok:
    print(f"  {o}")

print(f"\n❌ ISSUES ({len(issues)}):")
if issues:
    for i in issues:
        print(f"  {i}")
else:
    print("  None found!")
