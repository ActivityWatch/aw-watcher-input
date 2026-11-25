import unittest
from datetime import datetime, timedelta, timezone

from aw_transform.heartbeats import heartbeat_reduce

from aw_watcher_input.main import POLL_TIME, build_event

TIMEOUT = POLL_TIME + 0.1
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW = timedelta(seconds=POLL_TIME)


def build_windows(presses):
    """Build one event per poll window, as the watcher loop would."""
    events = []
    for seq, count in enumerate(presses):
        start = T0 + seq * WINDOW
        event, _ = build_event(
            start, start + WINDOW, {"presses": count}, {"clicks": 0}, seq
        )
        events.append(event)
    return events


class TestHeartbeatMerge(unittest.TestCase):
    def test_equal_count_input_windows_keep_all_presses(self):
        # #48: four 5 s windows with one key press each must not become a
        # single window that keeps only one press.
        events = build_windows([3, 3, 3, 3])
        merged = heartbeat_reduce(events, TIMEOUT)

        self.assertEqual(sum(e.data["presses"] for e in merged), 12)

    def test_equal_count_input_windows_do_not_merge(self):
        events = build_windows([3, 3])
        merged = heartbeat_reduce(events, 0.0)

        self.assertEqual(len(merged), 2)

    def test_idle_windows_still_merge(self):
        events = build_windows([0, 0, 0, 0])
        merged = heartbeat_reduce(events, TIMEOUT)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].duration, 4 * WINDOW)

    def test_input_windows_do_not_merge_across_idle_windows(self):
        # Input, an idle gap, then input again: the resumed window must not be
        # folded into either the earlier input or the merged idle event.
        events = build_windows([2, 2, 0, 0, 2])
        merged = heartbeat_reduce(events, TIMEOUT)

        self.assertEqual(sum(e.data["presses"] for e in merged), 6)
        self.assertEqual(len([e for e in merged if e.data["presses"]]), 3)

    def test_idle_window_data_is_unchanged(self):
        event, pulsetime = build_event(
            T0, T0 + WINDOW, {"presses": 0}, {"clicks": 0}, 1
        )

        self.assertEqual(event.data, {"presses": 0, "clicks": 0})
        self.assertEqual(pulsetime, TIMEOUT)

    def test_input_window_has_unique_data(self):
        first, pulsetime = build_event(
            T0, T0 + WINDOW, {"presses": 1}, {"clicks": 0}, 1
        )
        second, _ = build_event(
            T0 + WINDOW, T0 + 2 * WINDOW, {"presses": 1}, {"clicks": 0}, 2
        )

        self.assertNotEqual(first.data, second.data)
        self.assertEqual(pulsetime, 0.0)


if __name__ == "__main__":
    unittest.main()
