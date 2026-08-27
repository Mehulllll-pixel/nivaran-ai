const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = "C:\\Users\\mehul\\.gemini\\antigravity-ide\\brain\\62dcf72d-0969-4ad8-ab11-d94ed0ba2c40";

async function captureEventList() {
  console.log("Launching Chrome...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--window-size=1440,1100"],
    defaultViewport: { width: 1440, height: 1100, deviceScaleFactor: 2 },
  });

  const page = await browser.newPage();
  console.log("Navigating to http://localhost:5173/...");
  await page.goto("http://localhost:5173/", { waitUntil: "networkidle0" });
  await new Promise((r) => setTimeout(r, 1500));

  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });

  // Screenshot the entire table card
  const tableCard = await page.$("#events-table-card");
  if (tableCard) {
    const outPath = path.join(ARTIFACTS_DIR, "event_list_variety.png");
    await tableCard.screenshot({ path: outPath });
    console.log(`Saved screenshot: ${outPath}`);
  } else {
    console.error("Could not find #events-table-card");
  }

  await browser.close();
}

captureEventList().catch((err) => {
  console.error("Capture error:", err);
  process.exit(1);
});
