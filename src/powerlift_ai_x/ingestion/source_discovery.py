from __future__ import annotations

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://powerliftingindia.net"
RESULTS_URL = f"{BASE_URL}/result"

HEADERS = {
    "User-Agent": "PowerLift-AI-X/0.1.0",
}


def fetch(url: str) -> str:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def discover_year_links(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    discovered: dict[str, dict[str, str]] = {}

    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = link["href"].strip()

        if text.isdigit() and len(text) == 4:
            url = urljoin(BASE_URL, href)

            discovered[url] = {
                "year": text,
                "url": url,
            }

    return list(discovered.values())


def is_excluded(name: str) -> bool:
    value = name.lower()

    excluded_terms = (
        "bench press",
        "special olympics",
        "blind",
        "differently abled",
        "differently-abled",
        "disabled",
        "disability",
        "para",
    )

    return any(
        term in value
        for term in excluded_terms
    )


def is_full_powerlifting(name: str) -> bool:
    value = name.lower()

    return (
        "powerlifting" in value
        and not is_excluded(name)
    )


def extract_competition_blocks(
    html: str,
) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    results: list[dict[str, str]] = []

    for text_node in soup.find_all(
        string=lambda value:
        value and "Powerlifting" in value
    ):
        competition = text_node.strip()

        if not competition:
            continue

        if not is_full_powerlifting(competition):
            continue

        container = text_node.parent

        for _ in range(6):
            if container is None:
                break

            links = container.find_all(
                "a",
                href=True,
            )

            men_links = []

            for link in links:
                label = link.get_text(
                    " ",
                    strip=True,
                ).lower()

                if label == "men":
                    men_links.append(
                        urljoin(
                            BASE_URL,
                            link["href"].strip(),
                        )
                    )

            if men_links:
                results.append(
                    {
                        "competition": competition,
                        "men_url": men_links[0],
                    }
                )
                break

            container = container.parent

    unique: dict[
        tuple[str, str],
        dict[str, str],
    ] = {}

    for item in results:
        key = (
            item["competition"],
            item["men_url"],
        )

        unique[key] = item

    return list(unique.values())


def discover_sources() -> list[dict[str, str]]:
    results_html = fetch(RESULTS_URL)

    years = discover_year_links(results_html)

    sources = []

    for year in years:
        year_html = fetch(year["url"])

        competitions = extract_competition_blocks(
            year_html
        )

        for competition in competitions:
            sources.append(
                {
                    "year": year["year"],
                    "competition": competition[
                        "competition"
                    ],
                    "men_url": competition[
                        "men_url"
                    ],
                    "status": "NEEDS_VERIFICATION",
                }
            )

    return sources
