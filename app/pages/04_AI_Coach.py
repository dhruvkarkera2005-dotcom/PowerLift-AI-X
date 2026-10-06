from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.session_state import (
    get_performance_snapshot,
    get_planned_competition,
    initialize_session_state,
)
from app.styles.theme import apply_theme


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="AI Coach | PowerLift AI-X",
    page_icon="🧠",
    layout="wide",
)

initialize_session_state()
apply_theme()


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def esc(value) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def kg(value: float) -> str:
    return f"{value:.1f} kg"


def ceil_25(value: float) -> float:
    return math.ceil((float(value) - 1e-9) / 2.5) * 2.5


def get_weight_class(category: str, fallback: str = "—") -> str:
    match = re.search(r"(\d+(?:\.\d+)?\+?\s*kg)", str(category))
    return match.group(1) if match else fallback


def nav_link(path: str, label: str, active: bool = False) -> None:
    active_class = " pl-nav-active" if active else ""
    st.html(
        f"""
        <div class="pl-nav-wrap{active_class}">
            <a href="{path}" target="_self">{esc(label)}</a>
        </div>
        """
    )


def coach_signal(title: str, value: str, detail: str, kind: str = "blue"):
    st.html(
        f"""
        <div class="coach-signal {kind}">
            <div class="coach-signal-title">{esc(title)}</div>
            <div class="coach-signal-value">{esc(value)}</div>
            <div class="coach-signal-detail">{esc(detail)}</div>
        </div>
        """
    )


# ============================================================
# SIDEBAR
# ============================================================

