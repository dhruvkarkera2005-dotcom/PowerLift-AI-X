from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.components.ui import metric_card, page_header, section_header
from app.logic.competition_engine import (
    get_competitors,
    get_podium_threshold,
)
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
    page_title="Game Plan | PowerLift AI-X",
    page_icon="🏋️",
    layout="wide",
)

initialize_session_state()
apply_theme()


# ============================================================
# SIDEBAR
# ============================================================

SIDEBAR_CSS = """
<style>
section[data-testid="stSidebar"] {
    background: #070b12 !important;
    border-right: 1px solid rgba(148,163,184,.12) !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    display: none !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding-top: 2rem !important;
    padding-left: .8rem !important;
    padding-right: .8rem !important;
}

.pl-sidebar-brand {
    padding: 0 0 1.7rem 0;
    border-bottom: 1px solid rgba(148,163,184,.12);
}

.pl-brand-row {
    display: flex;
    align-items: center;
    gap: .65rem;
}

.pl-logo {
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: #ff9418;
    color: #080e17;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 950;
    flex: 0 0 auto;
}

.pl-brand-name {
    color: #ffffff;
    font-size: 17px;
    font-weight: 950;
    line-height: 1.15;
}

.pl-brand-sub {
    color: #7890b0;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 1.8px;
    line-height: 1.45;
    margin-top: .65rem;
}

.pl-sidebar-section {
    color: #7890b0;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 2.5px;
    margin: 2rem 0 1rem 0;
}

section[data-testid="stSidebar"] .stPageLink {
    margin: 0 !important;
    padding: 0 !important;
}

section[data-testid="stSidebar"] .stPageLink a {
    color: #9fb1c8 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: .58rem .72rem !important;
    margin: 0 0 .18rem 0 !important;
    border-radius: 9px !important;
    min-height: auto !important;
    line-height: 1.25 !important;
    transition: background .15s ease, color .15s ease;
}

section[data-testid="stSidebar"] .stPageLink a:hover {
    background: rgba(148,163,184,.08) !important;
    color: #ffffff !important;
}

section[data-testid="stSidebar"] .stPageLink a[aria-current="page"] {
    background: #252f3f !important;
    color: #ffffff !important;
    font-weight: 800 !important;
}

.pl-sidebar-divider {
    height: 1px;
    background: rgba(148,163,184,.12);
    margin: 1.35rem 0 1.25rem 0;
}

.pl-current-workflow {
    color: #ff9418;
    font-size: 12px;
    font-weight: 950;
    letter-spacing: 1px;
    margin-top: .7rem;
}
</style>
"""

st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

with st.sidebar:
    st.html(
        """
        <div class="pl-sidebar-brand">
            <div class="pl-brand-row">
                <span class="pl-logo">PL</span>
                <span class="pl-brand-name">PowerLift AI-X</span>
            </div>

            <div class="pl-brand-sub">
                SMARTER DATA. STRONGER LIFTS.
            </div>
        </div>

        <div class="pl-sidebar-section">
            WORKFLOW
        </div>
        """
    )

    # Session-safe Streamlit navigation.
    st.page_link("streamlit_app.py", label="Home", icon=None)
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

    st.html(
        """
        <div class="pl-sidebar-divider"></div>

        <div class="pl-sidebar-section">
            CURRENT WORKFLOW
        </div>

        <div class="pl-current-workflow">
            EXECUTE THE PLAN
        </div>
        """
    )


# ============================================================
# HELPERS
# ============================================================

def floor_25(value: float) -> float:
    return math.floor((float(value) + 1e-9) / 2.5) * 2.5


def ceil_25(value: float) -> float:
    return math.ceil((float(value) - 1e-9) / 2.5) * 2.5


def round_25(value: float) -> float:
    return math.floor(float(value) / 2.5 + 0.5) * 2.5


def safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def build_attempts(
    squat: float,
    bench: float,
    deadlift: float,
    target_total: float,
    opening_strategy: str = "Balanced",
) -> dict[str, dict[str, float | str]]:
    """Build realistic three-attempt progressions.

    The selected target is a planning objective, not a number that is
    artificially forced into the third attempts. If the target is feasible
    within the athlete's realistic progression range, the attempts move
    toward it. If it is not feasible, the plan stops at the realistic ceiling
    and the projected total shows the gap to the target.
    """

    current = {
        "Squat": max(0.0, squat),
        "Bench Press": max(0.0, bench),
        "Deadlift": max(0.0, deadlift),
    }

    strategy = str(opening_strategy or "Balanced")

    strategy_config = {
        "Conservative": {
            "opener": 0.93,
            "second": 1.00,
            "third_cap": 1.04,
        },
        "Balanced": {
            "opener": 0.95,
            "second": 1.02,
            "third_cap": 1.07,
        },
        "Aggressive": {
            "opener": 0.97,
            "second": 1.04,
            "third_cap": 1.10,
        },
    }

    config = strategy_config.get(strategy, strategy_config["Balanced"])

    opener = {
        name: min(
            round_25(value * config["opener"]),
            round_25(value),
        )
        for name, value in current.items()
    }

    second = {
        name: max(
            opener[name],
            round_25(value * config["second"]),
        )
        for name, value in current.items()
    }

    third_cap = {
        name: max(
            second[name],
            floor_25(value * config["third_cap"]),
        )
        for name, value in current.items()
    }

    current_total = sum(current.values())
    target_total_25 = ceil_25(max(target_total, current_total))
    target_increase = max(0.0, target_total_25 - current_total)

    shares = {
        name: value / current_total if current_total else 1 / 3
        for name, value in current.items()
    }

    # Start the third attempts from a proportional share of the requested
    # improvement, but never exceed the realistic third-attempt ceiling.
    third = {}
    for name in current:
        requested = current[name] + target_increase * shares[name]
        third[name] = min(
            third_cap[name],
            max(second[name], round_25(requested)),
        )

    # If the target is still feasible, use 2.5 kg increments to close the
    # remaining gap. This keeps the target useful without forcing an
    # unrealistic load onto one lift.
    while True:
        total = sum(third.values())
        remaining = target_total_25 - total

        if remaining < 2.5:
            break

        candidates = [
            name
            for name in current
            if third[name] + 2.5 <= third_cap[name] + 1e-9
        ]

        if not candidates:
            break

        # Prefer the lift with the largest remaining proportional share.
        candidates.sort(
            key=lambda name: (
                (current[name] + target_increase * shares[name]) - third[name],
                current[name],
            ),
            reverse=True,
        )

        chosen = candidates[0]
        third[chosen] += 2.5

    reasons = {}

    for name in current:
        if third[name] <= second[name]:
            reason_3 = "Protect the total"
        elif third[name] >= third_cap[name] - 1e-9:
            reason_3 = "Realistic upside ceiling"
        elif third[name] >= target_total_25 * shares[name] + current[name] - 1e-9:
            reason_3 = "Pursue the target"
        else:
            reason_3 = "Realistic upside"

        reasons[name] = reason_3

    return {
        "Squat": {
            "current": current["Squat"],
            "attempt_1": opener["Squat"],
            "attempt_2": second["Squat"],
            "attempt_3": third["Squat"],
            "reason_1": "Safe opener",
            "reason_2": "Build total",
            "reason_3": reasons["Squat"],
        },
        "Bench Press": {
            "current": current["Bench Press"],
            "attempt_1": opener["Bench Press"],
            "attempt_2": second["Bench Press"],
            "attempt_3": third["Bench Press"],
            "reason_1": "Safe opener",
            "reason_2": "Build total",
            "reason_3": reasons["Bench Press"],
        },
        "Deadlift": {
            "current": current["Deadlift"],
            "attempt_1": opener["Deadlift"],
            "attempt_2": second["Deadlift"],
            "attempt_3": third["Deadlift"],
            "reason_1": "Safe opener",
            "reason_2": "Build total",
            "reason_3": reasons["Deadlift"],
        },
    }


# ============================================================
# LOAD SHARED PLANNER / OUTLOOK STATE
# ============================================================

plan = get_planned_competition()
performance = get_performance_snapshot()

if plan is None or performance is None:
    page_header(
        "Game Plan",
        "Save a Competition Planner snapshot first. Game Plan uses that saved context.",
        eyebrow="EXECUTE THE PLAN",
    )

    st.info(
        "No active competition plan is available. "
        "Open Competition Planner, enter your performance and save the plan."
    )

    st.stop()


