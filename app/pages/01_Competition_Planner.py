from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.components.ui import (
    page_header,
    section_header,
)

from app.logic.competition_data import (
    DIVISIONS,
    EQUIPMENT,
    PLANNING_YEARS,
    get_competitions,
)

from app.services.session_state import (
    get_performance_snapshot,
    get_planned_competition,
    initialize_session_state,
    set_performance_snapshot,
    set_planned_competition,
)

from app.styles.theme import apply_theme


# ============================================================
# WEIGHT CLASS LOGIC
# ============================================================

def get_weight_class_from_bodyweight(bodyweight: float) -> str:
    """Map the athlete's bodyweight to the men's weight class."""
    bodyweight = float(bodyweight)

    if bodyweight <= 53:
        return "53 kg"
    if bodyweight <= 59:
        return "59 kg"
    if bodyweight <= 66:
        return "66 kg"
    if bodyweight <= 74:
        return "74 kg"
    if bodyweight <= 83:
        return "83 kg"
    if bodyweight <= 93:
        return "93 kg"
    if bodyweight <= 105:
        return "105 kg"
    if bodyweight <= 120:
        return "120 kg"
    return "120+ kg"


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Competition Planner | PowerLift AI-X",
    page_icon="🏋️",
    layout="wide",
)

initialize_session_state()
apply_theme()


# ============================================================
# SIDEBAR HELPERS
# ============================================================

def esc(value) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def nav_link(path: str, label: str, active: bool = False) -> None:
    """Session-safe sidebar navigation using Streamlit page links."""
    st.page_link(path, label=label, icon=None)


# ============================================================
# SIDEBAR
# ============================================================

