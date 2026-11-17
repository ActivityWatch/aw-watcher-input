"""Exercise evdev event handling without hardware or the optional evdev package."""

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from aw_watcher_input.listeners_wayland import EvdevMouseListener, _is_mouse


ECODES = SimpleNamespace(
    EV_KEY=1,
    EV_REL=2,
    KEY_A=30,
    KEY_Z=44,
    KEY_SPACE=57,
    KEY_ENTER=28,
    KEY_LEFTCTRL=29,
    BTN_MOUSE=272,
    BTN_LEFT=272,
    BTN_TASK=279,
    BTN_JOYSTICK=288,
    REL_X=0,
    REL_Y=1,
    REL_HWHEEL=6,
    REL_WHEEL=8,
)


class Device:
    def __init__(self, events=()):
        self.events = events
        self.closed = False

    def capabilities(self):
        return {
            ECODES.EV_KEY: [ECODES.KEY_A, ECODES.BTN_LEFT],
            ECODES.EV_REL: [ECODES.REL_X, ECODES.REL_Y],
        }

    def read_loop(self):
        return iter(self.events)

    def close(self):
        self.closed = True


def event(event_type, code, value):
    return SimpleNamespace(type=event_type, code=code, value=value)


class MouseEventsTest(unittest.TestCase):
    def setUp(self):
        self.evdev = patch.dict(sys.modules, {"evdev": SimpleNamespace(ecodes=ECODES)})
        self.evdev.start()
        self.addCleanup(self.evdev.stop)

    def test_only_mouse_buttons_count_as_clicks(self):
        device = Device(
            [
                event(ECODES.EV_KEY, ECODES.KEY_LEFTCTRL, 1),
                event(ECODES.EV_KEY, ECODES.BTN_LEFT, 1),
                event(ECODES.EV_KEY, ECODES.BTN_LEFT, 0),
                event(ECODES.EV_KEY, ECODES.BTN_LEFT, 2),
                event(ECODES.EV_KEY, ECODES.BTN_TASK, 1),
                event(ECODES.EV_KEY, ECODES.BTN_JOYSTICK, 1),
                event(ECODES.EV_REL, ECODES.REL_X, -7),
                event(ECODES.EV_REL, ECODES.REL_WHEEL, -1),
            ]
        )
        listener = EvdevMouseListener()
        listener._read_events(device)
        self.assertEqual(
            listener.next_event(),
            {"clicks": 2, "deltaX": 7, "deltaY": 0, "scrollX": 0, "scrollY": 1},
        )
        self.assertTrue(device.closed)
        self.assertEqual(listener.next_event()["clicks"], 0)

    def test_hybrid_keyboard_pointer_is_still_a_mouse(self):
        self.assertTrue(_is_mouse(Device()))
