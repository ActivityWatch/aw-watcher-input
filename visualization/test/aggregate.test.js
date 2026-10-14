const test = require("node:test");
const assert = require("node:assert/strict");
const { aggregate } = require("../src/aggregate");
const start = "2026-10-02T09:00:00Z";
const end = "2026-10-02T09:15:00Z";
const event = (timestamp, presses, clicks) => ({
  timestamp,
  data: { presses, clicks },
});

test("sums unsorted samples into five-minute bins and preserves quiet intervals", () => {
  const { bins, intervalMs } = aggregate(
    [
      event("2026-10-02T09:10:00Z", 7, 2),
      event(start, 12, 3),
      event("2026-10-02T09:04:59Z", 4, 1),
    ],
    start,
    end
  );
  assert.equal(intervalMs, 300000);
  assert.deepEqual(
    bins.map(({ presses, clicks }) => [presses, clicks]),
    [
      [16, 4],
      [0, 0],
      [7, 2],
    ]
  );
});

test("uses half-open range boundaries and puts exact interval boundaries in the next bin", () => {
  const { bins } = aggregate(
    [
      event("2026-10-02T08:59:59Z", 100, 100),
      event("2026-10-02T09:05:00Z", 5, 2),
      event(end, 100, 100),
    ],
    start,
    end
  );
  assert.deepEqual(
    bins.map((bin) => bin.presses),
    [0, 5, 0]
  );
});

test("accepts Date objects and offset timestamps for the same instant", () => {
  const { bins } = aggregate(
    [event("2026-10-02T11:01:00+02:00", 3, 1)],
    new Date(start),
    new Date(end)
  );
  assert.equal(bins[0].presses, 3);
});

test("uses hourly bins for daily ranges, including the last partial interval", () => {
  const { bins, intervalMs } = aggregate(
    [event("2026-10-02T16:00:00Z", 9, 1)],
    start,
    "2026-10-02T16:30:00Z"
  );
  assert.equal(intervalMs, 3600000);
  assert.equal(bins.length, 8);
  assert.equal(bins[7].presses, 9);
});

test("missing click fields or invalid values do not poison totals", () => {
  const { bins } = aggregate(
    [
      event(start, 3, undefined),
      event(start, NaN, -1),
      event(start, "4", Infinity),
      event("invalid", 100, 100),
    ],
    start,
    end
  );
  assert.deepEqual([bins[0].presses, bins[0].clicks], [3, 0]);
});

test("empty data produces zero bins and invalid ranges fail explicitly", () => {
  assert.deepEqual(
    aggregate([], start, end).bins.map((bin) => bin.presses),
    [0, 0, 0]
  );
  for (const range of [
    [end, start],
    [start, start],
    ["invalid", end],
  ]) {
    assert.throws(() => aggregate([], ...range), /range is invalid/);
  }
});