st.html(
    """
    <style>
        /* Hide Streamlit's automatic multipage navigation. */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            display: none !important;
        }

        section[data-testid="stSidebar"] {
            background: #070b11 !important;
            border-right: 1px solid rgba(148,163,184,.12);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.15rem;
        }

        .pl-sidebar-brand {
            padding: .45rem .2rem 1.25rem .2rem;
            border-bottom: 1px solid rgba(148,163,184,.12);
            margin-bottom: 1.15rem;
        }

        .pl-brand-row {
            display:flex;
            align-items:center;
        }

        .pl-logo {
            width:40px;
            height:40px;
            border-radius:11px;
            background:#ff9418;
            color:#05080d;
            display:inline-flex;
            align-items:center;
            justify-content:center;
            font-weight:900;
            font-size:15px;
            margin-right:10px;
        }

        .pl-brand-name {
            color:#ffffff !important;
            font-size:16px;
            font-weight:900;
        }

        .pl-brand-sub {
            color:#7890b0 !important;
            font-size:9px;
            letter-spacing:1.5px;
            font-weight:800;
            margin-top:7px;
            margin-left:50px;
        }

        .pl-sidebar-section {
            color:#7890b0 !important;
            font-size:10px;
            letter-spacing:1.8px;
            font-weight:900;
            margin:.3rem 0 .65rem .15rem;
        }

        .pl-nav-wrap {
            margin:.18rem 0;
            border-radius:9px;
        }

        .pl-nav-wrap a {
            display:block;
            padding:.68rem .72rem;
            color:#a9bfd9 !important;
            text-decoration:none !important;
            font-size:14px;
            font-weight:600;
            border-radius:9px;
        }

        .pl-nav-wrap a:hover {
            background:#111a27;
            color:#ffffff !important;
        }

        .pl-nav-active a {
            background:#252f3f;
            color:#ffffff !important;
            font-weight:800;
        }

        .pl-sidebar-divider {
            height:1px;
            background:rgba(148,163,184,.10);
            margin:1.25rem 0;
        }

        .pl-current-workflow {
            color:#ff9418 !important;
            font-size:10px;
            letter-spacing:1.3px;
            font-weight:900;
            line-height:1.5;
        }

        /* ====================================================
           PAGE
        ==================================================== */

        .coach-page {
            max-width:1500px;
            margin:0 auto;
            padding:.4rem 0 4rem;
        }

        .coach-hero {
            position:relative;
            overflow:hidden;
            border:1px solid rgba(255,148,24,.28);
            border-radius:22px;
            padding:2rem 2.2rem;
            margin:.4rem 0 2rem;
            background:
                radial-gradient(circle at 90% 15%, rgba(255,148,24,.11), transparent 28%),
                linear-gradient(135deg,#0a111b 0%,#080d14 62%,#100d09 100%);
            box-shadow:0 20px 60px rgba(0,0,0,.22);
        }

        .coach-kicker {
            color:#69a9ff;
            font-size:10px;
            letter-spacing:2px;
            font-weight:900;
            margin-bottom:.65rem;
        }

        .coach-hero-title {
            color:#f5f7fb;
            font-size:clamp(2rem,4vw,3.4rem);
            line-height:1.03;
            font-weight:900;
            letter-spacing:-1.5px;
            margin-bottom:.7rem;
        }

        .coach-hero-title span {
            color:#ff9418;
        }

        .coach-hero-copy {
            color:#8ca9cb;
            font-size:1rem;
            line-height:1.65;
            max-width:760px;
        }

        .coach-badge {
            display:inline-block;
            margin-top:1rem;
            padding:.48rem .75rem;
            border:1px solid rgba(255,148,24,.32);
            border-radius:999px;
            background:rgba(255,148,24,.07);
            color:#ffad45;
            font-size:10px;
            letter-spacing:1.4px;
            font-weight:900;
        }

        .coach-section {
            margin:2.1rem 0 .9rem;
        }

        .coach-eyebrow {
            color:#69a9ff;
            font-size:10px;
            letter-spacing:2px;
            font-weight:900;
            margin-bottom:.45rem;
        }

        .coach-title {
            color:#f5f7fb;
            font-size:1.65rem;
            font-weight:900;
            letter-spacing:-.4px;
        }

        .coach-copy {
            color:#7897bd;
            line-height:1.55;
            margin-top:.4rem;
        }

        .coach-read {
            border:1px solid rgba(255,148,24,.28);
            border-radius:18px;
            padding:1.45rem 1.55rem;
            background:
                radial-gradient(circle at 92% 0%,rgba(255,148,24,.08),transparent 28%),
                #09111b;
        }

        .coach-read-label {
            color:#ff9418;
            font-size:10px;
            letter-spacing:1.7px;
            font-weight:900;
            margin-bottom:.65rem;
        }

        .coach-read-title {
            color:#f7f9fc;
            font-size:1.35rem;
            font-weight:900;
            margin-bottom:.55rem;
        }

        .coach-read-copy {
            color:#9ab3d0;
            line-height:1.65;
        }

        .coach-signal {
            min-height:145px;
            padding:1.05rem 1.1rem;
            border-radius:15px;
            border:1px solid rgba(148,163,184,.14);
            background:#09111b;
        }

        .coach-signal.orange {
            border-color:rgba(255,148,24,.28);
        }

        .coach-signal.green {
            border-color:rgba(82,190,130,.25);
        }

        .coach-signal.blue {
            border-color:rgba(105,169,255,.22);
        }

        .coach-signal-title {
            color:#6f8fb8;
            font-size:9px;
            letter-spacing:1.5px;
            font-weight:900;
            margin-bottom:.5rem;
        }

        .coach-signal-value {
            color:#f4f7fb;
            font-size:1.35rem;
            font-weight:900;
            margin-bottom:.35rem;
        }

        .coach-signal-detail {
            color:#7f9bbd;
            font-size:.86rem;
            line-height:1.45;
        }

        .coach-lift {
            border:1px solid rgba(148,163,184,.14);
            border-radius:17px;
            padding:1.2rem;
            background:#09111b;
            height:100%;
        }

        .coach-lift-head {
            display:flex;
            justify-content:space-between;
            gap:1rem;
            align-items:flex-start;
            margin-bottom:.8rem;
        }

        .coach-lift-name {
            color:#f4f7fb;
            font-size:1.05rem;
            font-weight:900;
        }

        .coach-lift-base {
            color:#7897bd;
            font-size:.78rem;
            margin-top:.25rem;
        }

        .coach-lift-pill {
            padding:.38rem .55rem;
            border-radius:999px;
            border:1px solid rgba(255,148,24,.25);
            color:#ffab3f;
            background:rgba(255,148,24,.06);
            font-size:9px;
            letter-spacing:1px;
            font-weight:900;
            white-space:nowrap;
        }

        .coach-attempt {
            display:flex;
            justify-content:space-between;
            gap:1rem;
            align-items:center;
            padding:.7rem .75rem;
            margin-top:.5rem;
            border-radius:10px;
            background:#0c1520;
            border:1px solid rgba(148,163,184,.10);
        }

        .coach-attempt-label {
            color:#7897bd;
            font-size:.75rem;
            font-weight:700;
        }

        .coach-attempt-value {
            color:#f4f7fb;
            font-size:1rem;
            font-weight:900;
        }

        .coach-rule {
            border-left:3px solid #ff9418;
            border-radius:0 12px 12px 0;
            padding:.9rem 1rem;
            margin:.6rem 0;
            background:#09111b;
            border-top:1px solid rgba(148,163,184,.09);
            border-right:1px solid rgba(148,163,184,.09);
            border-bottom:1px solid rgba(148,163,184,.09);
        }

        .coach-rule strong {
            color:#f4f7fb;
        }

        .coach-rule span {
            color:#89a5c7;
        }

        .coach-ask {
            border:1px solid rgba(105,169,255,.20);
            border-radius:18px;
            padding:1.3rem;
            background:#09111b;
        }

        .coach-answer {
            margin-top:1rem;
            padding:1.05rem 1.15rem;
            border-radius:13px;
            border:1px solid rgba(255,148,24,.20);
            background:#0c1520;
        }

        .coach-answer-label {
            color:#ff9418;
            font-size:9px;
            letter-spacing:1.5px;
            font-weight:900;
            margin-bottom:.45rem;
        }

        .coach-answer-text {
            color:#d9e4f0;
            line-height:1.65;
        }

        .coach-trust {
            margin-top:1.4rem;
            padding:1rem 1.1rem;
            border-radius:12px;
            background:#080e16;
            border:1px solid rgba(148,163,184,.10);
            color:#718aa8;
            font-size:.78rem;
            line-height:1.55;
        }

        @media (max-width: 900px) {
            .coach-hero {
                padding:1.4rem;
            }
        }
    </style>
    """
)


