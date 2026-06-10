#!/bin/bash
# ─── KSA Bar Opstartscript ────────────────────────────────────────────────────
# Gebruik: bash start.sh
# Start de Flask webserver via gunicorn en opent Chromium in kiosk modus.

cd "$(dirname "$0")"

echo "=== KSA Bar starten ==="

# Verifieer Python omgeving
if [ ! -f "app.py" ]; then
    echo "FOUT: Voer dit script uit vanuit de Bar map."
    exit 1
fi

# Installeer dependencies als gunicorn nog niet beschikbaar is
if ! python3 -c "import gunicorn" 2>/dev/null; then
    echo "gunicorn installeren..."
    pip3 install gunicorn --quiet
fi

# Stop eventuele vorige instanties
pkill -f "gunicorn.*app:app" 2>/dev/null
sleep 1

# Start gunicorn (1 worker, threaded voor GPIO callbacks)
echo "Webserver starten..."
gunicorn \
    --workers 1 \
    --threads 4 \
    --bind 0.0.0.0:5000 \
    --timeout 120 \
    --keep-alive 5 \
    --log-level warning \
    --access-logfile - \
    "app:create_app()" &

GUNICORN_PID=$!
echo "Gunicorn PID: $GUNICORN_PID"

# Wacht tot de server beschikbaar is
echo "Wachten op server..."
for i in $(seq 1 15); do
    if curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "Server beschikbaar!"
        break
    fi
    sleep 1
done

# Open Chromium met Pi-vriendelijke instellingen
echo "Chromium openen..."
chromium-browser \
    --kiosk \
    --disable-gpu \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-background-networking \
    --disable-default-apps \
    --disable-extensions \
    --disable-sync \
    --disable-translate \
    --hide-scrollbars \
    --metrics-recording-only \
    --mute-audio \
    --no-first-run \
    --safebrowsing-disable-auto-update \
    --memory-pressure-off \
    http://localhost:5000 &

echo "=== KSA Bar draait ==="
echo "Druk Ctrl+C om alles te stoppen."

# Wacht op gunicorn
wait $GUNICORN_PID
