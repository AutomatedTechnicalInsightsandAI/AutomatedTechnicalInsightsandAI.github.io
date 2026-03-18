"""Free SEO Audit Tool — Enhanced Production Version
ATI & AI | AutomatedTechnicalInsightsandAI.github.io
"""

import csv
import io
import json
import os
import socket
import ssl
import zipfile
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup
import plotly.graph_objects as go

# Load .env file for local development if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Constants ──────────────────────────────────────────────────────────────────
MAX_LINKS_TO_CHECK = 10
HEADERS = {
    "User-Agent": (
        "ATI-SEO-AuditBot/1.0 (+https://automatedtechnicalinsightsandai.github.io)"
    )
}


def _get_admin_password():
    """Return admin password from Streamlit secrets or environment variable."""
    try:
        if hasattr(st, "secrets") and "ADMIN_PASSWORD" in st.secrets:
            return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        pass
    return os.getenv("ADMIN_PASSWORD", "ati-seo-admin")


# ── Page Configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Free SEO Audit Tool | ATI & AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2e86ab 100%);
        padding: 2rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    }
    .main-header h1 { color: white; margin: 0; font-size: 2rem; }
    .main-header p  { color: rgba(255,255,255,0.85); margin: 0.4rem 0 0; font-size: 1rem; }
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Session State ──────────────────────────────────────────────────────────────
if "audit_history" not in st.session_state:
    st.session_state.audit_history = []
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False


# ── Advanced SEO Check Helpers ─────────────────────────────────────────────────

def check_og_tags(soup):
    """Check Open Graph meta tags."""
    required = ["og:title", "og:description", "og:image", "og:url"]
    found = {}
    for tag in required:
        meta = soup.find("meta", property=tag) or soup.find(
            "meta", attrs={"property": tag}
        )
        found[tag] = meta.get("content", "").strip() if meta else None
    present = [k for k, v in found.items() if v]
    missing = [k for k, v in found.items() if not v]
    score = int(len(present) / len(required) * 100)
    return {
        "found": found,
        "present": present,
        "missing": missing,
        "score": score,
        "status": "pass" if score == 100 else ("warn" if score >= 50 else "fail"),
    }


def check_twitter_tags(soup):
    """Check Twitter Card meta tags."""
    required = ["twitter:card", "twitter:title", "twitter:description"]
    found = {}
    for tag in required:
        meta = soup.find("meta", attrs={"name": tag})
        found[tag] = meta.get("content", "").strip() if meta else None
    present = [k for k, v in found.items() if v]
    missing = [k for k, v in found.items() if not v]
    score = int(len(present) / len(required) * 100)
    return {
        "found": found,
        "present": present,
        "missing": missing,
        "score": score,
        "status": "pass" if score == 100 else ("warn" if score >= 33 else "fail"),
    }


def check_favicon(soup, website):
    """Check favicon presence."""
    for link_tag in soup.find_all("link"):
        rel = link_tag.get("rel", [])
        if any(r in rel for r in ("icon", "shortcut icon", "apple-touch-icon")):
            href = link_tag.get("href", "")
            favicon_url = urljoin(website, href) if href else None
            return {"present": True, "url": favicon_url, "status": "pass"}

    # Try default /favicon.ico
    parsed = urlparse(website)
    favicon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
    try:
        resp = requests.head(favicon_url, timeout=5, headers=HEADERS)
        if resp.status_code == 200:
            return {"present": True, "url": favicon_url, "status": "pass"}
    except Exception:
        pass
    return {"present": False, "url": None, "status": "fail"}


def check_h1_analysis(soup):
    """Analyse H1 tags."""
    h1_tags = soup.find_all("h1")
    count = len(h1_tags)
    texts = [h.get_text(strip=True) for h in h1_tags]
    if count == 0:
        status, message = "fail", "❌ No H1 tag found — add one for SEO"
    elif count == 1:
        status, message = "pass", f'✅ Single H1: "{texts[0][:80]}"'
    else:
        status, message = "warn", f"⚠️ Multiple H1 tags ({count}) — keep only one"
    return {"count": count, "texts": texts, "status": status, "message": message}


def check_heading_structure(soup):
    """Validate heading structure H1–H6."""
    headings = {}
    for level in range(1, 7):
        tags = soup.find_all(f"h{level}")
        headings[f"h{level}"] = {
            "count": len(tags),
            "texts": [t.get_text(strip=True)[:60] for t in tags[:5]],
        }
    issues = []
    for i in range(2, 6):
        if (
            headings[f"h{i}"]["count"] == 0
            and headings[f"h{i + 1}"]["count"] > 0
        ):
            issues.append(f"H{i + 1} used without H{i} — maintain hierarchy")
    return {
        "headings": headings,
        "issues": issues,
        "status": "pass" if not issues else "warn",
    }


