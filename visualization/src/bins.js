// Group input events into time bins for the bar chart.
// Kept free of DOM/Chart.js dependencies so it can be tested with plain node.

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

// Use hourly bins for ranges up to two days, daily bins for anything longer.
function binSizeFor(start, end) {
  return end - start <= 2 * DAY ? HOUR : DAY;
}

// Start of the bin containing `date`, in local time.
function floorToBin(date, binSize) {
  const d = new Date(date);
  if (binSize === DAY) {
    d.setHours(0, 0, 0, 0);
  } else {
    d.setMinutes(0, 0, 0);
  }
  return d;
}

function nextBin(date, binSize) {
  const d = new Date(date);
  if (binSize === DAY) {
    // setDate instead of adding 24h, so DST changes don't shift the bins
    d.setDate(d.getDate() + 1);
  } else {
    d.setTime(d.getTime() + HOUR);
  }
  return d;
}

function formatBin(date, binSize) {
  if (binSize === DAY) {
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }
  return String(date.getHours()).padStart(2, "0") + ":00";
}

// Returns { labels, presses, clicks }, with one entry per bin in [start, end].
// Each event is counted in the bin its timestamp falls in.
function binEvents(events, start, end) {
  start = new Date(start);
  end = new Date(end);
  const binSize = binSizeFor(start, end);

  const labels = [];
  const presses = [];
  const clicks = [];
  const index = new Map();
  for (let t = floorToBin(start, binSize); t <= end; t = nextBin(t, binSize)) {
    index.set(t.getTime(), labels.length);
    labels.push(formatBin(t, binSize));
    presses.push(0);
    clicks.push(0);
  }

  for (const e of events) {
    const i = index.get(floorToBin(e.timestamp, binSize).getTime());
    if (i === undefined) {
      continue;
    }
    presses[i] += e.data.presses || 0;
    clicks[i] += e.data.clicks || 0;
  }

  return { labels, presses, clicks };
}

module.exports = { binEvents, binSizeFor, HOUR, DAY };
