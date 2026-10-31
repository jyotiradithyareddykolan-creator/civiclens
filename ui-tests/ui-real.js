// UI check for the REAL dataset. Start the server with the default data, then: CIVICLENS_URL=http://localhost:8000 node ui-real.js
const { JSDOM } = require('jsdom');
const BASE = process.env.CIVICLENS_URL || 'http://localhost:8000';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failures = 0;
const check = (name, cond, extra) => { console.log((cond ? 'PASS ' : 'FAIL ') + name + (cond ? '' : '  -> ' + (extra || ''))); if (!cond) failures++; };

(async () => {
  const profile = { age: 19, annual_income: 200000, category: 'sc', gender: 'female', education_level: 'undergraduate', existing_benefits: [] };
  const dom = await JSDOM.fromURL(BASE + '/', { runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true, beforeParse(w) {
    w.fetch = (u, o) => fetch(new URL(u, BASE).href, o);
    w.scrollTo = () => {}; w.confirm = () => true;
    w.localStorage.setItem('civiclens.profile.v1', JSON.stringify(profile));
    w.__errs = []; w.addEventListener('error', (e) => w.__errs.push(e.message));
  } });
  const w = dom.window, d = w.document;
  const text = () => d.getElementById('main').textContent;
  const wf = async (fn, ms = 5000) => { const t = Date.now(); while (Date.now() - t < ms) { if (fn()) return true; await sleep(50); } return false; };
  const go = async (hash, cond, name) => { w.location.hash = hash; check(name, await wf(cond), text().slice(0, 200)); };

  check('home renders', await wf(() => d.getElementById('q')));
  const banner = d.getElementById('demo-banner');
  check('data banner says real-data preview, not demo', !banner.hidden && banner.textContent.includes('REAL-DATA PREVIEW') && !banner.textContent.includes('synthetic'));
  d.getElementById('q').value = 'scholarship for SC students';
  d.querySelector('form.searchbox').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  check('SC scholarship found', await wf(() => text().includes('Post-Matric Scholarship for Scheduled Caste students')), text().slice(0, 200));
  check('no demo tag on real schemes', !text().includes('Demo (synthetic)'));
  await go('#/scheme/PMS-SC/eligibility', () => d.querySelector('table.grid') && text().includes('2,50,000'), 'eligibility shows ₹2,50,000');
  check('never says likely eligible', !text().includes('Likely eligible'));
  check('manual-check note shown', text().includes('cannot be checked by this tool'));
  check('manual verification warning shown', text().includes('not been compared word for word'));
  await go('#/scheme/PMS-SC/evidence', () => text().includes('How this source was read') && text().includes('Excerpt as returned'), 'evidence tab: reading note + excerpt label');
  check('official PIB link shown', [...d.querySelectorAll('a')].some((a) => a.href.startsWith('https://www.pib.gov.in/')));
  await go('#/scheme/CSSS-PMUSP/checklist', () => text().includes('not verified'), 'CSSS checklist marks summary-only items unverified');
  await go('#/scheme/CSSS-PMUSP/changes', () => text().includes('nothing to compare') || text().includes('Only one version'), 'no comparison without two versions');
  await go('#/scheme/PM-YASASVI-PMS/eligibility', () => text().includes('unclear'), 'YASASVI validity flagged unclear');
  // Ask tab: output must never contain stray "null" or "[object ...]" text, with an answer, citations, or neither.
  await go('#/scheme/CSSS-PMUSP/ask', () => d.querySelector('section form.searchbox input'), 'ask tab renders');
  for (const q of ['What is the income limit and what all documents are needed?', 'qqqq zzzz unrelated words']) {
    const inp = d.querySelector('section form.searchbox input'); inp.value = q;
    inp.form.dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
    await wf(() => d.querySelector('[aria-live="polite"]') && d.querySelector('[aria-live="polite"]').children.length > 1, 5000);
    const outEl = d.querySelector('[aria-live="polite"]');
    const stray = [...outEl.childNodes].filter((n) => n.nodeType !== 1);   // bare text nodes = "null" / "[object ...]" leaks
    check('ask output has no stray text nodes (null/[object]): ' + q.slice(0, 18), outEl.textContent.length > 0 && stray.length === 0, stray.map((n) => n.textContent).join('|'));
  }
  const sel = d.getElementById('lang-select'); sel.value = 'hi'; sel.dispatchEvent(new w.Event('change'));
  await go('#/scheme/CSSS-PMUSP/eligibility', () => text().includes('4,50,000') && text().includes('फ़ेच'), 'Hindi keeps numbers and shows verification warning');
  check('no uncaught JS errors', w.__errs.length === 0, w.__errs.join('; '));
  console.log(failures ? `\n${failures} CHECK(S) FAILED` : '\nALL REAL-DATA UI CHECKS PASSED');
  w.close(); process.exit(failures ? 1 : 0);
})();
