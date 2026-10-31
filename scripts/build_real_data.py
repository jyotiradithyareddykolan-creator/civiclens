#!/usr/bin/env python3
"""Generate backend/data/schemes.json from OFFICIAL Government of India sources.

How this data was gathered (read before trusting it):
  * Each source below was opened on READ_ON through an automated web-fetch tool. That tool returns text that has
    been processed by a language model, NOT a byte-exact copy of the document. A passage is therefore stored only
    when the tool returned it as a quoted string; those are marked verbatim=True, excerpt=True.
  * Anything the tool only summarised is stored with verbatim=False. Such a passage can never verify a rule or a
    document requirement (the engine treats the item as "unknown") and is never offered as a citable quote.
  * Every document carries manual_verification=True: exact wording must be checked against the official source.
  * Only parts of some documents were read. Schemes are marked coverage="partial", so the engine never reports
    "likely eligible" for them.
Nothing here was invented. If you cannot find a quote in the official document, delete the entry.
"""
import json
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "backend" / "data" / "schemes.json"
READ_ON = "2026-10-30"

CATALOG = {
    "income_certificate": ("Income certificate", "आय प्रमाण पत्र"),
    "bank_account": ("Bank account in applicant's own name", "आवेदक के नाम पर बैंक खाता"),
    "caste_certificate": ("Caste certificate", "जाति प्रमाण पत्र"),
    "category_certificate": ("Category certificate (SC/ST/OBC)", "श्रेणी प्रमाण पत्र (अ.जा./अ.ज.जा./अ.पि.व.)"),
    "marksheet": ("Marksheet of last qualifying examination", "अंतिम उत्तीर्ण परीक्षा की अंकतालिका"),
}

NSP_NOTE = ("General official portal (National Scholarship Portal). It is listed in CivicLens's approved source list. "
            "This does not mean the scheme can be applied for there for every State; no scheme-specific application "
            "page has been verified.")
NSP_NOTE_HI = ("सामान्य आधिकारिक पोर्टल (राष्ट्रीय छात्रवृत्ति पोर्टल), जो CivicLens की स्वीकृत स्रोत सूची में है। इसका अर्थ यह नहीं कि "
               "हर राज्य के लिए योजना यहीं से आवेदन होती है; योजना-विशेष आवेदन पृष्ठ सत्यापित नहीं किया गया है।")


def portal(via):
    return dict(name="National Scholarship Portal", url="https://scholarships.gov.in/", verified=True,
                verified_via=via, note=NSP_NOTE, note_hi=NSP_NOTE_HI)


def doc(id, title, authority, doc_type, pub, url, passages, reading_note, status="validity_not_established", facts=None):
    return dict(
        id=id, title=title, authority=authority, doc_type=doc_type, version=1, publication_date=pub,
        effective_date=None, status=status, last_checked=READ_ON, url=url, demo=False, fetch_mode="static",
        retrieval_status="ok", manual_verification=True, reading_note=reading_note, facts=facts or {},
        passages=[dict(id=p, section=s, text=t, verbatim=v, excerpt=True) for p, s, t, v in passages],
    )


def rule(rid, doc_id, pid, criterion, label, label_hi, attribute, op, value, evidence, mandatory=True,
         exception=None, exception_hi=None, ambiguous=False, manual_check=False):
    return dict(id=rid, doc_id=doc_id, passage_id=pid, criterion=criterion, label=label, label_hi=label_hi,
                attribute=attribute, op=op, value=value, evidence=evidence, mandatory=mandatory,
                exception=exception, exception_hi=exception_hi, ambiguous=ambiguous, manual_check=manual_check)


def req(rid, doc_id, pid, key, classification, evidence, condition_note=None, condition_note_hi=None):
    return dict(id=rid, doc_id=doc_id, passage_id=pid, key=key, classification=classification, evidence=evidence,
                condition=None, condition_note=condition_note, condition_note_hi=condition_note_hi, how_to_obtain=None)