with st.sidebar:
    st.html(
        """
        <div class="pl-sidebar-brand">
            <div class="pl-brand-row">
                <span class="pl-logo">PL</span>
                <span class="pl-brand-name">PowerLift AI-X</span>
            </div>
            <div class="pl-brand-sub">SMARTER DATA. STRONGER LIFTS.</div>
        </div>

        <div class="pl-sidebar-section">WORKFLOW</div>
        """
    )

    nav_link("streamlit_app.py", "Home")
    nav_link("pages/01_Competition_Planner.py", "Competition Planner")
    nav_link("pages/02_Competition_Outlook.py", "Competition Outlook")
    nav_link("pages/03_Game_Plan.py", "Game Plan")
    nav_link("pages/04_AI_Coach.py", "AI Coach", active=True)

    st.html(
        """
        <div class="pl-sidebar-divider"></div>

        <div class="pl-sidebar-section">CURRENT WORKFLOW</div>
        <div class="pl-current-workflow">
            COACH ME THROUGH THE MEET
        </div>
        """
    )


# ============================================================
# LOAD SHARED STATE
# ============================================================

plan = get_planned_competition()
performance = get_performance_snapshot()
game_plan = st.session_state.get("game_plan_snapshot")

if plan is None or performance is None:
    st.html(
        """
        <div class="coach-page">
            <div class="coach-hero">
                <div class="coach-kicker">04 · AI COACH</div>
                <div class="coach-hero-title">
                    Build your profile <span>first.</span>
                </div>
                <div class="coach-hero-copy">
                    AI Coach uses your Competition Planner, Competition Outlook
                    and Game Plan context. Save an active competition plan first,
                    then return here for meet-specific coaching.
                </div>
            </div>
        </div>
        """
    )
    st.stop()


meet = plan.get("meet") or {}

meet_name = str(meet.get("name") or "Selected competition")
target_year = int(plan.get("target_year") or meet.get("year") or 0)
category = str(plan.get("category") or "Men • —")
equipment = str(plan.get("equipment") or "Classic / Raw")
goal = str(plan.get("goal") or "Podium")

user_name = str(performance.get("name") or "You")
bodyweight = safe_float(performance.get("bodyweight"))
squat = safe_float(performance.get("squat"))
bench = safe_float(performance.get("bench"))
deadlift = safe_float(performance.get("deadlift"))

current_total = squat + bench + deadlift

weight_class = get_weight_class(category)

