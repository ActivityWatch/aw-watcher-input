const aw_client = require("aw-client");
const Chart = require("chart.js/auto");
const { aggregate } = require("./aggregate");
let chart;

const url = new URL(window.location.href);

// Helper for sum-reduce
function add(accumulator, a) {
  return accumulator + a;
}

const VALID_THEMES = ["light", "dark", "auto"];

function normalizeTheme(theme) {
  return VALID_THEMES.includes(theme) ? theme : null;
}

function getStoredThemePreference() {
  try {
    return normalizeTheme(localStorage.getItem("theme"));
  } catch (_err) {
    return null;
  }
}

function resolveThemePreference() {
  return getStoredThemePreference() || "auto";
}

function resolveActualTheme(themePreference) {
  if (themePreference === "light" || themePreference === "dark") {
    return themePreference;
  }

  if (window.matchMedia) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return "light";
}

function applyTheme(actualTheme) {
  document.documentElement.dataset.theme = actualTheme;
  if (chart) {
    const color = getComputedStyle(document.body)
      .getPropertyValue("--text")
      .trim();
    chart.options.plugins.legend.labels.color = color;
    for (const axis of ["x", "y"]) {
      chart.options.scales[axis].ticks.color = color;
      chart.options.scales[axis].title.color = color;
    }
    chart.update();
  }
}

function applyCurrentTheme() {
  const themePreference = resolveThemePreference();
  const actualTheme = resolveActualTheme(themePreference);
  applyTheme(actualTheme);
}

function installThemeSync() {
  window.addEventListener("storage", (event) => {
    if (event.key === "theme") {
      applyCurrentTheme();
    }
  });

  if (!window.matchMedia) {
    return;
  }

  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  const onSystemThemeChange = () => {
    if (resolveThemePreference() === "auto") {
      applyCurrentTheme();
    }
  };

  if (mediaQuery.addEventListener) {
    mediaQuery.addEventListener("change", onSystemThemeChange);
  } else if (mediaQuery.addListener) {
    mediaQuery.addListener(onSystemThemeChange);
  }
}

let today_start = new Date();
today_start.setHours(0, 0, 0, 0);

let today_end = new Date();
today_end.setHours(24, 0, 0, 0);

const start = url.searchParams.get("start") || today_start;
const end = url.searchParams.get("end") || today_end;
const hostname = url.searchParams.get("hostname");

const aw = new aw_client.AWClient("aw-watcher-input", {
  baseURL: url.origin,
});

async function load() {
  applyCurrentTheme();
  installThemeSync();

  const statusEl = document.getElementById("status");
  const bucketName = `aw-watcher-input_${hostname}`;
  try {
    if (url.protocol === "file:") {
      throw new Error(
        "Open this visualization through ActivityWatch at /pages/aw-watcher-input/, rather than opening index.html directly."
      );
    }
    if (!hostname)
      throw new Error(
        "Select a host in ActivityWatch to view its input activity."
      );
    // Validate the range before requesting events.
    aggregate([], start, end);
    const buckets = await aw.getBuckets();
    if (!buckets[bucketName])
      throw new Error(
        `No input bucket for ${hostname}. Start aw-watcher-input on this host first.`
      );
    const events = await aw.getEvents(bucketName, { start, end });
    const { bins, intervalMs } = aggregate(events, start, end);
    const presses = bins.map((bin) => bin.presses).reduce(add, 0);
    const clicks = bins.map((bin) => bin.clicks).reduce(add, 0);
    document.getElementById("presses").textContent = presses;
    document.getElementById("clicks").textContent = clicks;
    const multipleDays = new Date(end) - new Date(start) > 24 * 3600000;
    const format = { hour: "2-digit", minute: "2-digit" };
    if (multipleDays) Object.assign(format, { month: "short", day: "numeric" });
    chart = new Chart(document.getElementById("input-chart"), {
      type: "bar",
      data: {
        labels: bins.map((bin) =>
          bin.timestamp.toLocaleString(undefined, format)
        ),
        datasets: [
          {
            label: "Presses",
            data: bins.map((bin) => bin.presses),
            backgroundColor: "#4285d4",
          },
          {
            label: "Clicks",
            data: bins.map((bin) => bin.clicks),
            backgroundColor: "#e39737",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: { labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              title: (items) =>
                bins[items[0].dataIndex].timestamp.toLocaleString(),
            },
          },
        },
        scales: {
          x: {
            stacked: true,
            ticks: { maxTicksLimit: 8 },
            title: {
              display: window.innerHeight > 200,
              text:
                intervalMs === 300000
                  ? "Time (5-minute intervals)"
                  : "Time (hourly intervals)",
            },
          },
          y: {
            stacked: true,
            beginAtZero: true,
            ticks: { precision: 0 },
            title: { display: window.innerHeight > 200, text: "Count" },
          },
        },
      },
    });
    applyCurrentTheme();
    statusEl.textContent =
      presses || clicks ? "" : "No input recorded in this time range.";
  } catch (error) {
    statusEl.textContent = error.message || String(error);
    document.getElementById("chart-container").hidden = true;
  }
}

load();
