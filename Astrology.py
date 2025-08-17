import streamlit as st
from datetime import date, time
import random
import re
from io import StringIO

if "qa_log" not in st.session_state:
    st.session_state.qa_log = []  # list of {q, a}
if "reading" not in st.session_state:
    st.session_state.reading = None  # core reading dict
if "user_info" not in st.session_state:
    st.session_state.user_info = None  # name, dob, tob, place, tz
def user_seed(name: str, dob: date):
    key = f"{name.strip().lower()}|{dob.isoformat()}"
    return abs(hash(key)) % (2**32)

# Astrology helpers
SIGN_DATES = [
    ("Capricorn", (12, 22), (1, 19)),
    ("Aquarius",  (1, 20),  (2, 18)),
    ("Pisces",    (2, 19),  (3, 20)),
    ("Aries",     (3, 21),  (4, 19)),
    ("Taurus",    (4, 20),  (5, 20)),
    ("Gemini",    (5, 21),  (6, 20)),
    ("Cancer",    (6, 21),  (7, 22)),
    ("Leo",       (7, 23),  (8, 22)),
    ("Virgo",     (8, 23),  (9, 22)),
    ("Libra",     (9, 23),  (10, 22)),
    ("Scorpio",   (10, 23), (11, 21)),
    ("Sagittarius",(11, 22),(12, 21)),
]

ELEMENT = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
}

SIGN_TRAITS = {
    "Aries": ["bold", "action-oriented", "competitive"],
    "Taurus": ["grounded", "patient", "resourceful"],
    "Gemini": ["curious", "communicative", "adaptable"],
    "Cancer": ["caring", "intuitive", "protective"],
    "Leo": ["confident", "expressive", "warm-hearted"],
    "Virgo": ["practical", "detail-focused", "helpful"],
    "Libra": ["diplomatic", "balanced", "aesthetic"],
    "Scorpio": ["intense", "transformational", "loyal"],
    "Sagittarius": ["optimistic", "philosophical", "adventurous"],
    "Capricorn": ["ambitious", "disciplined", "strategic"],
    "Aquarius": ["original", "humanitarian", "visionary"],
    "Pisces": ["empathetic", "artistic", "spiritual"],
}

KEYWORD_TOPICS = {
    "career": ["job", "career", "work", "promotion", "startup", "boss", "salary"],
    "love": ["love", "relationship", "marriage", "partner", "crush", "dating"],
    "health": ["health", "fitness", "wellness", "disease", "stress", "sleep"],
    "money": ["money", "finance", "wealth", "investment", "debt", "loan"],
    "education": ["exam", "study", "college", "research", "learning"],
    "travel": ["travel", "trip", "move", "relocation", "abroad"],
    "family": ["family", "parents", "home", "children"],
}

