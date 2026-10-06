from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st


def page_header(title: str, subtitle: str | None = None, *, eyebrow: str = "POWERLIFT AI-X") -> None:
    subtitle_html = (
        f'<div class="plx-page-subtitle">{escape(subtitle)}</div>'
        if subtitle
        else ""
    )
    st.markdown(
        "".join(
            [
                '<div class="plx-page-header">',
                f'<div class="plx-eyebrow">{escape(eyebrow)}</div>',
                f'<div class="plx-page-title">{escape(title)}</div>',
                subtitle_html,
                '</div>',
            ]
        ),
        unsafe_allow_html=True,
    )


def section_header(title: str, description: str | None = None) -> None:
    description_html = (
        f'<div class="plx-section-description">{escape(description)}</div>'
        if description
        else ""
    )
    st.markdown(
        "".join(
            [
                '<div class="plx-section-header">',
                f'<div class="plx-section-title">{escape(title)}</div>',
                description_html,
                '</div>',
            ]
        ),
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: Any, *, accent: bool = False, hint: str | None = None) -> None:
    value_class = " plx-accent" if accent else ""
    hint_html = (
        f'<div class="plx-card-hint">{escape(hint)}</div>'
        if hint
        else ""
    )
    st.markdown(
        "".join(
            [
                '<div class="plx-card plx-metric-card">',
                f'<div class="plx-card-title">{escape(str(label))}</div>',
                f'<div class="plx-card-value{value_class}">{escape(str(value))}</div>',
                hint_html,
                '</div>',
            ]
        ),
        unsafe_allow_html=True,
    )


def info_card(title: str, body: str, *, accent: bool = False) -> None:
    accent_class = " plx-info-accent" if accent else ""
    st.markdown(
        "".join(
            [
                f'<div class="plx-card plx-info-card{accent_class}">',
                f'<div class="plx-card-title">{escape(str(title))}</div>',
                f'<div class="plx-card-body">{escape(str(body))}</div>',
                '</div>',
            ]
        ),
        unsafe_allow_html=True,
    )


def status_pill(label: str, *, accent: bool = False) -> None:
    css_class = "plx-pill plx-pill-accent" if accent else "plx-pill"
    st.markdown(
        f'<span class="{css_class}">{escape(str(label))}</span>',
        unsafe_allow_html=True,
    )


def plan_summary(*, meet: str, category: str, equipment: str, goal: str, year: int | str | None = None) -> None:
    equipment_display = "Classic / Raw" if equipment == "CLASSIC" else "Equipped" if equipment == "EQUIPPED" else equipment
    year_value = str(year) if year is not None else "—"
    fields = (
        ("Competition", meet),
        ("Category", category),
        ("Equipment", equipment_display),
        ("Target year", year_value),
        ("Goal", goal),
    )
    cells = "".join(
        "".join(
            [
                '<div class="plx-plan-item">',
                f'<div class="plx-plan-label">{escape(label)}</div>',
                f'<div class="plx-plan-value">{escape(str(value))}</div>',
                '</div>',
            ]
        )
        for label, value in fields
    )
    st.markdown(
        "".join(
            [
                '<div class="plx-plan-summary">',
                '<div class="plx-plan-summary-top">',
                '<div class="plx-plan-summary-label">ACTIVE COMPETITION PLAN</div>',
                '<div class="plx-live-dot">ACTIVE</div>',
                '</div>',
                f'<div class="plx-plan-grid">{cells}</div>',
                '</div>',
            ]
        ),
        unsafe_allow_html=True,
    )
def athlete_selector(
    options: list[dict[str, str]],
    key: str = "athlete_selector",
) -> dict[str, str] | None:
    """Render a real athlete selector and return the selected athlete."""

    if not options:
        st.info("No prediction-eligible athletes are available.")
        return None

    labels = [
        (
            f"{option['athlete_name']} — "
            f"{option['division']} • "
            f"{option['weight_class']} kg • "
            f"{option['equipment']}"
        )
        for option in options
    ]

    selected_label = st.selectbox(
        "Athlete",
        labels,
        key=key,
    )

    selected_index = labels.index(selected_label)

    return options[selected_index]
