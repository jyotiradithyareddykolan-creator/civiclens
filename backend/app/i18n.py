"""English / Hindi strings. Scheme names, numbers, dates and citations are never translated."""

LANGS = ("en", "hi")

T = {
    "en": {
        "status_satisfied": "Satisfied",
        "status_not_satisfied": "Not satisfied",
        "status_unknown": "Unknown",
        "status_conflicting": "Conflicting",
        "overall_likely_eligible": "Likely eligible (preliminary)",
        "overall_likely_ineligible": "Likely ineligible (preliminary)",
        "overall_undetermined": "Eligibility undetermined",
        "overall_source_unavailable": "Source unavailable - cannot assess",
        "disclaimer": "This is a preliminary assessment, not an official decision. The final decision on eligibility and approval rests with the responsible government authority.",
        "summary": "{scheme}: {overall}. Of {total} mandatory criteria, {sat} satisfied, {not_sat} not satisfied, {unk} unknown or conflicting.",
        "summary_unavailable": "{scheme}: the official source could not be retrieved, so no eligibility result is shown.",
        "note_needs": "Needs your answer: {what}.",
        "note_not_met": "Your value ({user}) does not meet the requirement ({req}).",
        "note_met": "Your value ({user}) meets the requirement ({req}).",
        "note_unverified": "This criterion could not be verified automatically from the source text.",
        "warn_manual_verify_scheme": "The text shown for this scheme was read through an automated fetch tool and has not been compared word for word with the official documents. Please verify the exact wording at the official sources.",
        "warn_older": "'{title}' was published on {date}, more than two years ago, and no effective date is stated. Rules may have changed since.",
        "fu_why": "Needed to check: {what}.",
        "ver_match": "Quote found in the stored source passage.",
        "ver_match_manual": "Quote found in the stored passage. The passage itself has not yet been checked word for word against the original document.",
        "ver_unverified": "Not verified: the source text for this rule is only a summary, or its meaning is unclear.",
        "ver_manual": "Stated in the source, but this tool cannot test it.",
        "na_c_satisfied": "No action needed for this criterion.",
        "na_c_not_satisfied": "Your answer does not meet this requirement. Read the official source for any exception before deciding not to apply.",
        "na_c_conflicting": "Official sources disagree. Ask the responsible authority which rule applies.",
        "na_c_manual": "Check this condition yourself in the official source document.",
        "na_c_unverified": "Confirm this rule at the official source; this tool could not verify it.",
        "na_c_answer": "Answer: {question}",
        "na_c_check": "Check this criterion in the official source.",
        "blocker_partial": "Only part of the official text was read, so some rules may be missing.",
        "blocker_validity_unclear": "It is unclear whether the source is current.",
        "blocker_validity_expired": "The source appears to have expired.",
        "blocker_validity_unknown": "The current validity of the source has not been established.",
        "blocker_unknown": "Mandatory criteria that could not be assessed yet: {n} (missing answers, or conditions this tool cannot test).",
        "blocker_conflict": "Official sources disagree on at least one criterion.",
        "reason_likely_eligible": "Every mandatory criterion is satisfied by verified evidence, and nothing known blocks the conclusion. This is still only a preliminary assessment.",
        "reason_likely_ineligible": "At least one mandatory criterion is not met, based on a rule that matches the stored source text.",
        "reason_undetermined": "There is not enough verified information to say whether you may qualify.",
        "reason_source_unavailable": "The official source could not be retrieved.",
        "note_manual": "This condition is stated in the official source but cannot be checked by this tool. Please confirm it yourself in the source document.",
        "warn_partial": "Only part of the official text for this scheme has been read, so CivicLens cannot say 'likely eligible'. Check the full official guidelines.",
        "warn_manual_verify": "'{title}': the text shown was read through an automated fetch tool and has not been compared word for word with the official document. Please verify the exact wording at the official source.",
        "note_conflict": "Official sources disagree on this criterion. Your value ({user}) {verdict}.",
        "verdict_meets_all": "meets every version",
        "verdict_fails_all": "fails every version",
        "verdict_mixed": "meets some versions but not others",
        "verdict_unknown": "cannot be compared yet because the value is missing",
        "warn_no_effective": "Current validity of '{title}' has not been established (no effective date confirmed).",
        "warn_unclear": "'{title}': it is unclear whether this document is current or superseded.",
        "warn_stale": "'{title}' was last checked on {date}, more than {days} days ago.",
        "warn_unavailable": "'{title}' could not be retrieved from its official source.",
        "warn_never_checked": "'{title}' has no recorded check date.",
        "warn_conflict": "Official documents disagree on: {what}. No document has been treated as authoritative.",
        "warn_injection": "{n} source passage(s) contained instruction-like text and were ignored.",
        "warn_superseded": "'{title}' is superseded and was not used for the assessment.",
        "freshness_note": "'Last checked' shows when this copy was retrieved. It does not prove that the policy is still current.",
        "cl_mandatory": "Mandatory",
        "cl_optional": "Optional",
        "cl_conditional": "Conditionally required",
        "cl_unverified": "Mentioned, but requirement not verified",
        "source_disagreement": "Only some of the conflicting source documents list this document.",
        "ds_available": "Available",
        "ds_missing": "Missing",
        "ds_not_confirmed": "Not yet confirmed",
        "app_applies": "May apply to you",
        "app_not_applicable": "Not applicable to you",
        "app_unknown": "Depends on an answer we do not have yet",
        "na_available": "Keep this ready.",
        "na_missing_with_how": "Obtain this document. See the official instructions below.",
        "na_missing_no_how": "Obtain this document. No verified official instructions were found in the covered sources; check the official portal.",
        "na_not_confirmed": "Confirm whether you have this document.",
        "na_conditional_unknown": "Answer the follow-up question to find out whether this applies.",
        "no_results": "No suitable schemes were found in the currently covered sources. Try different words or broader filters. This does not mean no such scheme exists elsewhere.",
        "named_unverified": "Your question seems to name a specific scheme ('{name}'). It could not be verified in the covered sources, so no eligibility rules or links are shown for it. Related schemes below are only keyword matches.",
        "fetch_not_checked": "Demo document: no live official URL is configured, so no check was made.",
        "fetch_unavailable": "The source could not be retrieved. Current requirements have not been verified from it.",
        "fetch_ok": "The source was reachable on this check. This does not prove the policy is current.",
        "fetch_disabled": "Live fetching is disabled (CIVICLENS_LIVE_FETCH=0).",
        "fetch_blocked": "This URL is not on the approved official-domain list and was not fetched.",
        "ask_abstain": "No reliable evidence was found for this question in the covered sources.",
        "ask_extractive": "Relevant passages from the official documents are shown below. No AI summary was generated.",
        "ask_llm": "AI-generated answer based only on the cited passages. Check the passages themselves.",
        "no_deadline": "No deadline is stated in the source.",
        "deadline_passed": "The deadline stated in the source has passed.",
        "no_application": "No verified application guidance is available for this scheme.",
        "no_link": "No scheme-specific application URL has been verified, so none is shown. Use the official portal.",
        "privacy_notice": "CivicLens does not store your profile on the server. It stays in this browser and is sent only to compute results. You can delete it at any time.",
    },
    "hi": {
        "status_satisfied": "पूरी हुई",
        "status_not_satisfied": "पूरी नहीं हुई",
        "status_unknown": "अज्ञात",
        "status_conflicting": "परस्पर विरोधी",
        "overall_likely_eligible": "संभावित रूप से पात्र (प्रारंभिक)",
        "overall_likely_ineligible": "संभावित रूप से अपात्र (प्रारंभिक)",
        "overall_undetermined": "पात्रता अनिर्धारित",
        "overall_source_unavailable": "स्रोत उपलब्ध नहीं - आकलन संभव नहीं",
        "disclaimer": "यह केवल प्रारंभिक आकलन है, आधिकारिक निर्णय नहीं। पात्रता और स्वीकृति का अंतिम निर्णय संबंधित सरकारी प्राधिकरण का है।",
        "summary": "{scheme}: {overall}। {total} अनिवार्य मानदंडों में से {sat} पूरे हुए, {not_sat} पूरे नहीं हुए, {unk} अज्ञात या परस्पर विरोधी।",
        "summary_unavailable": "{scheme}: आधिकारिक स्रोत प्राप्त नहीं हो सका, इसलिए पात्रता परिणाम नहीं दिखाया गया।",
        "note_needs": "आपके उत्तर की आवश्यकता: {what}।",
        "note_not_met": "आपका मान ({user}) आवश्यकता ({req}) को पूरा नहीं करता।",
        "note_met": "आपका मान ({user}) आवश्यकता ({req}) को पूरा करता है।",
        "note_unverified": "स्रोत पाठ से इस मानदंड की स्वचालित पुष्टि नहीं हो सकी।",
        "warn_manual_verify_scheme": "इस योजना के लिए दिखाया गया पाठ स्वचालित फ़ेच टूल से पढ़ा गया है और आधिकारिक दस्तावेज़ों से शब्दशः मिलान नहीं किया गया है। कृपया आधिकारिक स्रोतों पर सटीक शब्द जाँचें।",
        "warn_older": "'{title}' दो वर्ष से अधिक पहले ({date}) प्रकाशित हुआ था और प्रभावी तिथि नहीं दी गई है। तब से नियम बदल सकते हैं।",
        "fu_why": "जाँचने के लिए आवश्यक: {what}।",
        "ver_match": "उद्धरण संग्रहीत स्रोत अंश में मिला।",
        "ver_match_manual": "उद्धरण संग्रहीत अंश में मिला। इस अंश का मूल दस्तावेज़ से शब्दशः मिलान अभी नहीं हुआ है।",
        "ver_unverified": "सत्यापित नहीं: इस नियम का स्रोत पाठ केवल सारांश है, या उसका अर्थ अस्पष्ट है।",
        "ver_manual": "स्रोत में दिया गया है, पर यह टूल इसकी जाँच नहीं कर सकता।",
        "na_c_satisfied": "इस मानदंड के लिए कोई कार्रवाई आवश्यक नहीं।",
        "na_c_not_satisfied": "आपका उत्तर इस शर्त को पूरा नहीं करता। आवेदन न करने का निर्णय लेने से पहले आधिकारिक स्रोत में अपवाद देखें।",
        "na_c_conflicting": "आधिकारिक स्रोत आपस में असहमत हैं। संबंधित प्राधिकरण से पूछें कि कौन-सा नियम लागू है।",
        "na_c_manual": "इस शर्त की जाँच आधिकारिक स्रोत दस्तावेज़ में स्वयं करें।",
        "na_c_unverified": "इस नियम की पुष्टि आधिकारिक स्रोत पर करें; यह टूल इसे सत्यापित नहीं कर सका।",
        "na_c_answer": "उत्तर दें: {question}",
        "na_c_check": "इस मानदंड की जाँच आधिकारिक स्रोत में करें।",
        "blocker_partial": "आधिकारिक पाठ का केवल एक भाग पढ़ा गया है, इसलिए कुछ नियम छूट सकते हैं।",
        "blocker_validity_unclear": "स्पष्ट नहीं है कि स्रोत वर्तमान है या नहीं।",
        "blocker_validity_expired": "स्रोत की अवधि समाप्त प्रतीत होती है।",
        "blocker_validity_unknown": "स्रोत की वर्तमान वैधता स्थापित नहीं हुई है।",
        "blocker_unknown": "जिन अनिवार्य मानदंडों का आकलन अभी नहीं हो सका: {n} (उत्तर अनुपलब्ध, या ऐसी शर्तें जिन्हें यह टूल जाँच नहीं सकता)।",
        "blocker_conflict": "कम से कम एक मानदंड पर आधिकारिक स्रोत असहमत हैं।",
        "reason_likely_eligible": "हर अनिवार्य मानदंड सत्यापित प्रमाण से पूरा होता है और कुछ भी ज्ञात रूप से निष्कर्ष को नहीं रोकता। यह फिर भी केवल प्रारंभिक आकलन है।",
        "reason_likely_ineligible": "कम से कम एक अनिवार्य मानदंड पूरा नहीं होता, ऐसे नियम के आधार पर जो संग्रहीत स्रोत पाठ से मेल खाता है।",
        "reason_undetermined": "आप पात्र हो सकते हैं या नहीं, यह कहने के लिए पर्याप्त सत्यापित जानकारी नहीं है।",
        "reason_source_unavailable": "आधिकारिक स्रोत प्राप्त नहीं हो सका।",
        "note_manual": "यह शर्त आधिकारिक स्रोत में दी गई है, पर यह टूल इसकी जाँच नहीं कर सकता। कृपया स्रोत दस्तावेज़ में स्वयं पुष्टि करें।",
        "warn_partial": "इस योजना के आधिकारिक पाठ का केवल एक भाग पढ़ा गया है, इसलिए CivicLens 'संभावित रूप से पात्र' नहीं कह सकता। पूर्ण आधिकारिक दिशानिर्देश देखें।",
        "warn_manual_verify": "'{title}': दिखाया गया पाठ स्वचालित फ़ेच टूल से पढ़ा गया है और आधिकारिक दस्तावेज़ से शब्दशः मिलान नहीं किया गया है। कृपया आधिकारिक स्रोत पर सटीक शब्द जाँचें।",
        "note_conflict": "इस मानदंड पर आधिकारिक स्रोत असहमत हैं। आपका मान ({user}) {verdict}।",
        "verdict_meets_all": "हर संस्करण को पूरा करता है",
        "verdict_fails_all": "हर संस्करण को पूरा नहीं करता",
        "verdict_mixed": "कुछ संस्करणों को पूरा करता है, कुछ को नहीं",
        "verdict_unknown": "अभी तुलना नहीं हो सकती क्योंकि मान उपलब्ध नहीं है",
        "warn_no_effective": "'{title}' की वर्तमान वैधता स्थापित नहीं है (प्रभावी तिथि की पुष्टि नहीं)।",
        "warn_unclear": "'{title}': स्पष्ट नहीं है कि यह दस्तावेज़ वर्तमान है या निरस्त।",
        "warn_stale": "'{title}' की अंतिम जाँच {date} को हुई थी, यानी {days} दिनों से अधिक पहले।",
        "warn_unavailable": "'{title}' अपने आधिकारिक स्रोत से प्राप्त नहीं हो सका।",
        "warn_never_checked": "'{title}' की जाँच की कोई तिथि दर्ज नहीं है।",
        "warn_conflict": "आधिकारिक दस्तावेज़ इस विषय पर असहमत हैं: {what}। किसी भी दस्तावेज़ को प्रामाणिक नहीं माना गया है।",
        "warn_injection": "{n} स्रोत अनुच्छेदों में निर्देश जैसा पाठ मिला और उन्हें अनदेखा किया गया।",
        "warn_superseded": "'{title}' निरस्त हो चुका है और आकलन में उपयोग नहीं किया गया।",
        "freshness_note": "'अंतिम जाँच' बताती है कि यह प्रति कब प्राप्त की गई। इससे यह सिद्ध नहीं होता कि नीति अब भी वर्तमान है।",
        "cl_mandatory": "अनिवार्य",
        "cl_optional": "वैकल्पिक",
        "cl_conditional": "शर्त के अनुसार आवश्यक",
        "cl_unverified": "उल्लेखित, पर आवश्यकता सत्यापित नहीं",
        "source_disagreement": "परस्पर विरोधी स्रोत दस्तावेज़ों में से केवल कुछ में यह दस्तावेज़ सूचीबद्ध है।",
        "ds_available": "उपलब्ध",
        "ds_missing": "उपलब्ध नहीं",
        "ds_not_confirmed": "अभी पुष्टि नहीं",
        "app_applies": "आप पर लागू हो सकता है",
        "app_not_applicable": "आप पर लागू नहीं",
        "app_unknown": "ऐसे उत्तर पर निर्भर जो अभी हमारे पास नहीं है",
        "na_available": "इसे तैयार रखें।",
        "na_missing_with_how": "यह दस्तावेज़ प्राप्त करें। नीचे आधिकारिक निर्देश देखें।",
        "na_missing_no_how": "यह दस्तावेज़ प्राप्त करें। उपलब्ध स्रोतों में सत्यापित आधिकारिक निर्देश नहीं मिले; आधिकारिक पोर्टल देखें।",
        "na_not_confirmed": "पुष्टि करें कि आपके पास यह दस्तावेज़ है या नहीं।",
        "na_conditional_unknown": "यह लागू होता है या नहीं, यह जानने के लिए अगला प्रश्न भरें।",
        "no_results": "वर्तमान में शामिल स्रोतों में कोई उपयुक्त योजना नहीं मिली। अलग शब्द या व्यापक फ़िल्टर आज़माएँ। इसका अर्थ यह नहीं कि अन्यत्र ऐसी योजना नहीं है।",
        "named_unverified": "आपका प्रश्न किसी विशिष्ट योजना ('{name}') का नाम लेता प्रतीत होता है। शामिल स्रोतों में इसकी पुष्टि नहीं हो सकी, इसलिए इसके लिए कोई पात्रता नियम या लिंक नहीं दिखाया गया। नीचे की संबंधित योजनाएँ केवल शब्द-मिलान हैं।",
        "fetch_not_checked": "डेमो दस्तावेज़: कोई लाइव आधिकारिक URL निर्धारित नहीं है, इसलिए जाँच नहीं की गई।",
        "fetch_unavailable": "स्रोत प्राप्त नहीं हो सका। इससे वर्तमान आवश्यकताओं की पुष्टि नहीं हुई है।",
        "fetch_ok": "इस जाँच में स्रोत उपलब्ध था। इससे यह सिद्ध नहीं होता कि नीति वर्तमान है।",
        "fetch_disabled": "लाइव फ़ेचिंग बंद है (CIVICLENS_LIVE_FETCH=0)।",
        "fetch_blocked": "यह URL स्वीकृत आधिकारिक डोमेन सूची में नहीं है, इसलिए प्राप्त नहीं किया गया।",
        "ask_abstain": "शामिल स्रोतों में इस प्रश्न के लिए विश्वसनीय प्रमाण नहीं मिला।",
        "ask_extractive": "आधिकारिक दस्तावेज़ों के प्रासंगिक अनुच्छेद नीचे दिखाए गए हैं। कोई AI सारांश नहीं बनाया गया।",
        "ask_llm": "केवल उद्धृत अनुच्छेदों पर आधारित AI-जनित उत्तर। कृपया अनुच्छेद स्वयं भी देखें।",
        "no_deadline": "स्रोत में कोई अंतिम तिथि नहीं दी गई है।",
        "deadline_passed": "स्रोत में बताई गई अंतिम तिथि बीत चुकी है।",
        "no_application": "इस योजना के लिए सत्यापित आवेदन मार्गदर्शन उपलब्ध नहीं है।",
        "no_link": "योजना-विशिष्ट आवेदन URL सत्यापित नहीं है, इसलिए नहीं दिखाया गया। आधिकारिक पोर्टल देखें।",
        "privacy_notice": "CivicLens आपकी प्रोफ़ाइल सर्वर पर संग्रहीत नहीं करता। यह इसी ब्राउज़र में रहती है और केवल परिणाम निकालने के लिए भेजी जाती है। आप इसे कभी भी हटा सकते हैं।",
    },
}