INCOME_LABEL = ("Annual family income within limit", "वार्षिक पारिवारिक आय सीमा के भीतर")
INCOME_EXC = ("The scheme counts family/parental income from the sources stated in the guidelines. Use the income on your income certificate.",
              "योजना दिशानिर्देशों में बताए स्रोतों की पारिवारिक/अभिभावक आय गिनती है। अपने आय प्रमाण पत्र की आय का उपयोग करें।")

# ====================================================================== 1. PM-USP CSSS (Ministry of Education)
CSSS_URL = "https://scholarships.gov.in/public/schemeGuidelines/CSSS_GUIDLINES_06022024.pdf"
CSSS_DOC = doc(
    "d-csss-guidelines", "Central Sector Scheme of Scholarship for College and University Students (PM-USP CSSS)",
    "Ministry of Education, Government of India", "scheme guidelines", None, CSSS_URL,
    [
        ("p1", "Cover page (title)", "Central Sector Scheme of Scholarship for College and University Students (PM-USP CSSS)", True),
        ("p2", "Cover page (applicability)", "Applicable for academic year 2022-23 onwards.", True),
        ("p3", "4(i) Eligibility: Class XII result", "above 80th percentile of successful candidates in the relevant stream", True),
        ("p4", "4(iv) Eligibility: other scholarships", "Not availing benefit of any other scholarship schemes including State run scholarship schemes", True),
        ("p5", "4(v) Eligibility: family income", "Students with gross parental/family income upto Rs. 4.5 lakh per annum", True),
        ("p6", "7 Amount (graduation level, first three years)", "Rs.12,000/-per annum", True),
        ("p7", "4(ii)-(iii) Courses (summary, not verbatim)",
         "Regular degree courses at institutions recognized by AICTE and relevant regulatory bodies. Correspondence, distance mode and diploma courses are not eligible.", False),
        ("p8", "4(v) Income certificate (summary, not verbatim)", "An income certificate is required only for fresh applicants.", False),
        ("p9", "8 Payment (summary, not verbatim)", "A bank account in the student's own name is required for DBT payment.", False),
        ("p10", "4(ix) How to apply (summary, not verbatim)",
         "Applications must be submitted online through the National Scholarships Portal (www.scholarships.gov.in). Applications sent directly to the Ministry are not accepted.", False),
    ],
    reading_note=("Read on 2026-10-30 via a fetch tool. Only quoted fragments are stored as quotes; section 4(ii), 4(v) documents, "
                  "section 8 and 4(ix) were only summarised by the tool and are marked 'not verbatim'. No issue date is stated in the text read. "
                  "A second file named 'CSSS_GUIDLINES_07022024_updated.pdf' appears in search results on the same portal but its "
                  "page refused automated access, so it was NOT read; which file is the current guideline is NOT established."),
    facts=dict(benefit=dict(value="Rs.12,000/-per annum (graduation level, first three years; other levels differ)", passage_id="p6", date=None)),
)
CSSS = dict(
    id="CSSS-PMUSP", name="Central Sector Scheme of Scholarship for College and University Students (PM-USP CSSS)",
    authority="Ministry of Education, Government of India (Department of Higher Education)", category="education",
    target_groups=["students"], scheme_type="scholarship", states=["all"], geography="All India", coverage="partial",
    description="Central scholarship for students admitted to regular degree courses after Class XII who scored above the 80th percentile in their stream and whose family income is within the limit. Applications are made on the National Scholarship Portal.",
    description_hi="कक्षा 12 के बाद नियमित डिग्री पाठ्यक्रमों में प्रवेश लेने वाले, अपनी स्ट्रीम में 80वें पर्सेंटाइल से ऊपर अंक पाने वाले और सीमा के भीतर पारिवारिक आय वाले विद्यार्थियों के लिए केंद्रीय छात्रवृत्ति। आवेदन राष्ट्रीय छात्रवृत्ति पोर्टल पर होते हैं।",
    keywords=["scholarship", "student", "college", "university", "degree", "undergraduate", "postgraduate", "central sector", "merit", "education", "pm-usp", "csss"],
    aliases=["PM-USP", "PM-USP CSSS", "CSSS", "Central Sector Scholarship", "Pradhan Mantri Uchchatar Shiksha Protsahan"],
    portal=portal("Named in the CSSS guidelines (section 4(ix), summary) and in the approved source list"),
    application=dict(summary="Apply online on the National Scholarship Portal. The guidelines summary says applications sent directly to the Ministry are not accepted. Check the portal for the current window.",
                     summary_hi="राष्ट्रीय छात्रवृत्ति पोर्टल पर ऑनलाइन आवेदन करें। दिशानिर्देश-सारांश के अनुसार मंत्रालय को सीधे भेजे आवेदन स्वीकार नहीं होते। वर्तमान अवधि पोर्टल पर देखें।",
                     doc_id="d-csss-guidelines", passage_id="p10"),
    documents=[CSSS_DOC],
    rules=[
        rule("r-csss-income", "d-csss-guidelines", "p5", "income", INCOME_LABEL[0], INCOME_LABEL[1], "annual_income", "lte", 450000,
             "gross parental/family income upto Rs. 4.5 lakh per annum", exception=INCOME_EXC[0], exception_hi=INCOME_EXC[1]),
        rule("r-csss-other", "d-csss-guidelines", "p4", "no_other_scholarship", "Not receiving another scholarship (central or state)",
             "कोई अन्य छात्रवृत्ति (केंद्र या राज्य) नहीं ले रहे", "existing_benefits", "not_contains", "other_scholarship",
             "Not availing benefit of any other scholarship schemes"),
        rule("r-csss-pct", "d-csss-guidelines", "p3", "class12_percentile", "Class XII result above the 80th percentile (your stream)",
             "कक्षा 12 में अपनी स्ट्रीम के 80वें पर्सेंटाइल से ऊपर", "class12_percentile", "eq",
             "Above the 80th percentile of successful candidates in the relevant stream",
             "above 80th percentile of successful candidates in the relevant stream", manual_check=True),
        rule("r-csss-course", "d-csss-guidelines", "p7", "course", "Enrolled in a regular degree course",
             "नियमित डिग्री पाठ्यक्रम में नामांकित", "education_level", "in", ["class_12", "undergraduate", "postgraduate"],
             "Regular degree courses at institutions recognized by AICTE"),
    ],
    required_documents=[
        req("q-csss-income", "d-csss-guidelines", "p8", "income_certificate", "conditional", "An income certificate is required only for fresh applicants",
            "The summary says this applies to fresh applicants only.", "सारांश के अनुसार यह केवल नए आवेदकों पर लागू है।"),
        req("q-csss-bank", "d-csss-guidelines", "p9", "bank_account", "mandatory", "A bank account in the student's own name is required"),
    ],
)

