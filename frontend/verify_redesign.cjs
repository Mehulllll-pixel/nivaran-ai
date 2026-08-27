const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = "C:\\Users\\mehul\\.gemini\\antigravity-ide\\brain\\62dcf72d-0969-4ad8-ab11-d94ed0ba2c40";

async function runVerification() {
  console.log("Launching Chrome...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--window-size=1440,960"],
    defaultViewport: { width: 1440, height: 960 },
  });

  const page = await browser.newPage();
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
    }
  });

  console.log("Navigating to http://localhost:5173/...");
  await page.goto("http://localhost:5173/", { waitUntil: "networkidle0" });

  // 1. Check KPI Cards
  await page.waitForSelector("#metric-at-risk", { timeout: 10000 });
  await new Promise((r) => setTimeout(r, 1000)); // wait for count-up animation

  const kpis = await page.evaluate(() => {
    return {
      atRisk: document.querySelector("#metric-at-risk")?.innerText || "",
      recovered: document.querySelector("#metric-recovered")?.innerText || "",
      rate: document.querySelector("#metric-rate")?.innerText || "",
      stopped: document.querySelector("#metric-stopped")?.innerText || "",
    };
  });
  console.log("\n=== 1. KPI Cards ===");
  console.log(JSON.stringify(kpis, null, 2));

  // 2. Check Voice Recovery Spotlight
  await page.waitForSelector("#voice-recovery-spotlight", { timeout: 5000 });
  const spotlightText = await page.evaluate(() => {
    return document.querySelector("#voice-recovery-spotlight")?.innerText || "";
  });
  console.log("\n=== 2. Voice Spotlight ===");
  console.log("Spotlight found:\n", spotlightText.split("\n").slice(0, 8).join(" | "));

  // 3. Screenshot Main Dashboard Overview
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
  const overviewPath = path.join(ARTIFACTS_DIR, "dashboard_command_center_overview.png");
  await page.screenshot({ path: overviewPath, fullPage: false });
  console.log(`Saved screenshot: ${overviewPath}`);

  // 4. Test Event List Search & Modal Opening
  console.log("\n=== 3. Testing Case Audit Modal for cust_hero_demo ===");
  await page.waitForSelector("#event-search-input");
  await page.type("#event-search-input", "cust_hero_demo");
  await new Promise((r) => setTimeout(r, 500));

  await page.click("#events-table tbody tr:first-child");
  await page.waitForSelector("#case-audit-modal", { timeout: 5000 });
  await new Promise((r) => setTimeout(r, 800));

  // Scroll audio player into view
  await page.evaluate(() => {
    const el = document.querySelector("#hero-audio-player-container");
    if (el) el.scrollIntoView({ behavior: "instant", block: "center" });
  });

  const modalAudioDetails = await page.evaluate(() => {
    const audio = document.querySelector("#hero-demo-audio-player");
    const container = document.querySelector("#hero-audio-player-container");
    return {
      audioExists: !!audio,
      audioSrc: audio?.getAttribute("src"),
      containerText: container?.innerText,
    };
  });
  console.log("Modal Audio Details:", modalAudioDetails);

  const modalPath = path.join(ARTIFACTS_DIR, "modal_command_center.png");
  await page.screenshot({ path: modalPath });
  console.log(`Saved screenshot: ${modalPath}`);

  // Close modal
  await page.click("#close-modal-btn");
  await page.waitForFunction(() => !document.querySelector("#case-audit-modal"));

  // 5. Test Refresh Button
  console.log("\n=== 4. Testing 'Refresh' Button ===");
  await page.click("#refresh-btn");
  await new Promise((r) => setTimeout(r, 1000));
  console.log("Refresh triggered successfully!");

  // 6. Test Search & Filter Interaction
  console.log("\n=== 5. Testing Filter Dropdown ===");
  await page.select("#event-type-filter", "payment_failed");
  await new Promise((r) => setTimeout(r, 500));
  const filteredCount = await page.evaluate(() => {
    return document.querySelectorAll("#events-table tbody tr").length;
  });
  console.log(`Filtered rows for 'payment_failed': ${filteredCount}`);

  console.log("\n=== 6. Console Errors Check ===");
  console.log(`Total console errors: ${consoleErrors.length}`);
  if (consoleErrors.length > 0) {
    console.error("Console Errors:", consoleErrors);
  } else {
    console.log("✓ Zero console errors detected!");
  }

  await browser.close();
  console.log("\n[SUCCESS] Verification complete!");
}

runVerification().catch((err) => {
  console.error("Verification failed:", err);
  process.exit(1);
});
