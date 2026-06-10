#!/bin/bash
# ─── KSA Bar Opstartscript ────────────────────────────────────────────────────
# Gebruik: bash start.sh

cd "$(dirname "$0")"

echo "=== KSA Bar starten ==="

if [ ! -f "app.py" ]; then
    echo "FOUT: Voer dit script uit vanuit de Bar map."
    exit 1
fi

# Zoek Python: gebruik venv als die bestaat, anders system python3
VENV_PATHS=(
    "$(dirname "$0")/venv"
    "/home/Bar/venv"
    "$HOME/Bar/venv"
    "$HOME/venv"
)

PYTHON="python3"
for venv in "${VENV_PATHS[@]}"; do
    if [ -f "$venv/bin/python3" ]; then
        PYTHON="$venv/bin/python3"
        echo "Venv gevonden: $venv"
        break
    fi
done

echo "Python: $PYTHON"

# Installeer gunicorn als het nog niet beschikbaar is
if ! "$PYTHON" -c "import gunicorn" 2>/dev/null; then
    echo "gunicorn installeren in venv..."
    "$PYTHON" -m pip install gunicorn --quiet
fi

# Stop eventuele vorige instanties
pkill -f "python3.*gunicorn" 2>/dev/null
sleep 1

# Start gunicorn via de venv python (1 worker, 4 threads voor GPIO callbacks)
echo "Webserver starten..."
"$PYTHON" -m gunicorn \
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

# Open Chromium met Pi-vriendelijke instellingen (--disable-gpu voorkomt bevriezing)
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
    http://localhost:5000 &

echo "=== KSA Bar draait ==="
echo "Druk Ctrl+C om alles te stoppen."

wait $GUNICORN_PID