# ====================================================================== 2. PMS-SC (Ministry of Social Justice & Empowerment)
PMSSC_2026 = doc(
    "d-pmssc-pib-2026", "Central Government Strengthens Access to Higher Education for SC Students through POST-MATRIC SCHOLARSHIP SCHEME",
    "Ministry of Social Justice & Empowerment (Press Information Bureau release)", "press release", "2026-08-12",
    "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2298357&reg=48&lang=1",
    [
        ("p1", "Press release: who is covered", "eligible SC students", True),
        ("p2", "Press release: income ceiling", "annual income from all sources not exceeding ₹2.5 lakh", True),
        ("p3", "Press release: nature of the scheme", "open-ended and demand-driven for eligible students studying in all recognized institutions across the country.", True),
        ("p4", "Press release: portal named", "National Scholarship Portal (NSP)", True),
    ],
    reading_note=("Read on 2026-10-30 via a fetch tool. This is a PIB press release (a government statement about the scheme), not the "
                  "scheme guidelines; it describes the scheme but does not list documents or application steps."),
)
PMSSC_2023 = doc(
    "d-pmssc-pib-2023", "Pre-Matric Scholarships Scheme for SCs & Others and Post-Matric Scholarships Scheme for SC students (PMS-SC)",
    "Ministry of Social Justice & Empowerment (Press Information Bureau release)", "press release", "2023-09-25",
    "https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1960387&reg=3&lang=2",
    [
        ("p1", "Press release: nature and coverage", "is a Centrally Sponsored Scheme for the SC students for studies in India only", True),
        ("p2", "Press release: income ceiling", "whose Parent/Guardian's income should not exceed Rs. 2.5 lakh per annum.", True),
    ],
    reading_note="Read on 2026-10-30 via a fetch tool. PIB press release (2023). It does not list required documents or application steps.",
)
PMSSC = dict(
    id="PMS-SC", name="Post-Matric Scholarship for Scheduled Caste students (PMS-SC)",
    authority="Ministry of Social Justice & Empowerment, Government of India", category="education",
    target_groups=["students"], scheme_type="scholarship", states=["all"], geography="All India (implemented through State governments)", coverage="partial",
    description="Centrally Sponsored post-matric scholarship for Scheduled Caste students studying in India, for students whose parent/guardian income is within the ceiling. Details come from two official press releases; the full scheme guidelines were not read.",
    description_hi="भारत में पढ़ रहे अनुसूचित जाति के विद्यार्थियों के लिए केंद्र प्रायोजित दसवीं-पश्चात छात्रवृत्ति, जिनके अभिभावक की आय सीमा के भीतर है। विवरण दो आधिकारिक प्रेस विज्ञप्तियों से लिया गया है; पूर्ण दिशानिर्देश नहीं पढ़े गए।",
    keywords=["scholarship", "post matric", "scheduled caste", "sc", "student", "social justice", "college", "higher education", "pms-sc"],
    aliases=["PMS-SC", "Post Matric Scholarship for SC", "Post-Matric Scholarship Scheme for SC students"],
    portal=portal("Named in the PIB release as the portal used for this scheme and in the approved source list; how students apply varies by State"),
    application=None,
    documents=[PMSSC_2026, PMSSC_2023],
    rules=[
        rule("r-pmssc-income-26", "d-pmssc-pib-2026", "p2", "income", INCOME_LABEL[0], INCOME_LABEL[1], "annual_income", "lte", 250000,
             "annual income from all sources not exceeding ₹2.5 lakh"),
        rule("r-pmssc-income-23", "d-pmssc-pib-2023", "p2", "income", INCOME_LABEL[0], INCOME_LABEL[1], "annual_income", "lte", 250000,
             "income should not exceed Rs. 2.5 lakh per annum"),
        rule("r-pmssc-cat-26", "d-pmssc-pib-2026", "p1", "category", "Belongs to a Scheduled Caste", "अनुसूचित जाति से संबंधित",
             "category", "eq", "sc", "eligible SC students"),
        rule("r-pmssc-cat-23", "d-pmssc-pib-2023", "p1", "category", "Belongs to a Scheduled Caste", "अनुसूचित जाति से संबंधित",
             "category", "eq", "sc", "for the SC students"),
        rule("r-pmssc-india", "d-pmssc-pib-2023", "p1", "study_in_india", "Studying in India", "भारत में अध्ययनरत",
             "study_location", "eq", "Studying in India", "for studies in India only", manual_check=True),
    ],
    required_documents=[],
)

