"""Profile field specifications: used by the API, the questionnaire and follow-up questions."""

STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

LEVELS = ["below_class_10", "class_10", "class_12", "undergraduate", "postgraduate", "doctorate"]


def opt(value, en, hi):
    return {"value": value, "en": en, "hi": hi}


FIELD_SPECS = {
    "age": {"type": "number", "min": 0, "max": 120, "label": ("Age (years)", "आयु (वर्ष)"),
            "q": ("What is your age in years?", "आपकी आयु कितने वर्ष है?")},
    "state": {"type": "state", "label": ("State / Union Territory of residence", "निवास का राज्य / केंद्र शासित प्रदेश"),
              "q": ("Which state or union territory do you live in?", "आप किस राज्य या केंद्र शासित प्रदेश में रहते हैं?")},
    "annual_income": {"type": "number", "min": 0, "max": 1000000000,
                      "label": ("Annual household income (₹)", "वार्षिक पारिवारिक आय (₹)"),
                      "q": ("What is your approximate annual household income in rupees?", "आपकी अनुमानित वार्षिक पारिवारिक आय रुपयों में कितनी है?")},
    "occupation": {"type": "select", "label": ("Main occupation", "मुख्य व्यवसाय"),
                   "q": ("What is your main occupation?", "आपका मुख्य व्यवसाय क्या है?"),
                   "options": [opt("student", "Student", "छात्र/छात्रा"), opt("farmer", "Farmer", "किसान"),
                               opt("salaried", "Salaried employee", "वेतनभोगी"), opt("self_employed", "Self-employed / business", "स्वरोजगार / व्यवसाय"),
                               opt("unemployed", "Unemployed / job seeker", "बेरोजगार / रोजगार-तलाशी"), opt("homemaker", "Homemaker", "गृहिणी / गृहस्थ"),
                               opt("retired", "Retired", "सेवानिवृत्त"), opt("other", "Other", "अन्य")]},
    "education_level": {"type": "select", "label": ("Education (current or highest)", "शिक्षा (वर्तमान या उच्चतम)"),
                        "q": ("What is your current or highest education level?", "आपका वर्तमान या उच्चतम शिक्षा स्तर क्या है?"),
                        "options": [opt("below_class_10", "Below Class 10", "कक्षा 10 से कम"), opt("class_10", "Class 10", "कक्षा 10"),
                                    opt("class_12", "Class 12", "कक्षा 12"), opt("undergraduate", "Undergraduate", "स्नातक"),
                                    opt("postgraduate", "Postgraduate", "स्नातकोत्तर"), opt("doctorate", "Doctorate", "डॉक्टरेट")]},
    "is_student": {"type": "boolean", "label": ("Currently enrolled as a student", "वर्तमान में छात्र के रूप में नामांकित"),
                   "q": ("Are you currently enrolled as a student?", "क्या आप वर्तमान में छात्र/छात्रा के रूप में नामांकित हैं?")},
    "gender": {"type": "select", "label": ("Gender", "लिंग"), "q": ("What is your gender?", "आपका लिंग क्या है?"),
               "options": [opt("female", "Female", "महिला"), opt("male", "Male", "पुरुष"), opt("other", "Other", "अन्य")]},
    "category": {"type": "select", "label": ("Social category (only if a scheme asks)", "सामाजिक श्रेणी (केवल यदि योजना पूछे)"),
                 "q": ("Which social category applies to you?", "आप पर कौन-सी सामाजिक श्रेणी लागू होती है?"),
                 "options": [opt("general", "General", "सामान्य"), opt("ews", "EWS", "ई.डब्ल्यू.एस."), opt("obc", "OBC", "अ.पि.व."),
                             opt("sc", "SC", "अ.जा."), opt("st", "ST", "अ.ज.जा."),
                             opt("ebc_dnt", "EBC / DNT", "ई.बी.सी. / डी.एन.टी.")]},
    "employment_status": {"type": "select", "label": ("Employment status", "रोजगार की स्थिति"),
                          "q": ("What is your employment status?", "आपकी रोजगार की स्थिति क्या है?"),
                          "options": [opt("employed", "Employed", "नियोजित"), opt("self_employed", "Self-employed", "स्वरोजगार"),
                                      opt("underemployed", "Underemployed", "अल्प-रोजगार"), opt("unemployed", "Unemployed", "बेरोजगार")]},
    "business_status": {"type": "select", "label": ("Business / enterprise", "व्यवसाय / उद्यम"),
                        "q": ("Are you planning to start, or already running, a small business?", "क्या आप छोटा व्यवसाय शुरू करने की योजना बना रहे हैं या पहले से चला रहे हैं?"),
                        "options": [opt("none", "Neither", "दोनों नहीं"), opt("planning", "Planning to start", "शुरू करने की योजना"), opt("running", "Already running", "पहले से चला रहे")]},
    "landholding_hectares": {"type": "number", "min": 0, "max": 100000, "step": 0.1,
                             "label": ("Total landholding of your family (hectares)", "परिवार की कुल भूमि-जोत (हेक्टेयर)"),
                             "q": ("What is your family's total operational landholding in hectares?", "आपके परिवार की कुल परिचालित भूमि-जोत हेक्टेयर में कितनी है?")},
    "land_tenure": {"type": "select", "label": ("Land you cultivate", "आप जिस भूमि पर खेती करते हैं"),
                    "q": ("Do you own the land you cultivate, or cultivate it as a tenant?", "क्या आप जिस भूमि पर खेती करते हैं वह आपकी है, या आप किरायेदार के रूप में खेती करते हैं?"),
                    "options": [opt("owner", "I own it", "मेरी अपनी है"), opt("tenant", "I am a tenant", "मैं किरायेदार हूँ"), opt("none", "I do not cultivate land", "मैं खेती नहीं करता/करती")]},
    "existing_benefits": {"type": "multi", "label": ("Benefits you already receive", "जो लाभ आप पहले से ले रहे हैं"),
                          "q": ("Do you already receive any of these benefits?", "क्या आप पहले से इनमें से कोई लाभ ले रहे हैं?"),
                          "options": [opt("other_pension", "Another government old-age pension", "अन्य सरकारी वृद्धावस्था पेंशन"),
                              opt("other_scholarship", "Another scholarship (central or state)", "अन्य छात्रवृत्ति (केंद्र या राज्य)")],
                          "allow_none": True},
}

# Follow-up helper: where a missing attribute can be asked for.
def question(attribute: str, lang: str) -> str:
    spec = FIELD_SPECS.get(attribute)
    if not spec:
        return attribute
    return spec["q"][1 if lang == "hi" else 0]


def label(attribute: str, lang: str) -> str:
    spec = FIELD_SPECS.get(attribute)
    if not spec:
        return attribute
    return spec["label"][1 if lang == "hi" else 0]


def spec_for_api() -> dict:
    out = {}
    for k, v in FIELD_SPECS.items():
        d = {kk: vv for kk, vv in v.items() if kk not in ("label", "q")}
        d["label"] = {"en": v["label"][0], "hi": v["label"][1]}
        d["question"] = {"en": v["q"][0], "hi": v["q"][1]}
        out[k] = d
    return out
