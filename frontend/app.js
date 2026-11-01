'use strict';
/* CivicLens frontend. No build step. All dynamic text is inserted with textContent (never innerHTML),
   so text from retrieved documents cannot inject markup. */

// ------------------------------------------------------------------ strings
const S = {
  en: {
    tagline: 'Find government schemes you may qualify for, with the official evidence to check.',
    navFind: 'Find schemes', navDetails: 'My details', navPrivacy: 'Privacy',
    searchPlaceholder: 'Describe what you need, e.g. “scholarship for a student in Delhi”',
    searchLabel: 'What are you looking for?', searchBtn: 'Search', searching: 'Searching official sources…',
    examples: ['Scholarship for a student', 'Support for small farmers', 'Pension for senior citizens', 'Skill training for job seekers', 'Business support for women in Maharashtra'],
    filters: 'Filters', fState: 'State', fCategory: 'Category', fGroup: 'Who it is for', fType: 'Type of scheme', all: 'All',
    useDetails: 'Use my details in this search', noDetailsYet: 'You have not entered any details yet.', addDetails: 'Add my details',
    resultsFor: 'Results', backHome: 'New search', viewScheme: 'View details and evidence',
    noProfileBadge: 'Add your details to check eligibility', prelimStatus: 'Preliminary status',
    followupTitle: 'A few answers would help', followupSub: 'Only questions needed for these schemes are asked. Leave blank anything you prefer not to share.',
    update: 'Update results', demoDoc: 'Demo (synthetic)', officialPortal: 'Official portal', portalNote: 'About this link',
    tabs: { eligibility: 'Eligibility', evidence: 'Evidence', checklist: 'Checklist', apply: 'How to apply', changes: 'Policy changes', ask: 'Ask a question' },
    whyMatched: 'Why this matched your search', matchNote: 'Matching shows the scheme text is related to your words. It does not mean you qualify.', eligAssessment: 'Eligibility assessment (preliminary)', notBecause: 'Why this is not “likely eligible”', unmetTitle: 'Requirement not met', yourAnswer: 'Your answer', noMatchWords: 'Matched on the overall topic of your search.', colEvidence: 'Evidence and verification', colNext: 'Next step', evType_verbatim: 'Exact quote (stored)', evType_summary: 'Summary only', evType_none: 'No source text', coverageLabel: 'Source coverage', validityLabel: 'Current validity', cov_partial: 'Partial', cov_complete: 'Complete', cov_unknown: 'Unknown', cov_not_declared: 'Not declared', val_confirmed: 'Confirmed', val_unclear: 'Unclear', val_expired: 'Expired', val_unknown: 'Not established', unresolvedTitle: 'Open questions about this scheme', whyNeeded: 'Why we ask', seeEvidenceLink: 'See the source passage',
    criterion: 'Criterion', required: 'Required', yours: 'Your answer', status: 'Status', mandatory: 'Mandatory', optional: 'Optional', notAnswered: 'Not answered',
    st_satisfied: 'Satisfied', st_not_satisfied: 'Not satisfied', st_unknown: 'Unknown', st_conflicting: 'Conflicting',
    seeEvidence: 'See evidence', satisfiedList: 'Satisfied', unmetList: 'Not satisfied', unknownList: 'Unknown or conflicting',
    sourcesTitle: 'Sources and freshness', published: 'Published', effective: 'Effective', lastChecked: 'Last checked', authority: 'Authority', version: 'Version',
    notStated: 'not stated', excerptNote: 'Excerpt as returned by an automated fetch tool; check exact wording at the official source.', summaryNote: 'Summary, not a quotation.', readingNote: 'How this source was read', demoDocFull: 'Demo document (synthetic text, not an official notification)', noUrl: 'No official URL configured for this demo document',
    checkSource: 'Check source now', checking: 'Checking…', allPassages: 'Show all passages of this document', withheld: 'Passage withheld: instruction-like text was detected and ignored',
    citationsTitle: 'Evidence for each criterion', officialText: 'Official text (original wording)', highlighted: 'The highlighted words are the evidence for the rule.',
    checklistTitle: 'Your document checklist', docName: 'Document', docType: 'Type', docStatus: 'Your status', nextAction: 'Next step', source: 'Source',
    print: 'Print', dlTxt: 'Download (.txt)', dlCsv: 'Download (.csv)', notApplicable: 'Not applicable to you', howObtain: 'Official instructions', generatedOn: 'Generated on',
    reqSummary: 'Required documents', haveIt: 'I have it', dontHave: 'I do not have it', notSure: 'Not sure yet',
    applyTitle: 'How to apply', deadline: 'Deadline', portal: 'Official portal', openPortal: 'Open the official portal', noSummary: 'No verified application guidance is available.',
    approvalNote: 'Eligibility is not approval. Appearing eligible here does not guarantee the benefit. The responsible authority makes the final decision.',
    changesTitle: 'Policy changes between versions', older: 'Older version', newer: 'Newer version', impact: 'What it means', verifiedChip: 'Verified', unverifiedChip: 'Unverified: needs human check',
    policyChange: 'Policy change', wordingOnly: 'Wording only', needsReview: 'Needs review', reeval: 'Effect on your eligibility', changeResult: 'Your result changes between versions', noChangeResult: 'Your result is the same in both versions',
    effectiveOn: 'Effective date', oldLabel: 'Old', newLabel: 'New',
    askTitle: 'Ask a question about these official documents', askPlaceholder: 'e.g. What is the income limit?', askBtn: 'Ask', answerTitle: 'Answer', fromAI: 'AI-written, based only on the cited passages',
    profileTitle: 'Your details', profileIntro: 'Share only what you are comfortable with. Every field is optional. Never enter Aadhaar, bank account numbers or passwords.',
    steps: ['About you', 'Work and income', 'Education', 'Land and benefits', 'Documents'], next: 'Next', back: 'Back', save: 'Save and find schemes', saved: 'Saved in this browser.',
    deleteData: 'Delete my details', deleted: 'Your details were removed from this browser.', confirmDelete: 'Delete all your saved details from this browser?',
    docsIntro: 'Tell us which documents you already have. This helps build your checklist.',
    yes: 'Yes', no: 'No', unanswered: '— not answered —', noneOfThese: 'None of these',
    privacyTitle: 'Privacy and limits', privacyPoints: [
      'Your details stay in this browser. The server computes results from them and does not store them.',
      'Do not enter Aadhaar numbers, bank account numbers, passwords or OTPs. The app rejects them.',
      'You can delete everything at any time using the button below.',
      'CivicLens is independent. It is not a government site and does not represent any authority.',
      'Results are preliminary. Final decisions rest with the responsible government authority.',
      '“Last checked” shows when a copy was retrieved. It does not prove that a policy is still current.',
      'AI is optional and never decides eligibility. Statuses come from deterministic rules checked against official text.'],
    coverage: 'Coverage', errGeneric: 'Something went wrong. Please try again.', retry: 'Try again', loading: 'Loading…',
    footer: 'CivicLens is an independent tool and is not affiliated with any government authority. It gives preliminary assessments only; the final decision rests with the responsible authority.',
    lowAnswer: 'No AI answer was generated. The relevant official passages are shown below.',
    ageUnit: 'years',
  },
  hi: {
    tagline: 'वे सरकारी योजनाएँ खोजें जिनके लिए आप पात्र हो सकते हैं, जाँचने के लिए आधिकारिक प्रमाण सहित।',
    navFind: 'योजनाएँ खोजें', navDetails: 'मेरी जानकारी', navPrivacy: 'गोपनीयता',
    searchPlaceholder: 'बताइए आपको क्या चाहिए, जैसे “दिल्ली के छात्र के लिए छात्रवृत्ति”',
    searchLabel: 'आप क्या खोज रहे हैं?', searchBtn: 'खोजें', searching: 'आधिकारिक स्रोतों में खोज रहे हैं…',
    examples: ['छात्र के लिए छात्रवृत्ति', 'छोटे किसानों के लिए सहायता', 'वरिष्ठ नागरिकों के लिए पेंशन', 'रोजगार-तलाशियों के लिए कौशल प्रशिक्षण', 'महाराष्ट्र में महिलाओं के लिए व्यवसाय सहायता'],
    filters: 'फ़िल्टर', fState: 'राज्य', fCategory: 'श्रेणी', fGroup: 'किनके लिए', fType: 'योजना का प्रकार', all: 'सभी',
    useDetails: 'इस खोज में मेरी जानकारी का उपयोग करें', noDetailsYet: 'आपने अभी कोई जानकारी नहीं भरी है।', addDetails: 'अपनी जानकारी भरें',
    resultsFor: 'परिणाम', backHome: 'नई खोज', viewScheme: 'विवरण और प्रमाण देखें',
    noProfileBadge: 'पात्रता जाँचने के लिए अपनी जानकारी भरें', prelimStatus: 'प्रारंभिक स्थिति',
    followupTitle: 'कुछ उत्तर और मदद करेंगे', followupSub: 'केवल वही प्रश्न पूछे जा रहे हैं जो इन योजनाओं के लिए ज़रूरी हैं। जो साझा नहीं करना चाहते उसे खाली छोड़ दें।',
    update: 'परिणाम अपडेट करें', demoDoc: 'डेमो (काल्पनिक)', officialPortal: 'आधिकारिक पोर्टल', portalNote: 'इस लिंक के बारे में',
    tabs: { eligibility: 'पात्रता', evidence: 'प्रमाण', checklist: 'चेकलिस्ट', apply: 'आवेदन कैसे करें', changes: 'नीति परिवर्तन', ask: 'प्रश्न पूछें' },
    whyMatched: 'यह आपकी खोज से क्यों मेल खाई', matchNote: 'मेल का अर्थ है कि योजना का पाठ आपके शब्दों से संबंधित है। इसका अर्थ यह नहीं कि आप पात्र हैं।', eligAssessment: 'पात्रता आकलन (प्रारंभिक)', notBecause: 'यह “संभावित रूप से पात्र” क्यों नहीं है', unmetTitle: 'पूरी न हुई शर्त', yourAnswer: 'आपका उत्तर', noMatchWords: 'आपकी खोज के सामान्य विषय से मेल।', colEvidence: 'प्रमाण और सत्यापन', colNext: 'अगला कदम', evType_verbatim: 'सटीक उद्धरण (संग्रहीत)', evType_summary: 'केवल सारांश', evType_none: 'कोई स्रोत पाठ नहीं', coverageLabel: 'स्रोत कवरेज', validityLabel: 'वर्तमान वैधता', cov_partial: 'आंशिक', cov_complete: 'पूर्ण', cov_unknown: 'अज्ञात', cov_not_declared: 'घोषित नहीं', val_confirmed: 'पुष्ट', val_unclear: 'अस्पष्ट', val_expired: 'समाप्त', val_unknown: 'स्थापित नहीं', unresolvedTitle: 'इस योजना के बारे में खुले प्रश्न', whyNeeded: 'हम यह क्यों पूछ रहे हैं', seeEvidenceLink: 'स्रोत अंश देखें',
    criterion: 'मानदंड', required: 'आवश्यकता', yours: 'आपका उत्तर', status: 'स्थिति', mandatory: 'अनिवार्य', optional: 'वैकल्पिक', notAnswered: 'उत्तर नहीं दिया',
    st_satisfied: 'पूरी हुई', st_not_satisfied: 'पूरी नहीं हुई', st_unknown: 'अज्ञात', st_conflicting: 'परस्पर विरोधी',
    seeEvidence: 'प्रमाण देखें', satisfiedList: 'पूरी हुई', unmetList: 'पूरी नहीं हुई', unknownList: 'अज्ञात या परस्पर विरोधी',
    sourcesTitle: 'स्रोत और ताज़गी', published: 'प्रकाशित', effective: 'प्रभावी', lastChecked: 'अंतिम जाँच', authority: 'प्राधिकरण', version: 'संस्करण',
    notStated: 'उल्लेख नहीं', excerptNote: 'स्वचालित फ़ेच टूल से प्राप्त अंश; सटीक शब्द आधिकारिक स्रोत पर जाँचें।', summaryNote: 'सारांश, उद्धरण नहीं।', readingNote: 'यह स्रोत कैसे पढ़ा गया', demoDocFull: 'डेमो दस्तावेज़ (काल्पनिक पाठ, आधिकारिक अधिसूचना नहीं)', noUrl: 'इस डेमो दस्तावेज़ के लिए कोई आधिकारिक URL निर्धारित नहीं',
    checkSource: 'स्रोत की जाँच करें', checking: 'जाँच हो रही है…', allPassages: 'इस दस्तावेज़ के सभी अनुच्छेद दिखाएँ', withheld: 'अनुच्छेद रोका गया: निर्देश जैसा पाठ मिला और उसे अनदेखा किया गया',
    citationsTitle: 'हर मानदंड के प्रमाण', officialText: 'आधिकारिक पाठ (मूल शब्दों में)', highlighted: 'रेखांकित शब्द नियम का प्रमाण हैं।',
    checklistTitle: 'आपकी दस्तावेज़ चेकलिस्ट', docName: 'दस्तावेज़', docType: 'प्रकार', docStatus: 'आपकी स्थिति', nextAction: 'अगला कदम', source: 'स्रोत',
    print: 'प्रिंट करें', dlTxt: 'डाउनलोड (.txt)', dlCsv: 'डाउनलोड (.csv)', notApplicable: 'आप पर लागू नहीं', howObtain: 'आधिकारिक निर्देश', generatedOn: 'तैयार की गई',
    reqSummary: 'आवश्यक दस्तावेज़', haveIt: 'मेरे पास है', dontHave: 'मेरे पास नहीं है', notSure: 'अभी पक्का नहीं',
    applyTitle: 'आवेदन कैसे करें', deadline: 'अंतिम तिथि', portal: 'आधिकारिक पोर्टल', openPortal: 'आधिकारिक पोर्टल खोलें', noSummary: 'सत्यापित आवेदन मार्गदर्शन उपलब्ध नहीं है।',
    approvalNote: 'पात्रता और स्वीकृति अलग हैं। यहाँ पात्र दिखना लाभ की गारंटी नहीं है। अंतिम निर्णय संबंधित प्राधिकरण का होता है।',
    changesTitle: 'संस्करणों के बीच नीति परिवर्तन', older: 'पुराना संस्करण', newer: 'नया संस्करण', impact: 'इसका अर्थ', verifiedChip: 'सत्यापित', unverifiedChip: 'असत्यापित: मानव जाँच आवश्यक',
    policyChange: 'नीति परिवर्तन', wordingOnly: 'केवल शब्दावली', needsReview: 'समीक्षा आवश्यक', reeval: 'आपकी पात्रता पर असर', changeResult: 'दोनों संस्करणों में आपका परिणाम बदलता है', noChangeResult: 'दोनों संस्करणों में आपका परिणाम समान है',
    effectiveOn: 'प्रभावी तिथि', oldLabel: 'पुराना', newLabel: 'नया',
    askTitle: 'इन आधिकारिक दस्तावेज़ों के बारे में प्रश्न पूछें', askPlaceholder: 'जैसे: आय सीमा क्या है?', askBtn: 'पूछें', answerTitle: 'उत्तर', fromAI: 'AI द्वारा लिखा गया, केवल उद्धृत अनुच्छेदों पर आधारित',
    profileTitle: 'आपकी जानकारी', profileIntro: 'केवल वही भरें जो आप साझा करना चाहते हैं। हर क्षेत्र वैकल्पिक है। आधार, बैंक खाता संख्या या पासवर्ड कभी न भरें।',
    steps: ['आपके बारे में', 'काम और आय', 'शिक्षा', 'भूमि और लाभ', 'दस्तावेज़'], next: 'आगे', back: 'पीछे', save: 'सहेजें और योजनाएँ खोजें', saved: 'इस ब्राउज़र में सहेजा गया।',
    deleteData: 'मेरी जानकारी हटाएँ', deleted: 'आपकी जानकारी इस ब्राउज़र से हटा दी गई।', confirmDelete: 'क्या इस ब्राउज़र से आपकी सारी सहेजी गई जानकारी हटा दें?',
    docsIntro: 'बताइए आपके पास कौन-से दस्तावेज़ पहले से हैं। इससे आपकी चेकलिस्ट बनाने में मदद मिलती है।',
    yes: 'हाँ', no: 'नहीं', unanswered: '— उत्तर नहीं दिया —', noneOfThese: 'इनमें से कोई नहीं',
    privacyTitle: 'गोपनीयता और सीमाएँ', privacyPoints: [
      'आपकी जानकारी इसी ब्राउज़र में रहती है। सर्वर उससे परिणाम निकालता है और उसे संग्रहीत नहीं करता।',
      'आधार संख्या, बैंक खाता संख्या, पासवर्ड या OTP न भरें। ऐप इन्हें अस्वीकार करता है।',
      'आप नीचे के बटन से कभी भी सब कुछ हटा सकते हैं।',
      'CivicLens स्वतंत्र है। यह सरकारी साइट नहीं है और किसी प्राधिकरण का प्रतिनिधित्व नहीं करता।',
      'परिणाम प्रारंभिक हैं। अंतिम निर्णय संबंधित सरकारी प्राधिकरण का है।',
      '“अंतिम जाँच” बताती है कि प्रति कब प्राप्त की गई। इससे यह सिद्ध नहीं होता कि नीति अब भी वर्तमान है।',
      'AI वैकल्पिक है और पात्रता तय नहीं करता। स्थितियाँ आधिकारिक पाठ से जाँचे गए निश्चित नियमों से आती हैं।'],
    coverage: 'कवरेज', errGeneric: 'कुछ गड़बड़ हुई। कृपया दोबारा प्रयास करें।', retry: 'दोबारा प्रयास करें', loading: 'लोड हो रहा है…',
    footer: 'CivicLens एक स्वतंत्र उपकरण है और किसी सरकारी प्राधिकरण से संबद्ध नहीं है। यह केवल प्रारंभिक आकलन देता है; अंतिम निर्णय संबंधित प्राधिकरण का है।',
    lowAnswer: 'कोई AI उत्तर नहीं बनाया गया। प्रासंगिक आधिकारिक अनुच्छेद नीचे दिखाए गए हैं।',
    ageUnit: 'वर्ष',
  },
};