# ====================================================================== 3. PMS-ST (Ministry of Tribal Affairs)
PMSST_DOC = doc(
    "d-pmsst-pib-2023", "Ministry of Tribal Affairs implements various Scholarship Schemes to promote and encourage basic and higher education amongst ST population",
    "Ministry of Tribal Affairs (Press Information Bureau release)", "press release", "2023-03-15",
    "https://www.pib.gov.in/PressReleasePage.aspx?PRID=1907241",
    [
        ("p1", "Press release: coverage", "ST students studying in in class XI and above", True),
        ("p2", "Press release: income limit", "whose parental annual income is up to Rs. 2.50 lakhs.", True),
    ],
    reading_note=("Read on 2026-10-30 via a fetch tool. PIB reply (2023) about the Post Matric Scholarship for ST students. The phrase "
                  "'in in' is reproduced exactly as the tool returned it. No scholarship amount, documents or application steps were stated."),
)
PMSST = dict(
    id="PMS-ST", name="Post Matric Scholarship for Scheduled Tribe students (PMS-ST)",
    authority="Ministry of Tribal Affairs, Government of India", category="education",
    target_groups=["students"], scheme_type="scholarship", states=["all"], geography="All India (implemented through State governments)", coverage="partial",
    description="Post-matric scholarship for Scheduled Tribe students in Class XI and above whose parental income is within the limit. Details come from one official press release (2023); the full guidelines were not read.",
    description_hi="कक्षा 11 और उससे ऊपर पढ़ रहे अनुसूचित जनजाति के विद्यार्थियों के लिए दसवीं-पश्चात छात्रवृत्ति, जिनकी पारिवारिक आय सीमा के भीतर है। विवरण एक आधिकारिक प्रेस विज्ञप्ति (2023) से लिया गया; पूर्ण दिशानिर्देश नहीं पढ़े गए।",
    keywords=["scholarship", "post matric", "scheduled tribe", "st", "tribal", "student", "class 11", "tribal affairs", "pms-st"],
    aliases=["PMS-ST", "Post Matric Scholarship for ST", "Post Matric Scholarship (PMS) for ST students"],
    portal=portal("General portal from the approved source list; the PIB text read did not mention a portal"),
    application=None,
    documents=[PMSST_DOC],
    rules=[
        rule("r-pmsst-cat", "d-pmsst-pib-2023", "p1", "category", "Belongs to a Scheduled Tribe", "अनुसूचित जनजाति से संबंधित",
             "category", "eq", "st", "ST students"),
        rule("r-pmsst-income", "d-pmsst-pib-2023", "p2", "income", INCOME_LABEL[0], INCOME_LABEL[1], "annual_income", "lte", 250000,
             "parental annual income is up to Rs. 2.50 lakhs"),
        rule("r-pmsst-level", "d-pmsst-pib-2023", "p1", "class_level", "Studying in Class XI or above", "कक्षा 11 या उससे ऊपर में अध्ययनरत",
             "education_level", "gte_level", "class_10", "studying in in class XI and above",
             exception="Ambiguous: the source says 'class XI and above', but your profile records your current or highest completed level, so a Class XI student may be recorded as Class 10. Check this yourself.",
             exception_hi="अस्पष्ट: स्रोत 'कक्षा 11 और उससे ऊपर' कहता है, जबकि आपकी प्रोफ़ाइल वर्तमान या उच्चतम पूर्ण स्तर दर्ज करती है; कक्षा 11 का विद्यार्थी 'कक्षा 10' दर्ज हो सकता है। इसे स्वयं जाँचें।",
             ambiguous=True),
    ],
    required_documents=[],
)

