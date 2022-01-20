aw-watcher-input
================

Track your keypresses and mouse movements with [ActivityWatch](https://activitywatch.net).

NOTE: Work in progress, contributions welcome!

NOTE: This does not track *which* keys you press, only that you pressed any key some number of times in a given time span. This is **not a keylogger**, and never will be (due to the massive security and privacy implications).


# Build

Make sure you have Python 3.7+ and `poetry` installed, then install with `poetry install`.


# Usage

Run `poetry run aw-watcher-input --help` for usage instructions.

We might eventually create binary builds (like the ones bundled with ActivityWatch for aw-watcher-afk and aw-watcher-window) to make it easier to get this watcher up and running, but it's still a bit too early for that.


## Custom visualization

This watcher ships with an **experimental** custom visualization which needs special configuration. 

**NOTE:** This is a work-in-progress. Custom visualizations is an experimental feature with little to no decent documentation, so far.

First, you need to build it, which you can do by:

```sh
cd visualization/
npm install -g pug browserify  # might need sudo
npm install
make build
```

You can then configure aw-server (aw-server-rust not yet supported) to host the custom visualization by adding the following to your aw-server config file:

```toml
[server.custom_static]
aw-watcher-input = "/home/user/path/to/aw-watcher-input/visualization/dist"
```

# Notes

This was massively inspired by ulogme by @karpathy, here's a screenshot of how it looks:

![screenshot of ulogme](https://karpathy.github.io/assets/ulogme_sv2.jpeg)

The idea is that we can do the same thing with ActivityWatch, and this watcher is an attempt to incorporate this specific part.

Here's a link to the blog post where he presents it: https://karpathy.github.io/2014/08/03/quantifying-productivity/
