from __future__ import annotations

from pathlib import Path
from textwrap import dedent
import sys
import base64

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.session_state import (
    initialize_session_state,
    set_performance_snapshot,
    get_performance_snapshot,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="PowerLift AI-X",
    page_icon="PL",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "onboarding_step": 1,
    "profile_complete": False,

    "profile_name": "",
    "profile_age": 21,
    "profile_gender": "Male",
    "profile_bodyweight": 0.0,
    "profile_division": "Open",
    "profile_equipment": "CLASSIC",

    "profile_squat": 0.0,
    "profile_bench": 0.0,
    "profile_deadlift": 0.0,

    "profile_experience": "Intermediate",
    "profile_goal": "Podium",

    "performance_snapshot": None,
}


initialize_session_state()

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================

def render_markdown(body: str) -> None:
    """Render custom HTML/Markdown without indentation becoming a code block."""
    cleaned = dedent(body)
    cleaned = "\n".join(line.lstrip() for line in cleaned.splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


HERO_IMAGE_PATH = PROJECT_ROOT / "powerlift_ai_x_hero_v2.png"

if not HERO_IMAGE_PATH.exists():
    HERO_IMAGE_PATH = PROJECT_ROOT / "assets" / "powerlift_ai_x_hero_v2.png"

hero_image_b64 = ""
if HERO_IMAGE_PATH.exists():
    hero_image_b64 = base64.b64encode(
        HERO_IMAGE_PATH.read_bytes()
    ).decode("utf-8")


def go_to_step(step: int) -> None:
    st.session_state.onboarding_step = step
    st.rerun()


def complete_profile() -> None:
    total = (
        float(st.session_state.profile_squat)
        + float(st.session_state.profile_bench)
        + float(st.session_state.profile_deadlift)
    )

    # Keep the onboarding profile and the shared application state
    # in sync. Other pages (Planner, Outlook and Game Plan) read
    # the shared session-state performance snapshot.
    set_performance_snapshot(
        athlete_id="USER-INPUT",
        name=st.session_state.profile_name,
        squat=float(st.session_state.profile_squat),
        bench=float(st.session_state.profile_bench),
        deadlift=float(st.session_state.profile_deadlift),
        bodyweight=float(st.session_state.profile_bodyweight),
        source="onboarding",
    )

    st.session_state.performance_snapshot = {
        "athlete_id": "USER-INPUT",
        "athlete_name": st.session_state.profile_name,
        "name": st.session_state.profile_name,
        "age": int(st.session_state.profile_age),
        "gender": st.session_state.profile_gender,
        "bodyweight": float(st.session_state.profile_bodyweight),
        "division": st.session_state.profile_division,
        "equipment": st.session_state.profile_equipment,
        "squat": float(st.session_state.profile_squat),
        "bench": float(st.session_state.profile_bench),
        "deadlift": float(st.session_state.profile_deadlift),
        "total": total,
        "experience": st.session_state.profile_experience,
        "goal": st.session_state.profile_goal,
        "source": "onboarding",
    }

    st.session_state.profile_complete = True
    st.session_state.onboarding_step = 5


def reset_profile() -> None:
    for key, value in DEFAULTS.items():
        st.session_state[key] = value

    st.rerun()


# ============================================================
# CUSTOM CSS
# ============================================================

render_markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: Arial, Helvetica, sans-serif;
}

/* ---------------------------------------------------------
   PROFESSIONAL PAGE / UI TRANSITIONS
   --------------------------------------------------------- */

/* Smooth entrance when Streamlit renders a new page. */
[data-testid="stAppViewContainer"] .main {
    animation: plPageEnter 0.38s ease-out;
}

@keyframes plPageEnter {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Keep navigation interactions subtle and responsive. */
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
    transition:
        background 0.18s ease,
        color 0.18s ease,
        border 0.18s ease,
        transform 0.18s ease !important;
}

section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
    transform: translateX(3px);
}

/* Smooth primary button interaction. */
.stButton > button {
    transition:
        transform 0.16s ease,
        box-shadow 0.16s ease,
        background 0.16s ease,
        border-color 0.16s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0);
}

