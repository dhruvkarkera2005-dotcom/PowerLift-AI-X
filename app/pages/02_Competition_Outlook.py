from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.logic.competition_engine import (
    get_competitors,
    get_gap_analysis,
    get_podium_threshold,
)
from app.services.ai_prediction_service import AIPredictionService
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
    page_title="Competition Outlook | PowerLift AI-X",
    page_icon="📊",
    layout="wide",
)
initialize_session_state()
apply_theme()


# ============================================================
# UI HELPERS
# ============================================================

def esc(value) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card(label: str, value: str, sub: str = "", accent: bool = False, cls: str = ""):
    accent_cls = " accent" if accent else ""
    st.markdown(
        f"""
        <div class="out-card {accent_cls} {cls}">
            <div class="out-label">{esc(label)}</div>
            <div class="out-value">{esc(value)}</div>
            {f'<div class="out-sub">{esc(sub)}</div>' if sub else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(eyebrow: str, title: str, description: str = ""):
    st.markdown(
        f"""
        <div class="out-section">
            <div class="out-eyebrow">{esc(eyebrow)}</div>
            <div class="out-title">{esc(title)}</div>
            {f'<div class="out-description">{esc(description)}</div>' if description else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str, kind: str = "blue"):
    st.markdown(
        f'<span class="out-pill {kind}">●&nbsp; {esc(text)}</span>',
        unsafe_allow_html=True,
    )


def format_gap(gap: float) -> str:
    return "Target reached" if gap <= 0 else f"+{gap:.1f} kg needed"


# ============================================================
# PREMIUM OUTLOOK STYLES
# ============================================================

st.markdown(
    """
    <style>
        /* Hide Streamlit's automatic multipage navigation.
           PowerLift AI-X uses the custom workflow navigation below. */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            display: none !important;
        }


    .stApp {
        background:
            radial-gradient(circle at 88% 0%, rgba(255,148,24,.055), transparent 27%),
            #05080d !important;
    }

    [data-testid="stHeader"] {
        background: #05080d !important;
        box-shadow: none !important;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.25rem;
        padding-bottom: 4rem;
    }

    section[data-testid="stSidebar"] {
        background: #070b11 !important;
        border-right: 1px solid rgba(148,163,184,.12);
    }

    .out-hero {
        border: 1px solid rgba(255,148,24,.30);
        border-radius: 22px;
        padding: 28px 32px;
        margin: 8px 0 28px;
        background:
            radial-gradient(circle at 88% 20%, rgba(255,148,24,.10), transparent 32%),
            linear-gradient(135deg, #0a111b 0%, #080d14 60%, #0d0c0a 100%);
        box-shadow: 0 20px 55px rgba(0,0,0,.22);
    }

    .out-hero-top { display:flex; justify-content:space-between; gap:24px; align-items:flex-start; }
    .out-kicker, .out-eyebrow, .out-label {
        color:#69a9ff;
        font-size:10px;
        letter-spacing:2px;
        font-weight:900;
        text-transform:uppercase;
    }
    .out-kicker { color:#ff9418; }
    .out-hero-title { color:#f7f9fc; font-size:42px; line-height:1.02; font-weight:950; margin-top:8px; }
    .out-hero-title span { color:#ff9418; }
    .out-hero-copy { color:#89a3c4; font-size:15px; line-height:1.65; max-width:850px; margin-top:12px; }
    .out-hero-badge {
        border:1px solid rgba(55,230,164,.25); background:rgba(55,230,164,.06);
        color:#49e7b0; border-radius:999px; padding:9px 13px; font-size:10px;
        font-weight:900; letter-spacing:1.2px; white-space:nowrap;
    }

    .out-section { margin: 30px 0 13px; }
    .out-title { color:#f4f7fb; font-size:25px; font-weight:900; margin-top:5px; letter-spacing:-.4px; }
    .out-description { color:#7892b3; font-size:14px; margin-top:5px; line-height:1.5; }

    .out-card {
        min-height:92px; box-sizing:border-box; border:1px solid rgba(117,145,177,.17);
        border-radius:16px; padding:18px 19px; background:linear-gradient(145deg,#0b131e,#080e16);
        box-shadow:0 10px 30px rgba(0,0,0,.10);
    }
    .out-card.accent { border-color:rgba(255,148,24,.34); background:linear-gradient(145deg,#10151c,#120e08); }
    .out-value { color:#f4f7fb; font-size:27px; font-weight:950; margin-top:6px; line-height:1.1; }
    .out-card.accent .out-value { color:#ff9d24; }
    .out-sub { color:#7189a9; font-size:11px; margin-top:7px; }

    .out-podium {
        border-radius:18px; border:1px solid rgba(117,145,177,.16); background:#090f17;
        padding:19px; min-height:118px;
    }
    .out-podium.gold { border-color:rgba(255,193,7,.30); }
    .out-podium.silver { border-color:rgba(190,205,220,.25); }
    .out-podium.bronze { border-color:rgba(205,127,50,.30); }
    .out-podium-name { color:#8299b8; font-size:10px; font-weight:900; letter-spacing:1.8px; }
    .out-podium-value { color:#f4f7fb; font-size:30px; font-weight:950; margin-top:7px; }
    .out-podium-gap { color:#7189a9; font-size:11px; margin-top:7px; }

    .out-callout {
        border:1px solid rgba(105,169,255,.18); background:#07111f; border-radius:16px;
        padding:17px 19px; color:#93aed0; line-height:1.6; font-size:13px;
    }
    .out-callout strong { color:#f3f7fb; }
    .out-callout.success { border-color:rgba(55,230,164,.22); background:#071411; }
    .out-callout.orange { border-color:rgba(255,148,24,.24); background:#120d07; }

    .out-rank {
        display:flex; align-items:center; justify-content:space-between; gap:16px;
        border:1px solid rgba(255,148,24,.20); border-radius:18px; padding:19px 22px;
        background:linear-gradient(90deg,#0b121b,#0b0e12);
    }
    .out-rank-number { color:#ff9418; font-size:42px; font-weight:950; line-height:1; }
    .out-rank-label { color:#7992b1; font-size:10px; letter-spacing:1.7px; font-weight:900; }
    .out-rank-copy { color:#8fa6c3; font-size:12px; }

    .out-trust {
        border:1px solid rgba(55,230,164,.20); background:#06120f; border-radius:17px;
        padding:17px 20px; color:#82b6a8; font-size:11px; line-height:1.7;
    }
    .out-trust b { color:#55e6b1; letter-spacing:1.5px; font-size:10px; }

    .out-table-wrap { border:1px solid rgba(117,145,177,.14); border-radius:17px; overflow:hidden; background:#080e16; }
    .out-table { width:100%; border-collapse:collapse; font-size:12px; }
    .out-table th { text-align:left; color:#6f88a8; font-size:9px; letter-spacing:1.2px; text-transform:uppercase; padding:13px 14px; background:#0b131d; border-bottom:1px solid rgba(117,145,177,.12); }
    .out-table td { color:#dbe5f1; padding:12px 14px; border-bottom:1px solid rgba(117,145,177,.08); }
    .out-table tr:last-child td { border-bottom:0; }
    .out-table .you td { background:rgba(255,148,24,.055); color:#fff; font-weight:800; }
    .out-table .rank { color:#8aa1be; width:55px; }
    .out-table .orange { color:#ff9b20; font-weight:900; }
    .out-table .muted { color:#6f819a; }

    .stDataFrame { border-radius:16px; overflow:hidden; }
    div[data-testid="stMetric"] { background:#080e16; border:1px solid rgba(117,145,177,.14); border-radius:16px; padding:12px 16px; }
    div[data-testid="stMetricLabel"] { color:#7890b0 !important; }
    div[data-testid="stMetricValue"] { color:#f5f8fc !important; }

    @media (max-width: 900px) {
        .out-hero-title { font-size:32px; }
        .out-hero-top { flex-direction:column; }
        .out-hero-badge { white-space:normal; }
    }
    .out-table-wrap table tbody tr:hover td { background: rgba(255,148,24,.045); }

    /* ========================================================
       POWERLIFT AI-X CUSTOM SIDEBAR
       ======================================================== */
    section[data-testid="stSidebar"] > div {
        padding-top: 78px !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding: 0 26px 30px !important;
    }

    .pl-sidebar-brand {
        padding: 0 4px 26px;
        border-bottom: 1px solid rgba(148,163,184,.10);
        margin-bottom: 28px;
    }

    .pl-sidebar-brand-row {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .pl-sidebar-logo {
        width: 48px;
        height: 48px;
        border-radius: 13px;
        background: #ff9418;
        color: #05080d;
        font-weight: 950;
        font-size: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 48px;
    }

    .pl-sidebar-name {
        color: #f7f9fc;
        font-size: 17px;
        line-height: 1.1;
        font-weight: 950;
    }

    .pl-sidebar-tagline {
        color: #617995;
        font-size: 9px;
        line-height: 1.65;
        letter-spacing: 1.45px;
        font-weight: 800;
        margin-top: 7px;
        max-width: 175px;
    }

    .pl-sidebar-section {
        color: #5f7898;
        font-size: 9px;
        letter-spacing: 1.8px;
        font-weight: 900;
        margin: 0 4px 10px;
    }

    section[data-testid="stSidebar"] [data-testid="stPageLink"] {
        margin: 0 0 10px !important;
        padding: 0 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a {
        display: flex !important;
        align-items: center !important;
        min-height: 42px !important;
        padding: 0 12px !important;
        border-radius: 9px !important;
        color: #89a6c8 !important;
        background: transparent !important;
        text-decoration: none !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        transition: background .15s ease, color .15s ease;
    }

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
        color: #dbe8f7 !important;
        background: rgba(148,163,184,.07) !important;
    }

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
        color: #dce8f7 !important;
        background: rgba(148,163,184,.10) !important;
    }

    .pl-sidebar-current {
        margin: 48px 0 0;
        padding-top: 27px;
        border-top: 1px solid rgba(148,163,184,.10);
    }

    .pl-sidebar-current-label {
        color: #5f7898;
        font-size: 9px;
        letter-spacing: 1.8px;
        font-weight: 900;
        margin-bottom: 10px;
    }

    .pl-sidebar-current-value {
        color: #ff9418;
        font-size: 13px;
        letter-spacing: .25px;
        font-weight: 950;
    }
</style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="pl-sidebar-brand">
            <div class="pl-sidebar-brand-row">
                <div class="pl-sidebar-logo">PL</div>
                <div>
                    <div class="pl-sidebar-name">PowerLift AI-X</div>
                    <div class="pl-sidebar-tagline">SMARTER DATA. STRONGER LIFTS.</div>
                </div>
            </div>
        </div>

        <div class="pl-sidebar-section">WORKFLOW</div>
        """,
        unsafe_allow_html=True,
    )

    st.page_link("streamlit_app.py", label="Home")
    st.page_link("pages/01_Competition_Planner.py", label="Competition Planner")
    st.page_link("pages/02_Competition_Outlook.py", label="Competition Outlook")
    st.page_link("pages/03_Game_Plan.py", label="Game Plan")
    st.page_link("pages/04_AI_Coach.py", label="AI Coach")

    st.markdown(
        """
        <div class="pl-sidebar-current">
            <div class="pl-sidebar-current-label">CURRENT WORKFLOW</div>
            <div class="pl-sidebar-current-value">KNOW THE FIELD</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LOAD PLAN / PERFORMANCE
# ============================================================

plan = get_planned_competition()
performance = get_performance_snapshot()

if plan is None:
    st.markdown(
        '<div class="out-hero"><div class="out-kicker">KNOW THE FIELD</div><div class="out-hero-title">Competition <span>Outlook</span></div><div class="out-hero-copy">Save a competition plan first. This page will then turn your plan into a competitive field, podium thresholds and performance outlook.</div></div>',
        unsafe_allow_html=True,
    )
    st.info("Open Competition Planner, enter your performance, choose your competition and save the plan.")
    st.stop()

if performance is None:
    st.markdown(
        '<div class="out-hero"><div class="out-kicker">KNOW THE FIELD</div><div class="out-hero-title">Competition <span>Outlook</span></div><div class="out-hero-copy">Enter your current performance first so PowerLift AI-X can compare your numbers with the competitive field.</div></div>',
        unsafe_allow_html=True,
    )
    st.warning("No performance data is available. Return to Competition Planner and enter your bodyweight, Squat, Bench and Deadlift.")
    st.stop()


# ============================================================
# CONTEXT
# ============================================================

meet = plan["meet"]
category_label = str(plan.get("category") or "")
match = re.search(r"(\d+\+?\s*kg)", category_label)
if not match:
    st.error("The active plan has no valid weight class.")
    st.stop()

weight_class = match.group(1)
engine_category = f"Men {weight_class}"
target_year = int(plan.get("target_year") or meet.get("year"))
meet_tier = str(meet.get("tier") or "")
division = str(plan.get("division") or "Open")
equipment = str(plan.get("equipment") or "CLASSIC").upper()

user_name = str(performance.get("name") or "You")
user_bodyweight = float(performance["bodyweight"])
user_squat = float(performance["squat"])
user_bench = float(performance["bench"])
user_deadlift = float(performance["deadlift"])
user_total = user_squat + user_bench + user_deadlift


# ============================================================
# HEADER
# ============================================================

st.markdown(
    f"""
    <div class="out-hero">
        <div class="out-hero-top">
            <div>
                <div class="out-kicker">KNOW THE FIELD</div>
                <div class="out-hero-title">Competition <span>Outlook</span></div>
                <div class="out-hero-copy">See where <b style="color:#dce8f5">{esc(user_name)}</b> stands against the analytical competitive field for the <b style="color:#dce8f5">{esc(meet['name'])}</b> in {target_year}.</div>
            </div>
            <div class="out-hero-badge">HISTORICAL DATA + CONDITIONAL PROJECTIONS</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONTEXT STRIP
# ============================================================

cols = st.columns([1.5, .8, 1, 1])
with cols[0]:
    card("Target competition", str(meet["name"]), str(meet.get("region") or ""))
with cols[1]:
    card("Target year", str(target_year), "Planning target")
with cols[2]:
    card("Category", category_label, str(plan.get("equipment") or ""))
with cols[3]:
    card("Your total", f"{user_total:.1f} kg", "Current baseline", accent=True)


# ============================================================
# YOUR PERFORMANCE
# ============================================================

section("CURRENT BASELINE", "Your performance", "The numbers entered in Competition Planner and used as the current benchmark.")
pcols = st.columns(5)
for col, label, value, accent in [
    (pcols[0], "Bodyweight", f"{user_bodyweight:.1f} kg", False),
    (pcols[1], "Squat", f"{user_squat:.1f} kg", False),
    (pcols[2], "Bench", f"{user_bench:.1f} kg", False),
    (pcols[3], "Deadlift", f"{user_deadlift:.1f} kg", False),
    (pcols[4], "Current total", f"{user_total:.1f} kg", True),
]:
    with col:
        card(label, value, accent=accent)


# ============================================================
# AI PREDICTION
# ============================================================

ai_prediction = None
ai_prediction_error = None
performance_athlete_id = str(performance.get("athlete_id") or "").strip()

if performance_athlete_id and performance_athlete_id != "USER-INPUT":
    try:
        ai_prediction = AIPredictionService().predict(
            athlete_id=performance_athlete_id,
            target_year=target_year,
            division=str(plan.get("division") or "Men"),
            weight_class=weight_class,
            equipment=str(plan.get("equipment") or "Classic"),
        )
    except (ValueError, KeyError, TypeError) as exc:
        ai_prediction_error = str(exc)

section("AI PERFORMANCE OUTLOOK", "Projected performance", "Model-based projection for the selected competition year.")

if ai_prediction is not None:
    predictions = ai_prediction["predictions"]
    ai_squat = float(predictions["future_best_squat"])
    ai_bench = float(predictions["future_best_bench"])
    ai_deadlift = float(predictions["future_best_deadlift"])
    ai_total = float(predictions["future_total"])

    acols = st.columns(4)
    for col, label, value, accent in [
        (acols[0], "AI Squat", ai_squat, False),
        (acols[1], "AI Bench", ai_bench, False),
        (acols[2], "AI Deadlift", ai_deadlift, False),
        (acols[3], "AI projected total", ai_total, True),
    ]:
        with col:
            card(label, f"{value:.1f} kg", "Model projection", accent=accent)
    st.caption("AI projection uses the athlete's linked historical competition records and the trained PowerLift-AI-X temporal model.")
elif performance_athlete_id == "USER-INPUT":
    st.markdown('<div class="out-callout">ℹ️ <strong>AI projection unavailable for this profile.</strong> Your performance was entered manually without linking a historical PowerLift-AI-X athlete.</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="out-callout">⚠️ <strong>AI projection unavailable.</strong> {esc(ai_prediction_error or "Insufficient historical data for a production prediction.")}</div>', unsafe_allow_html=True)


# ============================================================
# COMPETITIVE FIELD
# ============================================================

try:
    competitors = get_competitors(
        engine_category,
        meet_tier,
        target_year,
        competition=str(meet["name"]),
        region=str(meet.get("region") or ""),
        division=division,
        equipment=equipment,
    )

    threshold = get_podium_threshold(
        engine_category,
        meet_tier,
        target_year,
        competition=str(meet["name"]),
        region=str(meet.get("region") or ""),
        division=division,
        equipment=equipment,
    )

except Exception as exc:
    st.error("Competition Outlook failed while building the competition field.")
    st.exception(exc)
    st.stop()

field = competitors.copy()
field["total_kg"] = pd.to_numeric(field["total_kg"], errors="coerce")
field = field.dropna(subset=["total_kg"]).copy()


# ============================================================
# PODIUM LINE
# ============================================================

section("PODIUM TARGETS", "The podium line", "Projected totals required to reach the gold, silver and bronze thresholds.")

bronze = float(threshold["bronze"])
silver = float(threshold["silver"])
gold = float(threshold["gold"])

pc = st.columns(3)
for col, name, value, kind in [
    (pc[0], "GOLD", gold, "gold"),
    (pc[1], "SILVER", silver, "silver"),
    (pc[2], "BRONZE", bronze, "bronze"),
]:
    with col:
        st.markdown(
            f'<div class="out-podium {kind}"><div class="out-podium-name">{name}</div><div class="out-podium-value">{value:.1f} kg</div><div class="out-podium-gap">Required projected total</div></div>',
            unsafe_allow_html=True,
        )

bronze_gap = max(0.0, bronze - user_total)
silver_gap = max(0.0, silver - user_total)
gold_gap = max(0.0, gold - user_total)

st.write("")
gc = st.columns(3)
for col, name, gap in [(gc[0], "Gold gap", gold_gap), (gc[1], "Silver gap", silver_gap), (gc[2], "Bronze gap", bronze_gap)]:
    with col:
        card(name, format_gap(gap), "Current total vs podium threshold", accent=gap <= 0)

trend_label = {"rising": "Competitive bar is rising", "flat": "Competitive bar is broadly stable", "falling": "Competitive bar is easing"}.get(threshold.get("trend"), "Competitive trend unavailable")
pill(trend_label, "orange" if threshold.get("trend") == "rising" else "green" if threshold.get("trend") == "falling" else "blue")
st.caption(f"Projection method: {threshold.get('method', 'historical trend')}")


# ============================================================
# COMPETITOR PREDICTIONS
# ============================================================

competitor_ai_predictions = {}
competitor_ai_failures = 0
try:
    competitor_ai_service = AIPredictionService()
except Exception:
    competitor_ai_service = None

if competitor_ai_service is not None:
    for idx, row in field.iterrows():
        athlete_id = str(row.get("athlete_id") or "").strip()
        if not athlete_id:
            competitor_ai_failures += 1
            continue
        try:
            pred = competitor_ai_service.predict(
                athlete_id=athlete_id,
                target_year=target_year,
                division=str(row.get("division") or plan.get("division") or "Open"),
                weight_class=weight_class,
                equipment=str(row.get("equipment") or plan.get("equipment") or "CLASSIC"),
            )
            predicted = pred.get("predictions", {}).get("future_total")
            if predicted is not None:
                competitor_ai_predictions[idx] = float(predicted)
            else:
                competitor_ai_failures += 1
        except Exception:
            competitor_ai_failures += 1

field["ai_predicted_total_kg"] = pd.to_numeric(field.index.map(competitor_ai_predictions), errors="coerce")
field["projected_total_kg"] = field["ai_predicted_total_kg"].fillna(field["total_kg"])
field["projection_source"] = field["ai_predicted_total_kg"].notna().map({True: "AI prediction if competing", False: "Historical benchmark"})

user_row = pd.DataFrame([{
    "placing": None,
    "name": user_name,
    "total_kg": user_total,
    "ai_predicted_total_kg": ai_total if ai_prediction is not None else None,
    "projected_total_kg": user_total,
    "year": target_year,
    "is_user": True,
    "projection_source": "Your current total",
}])
field["is_user"] = False
comparison_field = pd.concat([field, user_row], ignore_index=True)
comparison_field = comparison_field.sort_values("projected_total_kg", ascending=False).reset_index(drop=True)
comparison_field["projected_rank"] = comparison_field.index + 1

user_positions = comparison_field.index[comparison_field["is_user"]].tolist()
projected_rank = int(user_positions[0] + 1) if user_positions else None


# ============================================================
# CURRENT POSITION
# ============================================================

section("COMPETITIVE POSITION", "Where you currently stand", "Your current total placed against the analytical target-year field.")

if projected_rank is not None:
    st.markdown(
        f"""
        <div class="out-rank">
            <div>
                <div class="out-rank-label">CURRENT BENCHMARK RANK</div>
                <div class="out-rank-number">#{projected_rank}</div>
                <div class="out-rank-copy">Based on current total vs the available analytical field.</div>
            </div>
            <div style="text-align:right">
                <div class="out-rank-label">YOUR TOTAL</div>
                <div style="color:#f5f8fc;font-size:30px;font-weight:950;margin-top:5px">{user_total:.1f} kg</div>
                <div class="out-rank-copy">Compared with {len(comparison_field)} lifters</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LEADERBOARD
# ============================================================

section("THE FIELD", "Target-year analytical leaderboard", "Historical competitors are ranked by target-year predicted total when a production prediction is available; otherwise their latest real total is used as a transparent fallback.")

show_n = min(12, len(comparison_field))
leader = comparison_field.head(show_n).copy()

rows = []
for _, r in leader.iterrows():
    rank = int(r["projected_rank"])
    name = esc(r.get("name") or "Unknown")
    hist = pd.to_numeric(r.get("total_kg"), errors="coerce")
    pred = pd.to_numeric(r.get("ai_predicted_total_kg"), errors="coerce")
    src = esc(r.get("projection_source") or "")
    year = esc(r.get("year") or "")
    is_you = bool(r.get("is_user"))
    hist_txt = "—" if pd.isna(hist) else f"{float(hist):.1f} kg"
    pred_txt = "—" if pd.isna(pred) else f"{float(pred):.1f} kg"
    rows.append(
        f'<tr class="{"you" if is_you else ""}"><td class="rank">{rank}</td><td>{name}{" <span style=\"color:#ff9418;font-size:9px\">YOU</span>" if is_you else ""}</td><td>{hist_txt}</td><td class="orange">{pred_txt}</td><td class="muted">{src}</td><td>{year}</td></tr>'
    )

st.markdown(
    f"""
    <div class="out-table-wrap">
      <table class="out-table">
        <thead><tr><th>Rank</th><th>Lifter</th><th>Historical total</th><th>Target-year total</th><th>Projection status</th><th>Year</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """,
    unsafe_allow_html=True,
)

if len(comparison_field) > show_n:
    st.caption(f"Showing top {show_n} of {len(comparison_field)} analytical lifters.")
if competitor_ai_failures:
    st.caption(f"{competitor_ai_failures} competitor(s) did not have enough history for a production AI projection and use their latest real historical total as the ranking fallback.")


# ============================================================
# LIFT COMPOSITION + GAP
# ============================================================

section("LIFT BREAKDOWN", "Where you need to improve", "Your current lift distribution and the gap-analysis returned by the competition engine.")

try:
    gap_analysis = get_gap_analysis(
        {"squat": user_squat, "bench": user_bench, "deadlift": user_deadlift},
        threshold,
    )
except (TypeError, ValueError, KeyError):
    gap_analysis = None

left, right = st.columns([1.05, 1.55])

with left:
    shares = [user_squat, user_bench, user_deadlift]
    fig = go.Figure(go.Pie(labels=["Squat", "Bench", "Deadlift"], values=shares, hole=.66, textinfo="label+percent", marker=dict(line=dict(color="#080e16", width=2))))
    fig.update_layout(
        showlegend=False,
        margin=dict(l=8,r=8,t=8,b=8),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dce7f3"),
        annotations=[dict(text=f"{user_total:.0f}<br>kg", x=.5, y=.5, font=dict(size=22, color="#ff9418", family="Arial Black"), showarrow=False)],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with right:
    gap_items = []
    if isinstance(gap_analysis, dict):
        for key in ("squat", "bench", "deadlift"):
            data = gap_analysis.get(key)
            if isinstance(data, dict):
                current = data.get("current", data.get("value", 0))
                gap = data.get("gap", data.get("required", 0))
                target = data.get("target")
                gap_items.append((key.title(), current, target, gap))

    if gap_items:
        gdf = pd.DataFrame(gap_items, columns=["Lift", "Current", "Target", "Gap"])
        for _, row in gdf.iterrows():
            current = float(row["Current"])
            target = None if pd.isna(row["Target"]) else float(row["Target"])
            gap = float(row["Gap"])
            target_txt = f" → {target:.1f} kg" if target is not None else ""
            st.markdown(
                f'<div style="padding:13px 0;border-bottom:1px solid rgba(117,145,177,.10)"><div style="display:flex;justify-content:space-between;gap:12px"><b style="color:#edf3fa">{esc(row["Lift"])}</b><span style="color:{"#49e7b0" if gap<=0 else "#ff9b20"};font-weight:900">{("Target reached" if gap<=0 else f"+{gap:.1f} kg")}</span></div><div style="color:#728aa8;font-size:11px;margin-top:5px">Current {current:.1f} kg{target_txt}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div class="out-callout">Detailed lift-level gap analysis is unavailable for this category. The podium-total gaps above remain available.</div>', unsafe_allow_html=True)


# ============================================================
# THREE-YEAR MOVEMENT
# ============================================================

section("HISTORICAL TREND", "Three-year movement", "The historical podium line used to construct the target-year threshold.")
history = threshold.get("history") or []
required = {"year", "gold", "silver", "bronze"}

if history:
    trend_df = pd.DataFrame(history)
    missing = required - set(trend_df.columns)
    if missing:
        st.warning("Historical podium history is incomplete: " + ", ".join(sorted(missing)) + ".")
    else:
        trend_df = trend_df[["year", "gold", "silver", "bronze"]].copy().sort_values("year")
        # Treat competition years as categories, not continuous numbers.
        # This prevents Plotly from inventing half-year ticks such as 2024.5.
        trend_df["year_label"] = trend_df["year"].astype(int).astype(str)

        fig = go.Figure()

        series = [
            ("Gold", "gold", "solid", "#ffb020"),
            ("Silver", "silver", "dash", "#b8c7d9"),
            ("Bronze", "bronze", "dot", "#e06a5f"),
        ]

        for name, col, dash, line_color in series:
            fig.add_trace(
                go.Scatter(
                    x=trend_df["year_label"],
                    y=trend_df[col],
                    mode="lines+markers",
                    name=name,
                    line=dict(
                        width=3,
                        dash=dash,
                        color=line_color,
                    ),
                    marker=dict(
                        size=7,
                        color=line_color,
                    ),
                    hovertemplate=(
                        f"<b>{name}</b><br>"
                        "%{x}: %{y:.1f} kg"
                        "<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            height=330,
            margin=dict(l=10, r=10, t=25, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="#a9bbd0",
                family="Inter, Arial, sans-serif",
            ),
            xaxis=dict(
                type="category",
                categoryorder="array",
                categoryarray=trend_df["year_label"].tolist(),
                showgrid=False,
                title="",
                tickfont=dict(color="#8fa5bf", size=12),
                fixedrange=True,
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(117,145,177,.10)",
                zeroline=False,
                title=dict(
                    text="Total (kg)",
                    font=dict(color="#8fa5bf", size=12),
                ),
                tickfont=dict(color="#8fa5bf", size=12),
                fixedrange=True,
            ),
            legend=dict(
                orientation="h",
                y=1.08,
                x=0,
                font=dict(color="#a9bbd0", size=12),
            ),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="#0b111a",
                bordercolor="rgba(255,148,24,.35)",
                font=dict(color="#f4f7fb"),
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

        # Premium podium-threshold history panel.
        # The values remain dynamic from trend_df; only presentation is upgraded.
        table_rows = []
        previous = None

        for _, row in trend_df.iterrows():
            year = int(row["year"])
            gold_value = float(row["gold"])
            silver_value = float(row["silver"])
            bronze_value = float(row["bronze"])

            if previous is None:
                gold_delta = "BASELINE"
                silver_delta = "BASELINE"
                bronze_delta = "BASELINE"
            else:
                gd = gold_value - previous["gold"]
                sd = silver_value - previous["silver"]
                bd = bronze_value - previous["bronze"]

                gold_delta = f'{"↓" if gd < 0 else "↑" if gd > 0 else "→"} {abs(gd):.1f} kg'
                silver_delta = f'{"↓" if sd < 0 else "↑" if sd > 0 else "→"} {abs(sd):.1f} kg'
                bronze_delta = f'{"↓" if bd < 0 else "↑" if bd > 0 else "→"} {abs(bd):.1f} kg'

            table_rows.append(
                f"""
                <tr style="
                    border-top:1px solid rgba(117,145,177,.10);
                ">
                    <td style="padding:15px 16px;vertical-align:middle;">
                        <div style="
                            display:inline-flex;
                            align-items:center;
                            justify-content:center;
                            min-width:54px;
                            height:30px;
                            padding:0 10px;
                            border-radius:8px;
                            background:#111c2a;
                            border:1px solid rgba(117,145,177,.18);
                            color:#f5f8fc;
                            font-weight:900;
                            font-size:13px;
                        ">
                            {year}
                        </div>
                    </td>

                    <td style="padding:15px 16px;">
                        <div style="color:#f5f8fc;font-size:16px;font-weight:900;">
                            {gold_value:.1f} kg
                        </div>
                        <div style="
                            margin-top:4px;
                            color:#d6a63a;
                            font-size:9px;
                            font-weight:800;
                            letter-spacing:1px;
                        ">
                            {gold_delta}
                        </div>
                    </td>

                    <td style="padding:15px 16px;">
                        <div style="color:#f5f8fc;font-size:16px;font-weight:900;">
                            {silver_value:.1f} kg
                        </div>
                        <div style="
                            margin-top:4px;
                            color:#9fb3c8;
                            font-size:9px;
                            font-weight:800;
                            letter-spacing:1px;
                        ">
                            {silver_delta}
                        </div>
                    </td>

                    <td style="padding:15px 16px;">
                        <div style="color:#f5f8fc;font-size:16px;font-weight:900;">
                            {bronze_value:.1f} kg
                        </div>
                        <div style="
                            margin-top:4px;
                            color:#c98a58;
                            font-size:9px;
                            font-weight:800;
                            letter-spacing:1px;
                        ">
                            {bronze_delta}
                        </div>
                    </td>
                </tr>
                """
            )

            previous = {
                "gold": gold_value,
                "silver": silver_value,
                "bronze": bronze_value,
            }

        st.html(
            f"""
            <div style="
                margin-top:1rem;
                border:1px solid rgba(255,148,24,.20);
                border-radius:18px;
                overflow:hidden;
                background:linear-gradient(
                    145deg,
                    #09111b 0%,
                    #07101a 100%
                );
                box-shadow:0 12px 34px rgba(0,0,0,.18);
            ">

                <div style="
                    padding:18px 20px 16px;
                    border-bottom:1px solid rgba(117,145,177,.12);
                    background:rgba(13,21,32,.72);
                ">
                    <div style="
                        color:#ff9418;
                        font-size:9px;
                        letter-spacing:1.8px;
                        font-weight:900;
                        margin-bottom:6px;
                    ">
                        PODIUM THRESHOLD HISTORY
                    </div>

                    <div style="
                        color:#f5f8fc;
                        font-size:20px;
                        line-height:1.2;
                        font-weight:900;
                    ">
                        Three-year benchmark movement
                    </div>

                    <div style="
                        margin-top:5px;
                        color:#7593b5;
                        font-size:11px;
                        line-height:1.5;
                    ">
                        Historical podium totals used to construct the target-year competition threshold.
                    </div>
                </div>

                <div style="padding:0 4px 4px;">
                    <table style="
                        width:100%;
                        border-collapse:collapse;
                        font-size:13px;
                        color:#dbe5f0;
                    ">
                        <thead>
                            <tr style="
                                background:#0b1521;
                                text-align:left;
                            ">
                                <th style="
                                    padding:12px 16px;
                                    color:#6f8eaf;
                                    font-size:9px;
                                    letter-spacing:1.3px;
                                    font-weight:900;
                                ">
                                    YEAR
                                </th>

                                <th style="
                                    padding:12px 16px;
                                    color:#d6a63a;
                                    font-size:9px;
                                    letter-spacing:1.3px;
                                    font-weight:900;
                                ">
                                    GOLD
                                </th>

                                <th style="
                                    padding:12px 16px;
                                    color:#9fb3c8;
                                    font-size:9px;
                                    letter-spacing:1.3px;
                                    font-weight:900;
                                ">
                                    SILVER
                                </th>

                                <th style="
                                    padding:12px 16px;
                                    color:#c98a58;
                                    font-size:9px;
                                    letter-spacing:1.3px;
                                    font-weight:900;
                                ">
                                    BRONZE
                                </th>
                            </tr>
                        </thead>

                        <tbody>
                            {"".join(table_rows)}
                        </tbody>
                    </table>
                </div>
            </div>
            """
        )
else:
    st.info("No complete historical podium history was returned for this competition/category.")


# ============================================================
# WHAT THIS MEANS
# ============================================================

section("COMPETITIVE READ", "What this means", "A concise interpretation of the current total against the projected podium line.")

if bronze_gap <= 0:
    summary_title = "Your current total is above the projected bronze threshold."
    summary_body = f"At {user_total:.1f} kg, the current baseline is {user_total - bronze:.1f} kg above the projected bronze line of {bronze:.1f} kg."
    callout_class = "success"
elif silver_gap <= 0:
    summary_title = "The current total is above the projected silver threshold."
    summary_body = f"At {user_total:.1f} kg, the current baseline is {user_total - silver:.1f} kg above the projected silver line of {silver:.1f} kg."
    callout_class = "success"
else:
    summary_title = "The immediate benchmark is the projected bronze line."
    summary_body = f"The current total is {user_total:.1f} kg, with approximately {bronze_gap:.1f} kg separating it from the projected bronze threshold of {bronze:.1f} kg."
    callout_class = "orange"

st.markdown(
    f'<div class="out-callout {callout_class}"><div style="color:#f5f8fc;font-size:20px;font-weight:900;margin-bottom:7px">{esc(summary_title)}</div>{esc(summary_body)}</div>',
    unsafe_allow_html=True,
)


# ============================================================
# DATA TRUST
# ============================================================

st.markdown(
    """
    <div class="out-trust" style="margin-top:26px">
        <b>DATA STATUS &amp; TRUST</b><br>
        Your performance is the current baseline entered through Competition Planner. Historical competition results are used to construct the analytical field. Target-year competitor totals and podium lines are conditional projections based on historical data; they are not confirmed meet entries, official start lists, or guarantees of future performance.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div style="margin-top:28px;padding-top:16px;border-top:1px solid rgba(117,145,177,.10);text-align:center;color:#4e6581;font-size:9px;letter-spacing:1.8px">POWERLIFT AI-X &nbsp;•&nbsp; DATA &nbsp;•&nbsp; COMPARE &nbsp;•&nbsp; PREDICT &nbsp;•&nbsp; PLAN</div>',
    unsafe_allow_html=True,
)
