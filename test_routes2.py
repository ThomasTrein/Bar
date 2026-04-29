import requests, re

s = requests.Session()
issues = []
ok = []

def page_title(text):
    m = re.search(r'<title>(.*?)</title>', text)
    return m.group(1) if m else 'n/a'

def check(label, r, expected_status=200, check_content=True):
    err_kw = ['Internal Server Error', 'Traceback (most recent call last)', 'AttributeError:',
              'OperationalError', 'ProgrammingError', 'TypeError: ', 'NameError: ', 'ValueError: ']
    content = r.text if hasattr(r, 'text') else ''
    found_errors = [kw for kw in err_kw if kw in content]
    title = page_title(content)

    if check_content and 'admin/login' in r.url and expected_status == 200 and 'login' not in label.lower():
        issues.append(f'[AUTH_REDIRECT] {label}: redirected to login (not authenticated)')
        return

    if r.status_code != expected_status:
        issues.append(f'[STATUS] {label}: expected {expected_status}, got {r.status_code} | title: {title}')
    elif found_errors:
        for kw in found_errors:
            idx = content.find(kw)
            snippet = content[max(0, idx-20):idx+300].replace('\n', ' ')
            issues.append(f'[ERROR_IN_PAGE] {label}: "{kw}" | {snippet[:250]}')
    else:
        ok.append(f'[OK] {label}: {r.status_code} | {title}')

# ── Login ──────────────────────────────────────────────────────────────────────
print("=== LOGIN ===")
r = s.get('http://localhost:5000/admin/login')
check('GET /admin/login', r)

r = s.post('http://localhost:5000/admin/login', data={'wachtwoord': 'admin'}, allow_redirects=True)
title = page_title(r.text)
if 'login' in r.url.lower():
    issues.append(f'[AUTH] Login FAILED with password "admin"! URL={r.url}, title={title}')
    # Try admin123
    r2 = s.post('http://localhost:5000/admin/login', data={'wachtwoord': 'admin123'}, allow_redirects=True)
    t2 = page_title(r2.text)
    if 'login' in r2.url.lower():
        issues.append(f'[AUTH] Login FAILED with "admin123" too! URL={r2.url}')
    else:
        ok.append(f'[OK] POST /admin/login with "admin123": success -> {r2.url}')
else:
    ok.append(f'[OK] POST /admin/login with "admin": success -> {r.url}')

# ── Kiosk GET ──────────────────────────────────────────────────────────────────
print("=== KIOSK ===")
kiosk = ['/', '/bestelling/naam', '/bestelling/extra-persoon', '/bestelling/producten',
         '/bestelling/overzicht', '/bestelling/wachten', '/stock', '/baravond',
         '/aanvullen', '/de-bond', '/de-bond/naam', '/de-bond/producten',
         '/de-bond/terugzetten', '/winkelaankoop', '/bak-bestellen']
for route in kiosk:
    r = s.get(f'http://localhost:5000{route}', allow_redirects=True)
    check(f'GET {route}', r, check_content=False)

# ── API ────────────────────────────────────────────────────────────────────────
print("=== API ===")
r = s.get('http://localhost:5000/api/deur-status')
if r.status_code == 200:
    try:
        j = r.json()
        ok.append(f'[OK] GET /api/deur-status: 200 JSON={j}')
    except Exception as e:
        issues.append(f'[JSON] GET /api/deur-status: not JSON - {e}')
else:
    issues.append(f'[STATUS] GET /api/deur-status: {r.status_code}')

r = s.get('http://localhost:5000/api/personen/zoeken?q=a')
person_id = None
if r.status_code == 200:
    try:
        data = r.json()
        ok.append(f'[OK] GET /api/personen/zoeken?q=a: {len(data)} results')
        if data:
            person_id = data[0].get('id')
            ok.append(f'  First: id={person_id} name={data[0].get("voornaam")}')
    except Exception as e:
        issues.append(f'[JSON] /api/personen/zoeken: {e} | {r.text[:100]}')
else:
    issues.append(f'[STATUS] GET /api/personen/zoeken: {r.status_code}')

r = s.get('http://localhost:5000/api/personen/zoeken?q=test')
if r.status_code != 200:
    issues.append(f'[STATUS] GET /api/personen/zoeken?q=test: {r.status_code}')
else:
    try:
        data = r.json()
        ok.append(f'[OK] GET /api/personen/zoeken?q=test: {len(data)} results')
    except:
        issues.append(f'[JSON] /api/personen/zoeken?q=test not JSON')

