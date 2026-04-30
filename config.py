"""Configuratie voor KSA Bar systeem."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database
DATABASE_PATH = os.path.join(BASE_DIR, 'ksa_bar.db')

# Paden
VIDEOS_DIR = os.path.join(BASE_DIR, 'videos')
BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
UPLOADS_PERSONS_DIR = os.path.join(UPLOADS_DIR, 'persons')
UPLOADS_PRODUCTS_DIR = os.path.join(UPLOADS_DIR, 'products')
UPLOADS_SCREENSAVER_DIR = os.path.join(UPLOADS_DIR, 'screensaver')

# Hardware detectie
IS_RASPBERRY_PI = os.path.exists('/proc/device-tree/model')

# GPIO pins (BCM nummering)
RELAY_PINS = {1: 17, 2: 27, 3: 22}
REED_PINS  = {1: 5,  2: 6,  3: 13}
RELAY_ACTIVE_HIGH = True  # False als relay actief-laag is

# Camera
CAMERA_RESOLUTION = (1280, 720)
CAMERA_FPS = 15
CAMERA_DEVICE = 0

# Standaard instellingen
DEFAULT_SETTINGS = {
    'admin_password':          'admin123',
    'deur_timeout_sec':        '120',
    'screensaver_timeout_min': '2',
    'admin_logout_min':        '10',
    'prijs_tonen':             'false',
    'product_kolommen':        '2',
    'persoon_kolommen':        '4',
    'video_bewaar_dagen':      '40',
    'pi_reboot_tijd':          '06:30',
}