meet = plan.get("meet") or {}
meet_name = str(meet.get("name") or "Selected competition")
target_year = int(plan.get("target_year") or meet.get("year") or 0)
category_label = str(plan.get("category") or "Men • —")
equipment = str(plan.get("equipment") or "Classic / Raw")
goal = str(plan.get("goal") or "Podium")

weight_match = re.search(r"(\d+(?:\.\d+)?\+?\s*kg)", category_label)
weight_class = weight_match.group(1) if weight_match else str(
    plan.get("weight_class") or "—"
)

engine_category = f"Men {weight_class}"
division = str(plan.get("division") or "Open")

user_name = str(performance.get("name") or "You")
bodyweight = safe_float(performance.get("bodyweight"))
squat = safe_float(performance.get("squat"))
bench = safe_float(performance.get("bench"))
deadlift = safe_float(performance.get("deadlift"))

current_total = squat + bench + deadlift


# ============================================================
# OUTLOOK BENCHMARK
# ============================================================

threshold = None

try:
    threshold = get_podium_threshold(
        engine_category,
        str(meet.get("tier") or "National"),
        target_year,
        competition=meet_name,
        region=str(meet.get("region") or plan.get("region") or "India"),
        division=division,
        equipment=equipment,
    )
except (ValueError, KeyError, TypeError):
    threshold = None


def get_top_five_benchmark() -> float | None:
    """Return the 5th-place benchmark from the real filtered field."""
    try:
        competitors = get_competitors(
            engine_category,
            str(meet.get("tier") or "National"),
            target_year,
            competition=meet_name,
            region=str(meet.get("region") or plan.get("region") or "India"),
            division=division,
            equipment=equipment,
        )
    except (ValueError, KeyError, TypeError):
        return None

    if competitors is None or competitors.empty or "total" not in competitors.columns:
        return None

    totals = pd.to_numeric(
        competitors["total"],
        errors="coerce",
    ).dropna().sort_values(ascending=False)

    if len(totals) < 5:
        return None

    return float(totals.iloc[4])


# ============================================================
# OBJECTIVE TARGET LOGIC
# ============================================================

objective_options = [
    "Podium",
    "Top 5",
    "Beat my PR",
]

saved_goal = str(plan.get("goal") or "Podium")
initial_objective = (
    saved_goal if saved_goal in objective_options else "Podium"
)

if "game_plan_objective" not in st.session_state:
    st.session_state.game_plan_objective = initial_objective

primary_objective = st.session_state.game_plan_objective

podium_benchmark = safe_float(
    (threshold or {}).get("bronze"),
    0.0,
)
top5_benchmark = get_top_five_benchmark()

if primary_objective == "Podium":
    # Reaching the podium means meeting the 3rd-place benchmark.
    recommended_target = max(
        current_total + 2.5,
        podium_benchmark,
    ) if podium_benchmark > 0 else current_total + 2.5

elif primary_objective == "Top 5":
    # Use the actual 5th-place total from the filtered historical field.
    recommended_target = max(
        current_total + 2.5,
        top5_benchmark,
    ) if top5_benchmark is not None else current_total + 2.5

else:
    # The planner stores the athlete's current best entered performance.
    # A PR attempt therefore starts at the next valid 2.5 kg increment.
    recommended_target = current_total + 2.5

recommended_target = ceil_25(recommended_target)

# Changing the objective should recalculate the planning target instead of
# leaving the previous objective's target in session state.
last_objective = st.session_state.get("game_plan_last_objective")
if last_objective != primary_objective:
    st.session_state.game_plan_target_total = recommended_target
    st.session_state.game_plan_last_objective = primary_objective
elif "game_plan_target_total" not in st.session_state:
    st.session_state.game_plan_target_total = recommended_target

if safe_float(st.session_state.game_plan_target_total, recommended_target) < current_total:
    st.session_state.game_plan_target_total = recommended_target


# ============================================================
# HEADER
# ============================================================

page_header(
    "Game Plan",
    (
        f"Turn your competition outlook into attempt-by-attempt "
        f"decisions for {meet_name}."
    ),
    eyebrow="EXECUTE THE PLAN",
)