def check_mobile_responsiveness(soup):
    """Check for viewport meta tag."""
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport:
        content = viewport.get("content", "")
        has_width = "width=device-width" in content
        has_scale = "initial-scale" in content
        if has_width and has_scale:
            return {
                "content": content,
                "status": "pass",
                "message": f"✅ Viewport configured: {content}",
            }
        return {
            "content": content,
            "status": "warn",
            "message": f"⚠️ Viewport incomplete: {content}",
        }
    return {
        "content": None,
        "status": "fail",
        "message": "❌ No viewport meta tag — site may not be mobile-friendly",
    }


def check_structured_data(soup):
    """Detect JSON-LD or microdata structured data."""
    json_ld_scripts = soup.find_all("script", type="application/ld+json")
    microdata = soup.find_all(attrs={"itemtype": True})
    schemas = []
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string or "{}")
            schemas.append(data.get("@type", "Unknown"))
        except (json.JSONDecodeError, AttributeError):
            schemas.append("Invalid JSON-LD")
    found = bool(json_ld_scripts or microdata)
    return {
        "json_ld_count": len(json_ld_scripts),
        "microdata_count": len(microdata),
        "schemas": schemas,
        "found": found,
        "status": "pass" if found else "warn",
        "message": (
            f"✅ Found {len(json_ld_scripts)} JSON-LD + {len(microdata)} microdata block(s)"
            if found
            else "⚠️ No structured data — consider adding Schema.org markup"
        ),
    }


def check_robots_sitemap(website):
    """Check for /robots.txt and /sitemap.xml."""
    parsed = urlparse(website)
    base = f"{parsed.scheme}://{parsed.netloc}"
    results = {}
    for path, key in [("/robots.txt", "robots"), ("/sitemap.xml", "sitemap")]:
        try:
            resp = requests.get(f"{base}{path}", timeout=5, headers=HEADERS)
            results[key] = {
                "url": f"{base}{path}",
                "status_code": resp.status_code,
                "found": resp.status_code == 200,
            }
        except Exception as exc:
            results[key] = {
                "url": f"{base}{path}",
                "found": False,
                "error": str(exc),
            }
    return results


def check_ssl(website):
    """Check SSL/HTTPS status."""
    if not website.startswith("https://"):
        return {
            "https": False,
            "status": "fail",
            "message": "❌ Site does not use HTTPS — SSL required for SEO",
        }
    parsed = urlparse(website)
    hostname = parsed.netloc.split(":")[0]
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as sock:
            sock.settimeout(5)
            sock.connect((hostname, 443))
            cert = sock.getpeercert()
        expire_str = cert.get("notAfter", "")
        if expire_str:
            expire_dt = datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z")
            days_left = (expire_dt - datetime.utcnow()).days
            if days_left > 30:
                return {
                    "https": True,
                    "valid": True,
                    "days_left": days_left,
                    "status": "pass",
                    "message": f"✅ SSL valid — expires in {days_left} days",
                }
            elif days_left > 0:
                return {
                    "https": True,
                    "valid": True,
                    "days_left": days_left,
                    "status": "warn",
                    "message": f"⚠️ SSL expiring soon — {days_left} days left",
                }
            else:
                return {
                    "https": True,
                    "valid": False,
                    "days_left": 0,
                    "status": "fail",
                    "message": "❌ SSL certificate has expired",
                }
    except Exception:
        pass
    # HTTPS in use but cert details unavailable
    return {
        "https": True,
        "valid": True,
        "status": "pass",
        "message": "✅ HTTPS enabled",
    }


def check_page_speed(response, soup):
    """Estimate page speed via basic metrics."""
    page_size_kb = round(len(response.content) / 1024, 1)
    n_scripts = len(soup.find_all("script", src=True))
    n_styles = len(
        soup.find_all("link", rel=lambda r: bool(r and "stylesheet" in r))
    )
    n_images = len(soup.find_all("img"))
    total_assets = n_scripts + n_styles + n_images
    if page_size_kb < 500 and total_assets < 30:
        status, note = "pass", "✅ Lightweight page"
    elif page_size_kb < 1000 and total_assets < 60:
        status, note = "warn", "⚠️ Moderate page weight"
    else:
        status, note = "fail", "❌ Heavy page — consider optimization"
    return {
        "page_size_kb": page_size_kb,
        "n_scripts": n_scripts,
        "n_stylesheets": n_styles,
        "n_images": n_images,
        "total_assets": total_assets,
        "status": status,
        "note": note,
    }