# ====================================================================== 4. AICTE Pragati (Ministry of Education)
PRAGATI_DOC = doc(
    "d-pragati-pib-2021", "Scholarship scheme under AICTE to encourage girls students to pursue Technical Education",
    "Ministry of Education (Press Information Bureau release)", "press release", "2021-12-08",
    "https://www.pib.gov.in/PressReleasePage.aspx?PRID=1779333",
    [
        ("p1", "Press release: admission year (degree/diploma)", "Students admitted in AICTE approved institutions in 1st year of Degree/ Diploma level course", True),
        ("p2", "Press release: lateral entry", "2nd year of Degree/ Diploma level course through lateral entry.", True),
        ("p3", "Press release: girls per family", "Maximum two girls per family.", True),
        ("p4", "Press release: family income", "Total income of the family less than Rs. 8 lakh per annum.", True),
        ("p5", "Press release: benefit", "a sum of Rs. 50,000/- per annum is disbursed to selected girl students", True),
    ],
    reading_note=("Read on 2026-10-30 via a fetch tool. This is a December 2021 Rajya Sabha reply published by PIB, almost five years old; "
                  "income limit and benefit may have changed. AICTE's own scheme page/FAQ was not readable (its page refused automated access)."),
    facts=dict(benefit=dict(value="Rs. 50,000/- per annum", passage_id="p5", date=None)),
)
PRAGATI = dict(
    id="AICTE-PRAGATI", name="AICTE Pragati Scholarship Scheme for girl students (technical education)",
    authority="All India Council for Technical Education (AICTE), Ministry of Education", category="education",
    target_groups=["students", "women"], scheme_type="scholarship", states=["all"], geography="All India", coverage="partial",
    description="Scholarship for girl students admitted to the first year (or second year by lateral entry) of AICTE-approved degree/diploma courses, with a family income limit and at most two girls per family. Based on a 2021 press release; confirm current terms with AICTE.",
    description_hi="AICTE-अनुमोदित डिग्री/डिप्लोमा पाठ्यक्रमों के प्रथम वर्ष (या लेटरल एंट्री से द्वितीय वर्ष) में प्रवेश लेने वाली छात्राओं के लिए छात्रवृत्ति; पारिवारिक आय सीमा और प्रति परिवार अधिकतम दो बालिकाएँ। 2021 की प्रेस विज्ञप्ति पर आधारित; वर्तमान शर्तें AICTE से जाँचें।",
    keywords=["scholarship", "girl", "girls", "women", "female", "technical", "engineering", "diploma", "degree", "aicte", "pragati"],
    aliases=["Pragati", "AICTE Pragati", "Pragati Scholarship", "AICTE Pragati Scholarship Scheme"],
    portal=portal("General portal from the approved source list; the PIB text read did not say where to apply"),
    application=None,
    documents=[PRAGATI_DOC],
    rules=[
        rule("r-pragati-gender", "d-pragati-pib-2021", "p5", "gender", "Girl student", "छात्रा", "gender", "eq", "female", "selected girl students"),
        rule("r-pragati-income", "d-pragati-pib-2021", "p4", "income", INCOME_LABEL[0], INCOME_LABEL[1], "annual_income", "lt", 800000,
             "Total income of the family less than Rs. 8 lakh per annum"),
        rule("r-pragati-siblings", "d-pragati-pib-2021", "p3", "girls_per_family", "At most two girls in the family from whom the scholarship is claimed",
             "परिवार में अधिकतम दो बालिकाएँ", "girls_in_family", "eq", "At most two girls per family", "Maximum two girls per family", manual_check=True),
        rule("r-pragati-admission", "d-pragati-pib-2021", "p1", "admission_year", "Admitted to year 1 of an AICTE-approved degree/diploma course (or year 2 by lateral entry)",
             "AICTE-अनुमोदित डिग्री/डिप्लोमा के प्रथम वर्ष (या लेटरल एंट्री से द्वितीय वर्ष) में प्रवेश",
             "admission_year", "eq", "1st year of Degree/Diploma, or 2nd year through lateral entry",
             "1st year of Degree/ Diploma level course", manual_check=True),
    ],
    required_documents=[],
)

