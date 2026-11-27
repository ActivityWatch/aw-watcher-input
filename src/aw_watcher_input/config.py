from aw_core.config import load_config_toml

default_config = """
[aw-watcher-input]
poll_time = 5

[aw-watcher-input-testing]
poll_time = 5
""".strip()


def load_config(testing: bool):
    section = "aw-watcher-input" + ("-testing" if testing else "")
    return load_config_toml("aw-watcher-input", default_config)[section]
