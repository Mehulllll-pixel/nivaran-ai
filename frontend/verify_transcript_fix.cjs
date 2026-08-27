const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");
const http = require("http");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = "C:\\Users\\mehul\\.gemini\\antigravity-ide\\brain\\62dcf72d-0969-4ad8-ab11-d94ed0ba2c40";

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = "";
      res.on("data", (chunk) => data += chunk);
      res.on("end", () => resolve(JSON.parse(data)));
    }).on("error", reject);
  });
}

async function run() {
  // 1. Fetch raw API and check cust_738813's voice_transcript
  console.log("Fetching /events/ from API...");
  const events = await fetchJson("http://127.0.0.1:8000/events/");
  
  const target = events.find(e => e.customer_id === "cust_738813");
  const voiceEvents = events.filter(e => e.voice_transcript !== null && e.voice_transcript !== undefined && e.voice_transcript !== "");
  
  console.log("\n=== RAW API: cust_738813 ===");
  if (target) {
    console.log(`  customer_id: ${target.customer_id}`);
    console.log(`  demo_transcript: ${JSON.stringify(target.demo_transcript)}`);
    console.log(`  voice_transcript: ${JSON.stringify(target.voice_transcript)}`);
  } else {
    console.log("  Event not found in API response.");
  }
  
  console.log(`\n=== Events WITH voice_transcript (first 5) ===`);
  voiceEvents.slice(0, 5).forEach(e => {
    console.log(`  ${e.customer_id}: "${e.voice_transcript}"`);
  });

  // 2. Screenshot: filter to cust_738813 row
  console.log("\nLaunching browser...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: ["--no-sandbox", "--window-size=1440,300"],
    defaultViewport: { width: 1440, height: 300, deviceScaleFactor: 2 },
  });
  const page = await browser.newPage();
  await page.goto("http://localhost:5173/", { waitUntil: "networkidle0" });
  await new Promise((r) => setTimeout(r, 1500));

  // Filter to cust_738813
  await page.evaluate((val) => {
    const input = document.getElementById("event-search-input");
    if (input) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      setter.call(input, val);
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }, "cust_738813");
  await new Promise((r) => setTimeout(r, 700));

  const tableCard = await page.$("#events-table-card");
  if (tableCard) {
    const p = path.join(ARTIFACTS_DIR, "cust738813_row.png");
    await tableCard.screenshot({ path: p });
    console.log("Saved cust_738813 row screenshot:", p);
  }

  // 3. Screenshot: events with real transcripts - show anchor events
  await page.evaluate(() => {
    const input = document.getElementById("event-search-input");
    if (input) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      setter.call(input, "cust_demo");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
  });
  await new Promise((r) => setTimeout(r, 700));

  const tableCard2 = await page.$("#events-table-card");
  if (tableCard2) {
    const p2 = path.join(ARTIFACTS_DIR, "anchor_transcripts.png");
    await tableCard2.screenshot({ path: p2 });
    console.log("Saved anchor transcripts screenshot:", p2);
  }

  await browser.close();
  console.log("Done.");
}

run().catch(err => { console.error(err); process.exit(1); });