r = s.post('http://localhost:5000/api/bestelling/item-verwijderen',
           json={'product_id': 1}, headers={'Content-Type': 'application/json'})
if r.status_code >= 500:
    issues.append(f'[STATUS] POST /api/bestelling/item-verwijderen: {r.status_code}')
    if 'Traceback' in r.text:
        idx = r.text.find('Traceback')
        issues.append(f'  Traceback: {r.text[idx:idx+300]}')
else:
    try:
        ok.append(f'[OK] POST /api/bestelling/item-verwijderen: {r.status_code} {r.json()}')
    except:
        ok.append(f'[OK] POST /api/bestelling/item-verwijderen: {r.status_code}')

for action in ['unlock', 'lock', 'simulate-open', 'simulate-close']:
    r = s.post(f'http://localhost:5000/api/hardware-test/deur/1/{action}')
    if r.status_code >= 500:
        issues.append(f'[STATUS] POST /api/hardware-test/deur/1/{action}: {r.status_code}')
    else:
        try:
            ok.append(f'[OK] /api/hardware-test/deur/1/{action}: {r.status_code} {r.json()}')
        except:
            ok.append(f'[OK] /api/hardware-test/deur/1/{action}: {r.status_code}')

# ── Admin GET ──────────────────────────────────────────────────────────────────
print("=== ADMIN GET ===")
admin_routes = ['/admin/', '/admin/producten', '/admin/personen', '/admin/bestellingen',
                '/admin/rekening', '/admin/baravond', '/admin/winst', '/admin/logs',
                '/admin/database', '/admin/hardware-test', '/admin/instellingen']
for route in admin_routes:
    r = s.get(f'http://localhost:5000{route}', allow_redirects=True)
    check(f'GET {route}', r)

# ── Admin exports ──────────────────────────────────────────────────────────────
print("=== EXPORTS ===")
r = s.get('http://localhost:5000/admin/rekening/export?formaat=excel&datum_van=2024-01-01&datum_tot=2024-12-31', allow_redirects=True)
if 'admin/login' in r.url:
    issues.append('[AUTH_REDIRECT] Excel export: redirected to login')
elif r.status_code != 200:
    issues.append(f'[STATUS] Excel export: {r.status_code}')
else:
    ct = r.headers.get('Content-Type', '')
    if 'spreadsheet' in ct or 'excel' in ct or 'octet-stream' in ct:
        ok.append(f'[OK] Excel export: real file, CT={ct}, size={len(r.content)}')
    elif 'Traceback' in r.text or 'Internal Server Error' in r.text:
        idx = r.text.find('Traceback') if 'Traceback' in r.text else r.text.find('Internal')
        issues.append(f'[ERROR] Excel export: server error | {r.text[idx:idx+400]}')
    else:
        issues.append(f'[CONTENT] Excel export: CT="{ct}" size={len(r.content)} — NOT real Excel')
        issues.append(f'  body preview: {r.text[:300]}')

r = s.get('http://localhost:5000/admin/rekening/export?formaat=pdf&datum_van=2024-01-01&datum_tot=2024-12-31', allow_redirects=True)
if 'admin/login' in r.url:
    issues.append('[AUTH_REDIRECT] PDF export: redirected to login')
elif r.status_code != 200:
    issues.append(f'[STATUS] PDF export: {r.status_code}')
else:
    ct = r.headers.get('Content-Type', '')
    if 'pdf' in ct or r.content[:4] == b'%PDF':
        ok.append(f'[OK] PDF export: real PDF, CT={ct}, size={len(r.content)}')
    elif 'Traceback' in r.text or 'Internal Server Error' in r.text:
        idx = r.text.find('Traceback') if 'Traceback' in r.text else r.text.find('Internal')
        issues.append(f'[ERROR] PDF export: server error | {r.text[idx:idx+400]}')
    else:
        issues.append(f'[CONTENT] PDF export: CT="{ct}" — NOT real PDF')
        issues.append(f'  body preview: {r.text[:300]}')

# ── 404 & edge cases ───────────────────────────────────────────────────────────
print("=== EDGE CASES ===")
r = s.get('http://localhost:5000/admin/bestellingen/999', allow_redirects=True)
if 'admin/login' in r.url:
    issues.append('[AUTH_REDIRECT] /admin/bestellingen/999: not authenticated')
elif r.status_code == 404:
    ok.append('[OK] /admin/bestellingen/999: 404 proper not-found')
elif r.status_code == 200 and 'Traceback' not in r.text:
    ok.append(f'[OK] /admin/bestellingen/999: 200 graceful | {page_title(r.text)}')