VALUE_HI = {
    "undergraduate": "स्नातक", "postgraduate": "स्नातकोत्तर", "doctorate": "डॉक्टरेट",
    "class_12": "कक्षा 12", "class_10": "कक्षा 10", "below_class_10": "कक्षा 10 से कम",
    "unemployed": "बेरोजगार", "underemployed": "अल्प-रोजगार", "employed": "नियोजित", "self_employed": "स्वरोजगार",
    "planning": "योजना बना रहे", "running": "चला रहे", "none": "कोई नहीं",
    "female": "महिला", "male": "पुरुष", "other": "अन्य",
    "farmer": "किसान", "student": "छात्र/छात्रा", "owner": "स्वामी", "tenant": "किरायेदार",
    "delhi": "दिल्ली", "maharashtra": "महाराष्ट्र",
    "general": "सामान्य", "ews": "ई.डब्ल्यू.एस.", "obc": "अ.पि.व.", "sc": "अ.जा.", "st": "अ.ज.जा.", "ebc_dnt": "ई.बी.सी. / डी.एन.टी.",
    "other_pension": "अन्य सरकारी वृद्धावस्था पेंशन", "other_scholarship": "अन्य छात्रवृत्ति (केंद्र या राज्य)",
    "true": "हाँ", "false": "नहीं",
}

