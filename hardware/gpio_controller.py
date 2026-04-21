"""
GPIO controller voor solenoid relays en reed contacten.
Op Raspberry Pi: gebruikt gpiozero.
Op andere systemen: stub-implementatie voor development.
"""
import threading, time, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import IS_RASPBERRY_PI, RELAY_PINS, REED_PINS, RELAY_ACTIVE_HIGH

try:
    from gpiozero import OutputDevice, Button
    GPIO_AVAILABLE = True
except Exception:
    GPIO_AVAILABLE = False
    print("[WARN] gpiozero niet beschikbaar -- stub modus (development)")


class DoorController:
    """Controller voor één frigo-deur: solenoid + reed contact."""

    def __init__(self, deur: int):
        self.deur = deur
        self._unlocked = False
        self._open = False
        self._callbacks = []

        if GPIO_AVAILABLE and IS_RASPBERRY_PI:
            self._relay = OutputDevice(RELAY_PINS[deur], active_high=RELAY_ACTIVE_HIGH, initial_value=False)
            self._reed  = Button(REED_PINS[deur], pull_up=True, bounce_time=0.05)
            self._reed.when_pressed  = self._on_open
            self._reed.when_released = self._on_close
        else:
            self._relay = None
            self._reed  = None

    def unlock(self):
        self._unlocked = True
        if self._relay:
            self._relay.on()
        self._fire('unlock')
        print(f"[UNLOCK] Deur {self.deur} ontgrendeld")

    def lock(self):
        self._unlocked = False
        if self._relay:
            self._relay.off()
        self._fire('lock')
        print(f"[LOCK] Deur {self.deur} vergrendeld")

    def is_unlocked(self) -> bool:
        return self._unlocked

    def is_open(self) -> bool:
        if self._reed:
            return self._reed.is_pressed
        return self._open

    def simulate_open(self):
        self._on_open()

    def simulate_close(self):
        self._on_close()

    def add_callback(self, cb):
        self._callbacks.append(cb)

    def _on_open(self):
        self._open = True
        self._fire('open')
        print(f"[OPEN] Deur {self.deur} open")

    def _on_close(self):
        self._open = False
        self._fire('close')
        print(f"[CLOSE] Deur {self.deur} dicht")

    def _fire(self, event: str):
        for cb in self._callbacks:
            try:
                cb(self.deur, event)
            except Exception as e:
                print(f"Callback fout deur {self.deur}: {e}")

    def cleanup(self):
        if self._relay:
            self._relay.off()
            self._relay.close()
        if self._reed:
            self._reed.close()


class FridgeController:
    """Beheert alle 3 frigo-deuren."""

    def __init__(self):
        self.doors = {i: DoorController(i) for i in (1, 2, 3)}
        self._event_cbs = []
        for ctrl in self.doors.values():
            ctrl.add_callback(self._on_door_event)

    def get_status(self) -> dict:
        return {
            d: {'unlocked': c.is_unlocked(), 'open': c.is_open()}
            for d, c in self.doors.items()
        }

    def unlock_doors(self, deuren: list, timeout_sec: int = 120, on_complete=None):
        """Start een individuele deur-cyclus per deur (in aparte thread)."""
        for deur in deuren:
            if deur in self.doors:
                t = threading.Thread(
                    target=self._door_cycle,
                    args=(deur, timeout_sec, on_complete),
                    daemon=True
                )
                t.start()

    def _door_cycle(self, deur: int, timeout_sec: int, on_complete):
        ctrl = self.doors[deur]
        ctrl.unlock()

        # Wacht tot deur open gaat
        start = time.time()
        while not ctrl.is_open():
            if time.time() - start > timeout_sec:
                print(f"[TIMEOUT] Deur {deur}: timeout (niet geopend)")
                ctrl.lock()
                self._fire_event('timeout', deur)
                if on_complete:
                    on_complete(deur, False)
                return
            time.sleep(0.1)

        # Wacht tot deur gesloten is
        while ctrl.is_open():
            time.sleep(0.1)

        ctrl.lock()
        self._fire_event('complete', deur)
        if on_complete:
            on_complete(deur, True)

    def unlock_all(self):
        for ctrl in self.doors.values():
            ctrl.unlock()

    def lock_all(self):
        for ctrl in self.doors.values():
            ctrl.lock()

    def add_event_callback(self, cb):
        self._event_cbs.append(cb)

    def _on_door_event(self, deur: int, event: str):
        self._fire_event(event, deur)

    def _fire_event(self, event: str, deur: int):
        for cb in self._event_cbs:
            try:
                cb(event, deur)
            except Exception as e:
                print(f"Event cb fout: {e}")

    def cleanup(self):
        for ctrl in self.doors.values():
            ctrl.cleanup()


_fridge: FridgeController = None


def get_fridge_controller() -> FridgeController:
    global _fridge
    if _fridge is None:
        _fridge = FridgeController()
    return _fridge