/* Smooth cards when hovered. */
.pl-mini-card,
.pl-metric {
    transition:
        transform 0.18s ease,
        border-color 0.18s ease,
        box-shadow 0.18s ease;
}

.pl-mini-card:hover,
.pl-metric:hover {
    transform: translateY(-2px);
}

/* Respect users who disable motion at OS/browser level. */
@media (prefers-reduced-motion: reduce) {
    [data-testid="stAppViewContainer"] .main,
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"],
    .stButton > button,
    .pl-mini-card,
    .pl-metric {
        animation: none !important;
        transition: none !important;
        transform: none !important;
    }
}

/* Streamlit chrome: keep the application dark from the very top. */
header[data-testid="stHeader"],
header[data-testid="stHeader"] > div,
[data-testid="stHeader"] {
    background: #05080d !important;
    background-color: #05080d !important;
    box-shadow: none !important;
    border: 0 !important;
}

[data-testid="stDecoration"] {
    display: none !important;
}

[data-testid="stToolbar"] {
    background: transparent !important;
}

.stApp {
    background:
        radial-gradient(
            circle at 80% 10%,
            rgba(255, 145, 0, 0.06),
            transparent 30%
        ),
        #05080d;
}

/* ---------------------------------------------------------
   SIDEBAR
--------------------------------------------------------- */

section[data-testid="stSidebar"] {
    background: #070b11 !important;
    border-right: 1px solid rgba(148, 163, 184, 0.12) !important;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.2rem;
    background: #070b11 !important;
}

/* Hide Streamlit's automatic multipage navigation.
   PowerLift AI-X uses the custom WORKFLOW navigation below. */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    display: none !important;
}

/* ---------------------------------------------------------
   CUSTOM WORKFLOW NAVIGATION
--------------------------------------------------------- */

section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
    width: 100% !important;
    min-height: 42px !important;
    display: flex !important;
    align-items: center !important;
    padding: 0.65rem 0.75rem !important;
    margin: 0.18rem 0 !important;
    border-radius: 9px !important;
    background: transparent !important;
    color: #dbe4ef !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    transition: background .15s ease, color .15s ease, border .15s ease !important;
}

section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] span,
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p {
    color: #dbe4ef !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
    background: #111a27 !important;
    color: #ffffff !important;
}

section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover span,
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover p {
    color: #ff9418 !important;
}

section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
    background: #252f3f !important;
    border-left: 3px solid #ff9418 !important;
    padding-left: calc(0.75rem - 3px) !important;
    color: #ffffff !important;
}

section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] span,
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] p {
    color: #ffffff !important;
    font-weight: 800 !important;
}

.pl-sidebar-brand {
    padding: 1.2rem 0.5rem 1.4rem 0.5rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.12);
    margin-bottom: 1.3rem;
}

.pl-logo {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: #ff9418;
    color: #05080d;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: 15px;
    margin-right: 10px;
}

.pl-brand-name {
    color: white;
    font-size: 16px;
    font-weight: 900;
    display: inline-block;
    vertical-align: middle;
}

.pl-brand-sub {
    color: #7290b4;
    font-size: 9px;
    letter-spacing: 1.5px;
    font-weight: 700;
    margin-top: 8px;
    margin-left: 48px;
}

.pl-sidebar-section {
    color: #687d9c;
    font-size: 10px;
    letter-spacing: 1.5px;
    font-weight: 800;
    margin: 1.4rem 0 0.6rem 0.2rem;
}

/* ---------------------------------------------------------
   MAIN
--------------------------------------------------------- */

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 4rem;
    max-width: 1450px;
}

/* ---------------------------------------------------------
   HERO
--------------------------------------------------------- */

.pl-hero {
    width: 100%;
    border: 1px solid rgba(255, 148, 24, 0.32);
    border-radius: 24px;
    overflow: hidden;
    background: #03070c;
}

.pl-hero-image {
    width: 100%;
    height: 520px;
    object-fit: cover;
    object-position: center center;
    display: block;
}

.pl-hero-content {
    padding: 2.4rem 4rem 3rem 4rem;
    background:
        radial-gradient(
            circle at 80% 10%,
            rgba(255, 145, 0, 0.08),
            transparent 35%
        ),
        #03070c;
}