VALUE_EN = {
    "ews": "EWS", "obc": "OBC", "sc": "SC", "st": "ST", "ebc_dnt": "EBC / DNT", "true": "Yes", "false": "No",
    "class_12": "Class 12", "class_10": "Class 10", "below_class_10": "Below Class 10",
    "other_pension": "another government old-age pension", "other_scholarship": "another scholarship (central or state)",
}

UNIT = {
    "annual_income": ("₹", ""),
    "landholding_hectares": ("", " hectares"),
    "age": ("", " years"),
}


def t(lang: str, key: str, **kw) -> str:
    lang = lang if lang in LANGS else "en"
    s = T[lang].get(key) or T["en"].get(key) or key
    return s.format(**kw) if kw else s


def inr(n) -> str:
    """Indian digit grouping: 300000 -> ₹3,00,000."""
    n = int(n)
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return ("-" if n < 0 else "") + "₹" + s


def value_label(lang: str, v) -> str:
    key = str(v).lower() if not isinstance(v, bool) else ("true" if v else "false")
    if lang == "hi" and key in VALUE_HI:
        return VALUE_HI[key]
    if key in VALUE_EN:
        return VALUE_EN[key]
    if isinstance(v, str):
        # keys like "other_pension" are title-cased; sentences from the source ("Above the 80th percentile...") are left alone
        return v.replace("_", " ").title() if ("_" in v or " " not in v) else v
    return str(v)


def fmt_value(lang: str, attribute: str, v) -> str:
    """Human display of a single value; numbers stay numerals in every language."""
    if v is None:
        return "-"
    if attribute == "annual_income" and isinstance(v, (int, float)) and not isinstance(v, bool):
        return inr(v)
    if attribute == "landholding_hectares":
        return f"{v:g} " + ("हेक्टेयर" if lang == "hi" else "hectares")
    if attribute == "age" and isinstance(v, (int, float)) and not isinstance(v, bool):
        return f"{v} " + ("वर्ष" if lang == "hi" else "years")
    if isinstance(v, list):
        return ", ".join(value_label(lang, x) for x in v) if v else ("कोई नहीं" if lang == "hi" else "none")
    return value_label(lang, v)
