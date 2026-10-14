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
npm ci
npm run build
```

You can then configure aw-server or aw-server-rust to host the custom visualization.

To do so for aw-server, add the following to your config file (with the correct path!):

```toml
[server.custom_static]
aw-watcher-input = "/home/user/path/to/aw-watcher-input/visualization/dist"
```

For aw-server-rust, instead add the following to your config file (with the correct path!):

```toml
[custom_static]
aw-watcher-input = "/home/user/path/to/aw-watcher-input/visualization/dist"
```

You then need to restart aw-server/aw-server-rust for the changes to take effect.

Once the server is restarted, you can open the Activity view in the web UI, click "Edit view", then "Add visualization", then click the cogwheel and select "Custom visualization". This will open a popup asking for which visualization, here enter "aw-watcher-input".

Enter a title (for example, "Keyboard and mouse") when prompted, then click Save.
Select the host running aw-watcher-input and the date/time range in the Activity view.
The chart stacks presses and clicks in five-minute intervals for ranges up to six
hours, and hourly intervals for longer ranges. Quiet intervals appear as zeroes;
the totals below the chart cover the selected range. Each watcher sample is counted
in the interval containing its timestamp, rather than multiplying by its duration.

### Troubleshooting

- Use the server's current TOML configuration, **not** the old `aw-server.ini`.
  The config is normally under `~/.config/activitywatch/aw-server/aw-server.toml`
  or `~/.config/activitywatch/aw-server-rust/config.toml` on Linux. See
  [ActivityWatch's directory documentation](https://docs.activitywatch.net/en/latest/directories.html)
  for other platforms. The server startup log names the config it actually loads.
- Point the static mapping at the absolute **`visualization/dist`** directory,
  which must contain both `index.html` and `bundle.js`. Restart the server after
  changing it. A 404 at `/pages/aw-watcher-input/` means the mapping is missing or
  points at the wrong directory.
- If running `aw-server --testing` on port 5666, use
  `[server-testing.custom_static]` instead of `[server.custom_static]`.
  For `aw-server-rust --testing`, add `[custom_static]` to its testing config
  (normally `config-testing.toml`), rather than the production config.
- Open the visualization through the Activity view or the server URL, never by
  double-clicking `index.html`. A `file://` page cannot access the server API.
  Do not disable CORS protection to work around this.
- A missing-bucket message means the selected host has no
  `aw-watcher-input_<hostname>` bucket. Start the watcher against the same server
  (`--testing` if the server is in testing mode), and check the Buckets page.
  An empty-range message means the bucket exists but there is no input in that range.

For a direct check, open this URL on the same server/port as your web UI, replacing
`YOUR_HOST` with the host shown in the Buckets page:

```text
http://localhost:5600/pages/aw-watcher-input/?hostname=YOUR_HOST&start=2026-10-02T00:00:00Z&end=2026-10-03T00:00:00Z
```

For visualization development, run `npm test` in `visualization/` to check the
aggregation boundaries, and rebuild with `npm run build` after changing the source.

The custom visualization supports both light and dark mode, and will follow the ActivityWatch Theme setting (including "Auto (System)").

# Notes

This was massively inspired by ulogme by @karpathy, here's a screenshot of how it looks:

![screenshot of ulogme](https://karpathy.github.io/assets/ulogme_sv2.jpeg)

The idea is that we can do the same thing with ActivityWatch, and this watcher is an attempt to incorporate this specific part.

Here's a link to the blog post where he presents it: https://karpathy.github.io/2014/08/03/quantifying-productivity/