if game_plan:
    target_total = safe_float(
        game_plan.get("target_total"),
        current_total,
    )
    planned_total = safe_float(
        game_plan.get("planned_total"),
        target_total,
    )
    attempts = game_plan.get("attempts") or {}
    strategy = str(
        st.session_state.get(
            "game_plan_opening_strategy",
            "Balanced",
        )
    )
else:
    target_total = current_total
    planned_total = current_total
    attempts = {}
    strategy = "Balanced"

gap = max(0.0, target_total - current_total)


# ============================================================
# COACHING INTERPRETATION
# ============================================================

if current_total <= 0:
    overall_read = (
        "Your performance baseline is incomplete. Enter valid squat, bench "
        "and deadlift numbers in Competition Planner before relying on this coach."
    )
elif gap <= 0:
    overall_read = (
        "Your current baseline already meets the selected planning target. "
        "The coaching priority is execution, attempt selection and protecting the total."
    )
elif gap <= 25:
    overall_read = (
        "The target is relatively close to your current total. "
        "Your priority should be a high-confidence opener and disciplined second attempts."
    )
elif gap <= 60:
    overall_read = (
        "There is a meaningful gap to the target. "
        "The meet-day plan should protect the total first, then use successful attempts "
        "to build toward the target."
    )
else:
    overall_read = (
        "The target requires a substantial increase from the current baseline. "
        "Treat the selected target as a planning objective, not a guaranteed meet result, "
        "and prioritize successful attempts."
    )


lift_data = []

for lift_name, baseline in (
    ("Squat", squat),
    ("Bench Press", bench),
    ("Deadlift", deadlift),
):
    data = attempts.get(lift_name) or {}
    a1 = safe_float(data.get("attempt_1"), baseline)
    a2 = safe_float(data.get("attempt_2"), baseline)
    a3 = safe_float(data.get("attempt_3"), baseline)

    lift_data.append(
        {
            "name": lift_name,
            "baseline": baseline,
            "a1": a1,
            "a2": a2,
            "a3": a3,
        }
    )

# Identify the lift with the largest planned third-attempt increase.
focus_lift = max(
    lift_data,
    key=lambda x: x["a3"] - x["baseline"],
)

# Identify the lift with the smallest planned increase.
stable_lift = min(
    lift_data,
    key=lambda x: x["a3"] - x["baseline"],
)


# ============================================================
# HERO
# ============================================================

st.html(
    f"""
    <div class="coach-page">

        <div class="coach-hero">
            <div class="coach-kicker">04 · AI COACH</div>

            <div class="coach-hero-title">
                Coach me through <span>{esc(meet_name)}</span>.
            </div>

            <div class="coach-hero-copy">
                A meet-specific coaching layer built from your saved athlete profile,
                competition context and Game Plan. The coach explains the plan —
                it does not replace your judgment on the platform.
            </div>

            <div class="coach-badge">
                {esc(category)} &nbsp;·&nbsp; {esc(equipment)} &nbsp;·&nbsp; {target_year}
            </div>
        </div>

        <div class="coach-section">
            <div class="coach-eyebrow">01 · COACH'S READ</div>
            <div class="coach-title">Here's what matters right now.</div>
        </div>

        <div class="coach-read">
            <div class="coach-read-label">MEET-DAY READ</div>
            <div class="coach-read-title">
                {esc(user_name)}, protect the total first.
            </div>
            <div class="coach-read-copy">
                {esc(overall_read)}
            </div>
        </div>
    </div>
    """
)


# ============================================================
# SIGNAL CARDS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    coach_signal(
        "CURRENT TOTAL",
        kg(current_total),
        f"{kg(target_total - current_total)} to the selected target"
        if target_total > current_total
        else "Target already covered",
        "blue",
    )

with c2:
    coach_signal(
        "PLANNING TARGET",
        kg(target_total),
        f"{goal} objective",
        "orange",
    )

with c3:
    coach_signal(
        "PLANNED TOTAL",
        kg(planned_total),
        f"{strategy} opening strategy",
        "green",
    )

with c4:
    coach_signal(
        "COACH FOCUS",
        focus_lift["name"],
        "Largest planned contribution toward the target",
        "orange",
    )


# ============================================================
# MEET-DAY PLAYBOOK
# ============================================================