.pl-eyebrow {
    color: #ff9418;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 3px;
    margin-bottom: 1rem;
}

.pl-hero-title {
    color: white;
    font-size: clamp(3.5rem, 7vw, 7rem);
    line-height: 0.88;
    font-weight: 950;
    letter-spacing: -4px;
    margin: 0;
}

.pl-hero-title span {
    color: #ff9418;
}

.pl-hero-text {
    color: #d5dfeb;
    max-width: 700px;
    margin-top: 1.4rem;
    font-size: 16px;
    line-height: 1.7;
}

.pl-hero-badge {
    display: inline-block;
    margin-top: 1.3rem;
    border: 1px solid rgba(255, 148, 24, 0.5);
    border-radius: 999px;
    padding: 0.55rem 0.9rem;
    color: #ff9418;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 1.4px;
}

/* ---------------------------------------------------------
   ONBOARDING CARD
--------------------------------------------------------- */

.pl-onboarding {
    background: #080e17;
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 22px;
    padding: 2rem;
}

.pl-step-label {
    color: #ff9418;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.pl-step-title {
    color: white;
    font-size: 32px;
    font-weight: 900;
    margin-top: 0.45rem;
}

.pl-step-subtitle {
    color: #7e96b7;
    font-size: 14px;
    line-height: 1.6;
    margin-bottom: 1.4rem;
}

/* ---------------------------------------------------------
   STEPPER
--------------------------------------------------------- */

.pl-stepper {
    display: flex;
    align-items: center;
    margin-bottom: 2rem;
}

.pl-step {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #7185a1;
    font-size: 11px;
    font-weight: 800;
    white-space: nowrap;
}

.pl-step.active {
    color: #ff9418;
}

.pl-step.done {
    color: #69e6b2;
}

.pl-step-number {
    width: 29px;
    height: 29px;
    border-radius: 50%;
    border: 1px solid #33445c;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 900;
}

.pl-step.active .pl-step-number {
    background: #ff9418;
    border-color: #ff9418;
    color: #05080d;
}

.pl-step.done .pl-step-number {
    background: #17372e;
    border-color: #69e6b2;
    color: #69e6b2;
}

.pl-step-line {
    height: 1px;
    background: #2b394c;
    flex: 1;
    margin: 0 10px;
}

/* ---------------------------------------------------------
   INFO CARDS
--------------------------------------------------------- */

.pl-mini-card {
    background: #0a111c;
    border: 1px solid rgba(148, 163, 184, 0.13);
    border-radius: 16px;
    padding: 1.25rem;
    min-height: 125px;
}

.pl-mini-line {
    width: 28px;
    height: 3px;
    background: #ff9418;
    margin-bottom: 1rem;
}

.pl-mini-title {
    color: white;
    font-size: 13px;
    font-weight: 900;
}

.pl-mini-text {
    color: #7890b0;
    font-size: 11px;
    line-height: 1.55;
    margin-top: 0.4rem;
}

/* ---------------------------------------------------------
   COMPLETION
--------------------------------------------------------- */

.pl-complete {
    text-align: center;
    padding: 2rem 1rem;
}

.pl-complete-number {
    color: #ff9418;
    font-size: 68px;
    line-height: 1;
    font-weight: 950;
}

.pl-complete-title {
    color: white;
    font-size: 36px;
    font-weight: 900;
    margin-top: 0.5rem;
}

.pl-complete-text {
    color: #8298b6;
    max-width: 650px;
    margin: 0.8rem auto 1.5rem auto;
    line-height: 1.7;
}

/* ---------------------------------------------------------
   METRICS
--------------------------------------------------------- */

.pl-metric {
    background: #080e17;
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 16px;
    padding: 1.2rem;
}

.pl-metric-label {
    color: #7890b0;
    font-size: 9px;
    letter-spacing: 1.5px;
    font-weight: 900;
}

.pl-metric-value {
    color: white;
    font-size: 28px;
    font-weight: 950;
    margin-top: 0.35rem;
}

.pl-metric-value.orange {
    color: #ff9418;
}

/* ---------------------------------------------------------
   STREAMLIT INPUTS
--------------------------------------------------------- */

