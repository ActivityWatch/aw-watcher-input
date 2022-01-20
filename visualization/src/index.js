const aw_client = require("aw-client");

const url = new URL(window.location.href); // www.test.com/?filename=test

// Helper for sum-reduce
function add(accumulator, a) {
  return accumulator + a;
}

// TODO: Avoid hardcoding and pass port directly to AWClient constructor
const testing = url.port == 5666;

let today_start = new Date();
today_start.setHours(0, 0, 0, 0);

let today_end = new Date();
today_end.setHours(23, 59, 59, 999);

const start = url.searchParams.get("start") || today_start;
const stop = url.searchParams.get("stop") || today_end;
const hostname = url.searchParams.get("hostname");
console.log(hostname, start, stop);

const aw = new aw_client.AWClient("aw-watcher-input", { testing: true });

function load() {
  const statusEl = document.getElementById("status");
  const pressesEl = document.getElementById("presses");
  const clicksEl = document.getElementById("clicks");
  const bucketName = `aw-watcher-input_${hostname}`;

  aw.getBuckets()
    .then(bs => {
      if (bs[bucketName] === undefined) {
        throw `no bucket called ${bucketName}`;
      }
    })
    .then(() => {
      return aw.getEvents(bucketName, { start: start, stop: stop });
    })
    .then(events => {
      console.log(events);
      const presses = events.map(e => e.data.presses).reduce(add, 0);
      const clicks = events.map(e => e.data.clicks).reduce(add, 0);
      pressesEl.append(presses);
      clicksEl.append(clicks);
    })
    .catch(msg => statusEl.append(msg));
}

load();
