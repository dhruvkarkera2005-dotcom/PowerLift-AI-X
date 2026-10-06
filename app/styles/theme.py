from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


def _data_uri(path: Path) -> str:
    try:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""


def apply_theme() -> None:
    """PowerLift AI-X global visual system.

    This file only controls presentation. Existing page/backend logic can
    continue using the same .plx-* classes.
    """
    asset = Path(__file__).resolve().parents[1] / "assets" / "powerlift_hero.png"
    hero_uri = _data_uri(asset)
    hero_bg = (
        f"url('{hero_uri}')"
        if hero_uri
        else "linear-gradient(120deg,#0b1019,#101827 55%,#06090f)"
    )

    st.markdown(
        f"""
        <style>
        :root {{
            --plx-bg: #05080e;
            --plx-bg-2: #080d15;
            --plx-panel: #0b121c;
            --plx-panel-2: #101925;
            --plx-border: rgba(148,163,184,.16);
            --plx-text: #f8fafc;
            --plx-muted: #91a0b8;
            --plx-accent: #ff9f1a;
            --plx-accent-2: #ff6f00;
            --plx-blue: #4da3ff;
            --plx-green: #32d583;
        }}

        html, body, [data-testid="stAppViewContainer"] {{
            background: var(--plx-bg) !important;
        }}

        .stApp {{
            background:
                radial-gradient(circle at 85% 0%, rgba(255,159,26,.075), transparent 28%),
                radial-gradient(circle at 20% 30%, rgba(49,130,206,.045), transparent 30%),
                linear-gradient(180deg,#05080e 0%,#070b12 100%);
            color: var(--plx-text);
        }}

        [data-testid="stHeader"] {{
            background: rgba(5,8,14,.82) !important;
        }}

        .block-container {{
            max-width: 1450px !important;
            padding-top: 1.8rem !important;
            padding-bottom: 4rem !important;
        }}

        /* ---------------- Sidebar ---------------- */
        [data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg,#070c14 0%,#05080e 100%) !important;
            border-right: 1px solid rgba(255,255,255,.08);
        }}

        [data-testid="stSidebar"] > div:first-child {{
            padding: 1.1rem .8rem 1.4rem !important;
        }}

        .plx-brand {{
            padding: .45rem .45rem 1.15rem;
            margin-bottom: .7rem;
            border-bottom: 1px solid rgba(148,163,184,.12);
        }}
        .plx-brand-mark {{
            width: 42px;height: 42px;border-radius: 12px;
            display:flex;align-items:center;justify-content:center;
            background:linear-gradient(135deg,var(--plx-accent),var(--plx-accent-2));
            color:#10131a;font-size:1.35rem;font-weight:950;
            box-shadow:0 8px 24px rgba(255,132,0,.20);
        }}
        .plx-brand-name {{
            color:#fff;font-size:1.08rem;font-weight:950;
            letter-spacing:-.035em;
        }}
        .plx-brand-name span {{ color:var(--plx-accent); }}
        .plx-brand-tag {{
            color:#66758e;font-size:.62rem;letter-spacing:.13em;
            margin-top:.25rem;font-weight:750;
        }}

        [data-testid="stSidebar"] .stPageLink {{
            border-radius: 11px !important;
            margin: .18rem 0 !important;
            min-height: 2.45rem !important;
        }}
        [data-testid="stSidebar"] .stPageLink:hover {{
            background: rgba(255,159,26,.08) !important;
        }}

        /* Prevent Streamlit Material Symbols from inheriting dashboard fonts. */
        [data-testid="stSidebar"] [data-testid="stIconMaterial"] {{
            font-family: "Material Symbols Rounded" !important;
        }}

        /* ---------------- Typography ---------------- */
        h1,h2,h3,h4 {{
            color:#fff !important;
            font-weight:900 !important;
            letter-spacing:-.045em !important;
        }}
        p, label, [data-testid="stMarkdownContainer"] {{
            color:var(--plx-muted);
        }}

        .plx-eyebrow {{
            color:var(--plx-accent);font-size:.66rem;font-weight:900;
            letter-spacing:.18em;text-transform:uppercase;
        }}
        .plx-section-title {{
            color:#fff;font-size:1.35rem;font-weight:900;
            letter-spacing:-.035em;margin-top:.18rem;
        }}
        .plx-section-copy {{
            color:#8291aa;font-size:.86rem;line-height:1.55;
            margin-bottom:.8rem;
        }}

        /* ---------------- Home hero ---------------- */
        .plx-home-hero {{
            position:relative;overflow:hidden;min-height:470px;
            border-radius:24px;
            border:1px solid rgba(255,159,26,.22);
            background-image:
                linear-gradient(90deg,rgba(5,8,14,.98) 0%,rgba(5,8,14,.90) 32%,rgba(5,8,14,.28) 72%,rgba(5,8,14,.48) 100%),
                {hero_bg};
            background-size:cover;background-position:center;
            box-shadow:0 30px 90px rgba(0,0,0,.42);
        }}
        .plx-home-content {{
            position:relative;z-index:2;padding:3.4rem 3.2rem 2.4rem;
            max-width:850px;
        }}
        .plx-home-kicker {{
            color:var(--plx-accent);font-size:.72rem;font-weight:900;
            letter-spacing:.2em;text-transform:uppercase;
        }}
        .plx-home-title {{
            color:#fff;font-size:clamp(3rem,6vw,5.9rem);font-weight:950;
            line-height:.91;letter-spacing:-.07em;margin:.65rem 0 1.1rem;
        }}
        .plx-home-title span {{ color:var(--plx-accent); }}
        .plx-home-subtitle {{
            max-width:670px;color:#d1d8e5;font-size:1rem;line-height:1.6;
        }}
        .plx-hero-badge {{
            display:inline-flex;margin-top:1.3rem;padding:.48rem .78rem;
            border:1px solid rgba(255,159,26,.30);border-radius:999px;
            background:rgba(255,159,26,.08);color:#ffbf55;
            font-size:.7rem;font-weight:850;letter-spacing:.08em;
        }}
        .plx-hero-quote {{
            margin-top:2.2rem;padding:1rem 1.2rem;
            width:max-content;max-width:90%;
            background:rgba(3,7,12,.70);border:1px solid rgba(255,255,255,.12);
            border-radius:14px;color:#fff;font-size:1.1rem;font-weight:850;
            backdrop-filter:blur(8px);
        }}

        /* ---------------- Cards ---------------- */
        .plx-card,.plx-kpi,.plx-workflow {{
            background:linear-gradient(145deg,rgba(15,24,36,.97),rgba(7,12,20,.98));
            border:1px solid var(--plx-border);border-radius:17px;
            box-shadow:0 16px 50px rgba(0,0,0,.20);
        }}
        .plx-card {{ padding:1.25rem 1.35rem; }}
        .plx-card-title,.plx-kpi-label {{
            color:#8190aa;font-size:.66rem;font-weight:850;
            letter-spacing:.14em;text-transform:uppercase;
        }}
        .plx-card-value {{ color:#fff;font-size:1.55rem;font-weight:900;line-height:1.15; }}
        .plx-card-body {{ color:#8d9bb1;font-size:.86rem;line-height:1.55;margin-top:.45rem; }}
        .plx-kpi {{ min-height:125px;padding:1.1rem; }}
        .plx-kpi-value {{ color:#fff;font-size:1.8rem;font-weight:950;margin-top:.42rem; }}
        .plx-kpi-value.accent {{ color:var(--plx-accent); }}
        .plx-kpi-meta {{ color:#718098;font-size:.72rem;margin-top:.2rem; }}

        .plx-workflow {{
            min-height:170px;padding:1.2rem;transition:.18s ease;
        }}
        .plx-workflow:hover {{
            transform:translateY(-3px);border-color:rgba(255,159,26,.36);
        }}
        .plx-step {{
            display:inline-flex;width:36px;height:36px;border-radius:50%;
            align-items:center;justify-content:center;
            background:linear-gradient(135deg,var(--plx-accent),var(--plx-accent-2));
            color:#111;font-size:.78rem;font-weight:950;
        }}
        .plx-workflow-title {{ color:#fff;font-size:1rem;font-weight:850;margin-top:.9rem; }}
        .plx-workflow-copy {{ color:#8391a8;font-size:.8rem;line-height:1.5;margin-top:.3rem; }}

        /* ---------------- Controls ---------------- */
        .stButton > button,.stLinkButton > a {{
            border-radius:10px !important;font-weight:850 !important;
            min-height:2.6rem !important;
        }}
        .stButton > button[kind="primary"] {{
            background:linear-gradient(90deg,#ffad24,#ff7b08) !important;
            color:#111 !important;border:0 !important;
            box-shadow:0 10px 30px rgba(255,132,0,.20);
        }}
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        textarea {{ border-radius:10px !important; }}
        [data-testid="stDataFrame"] {{ border-radius:13px;overflow:hidden; }}
        [data-testid="stAlert"] {{ border-radius:11px; }}

        /* ---------------- Professional motion ---------------- */
        /* Keep navigation immediate; do not animate the page container.
           Animating .main can make the browser show a white flash while
           Streamlit is mounting the newly selected page. */

        /* Session-safe sidebar navigation stays visually responsive. */
        [data-testid="stSidebar"] .stPageLink a {{
            transition:
                background .18s ease,
                color .18s ease,
                transform .18s ease,
                border-color .18s ease !important;
        }}

        [data-testid="stSidebar"] .stPageLink a:hover {{
            transform: translateX(3px);
        }}

        /* Buttons feel responsive without changing their existing styling. */
        .stButton > button,
        .stLinkButton > a {{
            transition:
                transform .16s ease,
                box-shadow .16s ease,
                background .16s ease,
                border-color .16s ease !important;
        }}

        .stButton > button:hover,
        .stLinkButton > a:hover {{
            transform: translateY(-1px);
        }}

        .stButton > button:active,
        .stLinkButton > a:active {{
            transform: translateY(0);
        }}

        /* Existing dashboard cards get a subtle lift on hover. */
        .plx-card,
        .plx-kpi,
        .plx-workflow {{
            transition:
                transform .18s ease,
                border-color .18s ease,
                box-shadow .18s ease;
        }}

        .plx-card:hover,
        .plx-kpi:hover {{
            transform: translateY(-2px);
        }}

        /* Respect reduced-motion accessibility preferences. */
        @media (prefers-reduced-motion: reduce) {{
            [data-testid="stSidebar"] .stPageLink a,
            .stButton > button,
            .stLinkButton > a,
            .plx-card,
            .plx-kpi,
            .plx-workflow {{
                transition: none !important;
                transform: none !important;
            }}
        }}

        /* Footer / status */
        .plx-footer {{
            margin-top:2.2rem;padding:1.1rem 0;
            border-top:1px solid rgba(148,163,184,.10);
            display:flex;justify-content:space-between;gap:1rem;
            color:#64738b;font-size:.7rem;
        }}
        .plx-footer strong {{ color:#ffae2d; }}

        @media(max-width:900px) {{
            .block-container {{ padding-top:1rem !important; }}
            .plx-home-hero {{ min-height:560px; }}
            .plx-home-content {{ padding:2.1rem 1.35rem; }}
            .plx-home-title {{ font-size:3.15rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