# ====================================================================== 5. PM YASASVI post-matric (OBC/EBC/DNT)
YAS_DOC = doc(
    "d-yasasvi-guidelines", "PM YOUNG ACHIEVERS SCHOLARSHIP AWARD SCHEME FOR VIBRANT INDIA FOR OBCs AND OTHERS (PM –YASASVI)",
    "Ministry of Social Justice & Empowerment, Department of Social Justice & Empowerment, Government of India", "scheme guidelines", None,
    "https://socialjustice.gov.in/public/ckeditor/upload/65661651839791.pdf",
    [
        ("p1", "Part B (post-matric) 5(i): who may apply", "The scholarships will be open to Indian nationals belonging to OBCs, EBCs and DNTs", True),
        ("p2", "Part B V(xiv): employed students", "Employed students whose income combined with the income of their parents/ guardians does not exceed Rs. 2.50 lakh per annum", True),
        ("p3", "Part B V(xv): unemployed students", "Unemployed students whose parents/guardians income from all sources does not exceed Rs. 2.50 lakh per annum", True),
        ("p4", "Part B 8.3: documents (list not read)", "Until the above system is brought into effect, the documents may be scanned and uploaded which include:", True),
    ],
    status="unclear",
    reading_note=("Read on 2026-10-30 via a fetch tool; roughly the first 100,000 of 119,414 characters were read, and the tool itself truncated "
                  "each quotation. The tool reported that the document covers 2021-22 to 2025-26 (summary, not verbatim); that period has ended, "
                  "and whether the scheme was extended or replaced was NOT established, so validity is marked unclear. Only the post-matric part "
                  "(Part B) is represented. The list of documents after para 8.3 was cut off and is NOT recorded."),
)
YAS = dict(
    id="PM-YASASVI-PMS", name="PM YASASVI: Post-Matric Scholarship for OBC, EBC and DNT students",
    authority="Ministry of Social Justice & Empowerment, Government of India", category="education",
    target_groups=["students"], scheme_type="scholarship", states=["all"], geography="All India (implemented through State governments)", coverage="partial",
    description="Post-matric scholarship for Indian students belonging to OBC, EBC or DNT categories whose family income is within the limit. Based on the PM YASASVI guidelines (post-matric part); the guidelines state a scheme period that has ended, so check whether it continues.",
    description_hi="OBC, EBC या DNT श्रेणी के भारतीय विद्यार्थियों के लिए दसवीं-पश्चात छात्रवृत्ति, जिनकी पारिवारिक आय सीमा के भीतर है। PM YASASVI दिशानिर्देशों (दसवीं-पश्चात भाग) पर आधारित; दिशानिर्देशों में बताई योजना-अवधि समाप्त हो चुकी है, इसलिए जाँचें कि योजना जारी है या नहीं।",
    keywords=["scholarship", "post matric", "obc", "ebc", "dnt", "other backward classes", "student", "yasasvi", "social justice"],
    aliases=["PM YASASVI", "PM-YASASVI", "YASASVI", "PM YASASVI Post Matric Scholarship"],
    portal=portal("General portal from the approved source list; the Part B passages read did not name an application URL"),
    application=None,
    documents=[YAS_DOC],
    rules=[
        rule("r-yas-cat", "d-yasasvi-guidelines", "p1", "category", "OBC, EBC or DNT category", "OBC, EBC या DNT श्रेणी",
             "category", "in", ["obc", "ebc_dnt"], "OBCs, EBCs and DNTs",
             exception="The scheme says 'as notified' by the Central/State Government; your category certificate must match the notified list.",
             exception_hi="योजना के अनुसार 'अधिसूचित' श्रेणी लागू है; आपका श्रेणी प्रमाण पत्र अधिसूचित सूची से मेल खाना चाहिए।"),
        rule("r-yas-income-unemp", "d-yasasvi-guidelines", "p3", "income", INCOME_LABEL[0], INCOME_LABEL[1], "annual_income", "lte", 250000,
             "does not exceed Rs. 2.50 lakh per annum"),
        rule("r-yas-income-emp", "d-yasasvi-guidelines", "p2", "income", INCOME_LABEL[0], INCOME_LABEL[1], "annual_income", "lte", 250000,
             "does not exceed Rs. 2.50 lakh per annum"),
    ],
    required_documents=[],
)

