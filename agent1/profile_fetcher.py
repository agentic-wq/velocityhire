"""
Profile Fetcher — LinkedIn URL → structured profile text

Strategy:
1. Attempt direct HTTP fetch of the public LinkedIn profile page
2. Parse visible text with BeautifulSoup
3. Extract structured sections: name, headline, about, experience, skills, etc.
4. Fall back gracefully with a helpful error message if blocked

Note: LinkedIn heavily rate-limits bots. This works reliably on public
profiles that are not behind an auth wall.  For a production system,
Proxycurl or similar APIs would be used.
"""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from typing import Optional


# ── Browser-like headers to avoid trivial bot detection ──────────────────────
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}


def _clean(text: str) -> str:
    """Strip excessive whitespace."""
    return re.sub(r"\s{3,}", "\n\n", text).strip()


def _extract_linkedin_sections(soup: BeautifulSoup) -> str:
    """Extract meaningful sections from a LinkedIn public profile page."""
    sections = []

    # Name
    name_tag = (
        soup.find("h1")
        or soup.find("span", {"class": re.compile(r"name", re.I)})
    )
    if name_tag:
        sections.append(f"Name: {name_tag.get_text(strip=True)}")

    # Headline
    headline = soup.find("div", {"class": re.compile(r"headline|top-card", re.I)})
    if headline:
        sections.append(f"Headline: {headline.get_text(strip=True)}")

    # About / Summary
    about = soup.find("section", {"class": re.compile(r"summary|about", re.I)})
    if about:
        sections.append(f"About:\n{about.get_text(separator=' ', strip=True)}")

    # Experience
    exp = soup.find("section", {"class": re.compile(r"experience", re.I)})
    if exp:
        sections.append(f"Experience:\n{exp.get_text(separator=' ', strip=True)}")

    # Skills
    skills = soup.find("section", {"class": re.compile(r"skill", re.I)})
    if skills:
        sections.append(f"Skills:\n{skills.get_text(separator=', ', strip=True)}")

    # Certifications / Licences
    certs = soup.find("section", {"class": re.compile(r"certif|license", re.I)})
    if certs:
        sections.append(f"Certifications:\n{certs.get_text(separator=' ', strip=True)}")

    # If nothing structured was found, fall back to all visible text
    if len(sections) <= 1:
        body_text = soup.get_text(separator="\n", strip=True)
        # Remove boilerplate navigation lines (first/last ~20 lines are usually nav)
        lines = [l for l in body_text.splitlines() if len(l.strip()) > 20]
        sections = lines[:120]   # cap at ~120 meaningful lines

    return _clean("\n\n".join(str(s) for s in sections))


def fetch_linkedin_profile(url: str, timeout: int = 20) -> dict:
    """
    Fetch a LinkedIn profile URL and return extracted text.

    Returns:
        {
            "success": bool,
            "profile_text": str,      # filled when success=True
            "error": str,             # filled when success=False
            "source": "linkedin_fetch"
        }
    """
    if not url.startswith("http"):
        url = "https://" + url

    # Normalise: ensure it's a linkedin.com URL
    if "linkedin.com" not in url:
        return {
            "success": False,
            "profile_text": "",
            "error": "URL does not appear to be a LinkedIn profile link.",
            "source": "linkedin_fetch",
        }

    # Small random delay to mimic human browsing
    time.sleep(random.uniform(0.5, 1.5))

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)

        # LinkedIn sends 999 for blocked bots
        if resp.status_code == 999:
            return {
                "success": False,
                "profile_text": "",
                "error": (
                    "LinkedIn blocked the request (status 999). "
                    "Please paste the profile text manually below."
                ),
                "source": "linkedin_fetch",
            }

        if resp.status_code == 401 or resp.status_code == 403:
            return {
                "success": False,
                "profile_text": "",
                "error": (
                    "This LinkedIn profile requires sign-in to view. "
                    "Please paste the profile text manually below."
                ),
                "source": "linkedin_fetch",
            }

        if resp.status_code != 200:
            return {
                "success": False,
                "profile_text": "",
                "error": f"LinkedIn returned HTTP {resp.status_code}. Try pasting the profile text manually.",
                "source": "linkedin_fetch",
            }

        # Check for LinkedIn's sign-in redirect HTML
        if "authwall" in resp.url or "login" in resp.url:
            return {
                "success": False,
                "profile_text": "",
                "error": (
                    "LinkedIn redirected to login — this profile is private. "
                    "Please paste the profile text manually below."
                ),
                "source": "linkedin_fetch",
            }

        soup = BeautifulSoup(resp.text, "lxml")

        # Remove script / style noise
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()

        profile_text = _extract_linkedin_sections(soup)

        if len(profile_text) < 100:
            return {
                "success": False,
                "profile_text": "",
                "error": (
                    "Couldn't extract enough profile data from LinkedIn. "
                    "Please paste the profile text manually below."
                ),
                "source": "linkedin_fetch",
            }

        return {
            "success": True,
            "profile_text": profile_text,
            "error": "",
            "source": "linkedin_fetch",
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "profile_text": "",
            "error": "Request timed out. Please try again or paste the profile text manually.",
            "source": "linkedin_fetch",
        }
    except Exception as exc:
        return {
            "success": False,
            "profile_text": "",
            "error": f"Fetch failed: {str(exc)}. Please paste the profile text manually.",
            "source": "linkedin_fetch",
        }