# ── Core Audit Function ────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def perform_seo_audit(website, keyword=None):
    """Perform a comprehensive SEO audit on the given URL."""
    try:
        response = requests.get(website, timeout=10, headers=HEADERS)
    except requests.RequestException as exc:
        return {"error": f"Failed to reach {website}. Reason: {str(exc)}"}

    accessible = response.status_code == 200
    if not accessible:
        return {
            "error": None,
            "url": website,
            "timestamp": datetime.utcnow().isoformat(),
            "accessible": False,
            "status_code": response.status_code,
        }

    soup = BeautifulSoup(response.text, "html.parser")

    # Basic meta
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc_text = desc_tag.get("content", "").strip() if desc_tag else ""

    keyword_results = {}
    if keyword:
        kw = keyword.lower()
        keyword_results = {
            "keyword": keyword,
            "in_title": kw in title_text.lower(),
            "in_description": kw in desc_text.lower(),
        }

    # Links check (preserves original logic)
    raw_links = [
        urljoin(website, a["href"])
        for a in soup.find_all("a", href=True)
        if a["href"]
        and not a["href"].startswith(("#", "mailto:", "javascript:", "tel:"))
    ]
    seen: set = set()
    sampled_links = []
    for link in raw_links:
        if link not in seen and link.startswith(("http://", "https://")):
            seen.add(link)
            sampled_links.append(link)
            if len(sampled_links) == MAX_LINKS_TO_CHECK:
                break

    broken = []
    ok_links = []
    for link in sampled_links:
        try:
            link_resp = requests.head(
                link, timeout=5, allow_redirects=True, headers=HEADERS
            )
            if link_resp.status_code == 405:
                # Some servers don't support HEAD; fall back to GET
                link_resp = requests.get(
                    link, timeout=5, allow_redirects=True, headers=HEADERS
                )
            if link_resp.status_code >= 400:
                broken.append({"url": link, "code": link_resp.status_code})
            else:
                ok_links.append({"url": link, "code": link_resp.status_code})
        except requests.RequestException as exc:
            broken.append({"url": link, "code": None, "error": str(exc)})

    total_on_page = len(
        {
            urljoin(website, a["href"])
            for a in soup.find_all("a", href=True)
            if a["href"]
        }
    )

    return {
        "error": None,
        "url": website,
        "keyword": keyword,
        "timestamp": datetime.utcnow().isoformat(),
        "accessible": True,
        "status_code": response.status_code,
        "title": title_text,
        "description": desc_text,
        "keyword_results": keyword_results,
        "links": {
            "sampled": sampled_links,
            "broken": broken,
            "ok": ok_links,
            "total_on_page": total_on_page,
        },
        "og_tags": check_og_tags(soup),
        "twitter_tags": check_twitter_tags(soup),
        "favicon": check_favicon(soup, website),
        "h1": check_h1_analysis(soup),
        "headings": check_heading_structure(soup),
        "mobile": check_mobile_responsiveness(soup),
        "structured_data": check_structured_data(soup),
        "robots_sitemap": check_robots_sitemap(website),
        "ssl": check_ssl(website),
        "page_speed": check_page_speed(response, soup),
    }


# ── SEO Score Calculator ───────────────────────────────────────────────────────

