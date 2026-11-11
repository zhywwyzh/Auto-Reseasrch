// Rasterize the SVG with an exact viewport; no network or model calls.
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const {pathToFileURL} = require('url');

function loadPlaywright() {
  if (process.env.PLAYWRIGHT_MODULE) return require(process.env.PLAYWRIGHT_MODULE);
  try { return require('playwright'); } catch {}
  const cache = path.join(os.homedir(), '.npm', '_npx');
  if (fs.existsSync(cache)) {
    for (const name of fs.readdirSync(cache)) {
      const candidate = path.join(cache, name, 'node_modules', 'playwright');
      if (fs.existsSync(path.join(candidate, 'package.json'))) return require(candidate);
    }
  }
  throw new Error('PNG export needs Playwright. Install it locally or set PLAYWRIGHT_MODULE to an existing installation.');
}

(async () => {
  const {chromium} = loadPlaywright();
  const svg = path.join(__dirname, 'figures', 'system-overview.svg');
  const png = path.join(__dirname, 'figures', 'system-overview.png');
  const chrome = process.env.CHROME_PATH || '/usr/bin/google-chrome';
  const browser = await chromium.launch({headless:true, ...(fs.existsSync(chrome) ? {executablePath:chrome} : {}), args:['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport:{width:1920,height:1080}, deviceScaleFactor:2});
    await page.goto(pathToFileURL(svg).href);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({path:png});
  } finally {
    await browser.close();
  }
  const bytes = fs.readFileSync(png);
  const width = bytes.readUInt32BE(16), height = bytes.readUInt32BE(20);
  if (width !== 3840 || height !== 2160) throw new Error('Unexpected PNG dimensions');
  const hash = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
  const manifest = {source:'system-overview.svg', source_sha256:hash(svg), png:'system-overview.png', png_sha256:hash(png), width, height, renderer:'Chromium via Playwright; exact 1920x1080 viewport at device scale 2'};
  fs.writeFileSync(path.join(__dirname, 'figures', 'manifest.json'), JSON.stringify(manifest,null,2)+'\n');
  process.stdout.write(JSON.stringify({figure:'system-overview.png',width,height})+'\n');
})().catch(error => { process.stderr.write(error.message+'\n'); process.exit(1); });
