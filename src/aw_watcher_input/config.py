import argparse
import sys

from aw_core.config import load_config_toml

default_config = """
[aw-watcher-input]
poll_time = 5

[aw-watcher-input-testing]
poll_time = 1
""".strip()


def load_config(testing: bool):
    section = "aw-watcher-input" + ("-testing" if testing else "")
    return load_config_toml("aw-watcher-input", default_config)[section]


def parse_args():
    # get testing in a dirty way, because we need it for the config lookup
    testing = "--testing" in sys.argv
    config = load_config(testing)

    default_poll_time = config["poll_time"]

    parser = argparse.ArgumentParser(
        description="A watcher for keyboard and mouse input."
    )
    parser.add_argument(
        "--testing", dest="testing", action="store_true", help="run in testing mode"
    )
    parser.add_argument(
        "--poll-time", dest="poll_time", type=float, default=default_poll_time
    )
    parsed_args = parser.parse_args()
    return parsed_args