/* Make every form label clearly visible on the dark page. */
.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stRadio > label {
    color: #f4f7fb !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}

/* Make markdown headings bright enough against the dark background. */
.stMarkdown h1,
.stMarkdown h2,
.stMarkdown h3,
.stMarkdown h4 {
    color: #f4f7fb !important;
    opacity: 1 !important;
}

/* Give labels a little breathing room above the controls. */
.stTextInput label p,
.stNumberInput label p,
.stSelectbox label p,
.stRadio > label p {
    color: #f4f7fb !important;
    font-size: 14px !important;
    font-weight: 700 !important;
}

/* ---------------------------------------------------------
   RADIO OPTIONS
   Streamlit/BaseWeb nests radio text several levels deep.
   Force the actual option text to stay bright on the dark UI.
--------------------------------------------------------- */

.stRadio [role="radiogroup"] label,
.stRadio [role="radiogroup"] label *,
.stRadio [data-baseweb="radio"],
.stRadio [data-baseweb="radio"] *,
.stRadio [data-baseweb="radio"] label,
.stRadio [data-baseweb="radio"] label *,
.stRadio [data-baseweb="radio"] span,
.stRadio [data-baseweb="radio"] p,
.stRadio [data-baseweb="radio"] div {
    color: #eaf0f7 !important;
    opacity: 1 !important;
    font-size: 14px !important;
}

/* Keep every radio option readable, including unselected options. */
.stRadio [data-baseweb="radio"] label span {
    color: #eaf0f7 !important;
    opacity: 1 !important;
    font-weight: 500 !important;
}

/* Selected radio option. */
.stRadio [data-baseweb="radio"][aria-checked="true"] label,
.stRadio [data-baseweb="radio"][aria-checked="true"] label *,
.stRadio [data-baseweb="radio"][aria-checked="true"] span {
    color: #ffffff !important;
    opacity: 1 !important;
    font-weight: 700 !important;
}

/* Streamlit can put the option text in a paragraph container. */
.stRadio [data-baseweb="radio"] [data-testid="stMarkdownContainer"],
.stRadio [data-baseweb="radio"] [data-testid="stMarkdownContainer"] * {
    color: #eaf0f7 !important;
    opacity: 1 !important;
}

/* ---------------------------------------------------------
   RADIO GROUP LABEL
--------------------------------------------------------- */

.stRadio [data-testid="stWidgetLabel"],
.stRadio [data-testid="stWidgetLabel"] *,
.stRadio > label,
.stRadio > label * {
    color: #f4f7fb !important;
    opacity: 1 !important;
    font-weight: 700 !important;
}

/* Keep the actual controls bright and easy to read. */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {
    background: #f2f4f7 !important;
    border-radius: 10px;
    border: 1px solid #d7dde7;
}

.stNumberInput input,
.stTextInput input {
    color: #101722 !important;
    font-size: 15px !important;
    font-weight: 500 !important;
}

.stSelectbox div[data-baseweb="select"] * {
    color: #101722 !important;
    font-size: 15px !important;
}

.stRadio label {
    color: #f4f7fb !important;
}

.stButton > button {
    border-radius: 8px;
    min-height: 44px;
    font-weight: 800;
}

.stButton > button[kind="primary"] {
    background: #ff9418;
    color: #05080d;
    border: 1px solid #ff9418;
}

.stButton > button[kind="primary"]:hover {
    background: #ffab3b;
    border-color: #ffab3b;
}

</style>
""",
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    render_markdown(
        """
        <div class="pl-sidebar-brand">
            <div>
                <span class="pl-logo">PL</span>
                <span class="pl-brand-name">PowerLift AI-X</span>
            </div>
            <div class="pl-brand-sub">
                SMARTER DATA. STRONGER LIFTS.
            </div>
        </div>
        """,
    )

    render_markdown('<div class="pl-sidebar-section">WORKFLOW</div>')

    st.page_link(
        "streamlit_app.py",
        label="Home",
        icon=None,
    )

    st.page_link(
        "pages/01_Competition_Planner.py",
        label="Competition Planner",
        icon=None,
    )

    st.page_link(
        "pages/02_Competition_Outlook.py",
        label="Competition Outlook",
        icon=None,
    )

    st.page_link(
        "pages/03_Game_Plan.py",
        label="Game Plan",
        icon=None,
    )

    st.page_link(
        "pages/04_AI_Coach.py",
        label="AI Coach",
        icon=None,
    )

    render_markdown("---")

    if st.session_state.profile_complete:
        render_markdown(
            f"""
            <div style="
                padding: .8rem;
                border: 1px solid rgba(255,148,24,.18);
                border-radius: 12px;
                background:#090f18;
            ">
                <div style="
                    color:#ff9418;
                    font-size:9px;
                    letter-spacing:1.5px;
                    font-weight:900;
                ">
                    ATHLETE
                </div>

                <div style="
                    color:white;
                    font-size:15px;
                    font-weight:900;
                    margin-top:.35rem;
                ">
                    {st.session_state.profile_name}
                </div>

                <div style="
                    color:#7890b0;
                    font-size:11px;
                    margin-top:.3rem;
                ">
                    {st.session_state.profile_bodyweight:.1f} kg
                    |
                    {st.session_state.profile_division}
                </div>
            </div>
            """,
            )

        st.write("")

        if st.button("Reset Profile", use_container_width=True):
            reset_profile()


# ============================================================
# HOME
# ============================================================

# ============================================================
# LEFT SIDE — BRAND / HERO
# ============================================================

render_markdown(
    f"""
<div class="pl-hero">

<img class="pl-hero-image" src="data:image/png;base64,{hero_image_b64}" alt="PowerLift AI-X powerlifting dashboard hero">

<div class="pl-hero-content">

<div class="pl-eyebrow">
POWERLIFTING INTELLIGENCE PLATFORM
</div>

<div class="pl-hero-title">
TRAIN SMART.<br>
<span>COMPETE STRONGER.</span>
</div>

<div class="pl-hero-text">
Build your athlete profile once.
PowerLift AI-X uses your numbers, experience,
goals and competition data to create a clearer
path from training to meet day.
</div>

<div class="pl-hero-badge">
TRACK&nbsp;&nbsp;|&nbsp;&nbsp;ANALYSE&nbsp;&nbsp;|&nbsp;&nbsp;PLAN
</div>

</div>

</div>    """,
)
st.write("")

# ============================================================
# ATHLETE PROFILE — FULL WIDTH BELOW HERO
# ============================================================

current_step = st.session_state.onboarding_step

# --------------------------------------------------------
# STEPPER
# --------------------------------------------------------

step_names = [
    "Your Profile",
    "Your Strength",
    "Experience",
    "Your Goal",
    "Complete",
]

step_html = '<div class="pl-stepper">'

for i, name in enumerate(step_names, start=1):

    if i < current_step:
        status = "done"
    elif i == current_step:
        status = "active"
    else:
        status = ""

    step_html += f"""
        <div class="pl-step {status}">
            <div class="pl-step-number">{i}</div>
            <div>{name}</div>
        </div>
    """

    if i < len(step_names):
        step_html += '<div class="pl-step-line"></div>'

step_html += "</div>"

render_markdown(step_html)

# --------------------------------------------------------
# ONBOARDING CONTAINER
# --------------------------------------------------------

# ========================================================
# STEP 1 — PROFILE
# ========================================================

if current_step == 1:

    render_markdown(
        '<div class="pl-step-label">ATHLETE PROFILE</div>',
        )

    render_markdown(
        "## Let's get to know you.",
    )

    render_markdown(
        """
        <div class="pl-step-subtitle">
            Start with the basics. You can update these later.
        </div>
        """,
        )

    name = st.text_input(
        "Your Name",
        value=st.session_state.profile_name,
        placeholder="Enter your name",
    )

    c1, c2 = st.columns(2)

    with c1:
        age = st.number_input(
            "Age",
            min_value=10,
            max_value=80,
            value=int(st.session_state.profile_age),
            step=1,
        )

    with c2:
        bodyweight = st.number_input(
            "Bodyweight (kg)",
            min_value=0.0,
            max_value=300.0,
            value=float(st.session_state.profile_bodyweight),
            step=0.5,
        )

    c1, c2 = st.columns(2)

    with c1:
        gender = st.selectbox(
            "Gender",
            ["Male", "Female"],
            index=0 if st.session_state.profile_gender == "Male" else 1,
        )

    with c2:
        division_options = [
            "Sub Junior",
            "Junior",
            "Open",
            "Master 1",
            "Master 2",
            "Master 3",
            "Master 4",
        ]

        division = st.selectbox(
            "Division",
            division_options,
            index=(
                division_options.index(st.session_state.profile_division)
                if st.session_state.profile_division in division_options
                else 2
            ),
        )

    equipment = st.selectbox(
        "Equipment",
        ["CLASSIC", "EQUIPPED"],
        index=(
            0
            if st.session_state.profile_equipment == "CLASSIC"
            else 1
        ),
    )

    if st.button(
        "Continue",
        type="primary",
        use_container_width=True,
    ):

        if not name.strip():
            st.error("Please enter your name.")
        elif bodyweight <= 0:
            st.error("Please enter your bodyweight.")
        else:
            st.session_state.profile_name = name.strip()
            st.session_state.profile_age = age
            st.session_state.profile_gender = gender
            st.session_state.profile_bodyweight = bodyweight
            st.session_state.profile_division = division
            st.session_state.profile_equipment = equipment

            go_to_step(2)

# ========================================================
# STEP 2 — STRENGTH
# ========================================================

elif current_step == 2:

    render_markdown(
        '<div class="pl-step-label">YOUR STRENGTH</div>',
        )

    render_markdown(
        "## How strong are you right now?",
    )

    render_markdown(
        """
        <div class="pl-step-subtitle">
            Enter your current competition-level PRs.
            These numbers become your baseline.
        </div>
        """,
        )

    squat = st.number_input(
        "Squat PR (kg)",
        min_value=0.0,
        max_value=500.0,
        value=float(st.session_state.profile_squat),
        step=2.5,
    )

    bench = st.number_input(
        "Bench Press PR (kg)",
        min_value=0.0,
        max_value=400.0,
        value=float(st.session_state.profile_bench),
        step=2.5,
    )

    deadlift = st.number_input(
        "Deadlift PR (kg)",
        min_value=0.0,
        max_value=500.0,
        value=float(st.session_state.profile_deadlift),
        step=2.5,
    )

    total = squat + bench + deadlift

    render_markdown(
        f"""
        <div class="pl-metric" style="margin-top:1rem;">
            <div class="pl-metric-label">CURRENT TOTAL</div>
            <div class="pl-metric-value orange">
                {total:.1f} kg
            </div>
        </div>
        """,
        )

    st.write("")

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "Back",
            use_container_width=True,
        ):
            go_to_step(1)

    with c2:
        if st.button(
            "Continue",
            type="primary",
            use_container_width=True,
        ):

            if squat <= 0 or bench <= 0 or deadlift <= 0:
                st.error(
                    "Please enter your squat, bench and deadlift PRs."
                )
            else:
                st.session_state.profile_squat = squat
                st.session_state.profile_bench = bench
                st.session_state.profile_deadlift = deadlift

                go_to_step(3)

# ========================================================
# STEP 3 — EXPERIENCE
# ========================================================

elif current_step == 3:

    render_markdown(
        '<div class="pl-step-label">EXPERIENCE</div>',
        )

    render_markdown(
        "## How experienced are you?",
    )

    render_markdown(
        """
        <div class="pl-step-subtitle">
            This helps PowerLift AI-X understand your
            competitive context.
        </div>
        """,
        )

    experience = st.radio(
        "Choose your current level",
        [
            "Beginner",
            "Intermediate",
            "Advanced",
            "Competitive",
        ],
        index=[
            "Beginner",
            "Intermediate",
            "Advanced",
            "Competitive",
        ].index(st.session_state.profile_experience),
    )

    descriptions = {
        "Beginner":
            "You are building your foundation and learning the competition process.",
        "Intermediate":
            "You have consistent training experience and are developing your competition total.",
        "Advanced":
            "You have substantial strength and structured competition experience.",
        "Competitive":
            "You regularly compete and are focused on maximizing meet-day performance.",
    }

    render_markdown(
        f"""
        <div class="pl-mini-card" style="margin-top:1rem;">
            <div class="pl-mini-line"></div>
            <div class="pl-mini-title">{experience.upper()}</div>
            <div class="pl-mini-text">
                {descriptions[experience]}
            </div>
        </div>
        """,
        )

    st.write("")

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "Back",
            use_container_width=True,
        ):
            go_to_step(2)

    with c2:
        if st.button(
            "Continue",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.profile_experience = experience
            go_to_step(4)

# ========================================================
# STEP 4 — GOAL
# ========================================================

elif current_step == 4:

    render_markdown(
        '<div class="pl-step-label">YOUR GOAL</div>',
        )

    render_markdown(
        "## What are you training for?",
    )

    render_markdown(
        """
        <div class="pl-step-subtitle">
            Your goal determines how PowerLift AI-X interprets
            competition benchmarks and builds your game plan.
        </div>
        """,
        )

    goal_options = [
        "Podium",
        "Top 5",
        "Beat my PR",
    ]

    goal = st.radio(
        "Primary goal",
        goal_options,
        index=(
            goal_options.index(st.session_state.profile_goal)
            if st.session_state.profile_goal in goal_options
            else 0
        ),
    )

    goal_description = {
        "Podium":
            "Build the plan around the podium benchmark for your target category.",
        "Top 5":
            "Use the top-five field benchmark as the primary competition target.",
        "Beat my PR":
            "Focus on creating a new personal best total.",
    }

    render_markdown(
        f"""
        <div class="pl-mini-card" style="margin-top:1rem;">
            <div class="pl-mini-line"></div>
            <div class="pl-mini-title">{goal.upper()}</div>
            <div class="pl-mini-text">
                {goal_description[goal]}
            </div>
        </div>
        """,
        )

    st.write("")

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "Back",
            use_container_width=True,
        ):
            go_to_step(3)

    with c2:
        if st.button(
            "Build My Profile",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.profile_goal = goal
            complete_profile()
            st.rerun()

# ========================================================
# STEP 5 — COMPLETE
# ========================================================

elif current_step == 5:

    total = (
        st.session_state.profile_squat
        + st.session_state.profile_bench
        + st.session_state.profile_deadlift
    )

    render_markdown(
        """
        <div class="pl-complete">

            <div class="pl-complete-number">
                05
            </div>

            <div class="pl-complete-title">
                Profile ready.
            </div>

            <div class="pl-complete-text">
                Your athlete profile is now the starting point
                for Competition Planner, Competition Outlook
                and Game Plan.
            </div>

        </div>
        """,
        )

    c1, c2, c3 = st.columns(3)

    with c1:
        render_markdown(
            f"""
            <div class="pl-metric">
                <div class="pl-metric-label">BODYWEIGHT</div>
                <div class="pl-metric-value">
                    {st.session_state.profile_bodyweight:.1f} kg
                </div>
            </div>
            """,
                )

    with c2:
        render_markdown(
            f"""
            <div class="pl-metric">
                <div class="pl-metric-label">CURRENT TOTAL</div>
                <div class="pl-metric-value orange">
                    {total:.1f} kg
                </div>
            </div>
            """,
                )

    with c3:
        render_markdown(
            f"""
            <div class="pl-metric">
                <div class="pl-metric-label">GOAL</div>
                <div class="pl-metric-value">
                    {st.session_state.profile_goal}
                </div>
            </div>
            """,
                )

    st.write("")

    st.success(
        "Profile saved. Your numbers are ready for Competition Planner."
    )

    if st.button(
        "Open Competition Planner",
        type="primary",
        use_container_width=True,
    ):
        st.switch_page("pages/01_Competition_Planner.py")


# ============================================================
# FOOTER
# ============================================================

render_markdown(
    """
    <div style="
        margin-top:3rem;
        padding-top:1.2rem;
        border-top:1px solid rgba(148,163,184,.10);
        color:#536b8a;
        font-size:10px;
        letter-spacing:1.4px;
        text-align:center;
    ">
        POWERLIFT AI-X
        &nbsp;&nbsp;|&nbsp;&nbsp;
        DATA
        &nbsp;&nbsp;|&nbsp;&nbsp;
        PREDICT
        &nbsp;&nbsp;|&nbsp;&nbsp;
        COMPARE
        &nbsp;&nbsp;|&nbsp;&nbsp;
        PLAN
    </div>
    """,
)