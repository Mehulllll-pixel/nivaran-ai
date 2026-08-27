const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = "C:\\Users\\mehul\\.gemini\\antigravity-ide\\brain\\62dcf72d-0969-4ad8-ab11-d94ed0ba2c40";

async function captureSpotlight() {
  console.log("Launching Chrome...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--window-size=1440,960"],
    defaultViewport: { width: 1440, height: 960, deviceScaleFactor: 2 },
  });

  const page = await browser.newPage();
  console.log("Navigating to http://localhost:5173/...");
  await page.goto("http://localhost:5173/", { waitUntil: "networkidle0" });

  await page.waitForSelector("#voice-recovery-spotlight", { timeout: 10000 });
  await new Promise((r) => setTimeout(r, 800));

  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });

  // 1. Capture focused screenshot of the Voice Recovery Spotlight Card
  const spotlightElement = await page.$("#voice-recovery-spotlight");
  const spotlightScreenshotPath = path.join(ARTIFACTS_DIR, "voice_spotlight_updated.png");
  if (spotlightElement) {
    await spotlightElement.screenshot({ path: spotlightScreenshotPath });
    console.log(`Saved spotlight screenshot to: ${spotlightScreenshotPath}`);
  }

  // 2. Capture full dashboard overview
  const overviewPath = path.join(ARTIFACTS_DIR, "dashboard_command_center_overview.png");
  await page.screenshot({ path: overviewPath, fullPage: false });
  console.log(`Saved overview screenshot to: ${overviewPath}`);

  await browser.close();
  console.log("\n[SUCCESS] Spotlight screenshot capture complete!");
}

captureSpotlight().catch((err) => {
  console.error("Capture error:", err);
  process.exit(1);
});