# ============================================================
# CONTEXT STRIP
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    metric_card("Target competition", meet_name)

with c2:
    metric_card("Year", target_year)

with c3:
    metric_card("Category", category_label)

with c4:
    metric_card(
        "Your current total",
        f"{current_total:.1f} kg",
        accent=True,
    )

st.caption(
    f"{user_name} • {bodyweight:.1f} kg bodyweight • "
    f"{equipment}"
)


# ============================================================
# COMPETITION STRATEGY
# ============================================================

st.write("")

section_header(
    "Competition strategy",
    "Set the target total and the overall approach for meet day.",
)

s1, s2, s3 = st.columns(3)

with s1:
    target_total = st.number_input(
        "Target total (kg)",
        min_value=float(ceil_25(current_total)),
        max_value=1500.0,
        value=float(
            safe_float(
                st.session_state.game_plan_target_total,
                recommended_target,
            )
        ),
        step=2.5,
        key="game_plan_target_total",
    )

with s2:
    opening_strategy = st.selectbox(
        "Opening strategy",
        [
            "Conservative",
            "Balanced",
            "Aggressive",
        ],
        index=0,
        key="game_plan_opening_strategy",
    )

with s3:
    st.selectbox(
        "Primary objective",
        objective_options,
        key="game_plan_objective",
        on_change=lambda: st.rerun(),
    )

    primary_objective = st.session_state.game_plan_objective


target_gain = max(0.0, target_total - current_total)

strategy_copy = {
    "Conservative": "Build a total with safe openers",
    "Balanced": "Balance total-building with upside",
    "Aggressive": "Push earlier for maximum upside",
}[opening_strategy]

objective_copy = {
    "Podium": "Target the podium benchmark for your category",
    "Top 5": "Target a top-five competitive position",
    "Beat my PR": "Target a new personal-best total",
}[primary_objective]

with st.container(border=True):
    st.html(
        f"""
        <div style="display:flex;justify-content:space-between;gap:2rem;
                    align-items:center;flex-wrap:wrap;">
            <div>
                <div style="color:#7890b0;font-size:10px;
                            letter-spacing:2px;font-weight:900;">
                    PLANNING TARGET
                </div>
                <div style="font-size:34px;font-weight:950;
                            color:#ff9418;margin-top:.25rem;">
                    {target_total:.1f} kg
                </div>
                <div style="color:#7890b0;margin-top:.2rem;">
                    +{target_gain:.1f} kg from current total
                </div>
            </div>

            <div style="text-align:right;min-width:260px;">
                <div style="color:#7890b0;font-size:10px;
                            letter-spacing:2px;font-weight:900;">
                    STRATEGY
                </div>
                <div style="color:white;font-size:18px;
                            font-weight:900;margin-top:.25rem;">
                    {strategy_copy}
                </div>
                <div style="color:#7890b0;margin-top:.25rem;">
                    {objective_copy}
                </div>
            </div>
        </div>
        """,
    )


# ============================================================
# ATTEMPT PLAN
# ============================================================

attempts = build_attempts(
    squat,
    bench,
    deadlift,
    target_total,
    opening_strategy,
)

st.write("")

section_header(
    "Your attempt plan",
    "Recommended attempts based on your current performance and competition analysis.",
)

st.caption(
    "Planned attempts — not guaranteed outcomes. "
    "All loads are expressed in 2.5 kg competition increments."
)


# Attempt cards
lift_columns = st.columns(3)

lift_order = [
    ("Squat", "SQUAT"),
    ("Bench Press", "BENCH PRESS"),
    ("Deadlift", "DEADLIFT"),
]

attempt_rows = []

