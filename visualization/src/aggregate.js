// Count each input sample once, in the interval containing its timestamp.
function aggregate(events, start, end) {
  const startMs = new Date(start).getTime();
  const endMs = new Date(end).getTime();
  if (
    !Number.isFinite(startMs) ||
    !Number.isFinite(endMs) ||
    endMs <= startMs
  ) {
    throw new Error("The selected time range is invalid.");
  }
  const intervalMs = endMs - startMs <= 6 * 3600000 ? 5 * 60000 : 3600000;
  const bins = Array.from(
    { length: Math.ceil((endMs - startMs) / intervalMs) },
    (_, i) => ({
      timestamp: new Date(startMs + i * intervalMs),
      presses: 0,
      clicks: 0,
    })
  );
  for (const event of events) {
    const timestamp = new Date(event.timestamp).getTime();
    if (
      !Number.isFinite(timestamp) ||
      timestamp < startMs ||
      timestamp >= endMs
    )
      continue;
    const bin = bins[Math.floor((timestamp - startMs) / intervalMs)];
    for (const key of ["presses", "clicks"]) {
      const value = event.data[key];
      if (typeof value === "number" && Number.isFinite(value) && value >= 0)
        bin[key] += value;
    }
  }
  return { bins, intervalMs };
}

module.exports = { aggregate };
