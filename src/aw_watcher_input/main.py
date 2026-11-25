import logging
from datetime import datetime, timezone
from time import sleep
from typing import Dict, Optional, Tuple

import aw_client
import click
from aw_core import Event
from aw_watcher_afk.listeners import KeyboardListener, MouseListener

logger = logging.getLogger(__name__)

POLL_TIME = 5


def build_event(
    last_run: datetime,
    now: datetime,
    keyboard_data: Dict[str, int],
    mouse_data: Dict[str, int],
    seq: int,
) -> Tuple[Event, float]:
    """Build the event for one poll window, and the pulsetime to send it with.

    Idle windows (all-zero counts) carry identical data and are sent as
    heartbeats that merge into one long event.

    Input windows are independent measurements: two consecutive windows can
    have the same counts, and heartbeat merging would fold them into a single
    event that keeps only one window's counts (#48). Merging only happens for
    events with identical data, so every input window is tagged with its own
    sequence number, which makes its data unique.
    """
    data = dict(**keyboard_data, **mouse_data)
    if all(count == 0 for count in data.values()):
        pulsetime = POLL_TIME + 0.1
    else:
        data["seq"] = seq
        pulsetime = 0.0
    return Event(timestamp=last_run, duration=(now - last_run), data=data), pulsetime


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

    # Register before connecting: the queue creates the bucket and retries
    # delivery even if the server is still starting (e.g. during a slow boot).
    bucket_name = "{}_{}".format(client.client_name, client.client_hostname)
    eventtype = "os.hid.input"
    client.create_bucket(bucket_name, eventtype, queued=True)
    client.connect()

    keyboard = KeyboardListener()
    keyboard.start()
    mouse = MouseListener()
    mouse.start()

    now = datetime.now(tz=timezone.utc)
    seq = 0

    while True:
        last_run = now

        # we want to ensure that the polling happens with a predictable cadence
        time_to_sleep = POLL_TIME - datetime.now().timestamp() % POLL_TIME
        # ensure that the sleep time is between 0 and poll_time (if system time is changed, this might be negative)
        time_to_sleep = max(min(time_to_sleep, POLL_TIME), 0)
        sleep(time_to_sleep)

        now = datetime.now(tz=timezone.utc)

        # If input:    Send a heartbeat with data, ensure the span is correctly set, and don't use pulsetime.
        # If no input: Send a heartbeat with all-zeroes in the data, use a pulsetime.
        # FIXME: Doesn't account for scrolling
        # FIXME: Counts both keyup and keydown
        keyboard_data = keyboard.next_event()
        mouse_data = mouse.next_event()
        seq += 1
        e, pulsetime = build_event(last_run, now, keyboard_data, mouse_data, seq)

        if pulsetime > 0:
            logger.info("No new input")
        else:
            logger.info(f"New input: {e}")

        client.heartbeat(bucket_name, e, pulsetime=pulsetime, queued=True)