const NAMES = {
  categories: { education: ['Education', 'शिक्षा'], agriculture: ['Agriculture', 'कृषि'], entrepreneurship: ['Entrepreneurship', 'उद्यमिता'],
    social_security: ['Social security', 'सामाजिक सुरक्षा'], employment: ['Employment and skills', 'रोजगार और कौशल'], housing: ['Housing', 'आवास'], health: ['Health', 'स्वास्थ्य'] },
  groups: { students: ['Students', 'छात्र'], farmers: ['Farmers', 'किसान'], women: ['Women', 'महिलाएँ'], job_seekers: ['Job seekers', 'रोजगार-तलाशी'],
    entrepreneurs: ['Entrepreneurs', 'उद्यमी'], senior_citizens: ['Senior citizens', 'वरिष्ठ नागरिक'], citizens: ['Citizens', 'नागरिक'] },
  types: { scholarship: ['Scholarship', 'छात्रवृत्ति'], grant: ['Grant', 'अनुदान'], pension: ['Pension', 'पेंशन'], training: ['Training', 'प्रशिक्षण'],
    stipend: ['Stipend', 'वजीफ़ा'], subsidy: ['Subsidy', 'सब्सिडी'] },
};

const ICON = { satisfied: '✓', likely_eligible: '✓', available: '✓', verified: '✓', not_satisfied: '✕', likely_ineligible: '✕', missing: '✕',
  unknown: '?', undetermined: '?', not_confirmed: '?', unverified: '!', conflicting: '⚠', source_unavailable: '!' };

