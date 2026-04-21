"""Backup service voor KSA Bar database."""
import os, shutil, sys
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DATABASE_PATH, BACKUPS_DIR


def backup_database() -> str:
    """Maak een timestamped backup van de SQLite database. Bewaar max 7 kopieën."""
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pad = os.path.join(BACKUPS_DIR, f"ksa_bar_{timestamp}.db")
    shutil.copy2(DATABASE_PATH, pad)

    backups = sorted(f for f in os.listdir(BACKUPS_DIR) if f.endswith('.db'))
    while len(backups) > 7:
        os.remove(os.path.join(BACKUPS_DIR, backups.pop(0)))

    print(f"[BACKUP] Backup: {pad}")
    return pad
