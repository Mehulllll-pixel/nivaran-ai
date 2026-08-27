const http = require("http");

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
  const events = await fetchJson("http://127.0.0.1:8000/events/");

  const ANCHOR_IDS = ["cust_hero_demo", "cust_demo_wrongnum", "cust_demo_dispute", "cust_demo_nocontact"];
  const CHECK_IDS = ["cust_738813", ...ANCHOR_IDS, "cust_104590", "cust_519856"];

  for (const id of CHECK_IDS) {
    const e = events.find(ev => ev.customer_id === id);
    if (!e) { console.log(`${id}: NOT FOUND`); continue; }
    const isAnchor = ANCHOR_IDS.includes(id);
    const label = isAnchor ? "[ANCHOR]" : id === "cust_738813" ? "[NO-VOICE]" : "[VOICE]";
    console.log(`${label} ${id}`);
    console.log(`  demo_transcript  : ${JSON.stringify(e.demo_transcript)}`);
    console.log(`  voice_transcript : ${JSON.stringify(e.voice_transcript)}`);
    console.log();
  }
}

run().catch(err => { console.error(err); process.exit(1); });