def calculate_seo_score(results):
    """Calculate SEO score (0–100) broken down by category."""
    if not results.get("accessible"):
        return {"total": 0, "categories": {}}

    categories = {
        "Technical SEO":        {"score": 0, "max": 30, "checks": []},
        "On-Page SEO":          {"score": 0, "max": 35, "checks": []},
        "Performance & Mobile": {"score": 0, "max": 20, "checks": []},
        "Links & Indexing":     {"score": 0, "max": 15, "checks": []},
    }

    # Technical SEO (30 pts)
    ssl_status = results.get("ssl", {}).get("status", "fail")
    pts = 10 if ssl_status == "pass" else (6 if ssl_status == "warn" else 0)
    categories["Technical SEO"]["score"] += pts
    categories["Technical SEO"]["checks"].append(("SSL Certificate", ssl_status))

    rs = results.get("robots_sitemap", {})
    for key, label in [("robots", "robots.txt"), ("sitemap", "sitemap.xml")]:
        if rs.get(key, {}).get("found"):
            categories["Technical SEO"]["score"] += 5
            categories["Technical SEO"]["checks"].append((label, "pass"))
        else:
            categories["Technical SEO"]["checks"].append((label, "fail"))

    if results.get("structured_data", {}).get("status") == "pass":
        categories["Technical SEO"]["score"] += 10
        categories["Technical SEO"]["checks"].append(("Structured Data", "pass"))
    else:
        categories["Technical SEO"]["checks"].append(("Structured Data", "warn"))

    # On-Page SEO (35 pts)
    title = results.get("title", "")
    if title:
        pts = 8 if 30 <= len(title) <= 65 else 5
        categories["On-Page SEO"]["score"] += pts
        categories["On-Page SEO"]["checks"].append(
            ("Meta Title", "pass" if pts == 8 else "warn")
        )
    else:
        categories["On-Page SEO"]["checks"].append(("Meta Title", "fail"))

    desc = results.get("description", "")
    if desc:
        pts = 8 if 50 <= len(desc) <= 160 else 5
        categories["On-Page SEO"]["score"] += pts
        categories["On-Page SEO"]["checks"].append(
            ("Meta Description", "pass" if pts == 8 else "warn")
        )
    else:
        categories["On-Page SEO"]["checks"].append(("Meta Description", "fail"))

    h1_status = results.get("h1", {}).get("status", "fail")
    pts = 7 if h1_status == "pass" else (3 if h1_status == "warn" else 0)
    categories["On-Page SEO"]["score"] += pts
    categories["On-Page SEO"]["checks"].append(("H1 Tag", h1_status))

    og_pts = round(results.get("og_tags", {}).get("score", 0) / 100 * 6)
    categories["On-Page SEO"]["score"] += og_pts
    categories["On-Page SEO"]["checks"].append(
        ("Open Graph Tags", results.get("og_tags", {}).get("status", "fail"))
    )

    tw_pts = round(results.get("twitter_tags", {}).get("score", 0) / 100 * 6)
    categories["On-Page SEO"]["score"] += tw_pts
    categories["On-Page SEO"]["checks"].append(
        ("Twitter Cards", results.get("twitter_tags", {}).get("status", "fail"))
    )

    # Performance & Mobile (20 pts)
    mobile_status = results.get("mobile", {}).get("status", "fail")
    pts = 8 if mobile_status == "pass" else (4 if mobile_status == "warn" else 0)
    categories["Performance & Mobile"]["score"] += pts
    categories["Performance & Mobile"]["checks"].append(("Viewport/Mobile", mobile_status))

    if results.get("favicon", {}).get("status") == "pass":
        categories["Performance & Mobile"]["score"] += 4
        categories["Performance & Mobile"]["checks"].append(("Favicon", "pass"))
    else:
        categories["Performance & Mobile"]["checks"].append(("Favicon", "fail"))

    speed_status = results.get("page_speed", {}).get("status", "fail")
    pts = 8 if speed_status == "pass" else (4 if speed_status == "warn" else 0)
    categories["Performance & Mobile"]["score"] += pts
    categories["Performance & Mobile"]["checks"].append(("Page Speed", speed_status))

    # Links & Indexing (15 pts)
    links = results.get("links", {})
    broken_count = len(links.get("broken", []))
    sampled_count = len(links.get("sampled", []))
    if sampled_count > 0:
        ratio = broken_count / sampled_count
        if ratio == 0:
            categories["Links & Indexing"]["score"] += 15
            categories["Links & Indexing"]["checks"].append(("Broken Links", "pass"))
        elif ratio < 0.2:
            categories["Links & Indexing"]["score"] += 8
            categories["Links & Indexing"]["checks"].append(("Broken Links", "warn"))
        else:
            categories["Links & Indexing"]["checks"].append(("Broken Links", "fail"))
    else:
        categories["Links & Indexing"]["score"] += 15
        categories["Links & Indexing"]["checks"].append(("Broken Links", "pass"))

    total_max = sum(c["max"] for c in categories.values())
    total_score = sum(c["score"] for c in categories.values())
    normalized = round(total_score / total_max * 100)
    return {
        "total": normalized,
        "categories": {
            k: {**v, "pct": round(v["score"] / v["max"] * 100)}
            for k, v in categories.items()
        },
    }


# ── Recommendations Generator ──────────────────────────────────────────────────

