"""
Comprehensive SEO audit engine.
"""

import ipaddress
import logging
import socket
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "ATI-SEO-AuditBot/2.0 (+https://automatedtechnicalinsightsandai.github.io)"
    )
}
REQUEST_TIMEOUT = 12

# Schemes we are willing to fetch
_ALLOWED_SCHEMES = {"http", "https"}


# ---------------------------------------------------------------------------
# SSRF protection
# ---------------------------------------------------------------------------

def _validated_url(url: str) -> Optional[str]:
    """
    Validate *url* against SSRF risks and return a normalised copy if safe,
    or None if the URL should be rejected.

    Rejects:
    - Non-http(s) schemes
    - Loopback, link-local, private, and other reserved IP ranges
    - Bare hostnames that resolve to such addresses

    Returning the validated URL (rather than a plain bool) ensures callers
    always use this function's output — not the original user-supplied string —
    which makes the SSRF guard visible to static-analysis tools.
    """
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return None
    hostname = parsed.hostname
    if not hostname:
        return None
    # Block obvious localhost variants
    if hostname.lower() in {"localhost", "ip6-localhost", "ip6-loopback"}:
        return None
    try:
        # Resolve to IP and check for private/reserved ranges
        addr_info = socket.getaddrinfo(hostname, None)
        for _family, _type, _proto, _canonname, sockaddr in addr_info:
            ip = ipaddress.ip_address(sockaddr[0])
            if (
                ip.is_loopback
                or ip.is_private
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_unspecified
            ):
                logger.warning("Blocked SSRF attempt to %s (%s)", url, ip)
                return None
    except (socket.gaierror, ValueError):
        # DNS failure or invalid IP — block it to be safe
        return None
    # Reconstruct from parsed components so the returned value is independent
    # of the raw user-supplied string.
    safe = parsed._replace(fragment="").geturl()
    return safe


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_get(url: str, timeout: int = REQUEST_TIMEOUT) -> Optional[requests.Response]:
    """Perform a GET request; return None on any failure or unsafe URL."""
    safe_url = _validated_url(url)
    if safe_url is None:
        logger.warning("Skipping unsafe URL: %s", url)
        return None
    try:
        resp = requests.get(safe_url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return resp
    except requests.RequestException as exc:
        logger.debug("GET %s failed: %s", safe_url, exc)
        return None


def _safe_head(url: str, timeout: int = 6) -> Optional[requests.Response]:
    """Perform a HEAD request (falling back to GET on 405) for safe URLs only."""
    safe_url = _validated_url(url)
    if safe_url is None:
        logger.warning("Skipping unsafe URL: %s", url)
        return None
    try:
        resp = requests.head(safe_url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code == 405:
            resp = requests.get(safe_url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return resp
    except requests.RequestException:
        return None


def _check(
    category: str,
    name: str,
    status: str,
    detail: str,
    recommendation: str = "",
) -> Dict[str, str]:
    return {
        "category": category,
        "name": name,
        "status": status,
        "detail": detail,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# Individual check groups
# ---------------------------------------------------------------------------

def _technical_checks(
    url: str,
    soup: BeautifulSoup,
    response: requests.Response,
    base_url: str,
) -> List[Dict[str, str]]:
    checks: List[Dict[str, str]] = []
    parsed = urlparse(url)

    # HTTPS / SSL
    if parsed.scheme == "https":
        checks.append(_check("Technical", "HTTPS / SSL", "pass", "Site is served over HTTPS."))
    else:
        checks.append(
            _check(
                "Technical",
                "HTTPS / SSL",
                "fail",
                "Site is not served over HTTPS.",
                "Migrate to HTTPS with a valid SSL certificate.",
            )
        )

    # robots.txt
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    robots_resp = _safe_get(robots_url, timeout=8)
    if robots_resp and robots_resp.status_code == 200 and len(robots_resp.text) > 10:
        checks.append(_check("Technical", "robots.txt", "pass", "robots.txt is present and accessible."))
    else:
        checks.append(
            _check(
                "Technical",
                "robots.txt",
                "warning",
                "robots.txt not found or empty.",
                "Create a robots.txt file to guide search engine crawlers.",
            )
        )

    # sitemap.xml
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
    sitemap_resp = _safe_get(sitemap_url, timeout=8)
    if sitemap_resp and sitemap_resp.status_code == 200:
        checks.append(_check("Technical", "XML Sitemap", "pass", "sitemap.xml is present."))
    else:
        checks.append(
            _check(
                "Technical",
                "XML Sitemap",
                "warning",
                "sitemap.xml not found.",
                "Create and submit an XML sitemap to help search engines discover your pages.",
            )
        )

    # Mobile viewport
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport and viewport.get("content"):
        checks.append(_check("Technical", "Mobile Viewport", "pass", f"Viewport meta tag found: {viewport.get('content')[:80]}"))
    else:
        checks.append(
            _check(
                "Technical",
                "Mobile Viewport",
                "fail",
                "No viewport meta tag found.",
                "Add <meta name='viewport' content='width=device-width, initial-scale=1'> for mobile-friendliness.",
            )
        )

    # Structured data (JSON-LD)
    json_ld = soup.find("script", attrs={"type": "application/ld+json"})
    if json_ld:
        checks.append(_check("Technical", "Structured Data (JSON-LD)", "pass", "JSON-LD structured data is present."))
    else:
        checks.append(
            _check(
                "Technical",
                "Structured Data (JSON-LD)",
                "warning",
                "No JSON-LD structured data found.",
                "Add structured data markup to improve rich-result eligibility.",
            )
        )

    # Canonical tag
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical and canonical.get("href"):
        checks.append(_check("Technical", "Canonical Tag", "pass", f"Canonical tag present: {canonical.get('href')[:80]}"))
    else:
        checks.append(
            _check(
                "Technical",
                "Canonical Tag",
                "warning",
                "No canonical tag found.",
                "Add a canonical tag to prevent duplicate content issues.",
            )
        )

    return checks


def _onpage_checks(
    soup: BeautifulSoup,
    keyword: Optional[str],
) -> List[Dict[str, str]]:
    checks: List[Dict[str, str]] = []
    kw = keyword.lower().strip() if keyword else None

    # Meta title
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    title_len = len(title_text)
    if not title_text:
        checks.append(
            _check("OnPage", "Meta Title", "fail", "No <title> tag found.", "Add a descriptive page title (50–60 characters).")
        )
    elif 50 <= title_len <= 60:
        checks.append(_check("OnPage", "Meta Title", "pass", f"Title is {title_len} chars: \"{title_text[:70]}\""))
    elif title_len < 50:
        checks.append(
            _check(
                "OnPage",
                "Meta Title",
                "warning",
                f"Title is short ({title_len} chars): \"{title_text[:70]}\"",
                "Expand the title to 50–60 characters for better visibility.",
            )
        )
    else:
        checks.append(
            _check(
                "OnPage",
                "Meta Title",
                "warning",
                f"Title is long ({title_len} chars): \"{title_text[:70]}\"",
                "Shorten the title to 50–60 characters to avoid truncation in SERPs.",
            )
        )

    # Meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc_text = desc_tag.get("content", "").strip() if desc_tag else ""
    desc_len = len(desc_text)
    if not desc_text:
        checks.append(
            _check("OnPage", "Meta Description", "fail", "No meta description found.", "Add a meta description (150–160 characters).")
        )
    elif 150 <= desc_len <= 160:
        checks.append(_check("OnPage", "Meta Description", "pass", f"Description is {desc_len} chars."))
    elif desc_len < 150:
        checks.append(
            _check(
                "OnPage",
                "Meta Description",
                "warning",
                f"Description is short ({desc_len} chars).",
                "Expand the meta description to 150–160 characters.",
            )
        )
    else:
        checks.append(
            _check(
                "OnPage",
                "Meta Description",
                "warning",
                f"Description is long ({desc_len} chars).",
                "Shorten the meta description to 150–160 characters.",
            )
        )

    # H1 tag
    h1_tags = soup.find_all("h1")
    h1_count = len(h1_tags)
    h1_text = h1_tags[0].get_text(strip=True) if h1_tags else ""
    if h1_count == 0:
        checks.append(_check("OnPage", "H1 Tag", "fail", "No H1 tag found.", "Add exactly one H1 tag that describes the page content."))
    elif h1_count == 1:
        checks.append(_check("OnPage", "H1 Tag", "pass", f"Exactly one H1 found: \"{h1_text[:70]}\""))
    else:
        checks.append(
            _check(
                "OnPage",
                "H1 Tag",
                "warning",
                f"Multiple H1 tags found ({h1_count}).",
                "Use only one H1 per page for clear document structure.",
            )
        )

    # H2 tags
    h2_tags = soup.find_all("h2")
    if h2_tags:
        checks.append(_check("OnPage", "H2 Tags", "pass", f"{len(h2_tags)} H2 tag(s) found."))
    else:
        checks.append(
            _check("OnPage", "H2 Tags", "warning", "No H2 tags found.", "Use H2 tags to structure content into sections.")
        )

    # OG tags
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    og_image = soup.find("meta", attrs={"property": "og:image"})
    og_count = sum(1 for t in [og_title, og_desc, og_image] if t)
    if og_count == 3:
        checks.append(_check("OnPage", "Open Graph Tags", "pass", "og:title, og:description, og:image all present."))
    elif og_count > 0:
        missing = [n for n, t in [("og:title", og_title), ("og:description", og_desc), ("og:image", og_image)] if not t]
        checks.append(
            _check(
                "OnPage",
                "Open Graph Tags",
                "warning",
                f"Some OG tags missing: {', '.join(missing)}.",
                "Add all three core OG tags for better social sharing.",
            )
        )
    else:
        checks.append(
            _check("OnPage", "Open Graph Tags", "fail", "No Open Graph tags found.", "Add OG meta tags to control how your page appears on social media.")
        )

    # Twitter card
    twitter_card = soup.find("meta", attrs={"name": "twitter:card"})
    if twitter_card:
        checks.append(_check("OnPage", "Twitter Card", "pass", "Twitter Card meta tag found."))
    else:
        checks.append(
            _check("OnPage", "Twitter Card", "warning", "No Twitter Card meta tag.", "Add Twitter Card tags for better sharing on Twitter/X.")
        )

    # Favicon
    favicon = (
        soup.find("link", attrs={"rel": "icon"})
        or soup.find("link", attrs={"rel": "shortcut icon"})
    )
    if favicon:
        checks.append(_check("OnPage", "Favicon", "pass", "Favicon link tag found."))
    else:
        checks.append(
            _check("OnPage", "Favicon", "warning", "No favicon link tag found.", "Add a favicon to improve brand recognition in browser tabs.")
        )

    # Keyword checks (only when keyword provided)
    if kw:
        kw_in_title = kw in title_text.lower()
        checks.append(
            _check(
                "OnPage",
                "Keyword in Title",
                "pass" if kw_in_title else "fail",
                f"Keyword '{keyword}' {'found' if kw_in_title else 'NOT found'} in title.",
                "" if kw_in_title else f"Include '{keyword}' in the page title.",
            )
        )
        kw_in_desc = kw in desc_text.lower()
        checks.append(
            _check(
                "OnPage",
                "Keyword in Description",
                "pass" if kw_in_desc else "warning",
                f"Keyword '{keyword}' {'found' if kw_in_desc else 'NOT found'} in meta description.",
                "" if kw_in_desc else f"Mention '{keyword}' naturally in the meta description.",
            )
        )
        kw_in_h1 = kw in h1_text.lower() if h1_text else False
        checks.append(
            _check(
                "OnPage",
                "Keyword in H1",
                "pass" if kw_in_h1 else "warning",
                f"Keyword '{keyword}' {'found' if kw_in_h1 else 'NOT found'} in H1.",
                "" if kw_in_h1 else f"Include '{keyword}' in your main heading.",
            )
        )

    return checks


def _performance_checks(
    soup: BeautifulSoup,
    response: requests.Response,
    load_time_ms: float,
) -> List[Dict[str, str]]:
    checks: List[Dict[str, str]] = []

    # Page size
    page_size_kb = len(response.content) / 1024
    if page_size_kb < 1024:
        checks.append(_check("Performance", "Page Size", "pass", f"Page size is {page_size_kb:.1f} KB (under 1 MB)."))
    elif page_size_kb < 3072:
        checks.append(
            _check(
                "Performance",
                "Page Size",
                "warning",
                f"Page size is {page_size_kb:.1f} KB.",
                "Consider optimising images and minifying resources to reduce page size.",
            )
        )
    else:
        checks.append(
            _check(
                "Performance",
                "Page Size",
                "fail",
                f"Page size is {page_size_kb:.1f} KB (over 3 MB).",
                "Significantly reduce page size by compressing images and removing unused code.",
            )
        )

    # Image alt tags
    images = soup.find_all("img")
    missing_alt = [img for img in images if not img.get("alt")]
    total_images = len(images)
    if total_images == 0:
        checks.append(_check("Performance", "Image Alt Tags", "pass", "No images found on the page."))
    elif not missing_alt:
        checks.append(_check("Performance", "Image Alt Tags", "pass", f"All {total_images} image(s) have alt attributes."))
    else:
        checks.append(
            _check(
                "Performance",
                "Image Alt Tags",
                "warning" if len(missing_alt) <= total_images // 2 else "fail",
                f"{len(missing_alt)} of {total_images} image(s) missing alt text.",
                "Add descriptive alt text to all images for accessibility and SEO.",
            )
        )

    # Load time estimate
    if load_time_ms < 2000:
        checks.append(_check("Performance", "Load Time", "pass", f"Estimated load time: {load_time_ms:.0f} ms."))
    elif load_time_ms < 4000:
        checks.append(
            _check(
                "Performance",
                "Load Time",
                "warning",
                f"Estimated load time: {load_time_ms:.0f} ms.",
                "Aim for under 2 seconds. Consider caching, CDN, and resource optimisation.",
            )
        )
    else:
        checks.append(
            _check(
                "Performance",
                "Load Time",
                "fail",
                f"Estimated load time: {load_time_ms:.0f} ms.",
                "Load time is high. Investigate server response time, large assets, and render-blocking resources.",
            )
        )

    return checks


def _links_checks(
    soup: BeautifulSoup,
    base_url: str,
    url: str,
) -> List[Dict[str, str]]:
    checks: List[Dict[str, str]] = []
    parsed_base = urlparse(url)
    base_domain = parsed_base.netloc

    all_links = [
        a.get("href", "").strip()
        for a in soup.find_all("a", href=True)
        if a.get("href", "").strip()
        and not a["href"].startswith(("#", "mailto:", "javascript:", "tel:"))
    ]
    abs_links = list({urljoin(url, lnk) for lnk in all_links})
    http_links = [lnk for lnk in abs_links if lnk.startswith(("http://", "https://"))]

    internal = [lnk for lnk in http_links if urlparse(lnk).netloc == base_domain]
    external = [lnk for lnk in http_links if urlparse(lnk).netloc != base_domain]

    checks.append(_check("Links", "Internal Links", "pass", f"{len(internal)} internal link(s) found."))
    checks.append(_check("Links", "External Links", "pass", f"{len(external)} external link(s) found."))

    # Broken link detection — sample up to 10
    sample = http_links[:10]
    broken: List[str] = []
    for lnk in sample:
        resp = _safe_head(lnk)
        if resp is None or resp.status_code >= 400:
            status_code = resp.status_code if resp else "unreachable"
            broken.append(f"{lnk} (HTTP {status_code})")

    if broken:
        checks.append(
            _check(
                "Links",
                "Broken Links",
                "fail",
                f"{len(broken)} broken link(s) found in sample of {len(sample)}: {'; '.join(broken[:3])}",
                "Fix or remove broken links to improve user experience and crawlability.",
            )
        )
    else:
        checks.append(
            _check("Links", "Broken Links", "pass", f"No broken links found in sample of {len(sample)} links.")
        )

    return checks


# ---------------------------------------------------------------------------
# Score calculation
# ---------------------------------------------------------------------------

def _calculate_score(checks: List[Dict[str, str]]) -> int:
    """Weighted score: pass=1, warning=0.5, fail=0 per check."""
    if not checks:
        return 0
    total_weight = len(checks)
    earned = sum(
        1.0 if c["status"] == "pass" else (0.5 if c["status"] == "warning" else 0.0)
        for c in checks
    )
    return min(100, max(0, round((earned / total_weight) * 100)))


def _category_scores(checks: List[Dict[str, str]]) -> Dict[str, int]:
    """Return per-category score as 0–100 int."""
    from collections import defaultdict

    cat_checks: Dict[str, list] = defaultdict(list)
    for c in checks:
        cat_checks[c["category"]].append(c)
    return {cat: _calculate_score(cc) for cat, cc in cat_checks.items()}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_full_audit(url: str, keyword: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a comprehensive SEO audit against *url*.

    Returns a structured dict with keys:
      score, url, timestamp, checks, summary, categories, page_info
    """
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # ---- Validate URL before any network activity ----------------------
    if _validated_url(url) is None:
        return {
            "score": 0,
            "url": url,
            "timestamp": timestamp,
            "error": "URL rejected: must be a publicly accessible http/https address.",
            "checks": [],
            "summary": {"total": 0, "passed": 0, "warnings": 0, "failed": 0, "score": 0},
            "categories": {},
            "page_info": {},
        }

    # ---- Fetch the page ------------------------------------------------
    start = time.time()
    response = _safe_get(url)
    load_time_ms = (time.time() - start) * 1000

    if response is None or response.status_code != 200:
        status_code = response.status_code if response else "unreachable"
        return {
            "score": 0,
            "url": url,
            "timestamp": timestamp,
            "error": f"Unable to fetch URL (status: {status_code})",
            "checks": [],
            "summary": {"total": 0, "passed": 0, "warnings": 0, "failed": 0, "score": 0},
            "categories": {},
            "page_info": {},
        }

    soup = BeautifulSoup(response.text, "html.parser")
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # ---- Run all checks ------------------------------------------------
    checks: List[Dict[str, str]] = []
    checks.extend(_technical_checks(url, soup, response, base_url))
    checks.extend(_onpage_checks(soup, keyword))
    checks.extend(_performance_checks(soup, response, load_time_ms))
    checks.extend(_links_checks(soup, base_url, url))

    # ---- Build summary -------------------------------------------------
    passed = sum(1 for c in checks if c["status"] == "pass")
    warnings = sum(1 for c in checks if c["status"] == "warning")
    failed = sum(1 for c in checks if c["status"] == "fail")
    score = _calculate_score(checks)

    summary = {
        "total": len(checks),
        "passed": passed,
        "warnings": warnings,
        "failed": failed,
        "score": score,
    }

    # ---- Page info -----------------------------------------------------
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc_text = desc_tag.get("content", "").strip() if desc_tag else ""
    h1_tags = soup.find_all("h1")
    h2_tags = soup.find_all("h2")
    h3_tags = soup.find_all("h3")
    all_links = soup.find_all("a", href=True)
    internal_links = [
        a for a in all_links
        if urlparse(urljoin(url, a["href"])).netloc == parsed.netloc
    ]
    external_links = [
        a for a in all_links
        if urlparse(urljoin(url, a["href"])).netloc != parsed.netloc
        and a["href"].startswith(("http://", "https://"))
    ]

    page_info = {
        "title": title_text,
        "description": desc_text,
        "h1_count": len(h1_tags),
        "h1_text": h1_tags[0].get_text(strip=True) if h1_tags else "",
        "heading_structure": {
            "h1": len(h1_tags),
            "h2": len(h2_tags),
            "h3": len(h3_tags),
        },
        "page_size_kb": round(len(response.content) / 1024, 1),
        "load_time_ms": round(load_time_ms),
        "link_count": len(all_links),
        "internal_links": len(internal_links),
        "external_links": len(external_links),
        "broken_links": [],  # populated by link checks above
    }

    return {
        "score": score,
        "url": url,
        "timestamp": timestamp,
        "checks": checks,
        "summary": summary,
        "categories": _category_scores(checks),
        "page_info": page_info,
    }