st.html(
    """
    <div class="coach-page">
        <div class="coach-section">
            <div class="coach-eyebrow">02 · MEET-DAY PLAYBOOK</div>
            <div class="coach-title">Coach the decisions, not the numbers.</div>
            <div class="coach-copy">
                Your Game Plan already contains the attempt loads. AI Coach focuses
                on how to execute, react and make decisions when the meet starts.
            </div>
        </div>
    </div>
    """
)

# Build context-specific guidance from the saved plan without duplicating
# the nine attempt numbers from Game Plan.
if gap <= 25:
    target_guidance = (
        "The target is relatively close. Once the first two lifts are moving well, "
        "you can use the final attempts to pursue it without compromising a valid total."
    )
elif gap <= 60:
    target_guidance = (
        "There is a meaningful gap to the target. Treat it as an objective, not a "
        "requirement. Let successful attempts earn the right to push later."
    )
else:
    target_guidance = (
        "The target is substantially above the current baseline. Protect the total "
        "first and let meet-day execution determine how far you push."
    )

playbook = [
    (
        "BEFORE THE MEET",
        "Arrive with the plan settled.",
        "Keep warm-ups familiar, confirm your opener with your coach, and avoid "
        "last-minute changes simply because another athlete posts a bigger number.",
    ),
    (
        "AFTER A SUCCESSFUL OPENER",
        "Build confidence, then build the total.",
        "If the opener moves as expected, stay disciplined. Use the second attempt "
        "to establish a strong total rather than spending energy proving something early.",
    ),
    (
        "AFTER A MISSED OPENER",
        "Reset before you chase.",
        "Identify the reason for the miss. Re-establish a successful lift before "
        "thinking about the original progression or the target.",
    ),
    (
        "AFTER A STRONG SECOND",
        "Earn the right to push.",
        "A strong second attempt gives you more information. Use bar speed, execution, "
        "fatigue and the competition situation to decide how ambitious the final attempt should be.",
    ),
    (
        "AFTER A DIFFICULT SECOND",
        "Protect the total.",
        "Do not force the planned third attempt automatically. Reassess the lift, "
        "your energy and what is required from the competition before committing.",
    ),
    (
        "THIRD ATTEMPT",
        "Make the decision from the platform.",
        f"{target_guidance} The final number should reflect what you have actually shown that day.",
    ),
]

for label, title, detail in playbook:
    st.html(
        f"""
        <div class="coach-page">
            <div class="coach-rule">
                <strong>{esc(label)} · {esc(title)}</strong>
                <span>{esc(detail)}</span>
            </div>
        </div>
        """
    )


# ============================================================
# COACH PRIORITIES
# ============================================================

st.html(
    """
    <div class="coach-page">
        <div class="coach-section">
            <div class="coach-eyebrow">03 · COACH PRIORITIES</div>
            <div class="coach-title">Three things to keep in your head.</div>
        </div>
    </div>
    """
)

p1, p2, p3 = st.columns(3)

with p1:
    st.html(
        """
        <div class="coach-signal blue">
            <div class="coach-signal-title">01 · PROTECT THE TOTAL</div>
            <div class="coach-signal-value">Get on the board.</div>
            <div class="coach-signal-detail">
                Successful attempts come before chasing a number. A strong total
                gives you more freedom later in the meet.
            </div>
        </div>
        """
    )

with p2:
    st.html(
        """
        <div class="coach-signal orange">
            <div class="coach-signal-title">02 · READ THE LIFT</div>
            <div class="coach-signal-value">Let execution speak.</div>
            <div class="coach-signal-detail">
                Use how the bar moved, your warm-ups, technique and fatigue as
                information before changing the plan.
            </div>
        </div>
        """
    )

with p3:
    st.html(
        """
        <div class="coach-signal green">
            <div class="coach-signal-title">03 · USE THE SITUATION</div>
            <div class="coach-signal-value">Adapt when needed.</div>
            <div class="coach-signal-detail">
                Your current total, remaining energy and competition situation
                matter more than blindly following a spreadsheet.
            </div>
        </div>
        """
    )


# ============================================================
# COACH'S CHECKLIST
# ============================================================

