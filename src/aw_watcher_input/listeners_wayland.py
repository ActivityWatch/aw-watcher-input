"""
Evdev-based keyboard and mouse listeners for Wayland.

Drop-in replacements for the pynput-based listeners from aw-watcher-afk
when running under Wayland, where pynput cannot capture global input events.

Requires the ``evdev`` package and read access to ``/dev/input/event*``
devices — typically via membership in the ``input`` group.
"""

import logging
import threading
from typing import Dict, List

from aw_watcher_afk.listeners import EventFactory

logger = logging.getLogger(__name__)


def _is_keyboard(device) -> bool:
    """Return True if *device* looks like a real keyboard (not a gamepad)."""
    import evdev

    caps = device.capabilities()
    if evdev.ecodes.EV_KEY not in caps:
        return False
    keys = set(caps[evdev.ecodes.EV_KEY])
    # Require ordinary keyboard keys to exclude gamepads / remotes.
    keyboard_markers = {
        evdev.ecodes.KEY_SPACE,
        evdev.ecodes.KEY_ENTER,
        evdev.ecodes.KEY_A,
        evdev.ecodes.KEY_Z,
    }
    return bool(keys & keyboard_markers)


def _is_mouse(device) -> bool:
    """Return True if *device* exposes relative pointing axes.

    Hybrid keyboard+pointer devices can be read by both listeners: the mouse
    reader filters button codes so keyboard presses are not counted as clicks.
    """
    import evdev

    caps = device.capabilities()
    if evdev.ecodes.EV_REL not in caps:
        return False
    axes = set(caps[evdev.ecodes.EV_REL])
    return evdev.ecodes.REL_X in axes and evdev.ecodes.REL_Y in axes


class EvdevKeyboardListener(EventFactory):
    """Keyboard listener using evdev — Wayland-compatible."""

    def __init__(self) -> None:
        EventFactory.__init__(self)
        self.logger = logger.getChild("keyboard_wayland")
        self._threads: List[threading.Thread] = []
        self._devices: list = []
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def _reset_data(self) -> None:
        self.event_data = {"presses": 0}

    def start(self) -> None:
        try:
            import evdev
        except ImportError:
            self.logger.warning(
                "evdev not installed; Wayland keyboard tracking unavailable. "
                "Install it with: pip install evdev"
            )
            return

        self._stop_event.clear()
        for path in evdev.list_devices():
            try:
                device = evdev.InputDevice(path)
            except (OSError, PermissionError):
                continue
            if _is_keyboard(device):
                self._devices.append(device)
                t = threading.Thread(
                    target=self._read_events,
                    args=(device,),
                    name=f"evdev-keyboard-{device.path}",
                    daemon=True,
                )
                t.start()
                self._threads.append(t)
            else:
                device.close()

        if self._devices:
            self.logger.info(
                "Wayland keyboard listener started for %d device(s): %s",
                len(self._devices),
                [d.name for d in self._devices],
            )
        else:
            self.logger.warning(
                "No keyboard devices found in /dev/input/. "
                "Ensure you are in the 'input' group: sudo usermod -aG input $USER"
            )

    def stop(self) -> None:
        self._stop_event.set()
        for device in self._devices:
            try:
                device.close()
            except (OSError, IOError):
                pass
        self._devices.clear()
        for t in self._threads:
            t.join(timeout=2.0)
        self._threads.clear()

    def is_alive(self) -> bool:
        return any(t.is_alive() for t in self._threads)

    def next_event(self) -> dict:
        with self._lock:
            self.new_event.clear()
            data = dict(self.event_data)
            self._reset_data()
        return data

    def _read_events(self, device) -> None:
        import evdev

        try:
            for event in device.read_loop():
                if self._stop_event.is_set():
                    break
                # Only count key-press events (value == 1); ignore repeats (value == 2)
                if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                    with self._lock:
                        self.event_data["presses"] += 1
                    self.new_event.set()
        except (OSError, IOError):
            self.logger.debug("Keyboard device %s disconnected", device.path)
        finally:
            try:
                device.close()
            except (OSError, IOError):
                pass


class EvdevMouseListener(EventFactory):
    """Mouse/pointer listener using evdev — Wayland-compatible."""

    def __init__(self) -> None:
        EventFactory.__init__(self)
        self.logger = logger.getChild("mouse_wayland")
        self._threads: List[threading.Thread] = []
        self._devices: list = []
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def _reset_data(self) -> None:
        self.event_data: Dict[str, int] = {
            "clicks": 0,
            "deltaX": 0,
            "deltaY": 0,
            "scrollX": 0,
            "scrollY": 0,
        }

    def start(self) -> None:
        try:
            import evdev
        except ImportError:
            self.logger.warning(
                "evdev not installed; Wayland mouse tracking unavailable. "
                "Install it with: pip install evdev"
            )
            return

        self._stop_event.clear()
        for path in evdev.list_devices():
            try:
                device = evdev.InputDevice(path)
            except (OSError, PermissionError):
                continue
            if _is_mouse(device):
                self._devices.append(device)
                t = threading.Thread(
                    target=self._read_events,
                    args=(device,),
                    name=f"evdev-mouse-{device.path}",
                    daemon=True,
                )
                t.start()
                self._threads.append(t)
            else:
                device.close()

        if self._devices:
            self.logger.info(
                "Wayland mouse listener started for %d device(s): %s",
                len(self._devices),
                [d.name for d in self._devices],
            )
        else:
            self.logger.warning(
                "No mouse devices found in /dev/input/. "
                "Ensure you are in the 'input' group: sudo usermod -aG input $USER"
            )

    def stop(self) -> None:
        self._stop_event.set()
        for device in self._devices:
            try:
                device.close()
            except (OSError, IOError):
                pass
        self._devices.clear()
        for t in self._threads:
            t.join(timeout=2.0)
        self._threads.clear()

    def is_alive(self) -> bool:
        return any(t.is_alive() for t in self._threads)

    def next_event(self) -> dict:
        with self._lock:
            self.new_event.clear()
            data = dict(self.event_data)
            self._reset_data()
        return data

    def _read_events(self, device) -> None:
        import evdev

        try:
            for event in device.read_loop():
                if self._stop_event.is_set():
                    break
                if (
                    event.type == evdev.ecodes.EV_KEY
                    and event.value == 1
                    and evdev.ecodes.BTN_MOUSE <= event.code < evdev.ecodes.BTN_JOYSTICK
                ):
                    # Only mouse buttons, not keyboard keys on hybrid devices.
                    with self._lock:
                        self.event_data["clicks"] += 1
                    self.new_event.set()
                elif event.type == evdev.ecodes.EV_REL:
                    with self._lock:
                        if event.code == evdev.ecodes.REL_X:
                            self.event_data["deltaX"] += abs(event.value)
                        elif event.code == evdev.ecodes.REL_Y:
                            self.event_data["deltaY"] += abs(event.value)
                        elif event.code == evdev.ecodes.REL_WHEEL:
                            self.event_data["scrollY"] += abs(event.value)
                        elif event.code == evdev.ecodes.REL_HWHEEL:
                            self.event_data["scrollX"] += abs(event.value)
                    self.new_event.set()
        except (OSError, IOError):
            self.logger.debug("Mouse device %s disconnected", device.path)
        finally:
            try:
                device.close()
            except (OSError, IOError):
                pass