for idx, (lift_name, display_name) in enumerate(lift_order):
    data = attempts[lift_name]

    attempts_view = [
        (1, data["attempt_1"], data["reason_1"]),
        (2, data["attempt_2"], data["reason_2"]),
        (3, data["attempt_3"], data["reason_3"]),
    ]

    cards_html = ""

    for number, load, reason in attempts_view:
        pct = (
            load / data["current"] * 100
            if data["current"] > 0
            else 0
        )

        border = (
            "rgba(255,148,24,.45)"
            if number == 3
            else "rgba(148,163,184,.10)"
        )

        cards_html += f"""
            <div style="
                margin-top:.75rem;
                padding:.85rem .9rem;
                border:1px solid {border};
                border-radius:12px;
                background:#0b121d;
            ">
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    gap:1rem;
                ">
                    <span style="
                        color:#7890b0;
                        font-size:9px;
                        font-weight:900;
                        letter-spacing:1.5px;
                    ">
                        ATTEMPT {number}
                    </span>
                    <span style="
                        color:white;
                        font-size:20px;
                        font-weight:950;
                        white-space:nowrap;
                    ">
                        {load:.1f} kg
                    </span>
                </div>
                <div style="
                    color:#d6dfeb;
                    font-size:11px;
                    margin-top:.3rem;
                ">
                    {reason}
                </div>
                <div style="
                    color:#607794;
                    font-size:10px;
                    margin-top:.25rem;
                ">
                    ~{pct:.0f}% of current
                </div>
            </div>
        """

    full_card = f"""
        <div style="
            background:#080e17;
            border:1px solid rgba(148,163,184,.15);
            border-radius:18px;
            padding:1.25rem;
        ">
            <div style="
                color:#7890b0;
                font-size:10px;
                font-weight:900;
                letter-spacing:2px;
            ">
                {display_name}
            </div>
            <div style="
                color:white;
                font-size:12px;
                margin-top:.35rem;
            ">
                Current <strong>{data["current"]:.1f} kg</strong>
            </div>
            {cards_html}
        </div>
    """

    with lift_columns[idx]:
        st.html(full_card)

    attempt_rows.append(
        {
            "Lift": lift_name,
            "Attempt 1": data["attempt_1"],
            "Attempt 2": data["attempt_2"],
            "Attempt 3": data["attempt_3"],
        }
    )


# ============================================================
# PROJECTED TOTAL
# ============================================================

planned_total = sum(
    safe_float(attempts[lift]["attempt_3"])
    for lift in ("Squat", "Bench Press", "Deadlift")
)

st.write("")

with st.container(border=True):
    pc1, pc2 = st.columns([2, 1])

    with pc1:
        st.html(
            """
            <div style="
                color:#7890b0;
                font-size:10px;
                font-weight:900;
                letter-spacing:2px;
            ">
                PROJECTED TOTAL
            </div>
            """,
        )

        st.html(
            f"""
            <div style="
                color:#ff9418;
                font-size:40px;
                font-weight:950;
                margin-top:.2rem;
            ">
                {planned_total:.1f} kg
            </div>
            <div style="color:#7890b0;">
                Based on the planned third attempts
            </div>
            """,
        )

    with pc2:
        difference = planned_total - target_total

        if abs(difference) < 0.01:
            status = "Target aligned"
            status_detail = "Third-attempt total matches the planning target."
        elif difference > 0:
            status = "Above target"
            status_detail = f"{difference:.1f} kg above the planning target."
        else:
            status = "Realistic plan below target"
            status_detail = (
                f"{abs(difference):.1f} kg remains to the target. "
                "The plan does not force unrealistic attempts."
            )

        st.html(
            f"""
            <div style="padding:1rem;border-radius:14px;
                        background:#0a111a;
                        border:1px solid rgba(148,163,184,.12);">
                <div style="color:#7890b0;font-size:10px;
                            font-weight:900;letter-spacing:1.5px;">
                    PLAN STATUS
                </div>
                <div style="color:white;font-size:20px;
                            font-weight:900;margin-top:.3rem;">
                    {status}
                </div>
                <div style="color:#7890b0;font-size:11px;
                            margin-top:.3rem;">
                    {status_detail}
                </div>
            </div>
            """,
        )


# ============================================================
# TARGET FEASIBILITY NOTE
# ============================================================

if planned_total < target_total - 0.01:
    st.info(
        f"The {target_total:.1f} kg target is a planning objective, not a forced "
        f"third-attempt total. Based on your current lifts and the selected "
        f"{opening_strategy.lower()} approach, the realistic plan projects "
        f"{planned_total:.1f} kg. The remaining {target_total - planned_total:.1f} kg "
        "should be treated as a longer-term performance gap rather than placed "
        "onto a single lift."
    )


# ============================================================
# MEET-DAY DECISION RULES
# ============================================================

st.write("")