# Curator judgements about how far each source can be trusted (CivicLens never infers these from keywords).
# validity: confirmed | unclear | expired | unknown. "unknown" = no effective date and no evidence it is still in force.
SCHEME_STATE = {
    "CSSS-PMUSP": dict(
        validity="unclear",
        validity_note="No issue or effective date appears in the text read, and a second file with a newer-looking name exists on the same portal but could not be read.",
        unresolved=[
            "Which guideline file is current: 'CSSS_GUIDLINES_06022024.pdf' (read) or 'CSSS_GUIDLINES_07022024_updated.pdf' (not readable).",
            "The document list, the course rule and the application window were only summarised by the fetch tool, so they are not recorded as verified rules.",
        ]),
    "PMS-SC": dict(
        validity="unknown",
        validity_note="Two press releases (2023, 2026) state the same income ceiling, but the scheme guidelines were not read, so their current effective terms are not established.",
        unresolved=[
            "Full scheme guidelines were not read: required documents, application steps and deadlines are unknown.",
            "The scheme is implemented through State governments, so the application route may differ by State.",
        ]),
    "PMS-ST": dict(
        validity="unknown",
        validity_note="Based on one 2023 press release; no effective date or guidelines were read.",
        unresolved=[
            "Full guidelines were not read: required documents, amounts, application steps and deadlines are unknown.",
            "'Class XI and above' cannot be matched reliably to the profile's education field.",
        ]),
    "AICTE-PRAGATI": dict(
        validity="unknown",
        validity_note="Based on a December 2021 press release (almost five years old); AICTE's own scheme page could not be read.",
        unresolved=[
            "The income limit, benefit and quotas in 2021 may have changed; the current AICTE terms are not established.",
            "Required documents and the application route are unknown.",
        ]),
    "PM-YASASVI-PMS": dict(
        validity="unclear",
        validity_note="The document reports a scheme period of 2021-22 to 2025-26 (summary, not verbatim); that period has ended and any extension is unknown.",
        unresolved=[
            "Whether the scheme continues after 2025-26.",
            "The list of documents after para 8.3 was cut off and is not recorded.",
            "A State domicile requirement was mentioned in the fetch tool's summary but is not recorded as a verified rule.",
        ]),
}
for _s in (CSSS, PMSSC, PMSST, PRAGATI, YAS):
    _s.update(SCHEME_STATE[_s["id"]])

