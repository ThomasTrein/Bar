"""
Camera opname module voor KSA Bar.
Gebruikt ffmpeg voor opname via USB webcam.
Op niet-Pi systemen: stub-modus (leeg MP4 bestand).
"""
import subprocess, threading, os, time, sys
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import VIDEOS_DIR, CAMERA_RESOLUTION, CAMERA_FPS, CAMERA_DEVICE, IS_RASPBERRY_PI

_lock = threading.Lock()
_active: 'Recording | None' = None


class Recording:
    def __init__(self, naam: str):
        self.naam = naam
        self.start_tijd = datetime.now()
        self.gestopt = False
        self._process = None

        datum_dir = self.start_tijd.strftime('%Y/%m/%d')
        os.makedirs(os.path.join(VIDEOS_DIR, datum_dir), exist_ok=True)

        ts = self.start_tijd.strftime('%Y%m%d_%H%M%S')
        safe = "".join(c for c in naam if c.isalnum() or c in '_-')
        self.bestand = f"{ts}_{safe}.mp4"
        self.pad = os.path.join(VIDEOS_DIR, datum_dir, self.bestand)
        self.relatief = os.path.join(datum_dir, self.bestand).replace('\\', '/')

    def start(self):
        w, h = CAMERA_RESOLUTION
        if IS_RASPBERRY_PI:
            cmd = [
                'ffmpeg', '-f', 'v4l2',
                '-video_size', f'{w}x{h}',
                '-framerate', str(CAMERA_FPS),
                '-i', f'/dev/video{CAMERA_DEVICE}',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                '-an', '-y', self.pad
            ]
            try:
                self._process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[REC] Opname gestart: {self.bestand}")
            except FileNotFoundError:
                print("[WARN] ffmpeg niet gevonden")
        else:
            # Development stub
            open(self.pad, 'wb').close()
            print(f"[STUB] Opname: {self.bestand}")

    def stop(self):
        if self.gestopt:
            return
        self.gestopt = True
        if self._process and self._process.poll() is None:
            try:
                self._process.communicate(input=b'q', timeout=5)
            except Exception:
                self._process.kill()
        print(f"[REC] Opname gestopt: {self.bestand}")

    def get_relatief_pad(self) -> str:
        return self.relatief


def start_recording(naam: str) -> Recording:
    global _active
    with _lock:
        if _active and not _active.gestopt:
            _active.stop()
        rec = Recording(naam)
        rec.start()
        _active = rec
        return rec


def stop_recording() -> str:
    global _active
    with _lock:
        if _active and not _active.gestopt:
            _active.stop()
            pad = _active.get_relatief_pad()
            _active = None
            return pad
        return ''


def get_active_recording():
    return _active


def cleanup_old_videos(bewaar_dagen: int = 40):
    cutoff = time.time() - (bewaar_dagen * 86400)
    n = 0
    for root, _, files in os.walk(VIDEOS_DIR):
        for f in files:
            p = os.path.join(root, f)
            if os.path.getmtime(p) < cutoff:
                try:
                    os.remove(p)
                    n += 1
                except Exception:
                    pass
    for root, dirs, files in os.walk(VIDEOS_DIR, topdown=False):
        if not os.listdir(root) and root != VIDEOS_DIR:
            try:
                os.rmdir(root)
            except Exception:
                pass
    print(f"[CLEANUP] {n} oude video(s) verwijderd")
    return n