st.html(
    """
    <div class="coach-page">
        <div class="coach-section">
            <div class="coach-eyebrow">04 · QUICK CHECKLIST</div>
            <div class="coach-title">Before you call the next attempt.</div>
        </div>

        <div class="coach-rule">
            <strong>Did the previous attempt move well?</strong>
            <span> If yes, progression may make sense. If no, reassess before increasing.</span>
        </div>

        <div class="coach-rule">
            <strong>Do you have a successful total?</strong>
            <span> If not, prioritize getting one before taking unnecessary risks.</span>
        </div>

        <div class="coach-rule">
            <strong>Has the competition situation changed?</strong>
            <span> Your final decision can respond to what the meet actually requires.</span>
        </div>

        <div class="coach-rule">
            <strong>Are you trying to force the original plan?</strong>
            <span> The Game Plan is a starting point, not a command.</span>
        </div>
    </div>
    """
)


# ============================================================
# ASK YOUR COACH
# ============================================================

st.html(
    """
    <div class="coach-page">
        <div class="coach-section">
            <div class="coach-eyebrow">04 · ASK YOUR COACH</div>
            <div class="coach-title">Get a quick answer from your plan.</div>
            <div class="coach-copy">
                Choose a question below. The response is generated from your
                current saved PowerLift AI-X context.
            </div>
        </div>
    </div>
    """
)

questions = [
    "What should I focus on most?",
    "What if I miss my opener?",
    "Should I chase the target?",
    "How should I approach my second attempts?",
    "How should I approach my third attempts?",
    "How do I protect my total?",
    "What should I remember on meet day?",
]

question = st.selectbox(
    "Coach question",
    questions,
    label_visibility="collapsed",
)

if question == "What should I focus on most?":
    answer = (
        f"Focus on {focus_lift['name']} as the largest planned contributor, "
        f"but don't sacrifice successful attempts on the other two lifts. "
        f"Your current total is {current_total:.1f} kg and the selected target is "
        f"{target_total:.1f} kg."
    )

elif question == "What if I miss my opener?":
    answer = (
        "Don't treat the miss as a reason to chase the plan. First identify why "
        "the attempt failed, then use the next attempt to secure a valid lift. "
        "The priority becomes building a total rather than forcing the original progression."
    )

elif question == "Should I chase the target?":
    if gap <= 25:
        answer = (
            "The target is relatively close to your current baseline. If the first "
            "two attempts are successful and moving well, the third attempt can be "
            "used to pursue the target. The decision should still be based on execution."
        )
    elif gap <= 60:
        answer = (
            "The target is meaningfully above your current baseline. Treat it as the "
            "planning objective, not a guaranteed outcome. Build a total first and "
            "only chase the target if the earlier attempts support it."
        )
    else:
        answer = (
            "The target is substantially above your current baseline. Protect the "
            "total and use the meet to execute successfully. Don't turn the final "
            "attempt into a forced number simply because it appears in the plan."
        )

elif question == "How should I approach my second attempts?":
    answer = (
        "Use the second attempt to build the total while collecting information. "
        "If the opener was clean and the second moves well, you earn more freedom "
        "for the final attempt. If it is difficult, reassess rather than forcing "
        "the original progression."
    )

elif question == "How should I approach my third attempts?":
    answer = (
        "Treat the third attempt as a decision, not a number you are obligated to take. "
        "Use the quality of the second attempt, fatigue, warm-ups, your current total "
        "and the competition situation to choose the final load."
    )

elif question == "How do I protect my total?":
    answer = (
        "Protect the total by prioritizing successful attempts. After a miss, "
        "re-establish a valid lift instead of automatically increasing. A successful "
        "total gives you more options than forcing an ambitious number."
    )

else:
    answer = (
        "Remember three things: make the opener, build the total, and make the "
        "third-attempt decision from what is actually happening on the platform. "
        "Your Game Plan is a guide — meet-day execution is the final input."
    )

st.html(
    f"""
    <div class="coach-page">
        <div class="coach-ask">
            <div class="coach-answer">
                <div class="coach-answer-label">AI COACH RESPONSE</div>
                <div class="coach-answer-text">
                    {esc(answer)}
                </div>
            </div>

            <div class="coach-trust">
                <strong>Data basis:</strong>
                Athlete profile + active competition plan + saved Game Plan.
                Coaching guidance is informational and should be adjusted using
                warm-ups, execution, competition conditions and meet-day judgment.
            </div>
        </div>
    </div>
    """
)