data = dict(
    meta=dict(
        data_notice=("REAL-DATA PREVIEW. Scheme details were read from official Government of India pages on 2026-10-30 through an automated "
                     "fetch tool. Wording has NOT been compared word-for-word with the original documents, some documents were read only in "
                     "part, and some sources are press releases rather than guidelines. Always confirm on the official source before applying."),
        data_notice_hi=("वास्तविक-डेटा पूर्वावलोकन। योजनाओं का विवरण 2026-10-30 को भारत सरकार के आधिकारिक पृष्ठों से स्वचालित फ़ेच टूल द्वारा पढ़ा गया। "
                        "शब्दों का मूल दस्तावेज़ से शब्दशः मिलान नहीं किया गया है, कुछ दस्तावेज़ केवल आंशिक रूप से पढ़े गए, और कुछ स्रोत दिशानिर्देश नहीं बल्कि "
                        "प्रेस विज्ञप्तियाँ हैं। आवेदन से पहले आधिकारिक स्रोत पर अवश्य पुष्टि करें।"),
        coverage_note="5 student-scholarship schemes. All are partially covered; none can show 'likely eligible'.",
        read_on=READ_ON,
        sources_read=[CSSS_URL, PMSSC_2026["url"], PMSSC_2023["url"], PMSST_DOC["url"], PRAGATI_DOC["url"], YAS_DOC["url"]],
        sources_not_readable=[
            "https://scholarships.gov.in/public/schemeGuidelines/CSSS_GUIDLINES_07022024_updated.pdf (robots_disallowed)",
            "https://www.minorityaffairs.gov.in/WriteReadData/RTF1984/1672032313.pdf (robots_disallowed)",
            "https://scholarships.gov.in/public/schemeGuidelines/AICTE/PM_USPY(SSSJKL)SchemeSpecifications.pdf (robots_disallowed)",
            "https://scholarships.gov.in/public/schemeGuidelines/ApprovedmodifieddraftofTopClassCollege.pdf (robots_disallowed)",
            "https://scholarships.gov.in/public/schemeGuidelines/AICTE/AICTE_2010_F.pdf (robots_disallowed)",
        ],
        generated_by="scripts/build_real_data.py",
    ),
    document_catalog={k: dict(name=v[0], name_hi=v[1]) for k, v in CATALOG.items()},
    schemes=[CSSS, PMSSC, PMSST, PRAGATI, YAS],
)

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT} ({len(data['schemes'])} schemes)")
