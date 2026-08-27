const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = "C:\\Users\\mehul\\.gemini\\antigravity-ide\\brain\\62dcf72d-0969-4ad8-ab11-d94ed0ba2c40";

async function captureAnchorModals() {
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
  await new Promise((r) => setTimeout(r, 1200));

  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });

  const anchors = [
    { customerId: "cust_demo_wrongnum", filename: "modal_wrong_number.png" },
    { customerId: "cust_demo_dispute", filename: "modal_dispute.png" },
    { customerId: "cust_demo_nocontact", filename: "modal_nocontact.png" },
  ];

  for (const anchor of anchors) {
    console.log(`\nFiltering for customer ID: ${anchor.customerId}...`);
    
    // Set search value and trigger input event for React
    await page.evaluate((val) => {
      const input = document.getElementById("event-search-input");
      if (input) {
        // Native setter to ensure React onChange fires
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeInputValueSetter.call(input, val);
        input.dispatchEvent(new Event("input", { bubbles: true }));
      }
    }, anchor.customerId);

    await new Promise((r) => setTimeout(r, 800));

    // Click the first matching row in the tbody
    const firstRow = await page.$("#events-table tbody tr");
    if (firstRow) {
      await firstRow.click();
      console.log(`Clicked table row for ${anchor.customerId}`);
      await page.waitForSelector("#case-audit-modal", { timeout: 6000 });
      await new Promise((r) => setTimeout(r, 700));

      const modalElement = await page.$("#case-audit-modal");
      if (modalElement) {
        const outPath = path.join(ARTIFACTS_DIR, anchor.filename);
        await modalElement.screenshot({ path: outPath });
        console.log(`Saved screenshot: ${outPath}`);
      }

      // Close modal
      const closeBtn = await page.$("#close-modal-btn");
      if (closeBtn) {
        await closeBtn.click();
        await new Promise((r) => setTimeout(r, 600));
      }
    } else {
      console.error(`Could not find row for ${anchor.customerId}`);
    }
  }

  await browser.close();
  console.log("\n[SUCCESS] All anchor screenshots captured successfully!");
}

captureAnchorModals().catch((err) => {
  console.error("Capture error:", err);
  process.exit(1);
});