def generate_recommendations(results):
    """Generate prioritised, actionable SEO recommendations."""
    recs = []
    title = results.get("title", "")
    if not title:
        recs.append("🔴 **Add a `<title>` tag** — every page needs a unique, descriptive title.")
    elif not (30 <= len(title) <= 65):
        recs.append(
            f"🟡 **Optimize title length** — currently {len(title)} chars; target 30–65."
        )

    desc = results.get("description", "")
    if not desc:
        recs.append(
            "🔴 **Add a meta description** — improves click-through rate from search results."
        )
    elif not (50 <= len(desc) <= 160):
        recs.append(
            f"🟡 **Optimize description length** — currently {len(desc)} chars; target 50–160."
        )

    h1 = results.get("h1", {})
    if h1.get("count", 0) == 0:
        recs.append("🔴 **Add an H1 tag** — every page needs exactly one H1.")
    elif h1.get("count", 0) > 1:
        recs.append("🟡 **Remove duplicate H1 tags** — keep only one per page.")

    og_missing = results.get("og_tags", {}).get("missing", [])
    if og_missing:
        recs.append(
            f"🟡 **Add Open Graph tags**: `{'`, `'.join(og_missing)}` — improves social sharing."
        )

    tw_missing = results.get("twitter_tags", {}).get("missing", [])
    if tw_missing:
        recs.append(
            f"🟡 **Add Twitter Card tags**: `{'`, `'.join(tw_missing)}` — improves Twitter previews."
        )

    if results.get("ssl", {}).get("status") == "fail":
        recs.append("🔴 **Enable HTTPS/SSL** — critical for SEO ranking and user trust.")

    if results.get("mobile", {}).get("status") != "pass":
        recs.append(
            "🔴 **Add viewport meta tag** — required for mobile-friendly search ranking."
        )

    if not results.get("favicon", {}).get("present"):
        recs.append("🟡 **Add a favicon** — improves brand recognition in browser tabs.")

    rs = results.get("robots_sitemap", {})
    if not rs.get("robots", {}).get("found"):
        recs.append(
            "🟡 **Create `robots.txt`** — helps search engines crawl your site properly."
        )
    if not rs.get("sitemap", {}).get("found"):
        recs.append(
            "🟡 **Create `sitemap.xml`** — helps search engines discover and index pages."
        )

    if not results.get("structured_data", {}).get("found"):
        recs.append(
            "🟡 **Add Schema.org markup** — enables rich snippets in search results."
        )

    broken = results.get("links", {}).get("broken", [])
    if broken:
        recs.append(
            f"🔴 **Fix {len(broken)} broken link(s)** — broken links hurt SEO and UX."
        )

    if results.get("page_speed", {}).get("status") == "fail":
        recs.append(
            "🟡 **Optimize page speed** — reduce assets/page size for faster load times."
        )

    return recs


# ── Plotly Chart Helpers ───────────────────────────────────────────────────────

