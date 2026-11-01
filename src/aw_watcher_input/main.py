import logging
import os
from datetime import datetime, timezone
from time import sleep
from typing import Optional, Tuple

import aw_client
import click
from aw_core import Event
from aw_watcher_afk.listeners import EventFactory, KeyboardListener, MouseListener

logger = logging.getLogger(__name__)


def _create_listeners() -> Tuple[EventFactory, EventFactory]:
    """Return (keyboard, mouse) listeners appropriate for the current session.

    On Wayland (WAYLAND_DISPLAY is set) the pynput-based listeners cannot
    capture global input events, so evdev-based alternatives are used instead.
    They require read access to /dev/input/event* — typically via the 'input'
    group (``sudo usermod -aG input $USER``).
    """
    if os.environ.get("WAYLAND_DISPLAY"):
        try:
            from aw_watcher_input.listeners_wayland import (
                EvdevKeyboardListener,
                EvdevMouseListener,
            )

            logger.info("Wayland display detected — using evdev-based listeners")
            return EvdevKeyboardListener(), EvdevMouseListener()
        except Exception as exc:
            logger.warning(
                "Failed to load evdev listeners (%s); falling back to pynput", exc
            )
    return KeyboardListener(), MouseListener()


@click.command()
@click.option("--host", default=None, help="Hostname of the aw-server to connect to.")
@click.option(
    "--port", default=None, type=int, help="Port of the aw-server to connect to."
)
@click.option("--testing", is_flag=True)
def main(testing: bool, host: Optional[str], port: Optional[int]):
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting watcher...")
    client = aw_client.ActivityWatchClient(
        "aw-watcher-input", testing=testing, host=host, port=port
    )
    client.wait_for_start()
    client.connect()

    # Create bucket
    bucket_name = "{}_{}".format(client.client_name, client.client_hostname)
    eventtype = "os.hid.input"
    client.create_bucket(bucket_name, eventtype, queued=False)
    poll_time = 5

    keyboard, mouse = _create_listeners()
    keyboard.start()
    mouse.start()

    now = datetime.now(tz=timezone.utc)

    while True:
        last_run = now

        # we want to ensure that the polling happens with a predictable cadence
        time_to_sleep = poll_time - datetime.now().timestamp() % poll_time
        # ensure that the sleep time is between 0 and poll_time (if system time is changed, this might be negative)
        time_to_sleep = max(min(time_to_sleep, poll_time), 0)
        sleep(time_to_sleep)

        now = datetime.now(tz=timezone.utc)

        # If input:    Send a heartbeat with data, ensure the span is correctly set, and don't use pulsetime.
        # If no input: Send a heartbeat with all-zeroes in the data, use a pulsetime.
        # FIXME: Doesn't account for scrolling
        # FIXME: Counts both keyup and keydown
        keyboard_data = keyboard.next_event()
        mouse_data = mouse.next_event()
        merged_data = dict(**keyboard_data, **mouse_data)
        e = Event(timestamp=last_run, duration=(now - last_run), data=merged_data)

        pulsetime = 0.0
        if all(map(lambda v: v == 0, merged_data.values())):
            pulsetime = poll_time + 0.1
            logger.info("No new input")
        else:
            logger.info(f"New input: {e}")

        client.heartbeat(bucket_name, e, pulsetime=pulsetime, queued=True)
