const aw_client = require("aw-client");

const url = new URL(window.location.href); // www.test.com/?filename=test

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
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return "light";
}

function applyTheme(actualTheme) {
  document.documentElement.dataset.theme = actualTheme;
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

function load() {
  applyCurrentTheme();
  installThemeSync();

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
      const presses = events.map((e) => e.data.presses).reduce(add, 0);
      const clicks = events.map((e) => e.data.clicks).reduce(add, 0);
      pressesEl.append(presses);
      clicksEl.append(clicks);
    })
    .catch((msg) => statusEl.append(msg));
}

load();