// ------------------------------------------------------------------ state
const state = { lang: 'en', meta: null, profile: {}, results: null, lastRequest: null, useProfile: true, filters: {}, query: '', step: 0 };
const LS_PROFILE = 'civiclens.profile.v1', LS_LANG = 'civiclens.lang';

function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* storage may be blocked */ } }
function lsDel(k) { try { localStorage.removeItem(k); } catch (e) { /* ignore */ } }

function loadState() {
  const l = lsGet(LS_LANG); if (l === 'en' || l === 'hi') state.lang = l;
  try { const p = JSON.parse(lsGet(LS_PROFILE) || '{}'); if (p && typeof p === 'object') state.profile = p; } catch (e) { state.profile = {}; }
}
function saveProfile() { lsSet(LS_PROFILE, JSON.stringify(state.profile)); }
const tr = (k) => (S[state.lang][k] !== undefined ? S[state.lang][k] : S.en[k]);
const L = (pair) => pair[state.lang === 'hi' ? 1 : 0];
const hasProfile = () => Object.keys(cleanProfile()).filter((k) => k !== 'language').length > 0;

function cleanProfile() {
  const out = {};
  for (const [k, v] of Object.entries(state.profile)) {
    if (v === undefined || v === null || v === '') continue;
    if (k === 'documents') { if (Object.keys(v).length) out.documents = v; continue; }
    out[k] = v;
  }
  out.language = state.lang;
  return out;
}

