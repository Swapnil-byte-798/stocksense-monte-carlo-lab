/* Optional: npm install && npx playwright install chromium && npm run test:ui */
const {
  chromium
} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');

(async () => {
  const base = process.env.STOCKSENSE_URL || 'http://127.0.0.1:8000';
  for (let i = 0; i < 50; i++) {
    try {
      if ((await fetch(base + '/api/health')).ok) break;
    } catch {}
    if (i === 49) throw new Error('Start python -m stocklab serve before browser checks');
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  const browser = await chromium.launch({
    headless: true
  });
  try {
    const page = await browser.newPage({
      reducedMotion: 'reduce',
      viewport: {
        width: 1512,
        height: 1100
      }
    });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base);
    await page.waitForFunction(() => document.querySelector('#status').textContent.includes('Simulation complete'));
    assert.equal(await page.locator('#order').innerText(), '975');
    assert.equal(await page.locator('#comparison tr').count(), 2);
    await fs.mkdir('output/browser', {
      recursive: true
    });
    await page.screenshot({
      path: 'output/browser/desktop.png',
      fullPage: true
    });
    await page.locator('#preset').selectOption('fragile');
    assert.match(await page.locator('#status').innerText(), /changed/);
    await page.locator('#run-button').click();
    await page.waitForFunction(() => document.querySelector('#status').textContent.includes('Simulation complete'));
    const download = page.waitForEvent('download');
    await page.locator('#export-json').click();
    const file = await download;
    await file.saveAs('output/browser/export.json');
    const exported = JSON.parse(await fs.readFile('output/browser/export.json', 'utf8'));
    assert.equal(exported.config.scenario.disruption_probability, .25);
    assert.equal(exported.evaluation_paths, 49152);
    const previous = await page.locator('#order').innerText();
    await page.locator('#cost').fill('100');
    await page.locator('#run-button').click();
    await page.waitForFunction(() => document.querySelector('#status').textContent.includes('Could not run'));
    assert.equal(await page.locator('#order').innerText(), previous);
    await page.locator('[data-view="history"]').click();
    await page.waitForFunction(() => document.querySelector('#history-rows').children.length > 0);
    await page.locator('[data-view="learn"]').click();
    assert.equal(await page.locator('#learn .lesson').count(), 7);
    await page.locator('[data-view="overview"]').click();
    await page.setViewportSize({
      width: 390,
      height: 844
    });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({
      path: 'output/browser/mobile.png',
      fullPage: true
    });
    // Verify the explicit read-only fallback by making only the health probe unavailable.
    await page.route('**/api/health', route => route.fulfill({
      status: 404,
      body: '{}'
    }));
    await page.reload();
    await page.waitForFunction(() => document.querySelector('#mode').textContent === 'Saved experiment preview');
    await page.waitForFunction(() => document.querySelector('#order').textContent === '975');
    assert.equal(await page.locator('#run-button').isDisabled(), true);
    assert.equal(await page.locator('#demand_mean').isDisabled(), true);
    assert.deepEqual(errors, []);
    console.log('Browser checks passed: render, scenario changes, export, errors, history, learning, mobile width, saved preview.');
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
