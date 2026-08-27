const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = "C:\\Users\\mehul\\.gemini\\antigravity-ide\\brain\\62dcf72d-0969-4ad8-ab11-d94ed0ba2c40";

async function verifyHeroAudioModal() {
  console.log("Launching Chrome...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--window-size=1400,900"],
    defaultViewport: { width: 1400, height: 900 },
  });

  const page = await browser.newPage();
  
  console.log("Navigating to http://localhost:5173/...");
  await page.goto("http://localhost:5173/", { waitUntil: "networkidle0" });

  await page.waitForSelector("#events-table tbody tr", { timeout: 10000 });

  // Find the row with cust_hero_demo
  const rows = await page.$$("#events-table tbody tr");
  let heroRowIndex = -1;
  let nonHeroRowIndex = -1;

  for (let i = 0; i < rows.length; i++) {
    const text = await page.evaluate((el) => el.innerText, rows[i]);
    if (text.includes("cust_hero_demo")) {
      heroRowIndex = i + 1;
    } else if (nonHeroRowIndex === -1) {
      nonHeroRowIndex = i + 1;
    }
  }

  console.log(`Hero demo row index: ${heroRowIndex}, Non-hero row index: ${nonHeroRowIndex}`);

  if (heroRowIndex === -1) {
    console.error("cust_hero_demo not found in table!");
    await browser.close();
    process.exit(1);
  }

  // 1. Check Non-Hero Case Modal (Must NOT have audio player)
  if (nonHeroRowIndex !== -1) {
    console.log(`Checking non-hero modal (row ${nonHeroRowIndex})...`);
    await page.click(`#events-table tbody tr:nth-child(${nonHeroRowIndex})`);
    await page.waitForSelector("#case-audit-modal", { timeout: 5000 });
    const hasAudioNonHero = await page.evaluate(() => {
      return !!document.querySelector("#hero-demo-audio-player");
    });
    console.log(`Audio player present in non-hero modal: ${hasAudioNonHero} (Expected: false)`);
    await page.click("#close-modal-btn");
    await page.waitForFunction(() => !document.querySelector("#case-audit-modal"));
  }

  // 2. Check Hero Demo Modal (MUST have audio player pointing at /hero-demo-response.mp3)
  console.log(`Checking hero demo modal (row ${heroRowIndex})...`);
  await page.click(`#events-table tbody tr:nth-child(${heroRowIndex})`);
  await page.waitForSelector("#case-audit-modal", { timeout: 5000 });

  const heroAudioDetails = await page.evaluate(() => {
    const player = document.querySelector("#hero-demo-audio-player");
    const container = document.querySelector("#hero-audio-player-container");
    if (!player) return null;
    return {
      exists: true,
      src: player.getAttribute("src"),
      containerText: container ? container.innerText : "",
    };
  });

  console.log("Hero Demo Audio Details:", heroAudioDetails);

  if (!heroAudioDetails || heroAudioDetails.src !== "/hero-demo-response.mp3") {
    console.error("Hero audio player verification failed!");
    await browser.close();
    process.exit(1);
  }

  // Scroll the audio player into view
  await page.evaluate(() => {
    const el = document.querySelector("#hero-audio-player-container");
    if (el) el.scrollIntoView({ behavior: "instant", block: "center" });
  });

  // Take screenshot of the Hero Case Audit Modal with Audio Player
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
  const screenshotPath = path.join(ARTIFACTS_DIR, "hero_demo_audio_modal.png");
  await page.screenshot({ path: screenshotPath });
  console.log(`Saved screenshot to: ${screenshotPath}`);

  await browser.close();
  console.log("\n[SUCCESS] UI verification of hero audio playback completed successfully!");
}

verifyHeroAudioModal().catch((err) => {
  console.error("UI test error:", err);
  process.exit(1);
});
