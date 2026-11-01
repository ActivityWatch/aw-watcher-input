const aw_client = require("aw-client");
// Browserify doesn't understand the "exports" field in chart.js's package.json,
// so require the UMD build directly.
const Chart = require("chart.js/dist/chart.umd.js");
const { binEvents } = require("./bins");

const url = new URL(window.location.href); // www.test.com/?filename=test

// Helper for sum-reduce
function add(accumulator, a) {
  return accumulator + a;
}

// TODO: Avoid testing-port assumption
const testing = url.port != 5600;

let today_start = new Date();
today_start.setHours(0, 0, 0, 0);

let today_end = new Date();
today_end.setHours(23, 59, 59, 999);

const start = url.searchParams.get("start") || today_start;
const end = url.searchParams.get("end") || today_end;
const hostname = url.searchParams.get("hostname");
//console.log(hostname, start, end);

const aw = new aw_client.AWClient("aw-watcher-input", {
  testing: testing,
  baseURL: url.origin,
});

function renderChart(events) {
  const { labels, presses, clicks } = binEvents(events, start, end);
  new Chart(document.getElementById("chart"), {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        { label: "Key presses", data: presses, backgroundColor: "#4e79a7" },
        { label: "Mouse clicks", data: clicks, backgroundColor: "#f28e2b" },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 } },
      },
    },
  });
}

function load() {
  const statusEl = document.getElementById("status");
  const pressesEl = document.getElementById("presses");
  const clicksEl = document.getElementById("clicks");
  const bucketName = `aw-watcher-input_${hostname}`;

  aw.getBuckets()
    .then((bs) => {
      if (bs[bucketName] === undefined) {
        throw `no bucket called ${bucketName}`;
      }
    })
    .then(() => {
      return aw.getEvents(bucketName, { start: start, end: end });
    })
    .then((events) => {
      console.debug(events);
      const presses = events.map((e) => e.data.presses || 0).reduce(add, 0);
      const clicks = events.map((e) => e.data.clicks || 0).reduce(add, 0);
      pressesEl.append(presses);
      clicksEl.append(clicks);
      renderChart(events);
    })
    .catch((msg) => statusEl.append(msg));
}

load();
