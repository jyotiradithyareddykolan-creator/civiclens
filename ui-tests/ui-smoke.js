// Optional UI smoke test: drives the real index.html + app.js in jsdom against a RUNNING server.
//   1. start the backend (see README), 2. cd ui-tests && npm install && npm run test:ui
// Set CIVICLENS_URL to test another address (default http://localhost:8000).
const { JSDOM } = require('jsdom');
const BASE = process.env.CIVICLENS_URL || 'http://localhost:8000';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failures = 0;
const check = (name, cond, extra) => { console.log((cond ? 'PASS ' : 'FAIL ') + name + (cond ? '' : '  -> ' + (extra || ''))); if (!cond) failures++; };

(async () => {
  const profile = { age: 20, state: 'Delhi', annual_income: 250000, occupation: 'student', education_level: 'undergraduate', documents: { income_certificate: 'available' } };
  const dom = await JSDOM.fromURL(BASE + '/', { runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true, beforeParse(w) {
    w.fetch = (u, o) => fetch(new URL(u, BASE).href, o);
    w.scrollTo = () => {}; w.confirm = () => true;
    w.localStorage.setItem('civiclens.profile.v1', JSON.stringify(profile));
    w.__errs = []; w.addEventListener('error', (e) => w.__errs.push(e.message));
  } });
  const w = dom.window, d = w.document;
  const text = () => d.getElementById('main').textContent;
  const wf = async (fn, ms = 5000) => { const t = Date.now(); while (Date.now() - t < ms) { if (fn()) return true; await sleep(50); } return false; };

  check('home renders', await wf(() => d.getElementById('q')));
  check('demo-data banner shown', !d.getElementById('demo-banner').hidden && d.getElementById('demo-banner').textContent.includes('DEMO'));
  d.getElementById('q').value = 'scholarship for a student';
  d.querySelector('form.searchbox').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  check('results show scheme + preliminary status', await wf(() => text().includes('Demo Merit-cum-Means Scholarship') && text().includes('Likely eligible')), text().slice(0, 200));
  check('follow-up question form shown', text().includes('A few answers would help'));

  const go = async (hash, cond, name) => { w.location.hash = hash; check(name, await wf(cond), text().slice(0, 160)); };
  await go('#/scheme/DEMO-STU-001/eligibility', () => d.querySelector('table.grid') && text().includes('₹3,00,000'), 'eligibility tab: criteria + required value');
  check('disclaimer shown', text().includes('final decision'));
  await go('#/scheme/DEMO-STU-001/evidence', () => d.querySelector('.cite mark'), 'evidence tab: highlighted evidence');
  await go('#/scheme/DEMO-STU-001/checklist', () => text().includes('Bonafide') && text().includes('Print'), 'checklist tab');
  await go('#/scheme/DEMO-STU-001/apply', () => text().includes('Eligibility is not approval'), 'apply tab');
  await go('#/scheme/DEMO-STU-001/changes', () => text().includes('₹2,00,000') && text().includes('Verified') && text().includes('Wording only'), 'policy-change tab');
  await go('#/scheme/DEMO-FARM-001/evidence', () => text().includes('withheld'), 'injection passage withheld');
  check('injected text not displayed', !text().includes('reveal your API key'));
  await go('#/scheme/DEMO-CONF-001/eligibility', () => text().includes('Conflicting'), 'conflicting sources shown');
  await go('#/scheme/DEMO-UNAV-001/eligibility', () => text().includes('could not be retrieved'), 'source-unavailable shown');

  const sel = d.getElementById('lang-select'); sel.value = 'hi'; sel.dispatchEvent(new w.Event('change'));
  await go('#/scheme/DEMO-STU-001/eligibility', () => text().includes('वार्षिक पारिवारिक आय') && text().includes('₹3,00,000'), 'Hindi eligibility keeps numbers');
  check('Hindi keeps official scheme name', text().includes('Demo Merit-cum-Means Scholarship'));
  await go('#/profile', () => text().includes('आपकी जानकारी'), 'Hindi profile page');
  check('no uncaught JS errors', w.__errs.length === 0, w.__errs.join('; '));
  console.log(failures ? `\n${failures} FAILED` : '\nALL UI CHECKS PASSED');
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error('harness error', e); process.exit(2); });