else:
    issues.append(f'[ERROR] /admin/bestellingen/999: status={r.status_code}')
    if 'Traceback' in r.text:
        idx = r.text.find('Traceback')
        issues.append(f'  {r.text[idx:idx+300]}')

r = s.get('http://localhost:5000/admin/database?tabel=products', allow_redirects=True)
check('GET /admin/database?tabel=products', r)

r = s.get('http://localhost:5000/admin/database?tabel=nonexistent', allow_redirects=True)
if r.status_code in (200, 400) and 'Traceback' not in r.text:
    ok.append(f'[OK] /admin/database?tabel=nonexistent: {r.status_code} graceful | {page_title(r.text)}')
else:
    issues.append(f'[ERROR] /admin/database?tabel=nonexistent: status={r.status_code}')
    if 'Traceback' in r.text:
        idx = r.text.find('Traceback')
        issues.append(f'  {r.text[idx:idx+300]}')

# ── Admin POST ─────────────────────────────────────────────────────────────────
print("=== ADMIN POST ===")
r = s.post('http://localhost:5000/admin/producten/nieuw',
           data={'naam': 'TestProduct', 'prijs': '1.50', 'categorie_id': '', 'btw': '21', 'beschikbaar': '1'},
           allow_redirects=True)
if r.status_code in (200, 302) and 'Traceback' not in r.text:
    ok.append(f'[OK] POST /admin/producten/nieuw: {r.status_code} | {page_title(r.text)}')
else:
    issues.append(f'[ERROR] POST /admin/producten/nieuw: {r.status_code} | {page_title(r.text)}')
    if 'Traceback' in r.text:
        idx = r.text.find('Traceback'); issues.append(f'  {r.text[idx:idx+300]}')

r = s.post('http://localhost:5000/admin/categorieen/nieuw',
           data={'naam': 'TestCategorie2'}, allow_redirects=True)
if r.status_code in (200, 302) and 'Traceback' not in r.text:
    ok.append(f'[OK] POST /admin/categorieen/nieuw: {r.status_code} | {page_title(r.text)}')
else:
    issues.append(f'[ERROR] POST /admin/categorieen/nieuw: {r.status_code} | {page_title(r.text)}')

r = s.post('http://localhost:5000/admin/personen/nieuw',
           data={'voornaam': 'TestPersoon2', 'achternaam': 'Test2'}, allow_redirects=True)
if r.status_code in (200, 302) and 'Traceback' not in r.text:
    ok.append(f'[OK] POST /admin/personen/nieuw: {r.status_code} | {page_title(r.text)}')
else:
    issues.append(f'[ERROR] POST /admin/personen/nieuw: {r.status_code} | {page_title(r.text)}')

r = s.post('http://localhost:5000/admin/instellingen',
           data={'admin_password': 'admin', 'deur_timeout_sec': '120',
                 'screensaver_timeout_min': '2', 'admin_logout_min': '10',
                 'prijs_tonen': 'false', 'product_kolommen': '4',
                 'video_bewaar_dagen': '40', 'pi_reboot_tijd': '06:30'},
           allow_redirects=True)
if r.status_code in (200, 302) and 'Traceback' not in r.text:
    ok.append(f'[OK] POST /admin/instellingen: {r.status_code} | {page_title(r.text)}')
else:
    issues.append(f'[ERROR] POST /admin/instellingen: {r.status_code} | {page_title(r.text)}')

if person_id:
    r = s.post('http://localhost:5000/bestelling/naam', data={'persoon_id': person_id}, allow_redirects=True)
    if r.status_code in (200, 302) and 'Traceback' not in r.text:
        ok.append(f'[OK] POST /bestelling/naam (person_id={person_id}): {r.status_code}')
    else:
        issues.append(f'[ERROR] POST /bestelling/naam: {r.status_code}')
        if 'Traceback' in r.text:
            idx = r.text.find('Traceback'); issues.append(f'  {r.text[idx:idx+300]}')
else:
    issues.append('[SKIP] POST /bestelling/naam: no person_id available')

r = s.get('http://localhost:5000/admin/logout', allow_redirects=True)
ok.append(f'[OK] GET /admin/logout: {r.status_code} -> {r.url}')

# ── Summary ────────────────────────────────────────────────────────────────────
print()
print('='*70)
print(f'RESULTS: {len(ok)} OK, {len(issues)} ISSUES')
print('='*70)
print(f'\nOK ({len(ok)}):')
for o in ok: print(f'  {o}')
print(f'\nISSUES ({len(issues)}):')
for i in issues: print(f'  {i}')
