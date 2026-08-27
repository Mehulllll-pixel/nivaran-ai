const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = "C:\\Users\\mehul\\.gemini\\antigravity-ide\\brain\\62dcf72d-0969-4ad8-ab11-d94ed0ba2c40";
const CUSTOMER_ID = "cust_417168";

async function captureRow() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--window-size=1440,800"],
    defaultViewport: { width: 1440, height: 800, deviceScaleFactor: 2 },
  });

  const page = await browser.newPage();
  await page.goto("http://localhost:5173/", { waitUntil: "networkidle0" });
  await new Promise((r) => setTimeout(r, 1200));

  // Filter by customer id
  await page.evaluate((val) => {
    const input = document.getElementById("event-search-input");
    if (input) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      setter.call(input, val);
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }, CUSTOMER_ID);

  await new Promise((r) => setTimeout(r, 700));

  // Screenshot the whole events table card showing the filtered row
  const tableCard = await page.$("#events-table-card");
  if (tableCard) {
    const outPath = path.join(ARTIFACTS_DIR, "list_cust417168.png");
    await tableCard.screenshot({ path: outPath });
    console.log("Saved list screenshot:", outPath);
  } else {
    console.error("Could not find events table card");
  }

  await browser.close();
}

captureRow().catch((err) => { console.error(err); process.exit(1); });