// ------------------------------------------------------------------ dom helpers
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? '' : String(v));
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid === null || kid === undefined || kid === false) continue;
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return el;
}
const main = () => document.getElementById('main');
function mount(...nodes) { const m = main(); m.replaceChildren(...nodes.flat(Infinity).filter(Boolean)); window.scrollTo({ top: 0 }); m.focus({ preventScroll: true }); }
function loading(text) { return h('p', { class: 'muted', role: 'status' }, h('span', { class: 'spinner', 'aria-hidden': 'true' }), text || tr('loading')); }
function badge(kind, text) { return h('span', { class: 'badge ' + kind }, h('span', { 'aria-hidden': 'true' }, ICON[kind] || '•'), text); }
function tag(text, cls) { return h('span', { class: 'tag' + (cls ? ' ' + cls : '') }, text); }
function notice(text, kind) { return h('div', { class: 'notice ' + (kind || ''), role: kind === 'error' ? 'alert' : 'note' }, text); }
function sevClass(s) { return s === 'error' ? 'error' : s === 'info' ? 'info' : ''; }
function warnings(list) { return (list || []).map((w) => notice(w.message, sevClass(w.severity))); }
function ext(href, text) { return h('a', { href, target: '_blank', rel: 'noopener noreferrer' }, text); }
function highlight(text, evidence) {
  if (!text) return '';
  const i = evidence ? text.toLowerCase().indexOf(evidence.toLowerCase()) : -1;
  if (i < 0) return text;
  return [text.slice(0, i), h('mark', {}, text.slice(i, i + evidence.length)), text.slice(i + evidence.length)];
}
function download(name, text, mime) {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = h('a', { href: url, download: name }); document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ------------------------------------------------------------------ api
async function api(path, opts = {}) {
  const res = await fetch('/api' + path, {
    method: opts.method || 'GET',
    headers: opts.body ? { 'Content-Type': 'application/json' } : {},
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch (e) { /* non-JSON error */ }
  if (!res.ok) {
    const err = new Error((data && data.message) || tr('errGeneric'));
    err.status = res.status; err.details = data && data.details; throw err;
  }
  return data;
}
function errorBox(err, retry) {
  const detail = err.details && err.details.length ? ' (' + err.details.map((d) => d.field + ': ' + d.message).join('; ') + ')' : '';
  return h('div', {}, notice(err.message + detail, 'error'), retry ? h('button', { class: 'btn secondary small', type: 'button', onclick: retry }, tr('retry')) : null);
}

// ------------------------------------------------------------------ field controls (questionnaire + follow-ups)
function fieldControl(attr, current) {
  const spec = state.meta.fields[attr];
  const label = spec.label[state.lang];
  const id = 'f-' + attr + '-' + Math.random().toString(36).slice(2, 7);
  const optLabel = (o) => o[state.lang] || o.en;

  if (spec.type === 'multi') {
    const set = new Set(Array.isArray(current) ? current : []);
    const answeredNone = Array.isArray(current) && current.length === 0;
    const boxes = spec.options.map((o) => ({ o, input: h('input', { type: 'checkbox', value: o.value, checked: set.has(o.value) }) }));
    const none = h('input', { type: 'checkbox', checked: answeredNone });
    const node = h('fieldset', { class: 'field' }, h('legend', { class: 'label' }, label),
      boxes.map((b) => h('label', { class: 'check' }, b.input, optLabel(b.o))),
      spec.allow_none ? h('label', { class: 'check' }, none, tr('noneOfThese')) : null);
    return { node, read: () => { const picked = boxes.filter((b) => b.input.checked).map((b) => b.o.value); if (picked.length) return picked; return none.checked ? [] : undefined; } };
  }

  let input;
  if (spec.type === 'number') {
    input = h('input', { type: 'number', id, min: spec.min, max: spec.max, step: spec.step || 1, inputmode: 'decimal', value: current ?? '' });
  } else if (spec.type === 'state') {
    input = h('select', { id }, h('option', { value: '' }, tr('unanswered')), state.meta.states.map((s) => h('option', { value: s, selected: current === s }, s)));
  } else if (spec.type === 'boolean') {
    input = h('select', { id }, h('option', { value: '' }, tr('unanswered')), h('option', { value: 'true', selected: current === true }, tr('yes')), h('option', { value: 'false', selected: current === false }, tr('no')));
  } else {
    input = h('select', { id }, h('option', { value: '' }, tr('unanswered')), spec.options.map((o) => h('option', { value: o.value, selected: current === o.value }, optLabel(o))));
  }
  const node = h('div', { class: 'field' }, h('label', { class: 'label', for: id }, label), input);
  const read = () => {
    const v = input.value;
    if (v === '') return undefined;
    if (spec.type === 'number') return spec.step ? parseFloat(v) : parseInt(v, 10);
    if (spec.type === 'boolean') return v === 'true';
    return v;
  };
  return { node, read };
}

function followupForm(questions, onSubmit) {
  if (!questions || !questions.length) return null;
  const controls = questions.map((q) => ({ q, c: fieldControl(q.attribute, state.profile[q.attribute]) }));
  const form = h('form', { class: 'followup', onsubmit: (e) => {
    e.preventDefault();
    for (const { q, c } of controls) { const v = c.read(); if (v !== undefined) state.profile[q.attribute] = v; }
    saveProfile(); onSubmit();
  } }, h('h3', {}, tr('followupTitle')), h('p', { class: 'small' }, tr('followupSub')),
  h('div', { class: 'form-grid' }, controls.map(({ q, c }) => h('div', {}, h('p', { class: 'small muted' }, q.question), q.why ? h('p', { class: 'small muted' }, tr('whyNeeded') + ': ' + q.why) : null, c.node))),
  h('div', { class: 'btn-row' }, h('button', { class: 'btn small', type: 'submit' }, tr('update'))));
  return form;
}

// ------------------------------------------------------------------ chrome (header, footer, nav)
function renderChrome(route) {
  document.documentElement.lang = state.lang;
  document.getElementById('lang-select').value = state.lang;
  document.getElementById('lang-label').textContent = state.lang === 'hi' ? 'भाषा' : 'Language';
  const nav = document.getElementById('nav');
  const items = [['#/', tr('navFind'), route.name === 'home' || route.name === 'results' || route.name === 'scheme'], ['#/profile', tr('navDetails'), route.name === 'profile'], ['#/privacy', tr('navPrivacy'), route.name === 'privacy']];
  nav.replaceChildren(...items.map(([href, text, cur]) => h('a', { href, 'aria-current': cur ? 'page' : null }, text)));
  const banner = document.getElementById('demo-banner');
  if (state.meta && state.meta.data_notice) { banner.textContent = state.meta.data_notice; banner.hidden = false; }
  document.getElementById('footer').replaceChildren(h('p', {}, tr('footer')));
}

// ------------------------------------------------------------------ views
function filterSelect(key, labelText, options) {
  const id = 'flt-' + key;
  return h('div', { class: 'field' }, h('label', { class: 'label', for: id }, labelText),
    h('select', { id, onchange: (e) => { state.filters[key] = e.target.value || undefined; } },
      h('option', { value: '' }, tr('all')), options.map(([v, t]) => h('option', { value: v, selected: state.filters[key] === v }, t))));
}

function viewHome() {
  const input = h('input', { type: 'search', id: 'q', name: 'q', value: state.query, placeholder: tr('searchPlaceholder'), maxlength: 500, autocomplete: 'off', 'aria-label': tr('searchLabel') });
  const submit = (e) => { if (e) e.preventDefault(); state.query = input.value.trim(); runSearch(); };
  const useBox = h('input', { type: 'checkbox', id: 'use-profile', checked: state.useProfile, onchange: (e) => { state.useProfile = e.target.checked; } });
  const onlineBox = h('input', { type: 'checkbox', id: 'use-online', checked: true });
  mount(
    h('section', { class: 'hero' }, h('h1', {}, 'CivicLens'), h('p', { class: 'lead' }, tr('tagline')),
      h('form', { class: 'searchbox', onsubmit: submit, role: 'search' }, input, h('button', { class: 'btn', type: 'submit' }, tr('searchBtn'))),
      h('div', { class: 'chips', 'aria-label': 'Examples' }, tr('examples').map((ex) => h('button', { class: 'chip', type: 'button', onclick: () => { input.value = ex; submit(); } }, ex)))),
    h('details', { open: Object.values(state.filters).some(Boolean) }, h('summary', {}, tr('filters')),
      h('div', { class: 'filters' },
        filterSelect('state', tr('fState'), state.meta.states.map((s) => [s, s])),
        filterSelect('category', tr('fCategory'), state.meta.categories.map((c) => [c, L(NAMES.categories[c] || [c, c])])),
        filterSelect('target_group', tr('fGroup'), state.meta.target_groups.map((c) => [c, L(NAMES.groups[c] || [c, c])])),
        filterSelect('scheme_type', tr('fType'), state.meta.scheme_types.map((c) => [c, L(NAMES.types[c] || [c, c])])))),
    h('div', { class: 'card' }, hasProfile()
      ? h('label', { class: 'check' }, useBox, tr('useDetails'))
      : h('p', { class: 'small' }, tr('noDetailsYet') + ' ', h('a', { href: '#/profile' }, tr('addDetails')))),
    h('div', { class: 'card' }, h('label', { class: 'check' }, onlineBox, ' Search official government sources online (recommended)'),
      h('p', { class: 'small muted' }, 'Find schemes directly from approved official government portals. Profile details are used only after a scheme is selected and official content is retrieved.')),
    h('p', { class: 'small muted' }, state.meta.coverage_note ? tr('coverage') + ': ' + state.meta.coverage_note : ''));
  input.focus();
}

async function runSearch() {
  const req = { query: state.query, filters: Object.fromEntries(Object.entries(state.filters).filter(([, v]) => v)), language: state.lang, max_schemes: 5,
    online: !!document.getElementById('use-online')?.checked };
  if (state.useProfile && hasProfile()) req.profile = cleanProfile();
  state.lastRequest = req;
  mount(loading(tr('searching')));
  try {
    // Render the reviewed catalogue immediately. Online discovery is a separate
    // request so a slow or unavailable official portal cannot hide local results.
    const localReq = { ...req, online: false };
    state.results = await api('/agent/run', { method: 'POST', body: localReq });
    if (req.online) state.results.online_discovery = { results: [], online: true, state: 'searching', notice: 'Searching approved official government sources…' };
    location.hash = '#/results';
    if (currentRoute().name === 'results') render();
    if (req.online) {
      try {
        const online = await api('/discover', { method: 'POST', body: { query: state.query, limit: req.max_schemes } });
        if (state.results && state.query === req.query) { state.results.online_discovery = online; render(); }
      } catch (err) {
        if (state.results && state.query === req.query) {
          state.results.online_discovery = { results: [], online: true, state: 'source_failure', notice: 'Official-source search failed; no online result is being treated as evidence.' };
          render();
        }
      }
    }
  } catch (err) { mount(h('h2', {}, tr('resultsFor')), errorBox(err, runSearch), h('a', { class: 'btn secondary small', href: '#/' }, tr('backHome'))); }
}

function assessmentBlock(card, ev) {
  const a = card.eligibility_assessment;
  if (!a) return h('section', { class: 'subcard' }, h('h4', {}, tr('eligAssessment')), h('p', {}, badge('neutral', tr('noProfileBadge'))));
  return h('section', { class: 'subcard assess s-' + a.status, 'aria-label': tr('eligAssessment') },
    h('h4', {}, tr('eligAssessment')),
    h('p', {}, badge(a.status, a.status_label), ' ', h('span', { class: 'small muted' }, a.counts.mandatory_total ? a.counts.satisfied + '/' + a.counts.mandatory_total : '')),
    h('p', { class: 'small' }, a.reason),
    a.failed.length ? h('div', {}, h('p', { class: 'small' }, h('strong', {}, tr('unmetTitle') + ':')),
      h('ul', { class: 'plain small' }, a.failed.map((f) => h('li', {}, f.label + ' — ' + f.required + (f.yours ? ' (' + tr('yourAnswer') + ': ' + f.yours + ')' : ''))))) : null,
    a.status !== 'likely_eligible' && a.status !== 'likely_ineligible' && a.blockers.length ? h('div', {}, h('p', { class: 'small' }, h('strong', {}, tr('notBecause') + ':')),
      h('ul', { class: 'plain small' }, a.blockers.map((b) => h('li', {}, b.message)))) : null,
    h('p', { class: 'small muted' }, tr('coverageLabel') + ': ' + tr('cov_' + a.source_coverage) + ' · ' + tr('validityLabel') + ': ' + tr('val_' + a.validity)));
}

function schemeCard(r) {
  const card = r.card, ev = r.eligibility;
  const status = card.preliminary_status || null;
  const names = card.target_groups.map((g) => tag(L(NAMES.groups[g] || [g, g])));
  return h('article', { class: 'card' + (status ? ' s-' + status : '') },
    h('h3', {}, card.name),
    h('p', { class: 'small muted' }, card.authority + ' · ' + card.geography),
    h('div', { class: 'tags' }, names, tag(L(NAMES.types[card.scheme_type] || [card.scheme_type, card.scheme_type])), card.demo ? tag(tr('demoDoc'), 'demo') : null),
    h('p', {}, card.description),
    h('section', { class: 'subcard match', 'aria-label': tr('whyMatched') },
      h('h4', {}, tr('whyMatched')),
      h('ul', { class: 'plain small' }, (card.why && card.why.length ? card.why : [tr('noMatchWords')]).map((w) => h('li', {}, w))),
      h('p', { class: 'small muted' }, tr('matchNote'))),
    assessmentBlock(card, ev),
    card.eligibility_summary.length ? h('details', {}, h('summary', {}, tr('tabs').eligibility), h('ul', { class: 'plain small' }, card.eligibility_summary.map((c) => h('li', {}, c.label + ': ' + c.required)))) : null,
    warnings(card.flags.filter((f) => f.severity !== 'info').slice(0, 2)),
    h('dl', { class: 'kv' },
      h('dt', {}, tr('published')), h('dd', {}, card.publication_date || tr('notStated')),
      h('dt', {}, tr('effective')), h('dd', {}, card.effective_date || tr('notStated')),
      h('dt', {}, tr('lastChecked')), h('dd', {}, card.last_checked || tr('notStated'))),
    h('div', { class: 'btn-row' },
      h('a', { class: 'btn small', href: '#/scheme/' + encodeURIComponent(card.id) + '/eligibility' }, tr('viewScheme')),
      card.portal ? ext(card.portal.url, tr('officialPortal') + ': ' + card.portal.name) : null));
}

function onlineLeadCard(lead) {
  const out = h('div', { class: 'small' });
  return h('article', { class: 'card' }, h('h3', {}, lead.name),
    h('p', { class: 'small muted' }, lead.authority + ' · official discovery lead'),
    h('p', {}, lead.description),
    h('p', { class: 'small' }, 'State: Not retrieved. Search relevance is not eligibility evidence; the description above will not be used as eligibility evidence.'),
    h('div', { class: 'btn-row' }, ext(lead.source_url, 'Open official source'),
      h('button', { class: 'btn secondary small', type: 'button', onclick: async (e) => {
        e.currentTarget.disabled = true; out.replaceChildren(loading('Retrieving official content…'));
        try {
          const r = await api('/discover/retrieve', { method: 'POST', body: lead });
          const ev = await api('/drafts/' + encodeURIComponent(r.draft_id) + '/eligibility', { method: 'POST', body: { profile: cleanProfile(), language: state.lang } });
          const doc = r.scheme && r.scheme.documents && r.scheme.documents[0];
          const evidence = (doc?.passages || []).slice(0, 2).map((p) => p.text).join(' ');
          out.replaceChildren(notice(r.message, 'info'),
            h('p', { class: 'small' }, 'State: ' + (r.rules_extracted ? 'Retrieved with criteria' : 'Retrieved without extractable criteria')),
            h('p', {}, 'Eligibility criteria extracted: ' + r.rules_extracted + ' · Coverage: ' + r.source_coverage),
            h('p', {}, 'Preliminary assessment: ' + ev.status_label),
            doc ? h('dl', { class: 'kv' },
              h('dt', {}, 'Official source URL'), h('dd', {}, ext(doc.retrieval_source_url || doc.url, doc.retrieval_source_url || doc.url)),
              h('dt', {}, 'Retrieved'), h('dd', {}, doc.last_checked || 'Not recorded')) : null,
            evidence ? h('p', { class: 'small' }, h('strong', {}, 'Supporting evidence: '), evidence) :
              h('p', { class: 'small muted' }, 'No supporting source passage was extracted; eligibility is undetermined.'),
            h('p', { class: 'small muted' }, ev.disclaimer));
        } catch (err) { out.replaceChildren(notice('State: Retrieval failed. Discovery text was not used as eligibility evidence.', 'error'), errorBox(err)); }
        e.currentTarget.disabled = false;
      } }, 'Retrieve and assess'), out));
}

function viewResults() {
  const data = state.results;
  if (!data) { location.hash = '#/'; return; }
  const questions = data.follow_up_questions || [];
  mount(
    h('h2', {}, tr('resultsFor') + (state.query ? ': “' + state.query + '”' : '')),
    h('div', { class: 'btn-row no-print' }, h('a', { class: 'btn secondary small', href: '#/' }, tr('backHome'))),
    (data.notices || []).filter((n) => !(n.code === 'no_results' && !data.results.length)).map((n) => notice(n.message, '')),
    followupForm(questions, runSearch),
    data.results.length ? data.results.map(schemeCard) : h('div', { class: 'empty' }, h('p', {}, (data.notices[0] || {}).message || '')),
    data.online_discovery ?
      h('section', { class: 'online-results' },
        h('h2', {}, 'Official online discovery'),
        h('p', { class: 'small muted' }, data.online_discovery.notice),
        data.online_discovery.state === 'source_failure' ? notice('Official-source retrieval failed. Try again later or broaden the search.', 'warning') : null,
        data.online_discovery.state === 'no_official_results' ? h('div', { class: 'empty' }, h('p', {}, 'No official schemes matched this search. This does not mean no such scheme exists.')) : null,
        data.online_discovery.results && data.online_discovery.results.length ? data.online_discovery.results.map(onlineLeadCard) : null) : null,
    h('p', { class: 'small muted' }, state.meta.disclaimer));
}

// ---- scheme page
async function viewScheme(id, tab) {
  mount(loading());
  const tabs = ['eligibility', 'evidence', 'checklist', 'apply', 'changes', 'ask'];
  if (!tabs.includes(tab)) tab = 'eligibility';
  try {
    const body = { profile: cleanProfile(), language: state.lang };
    const [a, d] = await Promise.all([
      api('/schemes/' + encodeURIComponent(id) + '/assessment', { method: 'POST', body }),
      api('/schemes/' + encodeURIComponent(id) + '?language=' + state.lang),
    ]);
    const reload = () => viewScheme(id, tab);
    const panels = { eligibility: tabEligibility, evidence: tabEvidence, checklist: tabChecklist, apply: tabApply, changes: tabChanges, ask: tabAsk };
    mount(
      h('p', { class: 'no-print' }, h('a', { href: '#/results' }, '← ' + tr('resultsFor'))),
      h('h1', {}, a.scheme.name),
      h('p', { class: 'muted' }, a.scheme.authority + ' · ' + a.scheme.geography),
      h('div', { class: 'tags' }, a.scheme.target_groups.map((g) => tag(L(NAMES.groups[g] || [g, g]))), a.scheme.demo ? tag(tr('demoDocFull'), 'demo') : null),
      h('p', {}, a.scheme.description),
      h('nav', { class: 'tabs', 'aria-label': 'Scheme sections' }, tabs.map((t) => h('a', { href: '#/scheme/' + encodeURIComponent(id) + '/' + t, 'aria-current': t === tab ? 'page' : null }, tr('tabs')[t]))),
      panels[tab](a, d, id, reload));
  } catch (err) { mount(errorBox(err, () => viewScheme(id, tab)), h('a', { href: '#/' }, tr('backHome'))); }
}

function criteriaTable(criteria, id) {
  return h('table', { class: 'grid stack' },
    h('thead', {}, h('tr', {}, [tr('criterion'), tr('required'), tr('yours'), tr('status'), tr('colEvidence'), tr('colNext')].map((x) => h('th', { scope: 'col' }, x)))),
    h('tbody', {}, criteria.map((c) => h('tr', {},
      h('td', { 'data-label': tr('criterion') }, h('strong', {}, c.label), ' ', tag(c.mandatory ? tr('mandatory') : tr('optional')),
        c.explanation ? h('div', { class: 'small muted' }, c.explanation) : null,
        c.exception ? h('div', { class: 'small' }, 'ⓘ ' + c.exception) : null,
        c.variants ? h('ul', { class: 'plain small' }, c.variants.map((v) => h('li', {}, v.required_display + ' (' + v.authority + ', ' + (v.publication_date || tr('notStated')) + ')'))) : null),
      h('td', { 'data-label': tr('required') }, c.required_display),
      h('td', { 'data-label': tr('yours') }, c.user_value_display || h('span', { class: 'muted' }, tr('notAnswered'))),
      h('td', { 'data-label': tr('status') }, badge(c.status, tr('st_' + c.status))),
      h('td', { 'data-label': tr('colEvidence') }, tag(tr('evType_' + c.evidence_type)),
        c.citations && c.citations[0] && c.citations[0].evidence ? h('div', { class: 'small' }, '“' + c.citations[0].evidence + '”') : null,
        h('div', { class: 'small muted' }, c.verification_label),
        id ? h('div', { class: 'small' }, h('a', { href: '#/scheme/' + encodeURIComponent(id) + '/evidence' }, tr('seeEvidenceLink') + ' →')) : null),
      h('td', { 'data-label': tr('colNext') }, c.next_action)))));
}

function tabEligibility(a, d, id, reload) {
  const ev = a.eligibility;
  return h('section', {},
    h('div', { class: 'card s-' + ev.status }, h('p', {}, badge(ev.status, ev.status_label)), h('p', {}, ev.summary), h('p', { class: 'small' }, ev.status_reason),
      ev.status !== 'likely_eligible' && ev.status !== 'likely_ineligible' && ev.blockers.length ? h('div', {}, h('p', { class: 'small' }, h('strong', {}, tr('notBecause') + ':')),
        h('ul', { class: 'plain small' }, ev.blockers.map((b) => h('li', {}, b.message)))) : null,
      h('p', { class: 'small muted' }, tr('coverageLabel') + ': ' + tr('cov_' + ev.source_coverage) + ' · ' + tr('validityLabel') + ': ' + tr('val_' + ev.validity.status)),
      ev.validity.note ? h('p', { class: 'small muted' }, ev.validity.note) : null,
      h('p', { class: 'small muted' }, ev.disclaimer)),
    warnings(ev.warnings),
    followupForm(ev.follow_up_questions, reload),
    ev.criteria.length ? criteriaTable(ev.criteria, id) : h('div', { class: 'empty' }, ev.summary),
    ev.criteria.length ? h('p', { class: 'small' }, h('a', { href: '#/scheme/' + encodeURIComponent(id) + '/evidence' }, tr('seeEvidence') + ' →')) : null,
    ev.unresolved_questions && ev.unresolved_questions.length ? h('details', { open: true }, h('summary', {}, tr('unresolvedTitle')), h('ul', { class: 'plain small' }, ev.unresolved_questions.map((u) => h('li', {}, u)))) : null,
    h('details', {}, h('summary', {}, 'How this was determined'), h('ul', { class: 'plain small' }, Object.values(ev.provenance).map((p) => h('li', {}, p)))));
}

function citeCard(c, showEvidence) {
  if (c.flagged) return h('div', { class: 'cite withheld' }, h('strong', {}, c.section || c.passage_id), h('p', { class: 'small' }, tr('withheld')));
  return h('div', { class: 'cite' },
    h('div', { class: 'cite-head' }, c.doc_title + (c.section ? ' · ' + c.section : '')),
    h('blockquote', {}, showEvidence ? highlight(c.text, c.evidence) : c.text),
    h('div', { class: 'meta' }, [c.authority, tr('published') + ': ' + (c.publication_date || tr('notStated')), tr('lastChecked') + ': ' + (c.last_checked || tr('notStated'))].join(' · ')),
    c.demo ? h('div', { class: 'meta' }, tr('demoDocFull')) : null,
    c.excerpt ? h('div', { class: 'meta' }, c.verbatim === false ? tr('summaryNote') : tr('excerptNote')) : null,
    c.url ? h('div', { class: 'meta' }, ext(c.url, c.url)) : null);
}

function tabEvidence(a, d) {
  const ev = a.eligibility;
  const checkResults = h('div', { 'aria-live': 'polite' });
  const docs = d.documents.map((doc) => {
    const out = h('div', {});
    return h('div', { class: 'card' },
      h('h3', {}, doc.title),
      h('dl', { class: 'kv' },
        h('dt', {}, tr('authority')), h('dd', {}, doc.authority), h('dt', {}, tr('version')), h('dd', {}, doc.version),
        h('dt', {}, tr('published')), h('dd', {}, doc.publication_date || tr('notStated')),
        h('dt', {}, tr('effective')), h('dd', {}, doc.effective_date || tr('notStated')),
        h('dt', {}, tr('lastChecked')), h('dd', {}, doc.last_checked || tr('notStated'))),
      doc.demo ? h('p', { class: 'small' }, tag(tr('demoDoc'), 'demo'), ' ', doc.url ? ext(doc.url, doc.url) : tr('noUrl')) : (doc.url ? ext(doc.url, doc.url) : null),
      warnings(doc.flags),
      doc.reading_note ? h('details', {}, h('summary', {}, tr('readingNote')), h('p', { class: 'small' }, doc.reading_note)) : null,
      h('button', { class: 'btn secondary small', type: 'button', onclick: async (e) => {
        const btn = e.currentTarget; btn.disabled = true; btn.textContent = tr('checking'); out.replaceChildren();
        try {
          const r = await api('/sources/' + encodeURIComponent(doc.id) + '/check?language=' + state.lang, { method: 'POST' });
          out.replaceChildren(notice(r.message + ' (' + r.checked_on + ')', r.status === 'unavailable' ? 'error' : 'info'));
        } catch (err) { out.replaceChildren(errorBox(err)); }
        btn.disabled = false; btn.textContent = tr('checkSource');
      } }, tr('checkSource')), out,
      doc.withheld_passages.length ? doc.withheld_passages.map(() => notice(tr('withheld'), 'info')) : null,
      doc.passages.length ? h('details', {}, h('summary', {}, tr('allPassages')), doc.passages.map((p) => citeCard({ ...p, doc_title: doc.title, section: p.section, text: p.text, authority: doc.authority, publication_date: doc.publication_date, last_checked: doc.last_checked, demo: false, flagged: false, excerpt: p.excerpt, verbatim: p.verbatim }, false))) : null);
  });
  return h('section', {},
    notice(d.freshness_note, 'info'),
    h('h2', {}, tr('citationsTitle')), h('p', { class: 'small muted' }, tr('highlighted')),
    ev.criteria.length ? ev.criteria.map((c) => h('div', {}, h('h3', {}, c.label + ' '), badge(c.status, tr('st_' + c.status)), c.citations.map((x) => citeCard(x, true)))) : null,
    h('h2', {}, tr('sourcesTitle')), checkResults, docs);
}

function csvEscape(s) { s = String(s ?? ''); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }

function tabChecklist(a, d, id, reload) {
  const cl = a.checklist;
  const setStatus = (key, v) => {
    state.profile.documents = state.profile.documents || {};
    if (v) state.profile.documents[key] = v; else delete state.profile.documents[key];
    saveProfile(); reload();
  };
  const rows = cl.items.map((it) => h('tr', {},
    h('td', { 'data-label': tr('docName') }, h('strong', {}, it.name),
      it.condition_note ? h('div', { class: 'small muted' }, it.condition_note) : null,
      it.source_disagreement ? h('div', { class: 'small' }, '⚠ ' + it.source_disagreement) : null),
    h('td', { 'data-label': tr('docType') }, it.classification_label, it.applies === 'unknown' ? h('div', { class: 'small muted' }, it.applies_label) : null),
    h('td', { 'data-label': tr('docStatus') },
      h('span', { class: 'print-only' }, it.user_status_label),
      h('select', { class: 'no-print', 'aria-label': it.name, onchange: (e) => setStatus(it.key, e.target.value) },
        h('option', { value: '', selected: it.user_status === 'not_confirmed' }, tr('notSure')),
        h('option', { value: 'available', selected: it.user_status === 'available' }, tr('haveIt')),
        h('option', { value: 'missing', selected: it.user_status === 'missing' }, tr('dontHave'))),
      ' ', badge(it.user_status, it.user_status_label)),
    h('td', { 'data-label': tr('nextAction') }, it.next_action,
      it.instructions ? h('details', {}, h('summary', {}, tr('howObtain')), h('p', {}, it.instructions.text), citeCard(it.instructions.citation, false)) : null),
    h('td', { 'data-label': tr('source') }, it.citations.slice(0, 1).map((c) => h('span', { class: 'small' }, (c.section || '') + ' · ' + c.doc_title)))));

  const lines = () => {
    const out = [a.scheme.name, tr('checklistTitle') + ' · ' + tr('generatedOn') + ' ' + cl.generated_on, ''];
    cl.items.forEach((it) => out.push('[' + it.user_status_label + '] ' + it.name + ' (' + it.classification_label + ') - ' + it.next_action));
    if (cl.deadline) out.push('', tr('deadline') + ': ' + cl.deadline.text);
    if (cl.portal) out.push(tr('portal') + ': ' + cl.portal.name + ' ' + cl.portal.url);
    out.push('', cl.disclaimer);
    return out.join('\n');
  };
  const csv = () => ['Document,Type,Your status,Next step,Source'].concat(cl.items.map((it) => [it.name, it.classification_label, it.user_status_label, it.next_action, (it.citations[0] || {}).doc_title].map(csvEscape).join(','))).join('\n');

  return h('section', { class: 'print-area' },
    h('h2', {}, tr('checklistTitle')),
    h('p', { class: 'small muted' }, a.scheme.name + ' · ' + tr('generatedOn') + ' ' + cl.generated_on),
    h('p', {}, badge('neutral', tr('reqSummary') + ': ' + cl.counts.required), ' ', badge('available', cl.counts.available + ' ✓'), ' ', badge('missing', cl.counts.missing + ' ✕'), ' ', badge('not_confirmed', cl.counts.not_confirmed + ' ?')),
    warnings(cl.warnings.filter((w) => w.severity !== 'info')),
    followupForm(cl.follow_up_questions, reload),
    cl.items.length ? h('table', { class: 'grid stack' }, h('thead', {}, h('tr', {}, [tr('docName'), tr('docType'), tr('docStatus'), tr('nextAction'), tr('source')].map((x) => h('th', { scope: 'col' }, x)))), h('tbody', {}, rows)) : h('div', { class: 'empty' }, tr('noSummary')),
    cl.not_applicable.length ? h('details', {}, h('summary', {}, tr('notApplicable') + ' (' + cl.not_applicable.length + ')'), h('ul', { class: 'plain' }, cl.not_applicable.map((n) => h('li', {}, n.name)))) : null,
    cl.deadline ? h('p', {}, h('strong', {}, tr('deadline') + ': '), cl.deadline.text, cl.deadline.note ? ' · ' + cl.deadline.note : '') : null,
    cl.portal ? h('p', {}, h('strong', {}, tr('portal') + ': '), cl.portal.name + ' ', ext(cl.portal.url, cl.portal.url), h('br'), h('span', { class: 'small muted' }, cl.portal.note)) : null,
    h('p', { class: 'small muted' }, cl.disclaimer),
    h('div', { class: 'btn-row no-print' },
      h('button', { class: 'btn small', type: 'button', onclick: () => window.print() }, tr('print')),
      h('button', { class: 'btn secondary small', type: 'button', onclick: () => download('civiclens-checklist.txt', '﻿' + lines(), 'text/plain;charset=utf-8') }, tr('dlTxt')),
      h('button', { class: 'btn secondary small', type: 'button', onclick: () => download('civiclens-checklist.csv', '﻿' + csv(), 'text/csv;charset=utf-8') }, tr('dlCsv'))));
}

function tabApply(a) {
  const ap = a.application, cl = a.checklist;
  return h('section', {},
    h('h2', {}, tr('applyTitle')),
    ap.summary ? h('div', { class: 'card' }, h('p', {}, ap.summary), citeCard(ap.citation, false)) : notice(ap.summary_note || tr('noSummary'), 'info'),
    cl.deadline ? h('div', { class: 'card' }, h('h3', {}, tr('deadline')), h('p', {}, cl.deadline.text), cl.deadline.note ? notice(cl.deadline.note) : null) : h('p', { class: 'muted' }, cl.deadline_note),
    ap.portal ? h('div', { class: 'card' }, h('h3', {}, tr('portal') + ': ' + ap.portal.name), h('p', { class: 'small' }, ap.portal.note),
      h('div', { class: 'btn-row' }, ext(ap.portal.url, tr('openPortal'))), h('p', { class: 'small muted' }, ap.application_link_note)) : null,
    notice(tr('approvalNote'), 'info'));
}

function changeKindBadge(c) {
  if (c.policy_change === false) return badge('neutral', tr('wordingOnly'));
  if (c.policy_change === null) return badge('unverified', tr('needsReview'));
  return badge('conflicting', tr('policyChange'));
}

function tabChanges(a) {
  const ch = a.changes;
  if (!ch.comparisons.length) return h('section', {}, h('h2', {}, tr('changesTitle')), h('div', { class: 'empty' }, ch.note || ''));
  return h('section', {}, h('h2', {}, tr('changesTitle')), ch.comparisons.map((cmp) => h('div', {},
    h('div', { class: 'card' },
      h('h3', {}, 'v' + cmp.old_doc.version + ' → v' + cmp.new_doc.version),
      h('p', {}, cmp.verified ? badge('verified', tr('verifiedChip')) : badge('unverified', tr('unverifiedChip')), ' ',
        cmp.effective_date ? h('span', { class: 'small' }, tr('effectiveOn') + ': ' + cmp.effective_date) : null),
      cmp.verification_note ? notice(cmp.verification_note) : null,
      cmp.re_evaluation ? h('p', {}, h('strong', {}, tr('reeval') + ': '), badge(cmp.re_evaluation.old_status, cmp.re_evaluation.old_status_label), ' → ', badge(cmp.re_evaluation.new_status, cmp.re_evaluation.new_status_label), ' ',
        h('span', { class: 'small' }, cmp.re_evaluation.result_changed ? tr('changeResult') : tr('noChangeResult'))) : null),
    cmp.changes.map((c) => h('div', { class: 'card' },
      h('h3', {}, c.label + ' '), changeKindBadge(c),
      (c.old_value !== null || c.new_value !== null) ? h('div', { class: 'compare' },
        h('div', { class: 'side' }, h('h4', {}, tr('oldLabel') + ' · v' + cmp.old_doc.version), h('div', { class: 'value-big' }, c.old_value ?? '—')),
        h('div', { class: 'side new' }, h('h4', {}, tr('newLabel') + ' · v' + cmp.new_doc.version), h('div', { class: 'value-big' }, c.new_value ?? '—'))) : null,
      h('p', {}, h('strong', {}, tr('impact') + ': '), c.impact),
      c.requires_human_verification ? notice(tr('unverifiedChip'), '') : null,
      h('details', {}, h('summary', {}, tr('officialText')),
        h('div', { class: 'compare' },
          h('div', { class: 'side' }, h('h4', {}, tr('oldLabel')), c.old_source ? citeCard({ ...c.old_source, authority: cmp.old_doc.authority, last_checked: cmp.old_doc.last_checked, demo: cmp.old_doc.demo }, false) : '—'),
          h('div', { class: 'side new' }, h('h4', {}, tr('newLabel')), c.new_source ? citeCard({ ...c.new_source, authority: cmp.new_doc.authority, last_checked: cmp.new_doc.last_checked, demo: cmp.new_doc.demo }, false) : '—'))))))));
}

function tabAsk(a, d, id) {
  const out = h('div', { 'aria-live': 'polite' });
  const input = h('input', { type: 'text', maxlength: 500, placeholder: tr('askPlaceholder'), 'aria-label': tr('askTitle'), required: true });
  const form = h('form', { class: 'searchbox', onsubmit: async (e) => {
    e.preventDefault(); out.replaceChildren(loading());
    try {
      const r = await api('/ask', { method: 'POST', body: { question: input.value, scheme_id: id, language: state.lang } });
      // replaceChildren() turns null and arrays into text ("null", "[object ...]"), so flatten and drop empties first.
      out.replaceChildren(...[
        notice(r.message, r.abstained ? 'info' : 'ok'),
        r.answer ? h('div', { class: 'card' }, h('h3', {}, tr('answerTitle')), h('p', {}, r.answer), h('p', { class: 'small muted' }, tr('fromAI'))) : null,
        r.citations.map((c) => citeCard(c, false)), h('p', { class: 'small muted' }, r.disclaimer)].flat(Infinity).filter(Boolean));
    } catch (err) { out.replaceChildren(errorBox(err)); }
  } }, input, h('button', { class: 'btn', type: 'submit' }, tr('askBtn')));
  return h('section', {}, h('h2', {}, tr('askTitle')), form, out);
}

// ---- profile questionnaire
const STEP_FIELDS = [['age', 'gender', 'state'], ['occupation', 'employment_status', 'annual_income', 'business_status'], ['education_level', 'is_student'], ['landholding_hectares', 'land_tenure', 'existing_benefits', 'category'], []];

function viewProfile() {
  const step = Math.min(state.step, STEP_FIELDS.length - 1);
  const status = h('p', { role: 'status', class: 'small' });
  let reads = [];
  let docSelects = [];
  const body = h('div', {});
  if (step < 4) {
    const controls = STEP_FIELDS[step].map((attr) => ({ attr, c: fieldControl(attr, state.profile[attr]) }));
    reads = controls;
    body.append(h('div', { class: 'form-grid' }, controls.map((x) => x.c.node)));
  } else {
    body.append(h('p', {}, tr('docsIntro')));
    const cat = state.meta.document_catalog;
    const docs = state.profile.documents || {};
    docSelects = Object.keys(cat).map((key) => {
      const sel = h('select', { id: 'doc-' + key }, h('option', { value: '' }, tr('notSure')), h('option', { value: 'available', selected: docs[key] === 'available' }, tr('haveIt')), h('option', { value: 'missing', selected: docs[key] === 'missing' }, tr('dontHave')));
      return { key, sel, node: h('div', { class: 'field' }, h('label', { class: 'label', for: 'doc-' + key }, cat[key][state.lang]), sel) };
    });
    body.append(h('div', { class: 'form-grid' }, docSelects.map((x) => x.node)));
  }
  const commit = () => {
    for (const { attr, c } of reads) { const v = c.read(); if (v === undefined) delete state.profile[attr]; else state.profile[attr] = v; }
    if (step === 4) { state.profile.documents = {}; for (const { key, sel } of docSelects) if (sel.value) state.profile.documents[key] = sel.value; }
    saveProfile();
  };
  const go = (n) => { commit(); state.step = n; viewProfile(); };
  mount(
    h('h1', {}, tr('profileTitle')), h('p', { class: 'lead muted' }, tr('profileIntro')),
    h('div', { class: 'stepper', role: 'group', 'aria-label': tr('profileTitle') }, tr('steps').map((s, i) => h('button', { type: 'button', 'aria-current': i === step ? 'step' : null, onclick: () => go(i) }, (i + 1) + '. ' + s))),
    h('form', { class: 'card', onsubmit: (e) => { e.preventDefault(); } }, h('h2', {}, tr('steps')[step]), body,
      h('div', { class: 'btn-row' },
        step > 0 ? h('button', { class: 'btn secondary', type: 'button', onclick: () => go(step - 1) }, tr('back')) : null,
        step < 4 ? h('button', { class: 'btn', type: 'button', onclick: () => go(step + 1) }, tr('next')) : null,
        h('button', { class: step < 4 ? 'btn secondary' : 'btn', type: 'button', onclick: () => { commit(); status.textContent = tr('saved'); state.useProfile = true; location.hash = '#/'; } }, tr('save')))),
    status,
    h('div', { class: 'btn-row' }, h('button', { class: 'btn danger small', type: 'button', onclick: deleteData }, tr('deleteData'))));
}

function deleteData() {
  if (!window.confirm(tr('confirmDelete'))) return;
  state.profile = {}; state.results = null; state.step = 0; lsDel(LS_PROFILE);
  mount(notice(tr('deleted'), 'ok'), h('a', { class: 'btn secondary small', href: '#/' }, tr('backHome')));
}

function viewPrivacy() {
  mount(h('h1', {}, tr('privacyTitle')), h('div', { class: 'card' }, h('ul', { class: 'plain' }, tr('privacyPoints').map((p) => h('li', {}, p)))),
    h('p', {}, state.meta.privacy_notice),
    state.meta.coverage_note ? h('p', { class: 'small muted' }, tr('coverage') + ': ' + state.meta.coverage_note) : null,
    h('div', { class: 'btn-row' }, h('button', { class: 'btn danger', type: 'button', onclick: deleteData }, tr('deleteData'))));
}

// ------------------------------------------------------------------ router
function currentRoute() {
  const parts = (location.hash.replace(/^#\/?/, '') || '').split('/').filter(Boolean).map(decodeURIComponent);
  if (!parts.length) return { name: 'home' };
  if (parts[0] === 'results') return { name: 'results' };
  if (parts[0] === 'profile') return { name: 'profile' };
  if (parts[0] === 'privacy') return { name: 'privacy' };
  if (parts[0] === 'scheme' && parts[1]) return { name: 'scheme', id: parts[1], tab: parts[2] || 'eligibility' };
  return { name: 'home' };
}

function render() {
  const r = currentRoute();
  renderChrome(r);
  if (!state.meta) return;
  if (r.name === 'home') viewHome();
  else if (r.name === 'results') viewResults();
  else if (r.name === 'profile') viewProfile();
  else if (r.name === 'privacy') viewPrivacy();
  else if (r.name === 'scheme') viewScheme(r.id, r.tab);
}

async function loadMeta() {
  state.meta = await api('/meta?language=' + state.lang);
}

async function boot() {
  loadState();
  document.getElementById('lang-select').addEventListener('change', async (e) => {
    state.lang = e.target.value; lsSet(LS_LANG, state.lang);
    try { await loadMeta(); } catch (err) { /* keep old meta */ }
    if (currentRoute().name === 'results' && state.lastRequest) { state.lastRequest.language = state.lang; if (state.lastRequest.profile) state.lastRequest.profile.language = state.lang; try { state.results = await api('/agent/run', { method: 'POST', body: state.lastRequest }); } catch (err) { /* keep old */ } }
    render();
  });
  window.addEventListener('hashchange', render);
  mount(loading());
  try { await loadMeta(); render(); } catch (err) { mount(errorBox(err, boot)); }
}
boot();