st.markdown(
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

        /* Session-safe Streamlit page links. */
        section[data-testid="stSidebar"] .stPageLink {
            margin:.18rem 0 !important;
            padding:0 !important;
        }

        section[data-testid="stSidebar"] .stPageLink a {
            display:block !important;
            padding:.68rem .72rem !important;
            color:#a9bfd9 !important;
            text-decoration:none !important;
            font-size:14px !important;
            font-weight:600 !important;
            border-radius:9px !important;
            min-height:auto !important;
        }

        section[data-testid="stSidebar"] .stPageLink a:hover {
            background:#111a27 !important;
            color:#ffffff !important;
        }

        section[data-testid="stSidebar"] .stPageLink a[aria-current="page"] {
            background:#252f3f !important;
            color:#ffffff !important;
            font-weight:800 !important;
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
    </style>
    """,
    unsafe_allow_html=True,
)


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

    nav_link("streamlit_app.py", "Home")
    nav_link(
        "pages/01_Competition_Planner.py",
        "Competition Planner",
    )
    nav_link(
        "pages/02_Competition_Outlook.py",
        "Competition Outlook",
    )
    nav_link(
        "pages/03_Game_Plan.py",
        "Game Plan",
    )
    nav_link(
        "pages/04_AI_Coach.py",
        "AI Coach",
    )

    st.html(
        """
        <div class="pl-sidebar-divider"></div>

        <div class="pl-sidebar-section">
            CURRENT WORKFLOW
        </div>

        <div class="pl-current-workflow">
            PLAN YOUR ATTACK
        </div>
        """
    )


# ============================================================
# HEADER
# ============================================================

page_header(
    "Competition Planner",
    "Enter your current performance, choose your target competition, and let PowerLift AI-X build your competitive outlook.",
    eyebrow="PLAN YOUR ATTACK",
)


# ============================================================
# CURRENT PERFORMANCE
# ============================================================

section_header(
    "My Performance",
    "Enter your current competition numbers. These values will drive your AI prediction and competition analysis.",
)

existing_performance = get_performance_snapshot() or {}


# ------------------------------------------------------------
# Name
# ------------------------------------------------------------

name = st.text_input(
    "Your name",
    value=str(existing_performance.get("name") or ""),
    placeholder="Enter your name",
)


# ------------------------------------------------------------
# Performance inputs
# ------------------------------------------------------------

performance_col1, performance_col2, performance_col3, performance_col4 = (
    st.columns(4)
)


with performance_col1:
    bodyweight = st.number_input(
        "Bodyweight (kg)",
        min_value=30.0,
        max_value=200.0,
        value=float(
            existing_performance.get("bodyweight")
            if existing_performance.get("bodyweight") is not None
            else 83.0
        ),
        step=0.1,
    )


with performance_col2:
    squat = st.number_input(
        "Squat (kg)",
        min_value=0.0,
        max_value=500.0,
        value=float(
            existing_performance.get("squat")
            if existing_performance.get("squat") is not None
            else 0.0
        ),
        step=2.5,
    )


with performance_col3:
    bench = st.number_input(
        "Bench Press (kg)",
        min_value=0.0,
        max_value=400.0,
        value=float(
            existing_performance.get("bench")
            if existing_performance.get("bench") is not None
            else 0.0
        ),
        step=2.5,
    )


with performance_col4:
    deadlift = st.number_input(
        "Deadlift (kg)",
        min_value=0.0,
        max_value=500.0,
        value=float(
            existing_performance.get("deadlift")
            if existing_performance.get("deadlift") is not None
            else 0.0
        ),
        step=2.5,
    )


# ============================================================
# CURRENT TOTAL
# ============================================================

current_total = squat + bench + deadlift


# Load the currently saved competition plan before any controls
# that use it (circuit, year, division, equipment, objective).
existing = get_planned_competition()


st.markdown(
    f"""
    <div class="plx-card" style="margin-top:1rem">
        <div class="plx-card-title">CURRENT TOTAL</div>
        <div class="plx-card-value">{current_total:.1f} kg</div>
        <div class="plx-card-body">
            Squat {squat:.1f} kg
            &nbsp;•&nbsp;
            Bench {bench:.1f} kg
            &nbsp;•&nbsp;
            Deadlift {deadlift:.1f} kg
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# COMPETITION
# ============================================================

section_header(
    "Competition",
    "Choose the competition circuit you want PowerLift AI-X to analyse.",
)


circuit_map = {
    "Nationals": ("Nationals", "India"),
    "East India": ("Regional", "East India"),
    "West India": ("Regional", "West India"),
    "North India": ("Regional", "North India"),
    "South India": ("Regional", "South India"),
}


current_circuit = "Nationals"


if existing:
    current_region = existing.get("region")

    if current_region in {
        "East India",
        "West India",
        "North India",
        "South India",
    }:
        current_circuit = current_region


circuit = st.selectbox(
    "Competition circuit",
    options=tuple(circuit_map),
    index=tuple(circuit_map).index(current_circuit),
)


competition_type, region = circuit_map[circuit]


competition_options = get_competitions(
    competition_type=competition_type,
    region=region,
)


if competition_options.empty:
    st.error(
        "No competition data is available for this circuit."
    )
    st.stop()


competition_name = st.selectbox(
    "Meet",
    options=competition_options["name"].tolist(),
)


selected_meet = competition_options.loc[
    competition_options["name"] == competition_name
].iloc[0].to_dict()


# ============================================================
# TARGET YEAR
# ============================================================

section_header(
    "Target",
    "Choose the season you want the competitive model to analyse.",
)


default_year = 2027


if existing and existing.get("target_year") in PLANNING_YEARS:
    default_year = int(existing["target_year"])


year = st.selectbox(
    "Target year",
    options=PLANNING_YEARS,
    index=PLANNING_YEARS.index(default_year),
    help=(
        "2026 is the current data year. "
        "Later years are planning targets and will use "
        "analytical projections where required."
    ),
)


# ============================================================
# LIFTER CATEGORY
# ============================================================

section_header(
    "Lifter Category",
    "Set the division, weight class and equipment standard used for the analysis.",
)


col1, col2, col3 = st.columns(3)


# ------------------------------------------------------------
# Division
# ------------------------------------------------------------

with col1:
    division = st.selectbox(
        "Division",
        options=DIVISIONS,
        index=(
            DIVISIONS.index(existing.get("division", "Open"))
            if existing
            and existing.get("division") in DIVISIONS
            else 2
        ),
    )


# ------------------------------------------------------------
# Weight class
# ------------------------------------------------------------

with col2:
    # Weight class is automatically derived from the athlete's
    # entered bodyweight so the entire workflow uses one category.
    weight_class = get_weight_class_from_bodyweight(bodyweight)

    st.text_input(
        "Weight class",
        value=weight_class,
        disabled=True,
        help="Automatically determined from your bodyweight.",
    )


# ------------------------------------------------------------
# Equipment
# ------------------------------------------------------------

with col3:
    equipment = st.selectbox(
        "Equipment",
        options=EQUIPMENT,
        index=(
            EQUIPMENT.index(existing.get("equipment"))
            if existing
            and existing.get("equipment") in EQUIPMENT
            else 0
        ),
        format_func=lambda value: (
            "Classic / Raw"
            if value == "CLASSIC"
            else "Equipped"
        ),
    )


# ============================================================
# OBJECTIVE
# ============================================================

section_header(
    "Objective",
    "Pick the outcome that should drive the analysis.",
)


goal_options = (
    "Podium",
    "Top 5",
    "Beat my PR",
)


goal = st.radio(
    "Primary objective",
    options=goal_options,
    index=(
        goal_options.index(existing.get("goal"))
        if existing
        and existing.get("goal") in goal_options
        else 0
    ),
    horizontal=True,
    label_visibility="collapsed",
)


# ============================================================
# SAVE
# ============================================================

st.write("")


save = st.button(
    "Save performance & competition plan  →",
    type="primary",
    use_container_width=True,
)


if save:

    # --------------------------------------------------------
    # Validate name
    # --------------------------------------------------------

    if not name.strip():
        st.error(
            "Please enter your name."
        )
        st.stop()


    # --------------------------------------------------------
    # Validate bodyweight
    # --------------------------------------------------------

    if bodyweight <= 0:
        st.error(
            "Please enter a valid bodyweight."
        )
        st.stop()


    # --------------------------------------------------------
    # Validate lifts
    # --------------------------------------------------------

    if squat <= 0:
        st.error(
            "Please enter a valid Squat."
        )
        st.stop()


    if bench <= 0:
        st.error(
            "Please enter a valid Bench Press."
        )
        st.stop()


    if deadlift <= 0:
        st.error(
            "Please enter a valid Deadlift."
        )
        st.stop()


    # --------------------------------------------------------
    # Save user performance
    # --------------------------------------------------------

    set_performance_snapshot(
        athlete_id="USER-INPUT",
        name=name.strip(),
        squat=squat,
        bench=bench,
        deadlift=deadlift,
        bodyweight=bodyweight,
        source="manual",
        competition=selected_meet["name"],
        year=year,
    )


    # --------------------------------------------------------
    # Save competition plan
    # --------------------------------------------------------

    meet = {
        "name": selected_meet["name"],
        "competition_type": selected_meet["competition_type"],
        "region": selected_meet["region"],
        "tier": selected_meet["tier"],
        "year": year,
    }


    category = f"{division} • {weight_class}"


    set_planned_competition(
        meet=meet,
        category=category,
        weight_class=weight_class,
        goal=goal,
        region=region,
        division=division,
        equipment=equipment,
    )


    st.success(
        "Performance and competition plan saved."
    )


    st.rerun()


# ============================================================
# ACTIVE PLAN
# ============================================================

existing = get_planned_competition()


if existing:
    meet = existing["meet"]

    # Render the active plan as a real PowerLift AI-X card.
    # This avoids Streamlit's plain-text fallback and keeps the
    # saved plan visually consistent with the current-total card.
    active_category = existing.get("category") or "—"
    active_equipment = existing.get("equipment") or "—"
    active_goal = existing.get("goal") or "—"
    active_year = meet.get("year") or existing.get("target_year") or "—"

    st.html(
        f'''
        <div class="plx-card" style="
            margin-top:1.15rem;
            margin-bottom:1.2rem;
            padding:1.35rem 1.45rem;
            border:1px solid rgba(255,148,24,.34);
            border-radius:18px;
            background:linear-gradient(
                135deg,
                rgba(10,17,27,.98),
                rgba(8,13,21,.98)
            );
            box-shadow:0 10px 30px rgba(0,0,0,.16);
        ">

            <div style="
                color:#ff9418;
                font-size:.70rem;
                letter-spacing:1.8px;
                font-weight:900;
                margin-bottom:.45rem;
            ">
                ACTIVE COMPETITION PLAN
            </div>

            <div style="
                color:#f5f7fb;
                font-size:1.55rem;
                line-height:1.2;
                font-weight:900;
                margin-bottom:1.05rem;
            ">
                {meet["name"]}
            </div>

            <div style="
                display:grid;
                grid-template-columns:repeat(4,minmax(0,1fr));
                gap:.8rem;
            ">

                <div style="
                    padding:.9rem 1rem;
                    border:1px solid rgba(148,163,184,.16);
                    border-radius:12px;
                    background:#0c1520;
                ">
                    <div style="
                        color:#6f8fb8;
                        font-size:.62rem;
                        letter-spacing:1.4px;
                        font-weight:900;
                        margin-bottom:.35rem;
                    ">
                        CATEGORY
                    </div>
                    <div style="
                        color:#f4f7fb;
                        font-size:1rem;
                        font-weight:800;
                    ">
                        {active_category}
                    </div>
                </div>

                <div style="
                    padding:.9rem 1rem;
                    border:1px solid rgba(148,163,184,.16);
                    border-radius:12px;
                    background:#0c1520;
                ">
                    <div style="
                        color:#6f8fb8;
                        font-size:.62rem;
                        letter-spacing:1.4px;
                        font-weight:900;
                        margin-bottom:.35rem;
                    ">
                        EQUIPMENT
                    </div>
                    <div style="
                        color:#f4f7fb;
                        font-size:1rem;
                        font-weight:800;
                    ">
                        {active_equipment}
                    </div>
                </div>

                <div style="
                    padding:.9rem 1rem;
                    border:1px solid rgba(148,163,184,.16);
                    border-radius:12px;
                    background:#0c1520;
                ">
                    <div style="
                        color:#6f8fb8;
                        font-size:.62rem;
                        letter-spacing:1.4px;
                        font-weight:900;
                        margin-bottom:.35rem;
                    ">
                        TARGET YEAR
                    </div>
                    <div style="
                        color:#ff9418;
                        font-size:1rem;
                        font-weight:900;
                    ">
                        {active_year}
                    </div>
                </div>

                <div style="
                    padding:.9rem 1rem;
                    border:1px solid rgba(148,163,184,.16);
                    border-radius:12px;
                    background:#0c1520;
                ">
                    <div style="
                        color:#6f8fb8;
                        font-size:.62rem;
                        letter-spacing:1.4px;
                        font-weight:900;
                        margin-bottom:.35rem;
                    ">
                        GOAL
                    </div>
                    <div style="
                        color:#f4f7fb;
                        font-size:1rem;
                        font-weight:800;
                    ">
                        {active_goal}
                    </div>
                </div>

            </div>
        </div>
        '''
    )




# ============================================================
# DATA TRUST NOTE
# ============================================================

st.markdown(
    '<div class="plx-card" style="margin-top:1.2rem">'
    '<div class="plx-card-title">DATA STATUS</div>'
    '<div class="plx-card-body">'
    'Your current performance is entered manually and stored '
    'as the baseline for AI analysis. '
    'Historical competition data is used separately to analyse '
    'the competitive field. Future competition fields are '
    'analytical projections and are not confirmed entry lists.'
    '</div></div>',
    unsafe_allow_html=True,
)