TOPIC_TEMPLATES = {
    ("Fire", "career"): "Your fire-sign drive is peaking. Set a bold target for the next 30 days and back it with consistent action; a mentor could accelerate your rise.",
    ("Earth", "career"): "Steady progress beats sudden leaps. Document your wins and renegotiate terms after delivering one measurable milestone.",
    ("Air", "career"): "Conversations open doors. Pitch two new ideas and follow up within 48 hours; collaboration brings a breakthrough.",
    ("Water", "career"): "Trust your intuition about people. Align with a values-matched team; impact will follow security.",
    
    ("Fire", "love"): "Lead with sincerity and a playful plan. A confident invitation creates the spark you want.",
    ("Earth", "love"): "Show reliability through small rituals. Consistency and care speak louder than grand gestures.",
    ("Air", "love"): "Talk it out. A clear, light-hearted conversation dissolves a lingering misunderstanding.",
    ("Water", "love"): "Share feelings without flooding the moment. Vulnerability in doses deepens the bond.",

    ("Fire", "health"): "Channel energy into structured training. Short, intense sessions plus proper rest keep you sharp.",
    ("Earth", "health"): "Build a realistic routine. Nutrition and sleep hygiene are your quiet superpowers.",
    ("Air", "health"): "Learn what your body is saying. Track patterns; tiny tweaks bring quick wins.",
    ("Water", "health"): "Gentle movement and breathwork reset your system. Protect your emotional boundaries.",

    ("Fire", "money"): "Take initiative on income. A calculated side project can scale; manage risk with clear caps.",
    ("Earth", "money"): "Consolidate and plan. Automate savings and review fixed costs; security grows steadily.",
    ("Air", "money"): "Network for opportunities. Diversify skills and keep cashflow flexible.",
    ("Water", "money"): "Follow values-based spending. Invest in stability and peace of mind.",

    ("Fire", "education"): "Aim for mastery via sprints. Present your learning publicly to lock it in.",
    ("Earth", "education"): "Build from fundamentals. A tidy schedule and spaced repetition compound fast.",
    ("Air", "education"): "Study with peers. Teaching others clarifies your own understanding.",
    ("Water", "education"): "Use emotion to remember. Stories, music, and imagery cement concepts.",

    ("Fire", "travel"): "Go where the challenge is. A dynamic environment sparks growth.",
    ("Earth", "travel"): "Plan details and budget. Comfort enables deeper exploration.",
    ("Air", "travel"): "Choose vibrant, social places. Serendipity is your compass.",
    ("Water", "travel"): "Seek water and calm culture. Reflection unlocks insight.",

    ("Fire", "family"): "Lead with warmth and action. A shared activity heals old friction.",
    ("Earth", "family"): "Offer practical support. Small, reliable help rebuilds trust.",
    ("Air", "family"): "Facilitate dialogue. Listening first creates harmony.",
    ("Water", "family"): "Acknowledge feelings. Empathy transforms the home atmosphere.",
}

INTRO_LINES = [
    "The stars don't decide—*you* do. But they can offer a nudge.",
    "Astrology is a mirror, not a map. Let's look together.",
    "Consider this a poetic forecast inspired by your birth details.",
]

OUTRO_LINES = [
    "Use this as guidance, not a guarantee.",
    "Take what resonates and leave the rest.",
    "Fortune favors the prepared—act on the insight.",
]

# Core functions
def get_sun_sign(d: date) -> str:
    m, day = d.month, d.day
    for sign, (sm, sd), (em, ed) in SIGN_DATES:
        if (m == sm and day >= sd) or (m == em and day <= ed):
            return sign
        if sm > em:  # spans year end (Capricorn)
            if (m == sm and day >= sd) or (m == em and day <= ed) or (m == 12 and day >= sd) or (m == 1 and day <= ed):
                return sign
    return "Aries"


def life_path_number(d: date) -> int:
    def digit_sum(n):
        s = sum(int(c) for c in str(n))
        return s if s < 10 or s in (11, 22, 33) else digit_sum(s)
    ymd = int(d.strftime("%Y%m%d"))
    return digit_sum(ymd)


def build_core_reading(name: str, dob: date, tob: time, place: str) -> dict:
    sign = get_sun_sign(dob)
    element = ELEMENT.get(sign, "Fire")
    traits = SIGN_TRAITS.get(sign, [])
    lp = life_path_number(dob)

    rng = random.Random(user_seed(name, dob))
    intro = rng.choice(INTRO_LINES)
    outro = rng.choice(OUTRO_LINES)

    affirmations = {
        "Fire": ["I act with courage.", "My energy creates momentum."],
        "Earth": ["I build steady foundations.", "Consistency compounds."],
        "Air": ["I communicate clearly.", "Ideas flow through me."],
        "Water": ["I trust my intuition.", "Calm is my power."]
    }

    lucky = {
        "Fire": {"colors": ["crimson", "gold"], "days": ["Tuesday", "Sunday"]},
        "Earth": {"colors": ["emerald", "olive"], "days": ["Friday", "Saturday"]},
        "Air": {"colors": ["sky blue", "silver"], "days": ["Wednesday", "Saturday"]},
        "Water": {"colors": ["sea green", "indigo"], "days": ["Monday", "Thursday"]},
    }

    luck = lucky[element]
    return {
        "sign": sign,
        "element": element,
        "traits": traits,
        "life_path": lp,
        "intro": intro,
        "outro": outro,
        "affirmation": rng.choice(affirmations[element]),
        "lucky_colors": ", ".join(luck["colors"]),
        "lucky_days": ", ".join(luck["days"]),
    }