def _gauge_chart(score):
    """SEO score gauge."""
    if score >= 80:
        color, label = "#27ae60", "Excellent"
    elif score >= 60:
        color, label = "#f39c12", "Good"
    elif score >= 40:
        color, label = "#e67e22", "Needs Work"
    else:
        color, label = "#e74c3c", "Poor"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={
                "text": (
                    f"SEO Score<br>"
                    f"<span style='font-size:0.8em;color:{color}'>{label}</span>"
                )
            },
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": color},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
                    {"range": [0,  40], "color": "#fde8e8"},
                    {"range": [40, 60], "color": "#fef3e2"},
                    {"range": [60, 80], "color": "#fefae0"},
                    {"range": [80, 100], "color": "#e8f8e8"},
                ],
            },
            number={"suffix": "/100", "font": {"size": 28}},
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _link_pie_chart(results):
    """Link status pie chart."""
    links = results.get("links", {})
    broken_count = len(links.get("broken", []))
    ok_count = len(links.get("ok", []))
    if broken_count == 0 and ok_count == 0:
        return None
    fig = go.Figure(
        go.Pie(
            labels=["✅ Working", "❌ Broken"],
            values=[ok_count, broken_count],
            hole=0.4,
            marker_colors=["#27ae60", "#e74c3c"],
            textinfo="label+percent+value",
        )
    )
    fig.update_layout(
        title="Link Status Distribution",
        height=300,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _heading_bar_chart(results):
    """Heading structure bar chart."""
    headings = results.get("headings", {}).get("headings", {})
    if not headings:
        return None
    levels = [f"H{i}" for i in range(1, 7)]
    counts = [headings.get(f"h{i}", {}).get("count", 0) for i in range(1, 7)]
    colors = ["#1e3a5f", "#2e86ab", "#3498db", "#5dade2", "#85c1e9", "#aed6f1"]
    fig = go.Figure(
        go.Bar(x=levels, y=counts, marker_color=colors, text=counts, textposition="auto")
    )
    fig.update_layout(
        title="Heading Structure (H1–H6)",
        xaxis_title="Heading Level",
        yaxis_title="Count",
        height=300,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _category_bar_chart(score_data):
    """Category score bar chart."""
    categories = score_data.get("categories", {})
    if not categories:
        return None
    names = list(categories.keys())
    pcts = [c["pct"] for c in categories.values()]
    colors = [
        "#27ae60" if p >= 80 else "#f39c12" if p >= 60 else "#e74c3c" for p in pcts
    ]
    fig = go.Figure(
        go.Bar(
            x=names,
            y=pcts,
            marker_color=colors,
            text=[f"{p}%" for p in pcts],
            textposition="auto",
        )
    )
    fig.update_layout(
        title="Score by Category",
        yaxis={"range": [0, 100], "title": "Score (%)"},
        height=300,
        margin=dict(l=10, r=10, t=50, b=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── Export Helpers (Admin Only) ────────────────────────────────────────────────

def _export_csv(audit_list):
    """Serialize audit list to CSV string."""
    if not audit_list:
        return ""
    fieldnames = [
        "timestamp", "url", "keyword", "seo_score",
        "title", "title_length", "description", "description_length",
        "h1_count", "h1_status",
        "og_score", "twitter_score",
        "mobile_status", "favicon_status", "ssl_status",
        "robots_found", "sitemap_found", "structured_data_found",
        "broken_links", "total_sampled_links",
        "page_size_kb", "total_assets",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in audit_list:
        score_data = calculate_seo_score(r)
        rs = r.get("robots_sitemap", {})
        writer.writerow(
            {
                "timestamp":             r.get("timestamp", ""),
                "url":                   r.get("url", ""),
                "keyword":               r.get("keyword", ""),
                "seo_score":             score_data.get("total", 0),
                "title":                 r.get("title", ""),
                "title_length":          len(r.get("title", "")),
                "description":           r.get("description", ""),
                "description_length":    len(r.get("description", "")),
                "h1_count":              r.get("h1", {}).get("count", 0),
                "h1_status":             r.get("h1", {}).get("status", ""),
                "og_score":              r.get("og_tags", {}).get("score", 0),
                "twitter_score":         r.get("twitter_tags", {}).get("score", 0),
                "mobile_status":         r.get("mobile", {}).get("status", ""),
                "favicon_status":        r.get("favicon", {}).get("status", ""),
                "ssl_status":            r.get("ssl", {}).get("status", ""),
                "robots_found":          rs.get("robots", {}).get("found", False),
                "sitemap_found":         rs.get("sitemap", {}).get("found", False),
                "structured_data_found": r.get("structured_data", {}).get("found", False),
                "broken_links":          len(r.get("links", {}).get("broken", [])),
                "total_sampled_links":   len(r.get("links", {}).get("sampled", [])),
                "page_size_kb":          r.get("page_speed", {}).get("page_size_kb", 0),
                "total_assets":          r.get("page_speed", {}).get("total_assets", 0),
            }
        )
    return output.getvalue()


def _export_json(audit_list):
    """Serialize audit list to JSON string (enriched with scores)."""
    enriched = []
    for r in audit_list:
        score_data = calculate_seo_score(r)
        enriched.append(
            {
                "seo_score": score_data.get("total", 0),
                "score_by_category": {
                    k: {"score": v["score"], "max": v["max"], "pct": v["pct"]}
                    for k, v in score_data.get("categories", {}).items()
                },
                **r,
            }
        )
    return json.dumps(enriched, indent=2, default=str)


def _session_zip(audit_list):
    """Create a ZIP bundle (CSV + JSON) of all session audits."""
    buf = io.BytesIO()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"seo_audit_{ts}.csv",  _export_csv(audit_list))
        zf.writestr(f"seo_audit_{ts}.json", _export_json(audit_list))
    buf.seek(0)
    return buf.read()


# ── Dashboard Tab Renderers ────────────────────────────────────────────────────

def _render_technical(results):
    ssl_info = results.get("ssl", {})
    rs = results.get("robots_sitemap", {})
    sd = results.get("structured_data", {})
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("🔒 SSL Certificate", expanded=True):
            st.markdown(ssl_info.get("message", "Unknown"))
            if ssl_info.get("days_left") is not None:
                st.metric("Days Until Expiry", ssl_info["days_left"])
        with st.expander("🤖 robots.txt", expanded=True):
            rob = rs.get("robots", {})
            if rob.get("found"):
                st.success(f"✅ Found at {rob.get('url', '')}")
            else:
                st.error(f"❌ Not found at {rob.get('url', 'unknown')}")
    with col2:
        with st.expander("🗺️ sitemap.xml", expanded=True):
            sit = rs.get("sitemap", {})
            if sit.get("found"):
                st.success(f"✅ Found at {sit.get('url', '')}")
            else:
                st.error(f"❌ Not found at {sit.get('url', 'unknown')}")
        with st.expander("📊 Structured Data", expanded=True):
            st.markdown(sd.get("message", ""))
            if sd.get("schemas"):
                st.markdown("**Schema types:** " + ", ".join(sd["schemas"]))


def _render_onpage(results):
    title = results.get("title", "")
    desc = results.get("description", "")
    h1 = results.get("h1", {})
    og = results.get("og_tags", {})
    tw = results.get("twitter_tags", {})
    kw = results.get("keyword_results", {})
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("📰 Meta Title", expanded=True):
            if title:
                tlen = len(title)
                icon = "✅" if 30 <= tlen <= 65 else "⚠️"
                st.markdown(f"**Title:** {title}")
                st.markdown(f"**Length:** {tlen} chars {icon} *(ideal: 30–65)*")
            else:
                st.error("❌ No `<title>` tag found")
        with st.expander("📝 Meta Description", expanded=True):
            if desc:
                dlen = len(desc)
                icon = "✅" if 50 <= dlen <= 160 else "⚠️"
                st.markdown(f"**Description:** {desc}")
                st.markdown(f"**Length:** {dlen} chars {icon} *(ideal: 50–160)*")
            else:
                st.error("❌ No meta description found")
        if kw:
            with st.expander("🔑 Keyword Analysis", expanded=True):
                st.markdown(f"**Keyword:** `{kw.get('keyword', '')}`")
                st.markdown(
                    "✅ In title" if kw.get("in_title") else "❌ Not in title — consider adding it"
                )
                st.markdown(
                    "✅ In description"
                    if kw.get("in_description")
                    else "❌ Not in description"
                )
    with col2:
        with st.expander("📑 H1 Analysis", expanded=True):
            st.markdown(h1.get("message", ""))
            for i, text in enumerate(h1.get("texts", []), 1):
                st.markdown(f"  {i}. _{text}_")
        with st.expander("🏷️ Open Graph Tags", expanded=True):
            for tag, val in og.get("found", {}).items():
                if val:
                    st.success(f"✅ **{tag}**: {val[:80]}")
                else:
                    st.warning(f"⚠️ **{tag}**: Missing")
        with st.expander("🐦 Twitter Card Tags", expanded=True):
            for tag, val in tw.get("found", {}).items():
                if val:
                    st.success(f"✅ **{tag}**: {val[:80]}")
                else:
                    st.warning(f"⚠️ **{tag}**: Missing")


def _render_performance(results):
    mobile = results.get("mobile", {})
    favicon = results.get("favicon", {})
    speed = results.get("page_speed", {})
    headings = results.get("headings", {})
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("📱 Mobile Responsiveness", expanded=True):
            st.markdown(mobile.get("message", ""))
        with st.expander("🔖 Favicon", expanded=True):
            if favicon.get("present"):
                st.success(f"✅ Favicon found: {favicon.get('url', '')}")
            else:
                st.error("❌ No favicon detected")
    with col2:
        with st.expander("⚡ Page Speed Metrics", expanded=True):
            st.markdown(speed.get("note", ""))
            m1, m2, m3 = st.columns(3)
            m1.metric("Page Size", f"{speed.get('page_size_kb', 0)} KB")
            m2.metric("Scripts",   speed.get("n_scripts", 0))
            m3.metric("Images",    speed.get("n_images", 0))
        with st.expander("🏗️ Heading Structure", expanded=True):
            h_data = headings.get("headings", {})
            for level in range(1, 7):
                count = h_data.get(f"h{level}", {}).get("count", 0)
                icon = "✅" if count > 0 else "—"
                st.markdown(f"**H{level}**: {count} {icon}")
            if headings.get("issues"):
                st.warning("⚠️ Hierarchy issues:")
                for issue in headings["issues"]:
                    st.markdown(f"  - {issue}")


def _render_links(results):
    links = results.get("links", {})
    broken = links.get("broken", [])
    ok = links.get("ok", [])
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Links on Page", links.get("total_on_page", 0))
    c2.metric("Links Checked",       len(links.get("sampled", [])))
    c3.metric("Broken Links",        len(broken))
    if broken:
        st.error(f"❌ {len(broken)} broken link(s) found:")
        for b in broken:
            code = b.get("code", "N/A")
            st.markdown(f"- `{b['url']}` — HTTP {code}")
    else:
        st.success("✅ No broken links found in sample")
    if ok:
        with st.expander(f"View {len(ok)} working link(s)"):
            for link in ok:
                st.markdown(f"- ✅ [{link['url']}]({link['url']}) (HTTP {link['code']})")


def _render_charts(results, score_data):
    col1, col2 = st.columns(2)
    with col1:
        fig = _link_pie_chart(results)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No link data available")
    with col2:
        fig = _category_bar_chart(score_data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    fig = _heading_bar_chart(results)
    if fig:
        st.plotly_chart(fig, use_container_width=True)


def display_results(results, score_data):
    """Render the full results dashboard."""
    st.markdown("---")
    col_gauge, col_info = st.columns([1, 2])
    with col_gauge:
        st.plotly_chart(_gauge_chart(score_data["total"]), use_container_width=True)
    with col_info:
        st.markdown("### 📋 Quick Summary")
        st.markdown(f"**URL:** {results.get('url', '')}")
        st.markdown(f"**Audited:** {results.get('timestamp', '')} UTC")
        st.markdown("---")
        for cat, data in score_data["categories"].items():
            pct = data["pct"]
            dot = "🟢" if pct >= 80 else ("🟡" if pct >= 60 else "🔴")
            st.markdown(f"{dot} **{cat}**: {pct}%")

    st.markdown("---")
    st.markdown("## 📊 Detailed Analysis")
    tabs = st.tabs(
        ["🔒 Technical", "📝 On-Page", "📱 Performance", "🔗 Links", "📈 Charts"]
    )
    with tabs[0]:
        _render_technical(results)
    with tabs[1]:
        _render_onpage(results)
    with tabs[2]:
        _render_performance(results)
    with tabs[3]:
        _render_links(results)
    with tabs[4]:
        _render_charts(results, score_data)

    recs = generate_recommendations(results)
    if recs:
        st.markdown("---")
        st.markdown("## 💡 Recommendations")
        for rec in recs:
            st.markdown(rec)


# ── Admin Panel (Sidebar, password-protected) ──────────────────────────────────

def render_admin_panel():
    """Internal admin panel — not intended for end-users."""
    with st.sidebar:
        st.markdown("## 🔧 Admin Tools")
        if not st.session_state.admin_auth:
            pwd = st.text_input("Admin Password", type="password", key="admin_pwd_input")
            if st.button("Unlock"):
                if pwd == _get_admin_password():
                    st.session_state.admin_auth = True
                    st.rerun()
                else:
                    st.error("Invalid password")
            return

        st.success("🔓 Admin mode active")
        if st.button("🔒 Lock"):
            st.session_state.admin_auth = False
            st.rerun()

        st.markdown("---")
        st.markdown("### 📥 Export Results")
        history = st.session_state.audit_history
        if not history:
            st.info("Run at least one audit to enable export.")
        else:
            ts_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            st.metric("Audits in Session", len(history))
            st.download_button(
                "⬇️ Download CSV",
                data=_export_csv(history),
                file_name=f"seo_audit_{ts_str}.csv",
                mime="text/csv",
            )
            st.download_button(
                "⬇️ Download JSON",
                data=_export_json(history),
                file_name=f"seo_audit_{ts_str}.json",
                mime="application/json",
            )
            st.download_button(
                "⬇️ Download All (ZIP)",
                data=_session_zip(history),
                file_name=f"seo_audits_{ts_str}.zip",
                mime="application/zip",
            )

        st.markdown("---")
        st.markdown("### 🔁 Batch Audit")
        batch_urls = st.text_area(
            "Enter URLs (one per line)",
            placeholder="https://example.com\nhttps://another.com",
            height=120,
        )
        batch_kw = st.text_input("Batch Keyword (optional)", key="batch_kw")
        if st.button("▶️ Run Batch Audit"):
            urls = [u.strip() for u in batch_urls.split("\n") if u.strip()]
            if urls:
                prog = st.progress(0)
                for i, u in enumerate(urls):
                    with st.spinner(f"Auditing {u}…"):
                        r = perform_seo_audit(u, batch_kw or None)
                        if not r.get("error"):
                            st.session_state.audit_history.append(r)
                    prog.progress((i + 1) / len(urls))
                st.success(f"✅ Batch complete — {len(urls)} URL(s) audited")
            else:
                st.warning("Enter at least one URL")

        st.markdown("---")
        if st.button("🗑️ Clear Session History"):
            st.session_state.audit_history = []
            st.success("Session cleared")


# ── Main App ───────────────────────────────────────────────────────────────────

st.markdown(
    """
<div class="main-header">
    <h1>🔍 Free SEO Audit Tool</h1>
    <p>Powered by ATI &amp; AI · Uncover SEO opportunities in seconds</p>
</div>
""",
    unsafe_allow_html=True,
)

render_admin_panel()

col_url, col_kw, col_btn = st.columns([3, 2, 1])
with col_url:
    url = st.text_input(
        "Website URL",
        placeholder="https://example.com",
        label_visibility="collapsed",
    )
with col_kw:
    keyword = st.text_input(
        "Target Keyword (optional)",
        placeholder="e.g., AI tools for SEO",
        label_visibility="collapsed",
    )
with col_btn:
    run_audit = st.button("🚀 Run Audit", use_container_width=True)

if run_audit:
    if not url:
        st.error("Please enter a valid URL before running the audit.")
    else:
        progress_bar = st.progress(0, text="Starting audit…")
        try:
            progress_bar.progress(10, text="Fetching page…")
            results = perform_seo_audit(url, keyword or None)
            progress_bar.progress(80, text="Calculating score…")
            if results.get("error"):
                progress_bar.empty()
                st.error(f"❌ {results['error']}")
            elif not results.get("accessible"):
                progress_bar.empty()
                st.error(
                    f"❌ Page not accessible (HTTP {results.get('status_code', 'unknown')})"
                )
            else:
                score_data = calculate_seo_score(results)
                progress_bar.progress(100, text="Complete!")
                if results not in st.session_state.audit_history:
                    st.session_state.audit_history.append(results)
                progress_bar.empty()
                st.success(
                    f"✅ Audit complete — SEO Score: **{score_data['total']}/100**"
                )
                display_results(results, score_data)
        except Exception as exc:
            progress_bar.empty()
            st.error(f"An unexpected error occurred: {str(exc)}")