section_header(
    "Meet-day decision rules",
    "Simple rules for adapting the plan without losing the total.",
)

r1, r2, r3 = st.columns(3)

rules = [
    (
        "01",
        "Take the opener only if warm-ups move as expected.",
    ),
    (
        "02",
        "Adjust the second attempt using bar speed, execution and the field.",
    ),
    (
        "03",
        "Protect the total on attempt three; chase more only when the second attempt is successful.",
    ),
]

for col, (number, text) in zip((r1, r2, r3), rules):
    with col:
        st.html(
            f"""
            <div style="
                background:#080e17;
                border:1px solid rgba(148,163,184,.13);
                border-radius:16px;
                padding:1.15rem;
                min-height:150px;
            ">
                <div style="color:#ff9418;font-size:10px;
                            font-weight:900;letter-spacing:2px;">
                    RULE {number}
                </div>
                <div style="color:#dbe4ef;font-size:13px;
                            line-height:1.55;margin-top:.7rem;">
                    {text}
                </div>
            </div>
            """,
        )


# ============================================================
# KEY TAKEAWAY
# ============================================================

st.write("")

with st.container(border=True):
    st.html(
        """
        <div style="color:#7890b0;font-size:10px;
                    font-weight:900;letter-spacing:2px;">
            KEY TAKEAWAY
        </div>
        """,
    )

    if threshold:
        if primary_objective == "Podium":
            relevant_threshold = podium_benchmark
        elif primary_objective == "Top 5":
            relevant_threshold = top5_benchmark or 0.0
        else:
            relevant_threshold = current_total

        if relevant_threshold > 0:
            if current_total >= relevant_threshold and primary_objective != "Beat my PR":
                takeaway = (
                    f"Your current {current_total:.1f} kg total is already "
                    f"at or above the selected {primary_objective.lower()} benchmark "
                    f"of {relevant_threshold:.1f} kg."
                )
            elif primary_objective == "Beat my PR":
                takeaway = (
                    f"Your current PR baseline is {current_total:.1f} kg. "
                    f"The first PR target is {target_total:.1f} kg."
                )
            else:
                takeaway = (
                    f"Your current total is {current_total:.1f} kg. "
                    f"The selected benchmark is {relevant_threshold:.1f} kg."
                )
        else:
            takeaway = (
                f"Your planning target is {target_total:.1f} kg, "
                f"which is +{target_gain:.1f} kg from your current total."
            )
    else:
        takeaway = (
            f"Your planning target is {target_total:.1f} kg, "
            f"which is +{target_gain:.1f} kg from your current total."
        )

    st.html(
        f"""
        <div style="color:white;font-size:24px;
                    font-weight:950;line-height:1.2;
                    margin-top:.45rem;">
            {takeaway}
        </div>
        <div style="color:#7890b0;font-size:13px;
                    line-height:1.6;margin-top:.7rem;">
            The attempt plan converts the Competition Planner baseline
            and Competition Outlook benchmarks into a meet-day structure.
        </div>
        """,
    )


# ============================================================
# DATA & TRUST
# ============================================================

st.write("")

st.html(
    """
    <div style="
        padding:1.1rem 1.25rem;
        border:1px solid rgba(35,180,130,.24);
        border-radius:16px;
        background:rgba(7,35,30,.35);
    ">
        <div style="
            color:#55e6b4;
            font-size:10px;
            font-weight:900;
            letter-spacing:2px;
        ">
            DATA & TRUST
        </div>
        <div style="
            color:#9db5ad;
            font-size:12px;
            line-height:1.65;
            margin-top:.45rem;
        ">
            These attempt selections are planning recommendations based on
            your entered performance and competition analysis. They are not
            guaranteed results. Adjust on meet day based on warm-ups, execution,
            how you feel, the competition environment and the required total
            for your objective.
        </div>
    </div>
    """
)


# ============================================================
# STORE GAME PLAN SNAPSHOT
# ============================================================

st.session_state.game_plan_snapshot = {
    "competition": meet_name,
    "target_year": target_year,
    "category": category_label,
    "equipment": equipment,
    "goal": primary_objective,
    "current_total": current_total,
    "target_total": target_total,
    "planned_total": planned_total,
    "attempts": attempts,
}
