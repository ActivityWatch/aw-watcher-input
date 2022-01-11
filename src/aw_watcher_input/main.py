from time import sleep
from datetime import datetime, timezone
import logging

import click

import aw_client
from aw_core import Event
from aw_watcher_afk.listeners import KeyboardListener, MouseListener

logger = logging.getLogger(__name__)


@click.command()
@click.option("--testing", is_flag=True)
def main(testing: bool):
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting watcher...")
    client = aw_client.ActivityWatchClient("aw-watcher-input", testing=testing)
    client.connect()

    # Create bucjet
    bucket_name = "{}_{}".format(client.client_name, client.client_hostname)
    eventtype = "os.hid.input"
    client.create_bucket(bucket_name, eventtype, queued=True)
    poll_time = 1

    keyboard = KeyboardListener()
    keyboard.start()
    mouse = MouseListener()
    mouse.start()

    now = datetime.now(tz=timezone.utc)

    while True:
        last_run = now
        sleep(poll_time)
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