def detect_topic(question: str) -> str:
    q = question.lower()
    for topic, words in KEYWORD_TOPICS.items():
        if any(re.search(rf"\\b{w}\\b", q) for w in words):
            return topic
    return "general"


def answer_question(element: str, life_path: int, sign: str, question: str):
    topic = detect_topic(question)
    if topic == "general":
        text = (
            f"As a {sign} with {element.lower()} energy, focus on one clear intention this week. "
            f"Your Life Path {life_path} favors decisions that simplify and align with your core values."
        )
    else:
        template = TOPIC_TEMPLATES.get((element, topic))
        if template:
            suffix = " With Life Path {lp}, choose the option that enhances long-term alignment over short-term noise.".format(lp=life_path)
            text = template + " " + suffix
        else:
            text = (
                f"Tune into your {element.lower()} strengths. Life Path {life_path} suggests a step-by-step approach."
            )
    return text, topic

# UI of streamlit dashboard
st.set_page_config(page_title="AI Astrologer by - SACHIN MAURYA", page_icon="✨", layout="centered")

with st.sidebar:
    st.markdown("""
    # ✨ AI Astrologer
    Provide your birth details to get a personalized, astrology-inspired reading. 

    **Note:** This is for guidance and reflection—not a substitute for professional advice, I (Sachin Maurya) Create this for my Assignment and project purpose,
                 I am not taking any responsiblility for any prediction and it's Impects )
    """)

