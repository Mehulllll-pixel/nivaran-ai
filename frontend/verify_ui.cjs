const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const ARTIFACTS_DIR = "C:\\Users\\mehul\\.gemini\\antigravity-ide\\brain\\4e9578a6-add3-4677-a066-7b444241abe1";
const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

async function run() {
  console.log("Launching headless Chrome...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--window-size=1400,900"],
    defaultViewport: { width: 1400, height: 900 },
  });

  const page = await browser.newPage();
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
    }
  });

  console.log("Navigating to http://127.0.0.1:5173/...");
  await page.goto("http://127.0.0.1:5173/", { waitUntil: "networkidle0" });

  // 1. Check KPI cards
  await page.waitForSelector("#metric-at-risk", { timeout: 10000 });
  const kpiCards = await page.evaluate(() => {
    const atRisk = document.querySelector("#metric-at-risk")?.innerText || "";
    const recovered = document.querySelector("#metric-recovered")?.innerText || "";
    const rate = document.querySelector("#metric-rate")?.innerText || "";
    const stopped = document.querySelector("#metric-stopped")?.innerText || "";
    return { atRisk, recovered, rate, stopped };
  });
  console.log("\n=== 1. KPI Cards Text ===");
  console.log(JSON.stringify(kpiCards, null, 2));

  // Screenshot main dashboard
  const overviewPath = path.join(ARTIFACTS_DIR, "dashboard_overview.png");
  await page.screenshot({ path: overviewPath, fullPage: false });
  console.log(`Saved screenshot: ${overviewPath}`);

  // 2. Click 1st event row
  console.log("\n=== 2. Testing Case Audit Modal - Event 1 ===");
  await page.waitForSelector("#events-table tbody tr");
  const firstRowBtn = await page.$("#events-table tbody tr:first-child button");
  if (firstRowBtn) {
    await firstRowBtn.click();
  } else {
    await page.click("#events-table tbody tr:first-child");
  }

  await page.waitForSelector("#case-audit-modal", { timeout: 5000 });
  const modal1Text = await page.evaluate(() => {
    return document.querySelector("#case-audit-modal")?.innerText || "";
  });
  console.log("Modal 1 Content:\n" + modal1Text.split("\n").slice(0, 15).join("\n") + "\n...");

  const modal1Path = path.join(ARTIFACTS_DIR, "case_modal_1.png");
  await page.screenshot({ path: modal1Path });
  console.log(`Saved screenshot: ${modal1Path}`);

  // Close modal
  await page.click("#close-modal-btn");
  await page.waitForFunction(() => !document.querySelector("#case-audit-modal"));

  // 3. Click 2nd event row
  console.log("\n=== 3. Testing Case Audit Modal - Event 2 ===");
  const secondRowBtn = await page.$("#events-table tbody tr:nth-child(2) button");
  if (secondRowBtn) {
    await secondRowBtn.click();
  }

  await page.waitForSelector("#case-audit-modal", { timeout: 5000 });
  const modal2Text = await page.evaluate(() => {
    return document.querySelector("#case-audit-modal")?.innerText || "";
  });
  console.log("Modal 2 Content:\n" + modal2Text.split("\n").slice(0, 15).join("\n") + "\n...");

  const modal2Path = path.join(ARTIFACTS_DIR, "case_modal_2.png");
  await page.screenshot({ path: modal2Path });
  console.log(`Saved screenshot: ${modal2Path}`);

  await page.click("#close-modal-btn");
  await page.waitForFunction(() => !document.querySelector("#case-audit-modal"));

  // 4. Test "Run Agent Batch" button
  console.log("\n=== 4. Testing 'Run Agent Batch' Button ===");
  await page.click("#run-batch-btn");
  console.log("Clicked 'Run Agent Batch', waiting for batch to complete (calling Groq/FastAPI backend)...");
  
  await page.waitForFunction(
    () => {
      const btn = document.querySelector("#run-batch-btn");
      return btn && !btn.disabled && document.body.innerText.includes("Batch complete");
    },
    { timeout: 120000 }
  );

  const postBatchKPIs = await page.evaluate(() => {
    const atRisk = document.querySelector("#metric-at-risk")?.innerText || "";
    const recovered = document.querySelector("#metric-recovered")?.innerText || "";
    const rate = document.querySelector("#metric-rate")?.innerText || "";
    const stopped = document.querySelector("#metric-stopped")?.innerText || "";
    const feedback = document.querySelector("header")?.innerText || "";
    return { atRisk, recovered, rate, stopped, feedbackSnippet: feedback.split("\n").join(" | ") };
  });
  console.log("Post-batch KPI State:\n" + JSON.stringify(postBatchKPIs, null, 2));

  // 5. Test "Refresh" button
  console.log("\n=== 5. Testing 'Refresh' Button ===");
  await page.click("#refresh-btn");
  await page.waitForTimeout ? page.waitForTimeout(1000) : new Promise((r) => setTimeout(r, 1000));
  console.log("Refresh button clicked successfully.");

  const postBatchPath = path.join(ARTIFACTS_DIR, "dashboard_post_batch.png");
  await page.screenshot({ path: postBatchPath });
  console.log(`Saved screenshot: ${postBatchPath}`);

  console.log("\n=== Console Errors ===");
  console.log(consoleErrors.length === 0 ? "Zero console errors detected!" : consoleErrors);

  await browser.close();
  console.log("\nVerification complete!");
}

run().catch((err) => {
  console.error("Verification failed with error:", err);
  process.exit(1);
});
