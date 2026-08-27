const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = "C:\\Users\\mehul\\.gemini\\antigravity-ide\\brain\\62dcf72d-0969-4ad8-ab11-d94ed0ba2c40";

const CASES = [
  { customerId: "cust_665614", filename: "modal_gateway_timeout.png" },
  { customerId: "cust_654765", filename: "modal_otp_mismatch.png" },
  { customerId: "cust_120173", filename: "modal_card_expired.png" },
];

async function captureModalScreenshots() {
  console.log("Launching browser...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: ["--no-sandbox", "--window-size=1440,1100"],
    defaultViewport: { width: 1440, height: 1100, deviceScaleFactor: 2 },
  });

  const page = await browser.newPage();

  for (const { customerId, filename } of CASES) {
    console.log(`Navigating for ${customerId}...`);
    await page.goto("http://localhost:5173/", { waitUntil: "networkidle0" });
    await new Promise((r) => setTimeout(r, 1200));

    // Filter to the specific customer ID
    await page.evaluate((val) => {
      const input = document.getElementById("event-search-input");
      if (input) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        setter.call(input, val);
        input.dispatchEvent(new Event("input", { bubbles: true }));
      }
    }, customerId);
    await new Promise((r) => setTimeout(r, 800));

    // Click inspect button
    const btnSelector = `#inspect-btn-${customerId}`;
    await page.waitForSelector(btnSelector, { timeout: 4000 });
    await page.click(btnSelector);

    // Wait for modal
    await page.waitForSelector("#case-audit-modal", { timeout: 4000 });
    await new Promise((r) => setTimeout(r, 1000));

    const modal = await page.$("#case-audit-modal");
    if (modal) {
      const outPath = path.join(ARTIFACTS_DIR, filename);
      await modal.screenshot({ path: outPath });
      console.log(`Saved screenshot: ${outPath}`);
    } else {
      console.error(`Could not find #case-audit-modal for ${customerId}`);
    }
  }

  await browser.close();
}

captureModalScreenshots().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