st.markdown(
    """
    <style>
        .title {font-size: 36px; font-weight: 800;}
        .subtitle {opacity: 0.85;}
        .card {padding: 1.25rem; border-radius: 1rem; border: 1px solid #eee;}
        .muted {opacity: .8}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">Your Free AI Astrologer </div>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Enter details and receive a concise, friendly reading plus Q&A.</p>', unsafe_allow_html=True)

# -------- Birth Details Form ---------
with st.form("birth_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name", placeholder="e.g., Aisha Sharma")
        dob = st.date_input("Date of Birth", value=date(1999, 1, 1))
        place = st.text_input("Birth Place (City, Country)", placeholder="e.g., Mumbai, India")
    with col2:
        tob = st.time_input("Time of Birth", value=time(12, 0))
        tz_hint = st.text_input("Time Zone (optional)", placeholder="e.g., IST, UTC+5:30")
    colA, colB = st.columns([1,1])
    with colA:
        submitted = st.form_submit_button("Generate Reading ✨")
    with colB:
        reset_all = st.form_submit_button("New Reading ♻️")

if reset_all:
    st.session_state.qa_log = []
    st.session_state.reading = None
    st.session_state.user_info = None

if submitted:
    if not name.strip():
        st.warning("Please enter your name to personalize the reading.")
    else:
        core = build_core_reading(name, dob, tob, place)
        st.session_state.reading = core
        st.session_state.user_info = {
            "name": name, "dob": dob, "tob": tob, "place": place, "tz": tz_hint
        }
        # Reset Q&A for a fresh consultation for this user
        st.session_state.qa_log = []

# -------- Tabs ---------
reading_tab, guidance_tab, download_tab = st.tabs(["📖 Reading", "💬 Guidance", "⬇️ Download"]) 

with reading_tab:
    if st.session_state.reading is None:
        st.info("Submit your birth details above to generate your reading.")
    else:
        core = st.session_state.reading
        name = st.session_state.user_info.get("name", "Friend")
        sign = core["sign"]
        element = core["element"]

        st.markdown("---")
        st.markdown(f"### 🌟 Hello {name}! Here's your snapshot:")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"""
                <div class=\"card\">
                <b>Sun Sign:</b> {sign}  
                <b>Element:</b> {element}  
                <b>Life Path:</b> {core['life_path']}  
                <b>Traits:</b> {', '.join(core['traits'])}
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class=\"card\">
                <b>Lucky Colors:</b> {core['lucky_colors']}  
                <b>Lucky Days:</b> {core['lucky_days']}  
                <b>Affirmation:</b> “{core['affirmation']}”
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.info(core["intro"])
        st.markdown("#### ✍️ Guidance")
        st.write(
            f"As a **{sign}** influenced by **{element}**, you're encouraged to lean on your natural strengths. "
            f"Life Path **{core['life_path']}** highlights a theme of growth through alignment and steady choices."
        )
        st.caption(core["outro"])

with guidance_tab:
    if st.session_state.reading is None:
        st.warning("Please generate your reading first in the Reading tab.")
    else:
        core = st.session_state.reading
        sign, element, lp = core["sign"], core["element"], core["life_path"]

        st.markdown("---")
        st.subheader("Ask a Free-Text Question")
        q = st.text_area("Type your question (e.g., 'Will I get a promotion?')", height=120, key="q_text")
        col1, col2 = st.columns([1,1])
        with col1:
            ask = st.button("Get Guidance 🔮")
        with col2:
            clear_log = st.button("Reset this Guidance Session ♻️")

        if clear_log:
            st.session_state.qa_log = []

        if ask:
            if not q.strip():
                st.warning("Please enter a question.")
            else:
                reply, topic = answer_question(element, lp, sign, q)
                st.session_state.qa_log.append({"q": q.strip(), "a": reply, "topic": topic})
                st.success(reply)
                st.caption(f"(NLP intent detected: **{topic}**) ")

        if st.session_state.qa_log:
            st.markdown("#### Conversation History")
            for i, qa in enumerate(reversed(st.session_state.qa_log), start=1):
                st.markdown(f"**Q{i}:** {qa['q']}")
                st.markdown(f"<div class='card muted'>A{i}: {qa['a']}</div>", unsafe_allow_html=True)

with download_tab:
    if st.session_state.reading is None:
        st.info("Nothing to download yet. Generate your reading first.")
    else:
        core = st.session_state.reading
        info = st.session_state.user_info or {}
        # Build a text report
        buf = StringIO()
        buf.write("AI Astrologer Session\n")
        buf.write("======================\n\n")
        buf.write("User Details\n")
        buf.write(f"Name: {info.get('name','')}\n")
        buf.write(f"DOB: {info.get('dob','')} | TOB: {info.get('tob','')} | Place: {info.get('place','')} | TZ: {info.get('tz','')}\n\n")
        buf.write("Reading\n")
        buf.write(f"Sun Sign: {core['sign']} | Element: {core['element']} | Life Path: {core['life_path']}\n")
        buf.write(f"Traits: {', '.join(core['traits'])}\n")
        buf.write(f"Lucky Colors: {core['lucky_colors']} | Lucky Days: {core['lucky_days']}\n")
        buf.write(f"Affirmation: {core['affirmation']}\n")
        buf.write(f"Intro: {core['intro']}\n")
        buf.write(f"Outro: {core['outro']}\n\n")
        if st.session_state.qa_log:
            buf.write("Q&A\n")
            for i, qa in enumerate(st.session_state.qa_log, start=1):
                buf.write(f"Q{i}: {qa['q']}\n")
                buf.write(f"A{i}: {qa['a']}\n")
                buf.write(f"(intent: {qa['topic']})\n\n")
        content = buf.getvalue().encode("utf-8")
        st.download_button(
            label="Download Session (.txt)",
            data=content,
            file_name=f"astrology_session_{(info.get('name') or 'user').replace(' ', '_').lower()}.txt",
            mime="text/plain",
        )
        st.caption("Download includes your reading and entire Guidance conversation.")

# Footer disclaimer
st.markdown("---")
st.caption("Astrology content generated for reflection. Not medical, legal, or financial advice.")
