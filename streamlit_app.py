"""Free SEO Audit Tool — Enhanced Production Version
ATI & AI | AutomatedTechnicalInsightsandAI.github.io
"""

import csv
import io
import json
import os
import smtplib
import socket
import ssl
import zipfile
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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

# Private / reserved IPv4 ranges that must never be fetched (SSRF guard)
import ipaddress as _ipaddress

_PRIVATE_NETWORKS = [
    _ipaddress.ip_network(cidr)
    for cidr in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
        "169.254.0.0/16",   # link-local
        "100.64.0.0/10",    # shared address space
        "::1/128",          # IPv6 loopback
        "fc00::/7",         # IPv6 unique local
        "fe80::/10",        # IPv6 link-local
    )
]


def _is_safe_url(url: str) -> tuple[bool, str]:
    """
    Validate that a URL is safe to fetch:
      - Must use http or https scheme
      - Hostname must resolve to a public IP (blocks SSRF to internal services)
    Returns (is_safe, reason).
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported scheme '{parsed.scheme}' — only http/https allowed"

    hostname = parsed.hostname
    if not hostname:
        return False, "No hostname in URL"

    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False, f"Cannot resolve hostname '{hostname}'"

    for _family, _type, _proto, _canonname, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        try:
            addr = _ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        for net in _PRIVATE_NETWORKS:
            if addr in net:
                return False, (
                    f"Hostname '{hostname}' resolves to a private/reserved address "
                    f"({ip_str}) — fetching internal addresses is not permitted"
                )
    return True, ""


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
  /* ── Global ── */
  #MainMenu { visibility: hidden; }
  footer     { visibility: hidden; }

  /* ── Hero ── */
  .hero {
    background: linear-gradient(135deg, #0d2137 0%, #1e3a5f 50%, #2e86ab 100%);
    padding: 3.5rem 2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 0;
    color: white;
    text-align: center;
  }
  .hero h1 {
    color: white; margin: 0 0 0.5rem;
    font-size: 2.6rem; font-weight: 800; letter-spacing: -0.5px;
  }
  .hero .tagline {
    color: rgba(255,255,255,0.9); font-size: 1.15rem; margin: 0 0 1.5rem;
  }
  .hero .stats {
    display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;
    margin-top: 1.5rem;
  }
  .hero .stat {
    text-align: center;
  }
  .hero .stat-num {
    font-size: 1.8rem; font-weight: 800; color: #7ecfff;
  }
  .hero .stat-label {
    font-size: 0.75rem; color: rgba(255,255,255,0.7); text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* ── Service Cards ── */
  .svc-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
  }
  .svc-card {
    background: #fff;
    border: 2px solid #e8ecf0;
    border-radius: 14px;
    padding: 1.4rem 1rem 1rem;
    text-align: center;
    cursor: pointer;
    transition: box-shadow 0.2s, border-color 0.2s, transform 0.15s;
  }
  .svc-card:hover {
    box-shadow: 0 6px 24px rgba(46,134,171,0.18);
    border-color: #2e86ab;
    transform: translateY(-3px);
  }
  .svc-card.active {
    border-color: #2e86ab;
    background: linear-gradient(135deg, #f0f8ff, #e8f4fb);
    box-shadow: 0 4px 16px rgba(46,134,171,0.2);
  }
  .svc-icon { font-size: 2rem; margin-bottom: 0.5rem; }
  .svc-name { font-weight: 700; font-size: 0.95rem; color: #1e3a5f; margin-bottom: 0.3rem; }
  .svc-desc { font-size: 0.78rem; color: #666; line-height: 1.4; }

  /* ── Section divider ── */
  .section-label {
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.5px;
    color: #999; margin: 2rem 0 0.5rem; font-weight: 600;
  }

  /* ── Proof strip ── */
  .proof-strip {
    background: #f7f9fc;
    border-radius: 10px;
    padding: 1rem 1.5rem;
    display: flex; flex-wrap: wrap; gap: 1rem;
    justify-content: space-around;
    margin: 1rem 0 0;
  }
  .proof-item { text-align: center; }
  .proof-num  { font-size: 1.4rem; font-weight: 800; color: #1e3a5f; }
  .proof-lbl  { font-size: 0.75rem; color: #888; }

  /* ── How It Works ── */
  .hiw-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem; margin: 1rem 0;
  }
  .hiw-card {
    background: #fff; border-radius: 12px;
    padding: 1.2rem 0.9rem; text-align: center;
    border: 1px solid #e8ecf0;
  }
  .hiw-num {
    width: 32px; height: 32px; border-radius: 50%;
    background: #1e3a5f; color: #fff;
    font-size: 0.85rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 0.6rem;
  }
  .hiw-title { font-weight: 700; font-size: 0.88rem; color: #1e3a5f; margin-bottom: 0.3rem; }
  .hiw-body  { font-size: 0.78rem; color: #666; line-height: 1.4; }

  /* ── Footer ── */
  .app-footer {
    background: #0d2137;
    border-radius: 12px;
    padding: 2rem 1.5rem;
    margin-top: 2rem;
    color: rgba(255,255,255,0.7);
    text-align: center;
    font-size: 0.82rem;
  }
  .app-footer a { color: #7ecfff; text-decoration: none; }
  .app-footer .footer-links {
    display: flex; flex-wrap: wrap; justify-content: center;
    gap: 1.5rem; margin-bottom: 1rem;
  }
  .app-footer .footer-brand {
    font-size: 1.1rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem;
  }
</style>
""",
    unsafe_allow_html=True,
)

# ── Session State ──────────────────────────────────────────────────────────────
if "audit_history" not in st.session_state:
    st.session_state.audit_history = []
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False
if "ab_history" not in st.session_state:
    st.session_state.ab_history = []
if "revenue_projections" not in st.session_state:
    st.session_state.revenue_projections = {}
if "active_service" not in st.session_state:
    st.session_state.active_service = "audit"


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
        # Enforce TLS 1.2 minimum — TLS 1.0 and 1.1 are deprecated and insecure
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
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
    safe, reason = _is_safe_url(website)
    if not safe:
        return {"error": reason}
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
            "status_code": response.status_code,}
        
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
        link_safe, _link_reason = _is_safe_url(link)
        if not link_safe:
            # Skip links that resolve to private/internal addresses
            continue
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


# ── Email Notification & HTML Report ──────────────────────────────────────────

def _get_email_config():
    """
    Load SMTP / notification settings from Streamlit secrets or environment vars.

    Required secrets/env keys:
        SMTP_HOST      — SMTP server hostname  (e.g. smtp.gmail.com)
        SMTP_PORT      — SMTP port             (587 for STARTTLS, 465 for SSL)
        SMTP_USER      — Sender email address
        SMTP_PASSWORD  — Sender password / app password
        NOTIFY_EMAIL   — Your destination address (where reports are sent)
    """
    def _get(key):
        try:
            if hasattr(st, "secrets") and key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
        return os.getenv(key, "")

    return {
        "host":     _get("SMTP_HOST"),
        "port":     int(_get("SMTP_PORT") or 587),
        "user":     _get("SMTP_USER"),
        "password": _get("SMTP_PASSWORD"),
        "notify":   _get("NOTIFY_EMAIL"),
    }


def _email_configured():
    """Return True when all required SMTP fields are present."""
    cfg = _get_email_config()
    return all([cfg["host"], cfg["user"], cfg["password"], cfg["notify"]])


def _score_color(score):
    """Return a hex colour based on the score value."""
    if score >= 80:
        return "#27ae60"
    if score >= 60:
        return "#f39c12"
    if score >= 40:
        return "#e67e22"
    return "#e74c3c"


def _status_badge(status):
    """Return a coloured HTML badge for pass / warn / fail."""
    badges = {
        "pass": '<span style="background:#27ae60;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.8em">✅ Pass</span>',
        "warn": '<span style="background:#f39c12;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.8em">⚠️ Warn</span>',
        "fail": '<span style="background:#e74c3c;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.8em">❌ Fail</span>',
    }
    return badges.get(status, badges["fail"])


def _progress_bar(pct, color):
    """Return an inline HTML progress bar."""
    return (
        f'<div style="background:#e0e0e0;border-radius:6px;height:14px;width:100%">'
        f'<div style="background:{color};width:{pct}%;border-radius:6px;height:14px"></div>'
        f"</div>"
    )


def build_report_html(results, score_data):
    """
    Build a self-contained HTML audit report for email delivery.
    Uses only inline CSS — no external resources required.
    """
    total = score_data.get("total", 0)
    total_color = _score_color(total)
    categories = score_data.get("categories", {})
    recs = generate_recommendations(results)
    rs = results.get("robots_sitemap", {})
    timestamp = results.get("timestamp", datetime.utcnow().isoformat())
    audited_url = results.get("url", "")
    keyword = results.get("keyword") or "—"

    # ── Category rows ──
    cat_rows = ""
    for cat, data in categories.items():
        pct = data["pct"]
        color = _score_color(pct)
        cat_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">{cat}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;width:200px">
            {_progress_bar(pct, color)}
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center;font-weight:bold;color:{color}">{pct}%</td>
        </tr>"""

    # ── Key findings table ──
    title = results.get("title", "") or "—"
    desc  = results.get("description", "") or "—"
    title_len = len(results.get("title", ""))
    desc_len  = len(results.get("description", ""))
    h1_info   = results.get("h1", {})
    ssl_info  = results.get("ssl", {})
    mobile    = results.get("mobile", {})
    favicon   = results.get("favicon", {})
    speed     = results.get("page_speed", {})
    og        = results.get("og_tags", {})
    tw        = results.get("twitter_tags", {})
    sd        = results.get("structured_data", {})
    broken_n  = len(results.get("links", {}).get("broken", []))

    def _row(label, value, status):
        return (
            f'<tr><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;color:#555">{label}</td>'
            f'<td style="padding:6px 12px;border-bottom:1px solid #f0f0f0">{value}</td>'
            f'<td style="padding:6px 12px;border-bottom:1px solid #f0f0f0">{_status_badge(status)}</td></tr>'
        )

    findings_rows = (
        _row("Meta Title",       f"{title[:60]}… ({title_len} chars)" if title_len > 60 else f"{title} ({title_len} chars)",
             "pass" if 30 <= title_len <= 65 else ("warn" if title_len > 0 else "fail"))
        + _row("Meta Description", f"{desc[:80]}… ({desc_len} chars)" if desc_len > 80 else f"{desc} ({desc_len} chars)",
               "pass" if 50 <= desc_len <= 160 else ("warn" if desc_len > 0 else "fail"))
        + _row("H1 Tag",           h1_info.get("message", "—"),        h1_info.get("status", "fail"))
        + _row("SSL / HTTPS",      ssl_info.get("message", "—"),       ssl_info.get("status", "fail"))
        + _row("Mobile Viewport",  mobile.get("message", "—"),         mobile.get("status", "fail"))
        + _row("Favicon",          "Present" if favicon.get("present") else "Missing",
               favicon.get("status", "fail"))
        + _row("Open Graph",       f"{og.get('score', 0)}% complete",  og.get("status", "fail"))
        + _row("Twitter Cards",    f"{tw.get('score', 0)}% complete",  tw.get("status", "fail"))
        + _row("Structured Data",  sd.get("message", "—"),             sd.get("status", "warn"))
        + _row("robots.txt",       "Found" if rs.get("robots", {}).get("found") else "Missing",
               "pass" if rs.get("robots", {}).get("found") else "fail")
        + _row("sitemap.xml",      "Found" if rs.get("sitemap", {}).get("found") else "Missing",
               "pass" if rs.get("sitemap", {}).get("found") else "fail")
        + _row("Broken Links",     f"{broken_n} broken (in sample)",
               "pass" if broken_n == 0 else ("warn" if broken_n < 3 else "fail"))
        + _row("Page Speed",       speed.get("note", "—"),             speed.get("status", "fail"))
    )

    # ── Recommendations ──
    rec_items = "".join(f"<li style='margin-bottom:6px'>{r}</li>" for r in recs) if recs else "<li>No critical issues found 🎉</li>"

    # ── Score arc (pure CSS) ──
    circumference = 251  # ≈ 2π × 40
    dash = round(total / 100 * circumference)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>SEO Audit Report — {audited_url}</title>
</head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background:#f5f7fa;color:#333">

<!-- Header -->
<table width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="background:linear-gradient(135deg,#1e3a5f,#2e86ab);padding:30px 40px;text-align:center">
      <h1 style="color:#fff;margin:0;font-size:1.8rem">🔍 SEO Audit Report</h1>
      <p style="color:rgba(255,255,255,0.85);margin:6px 0 0">Powered by ATI &amp; AI</p>
    </td>
  </tr>
</table>

<!-- Meta strip -->
<table width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="background:#1e3a5f;padding:10px 40px">
      <p style="color:#fff;margin:0;font-size:0.85rem">
        <strong>URL:</strong> {audited_url} &nbsp;|&nbsp;
        <strong>Keyword:</strong> {keyword} &nbsp;|&nbsp;
        <strong>Audited:</strong> {timestamp} UTC
      </p>
    </td>
  </tr>
</table>

<!-- Body -->
<table width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="padding:30px 40px">

      <!-- Score card -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:24px">
        <tr>
          <td style="padding:30px;text-align:center">
            <svg width="120" height="120" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#e0e0e0" stroke-width="10"/>
              <circle cx="50" cy="50" r="40" fill="none" stroke="{total_color}" stroke-width="10"
                      stroke-dasharray="{dash} {circumference}"
                      stroke-dashoffset="63"
                      stroke-linecap="round"
                      transform="rotate(-90 50 50)"/>
              <text x="50" y="55" text-anchor="middle" font-size="22" font-weight="bold" fill="{total_color}">{total}</text>
              <text x="50" y="68" text-anchor="middle" font-size="9" fill="#999">/100</text>
            </svg>
            <p style="margin:8px 0 0;font-size:1.1rem;font-weight:bold;color:{total_color}">
              {"Excellent" if total >= 80 else "Good" if total >= 60 else "Needs Work" if total >= 40 else "Poor"}
            </p>
            <p style="margin:4px 0 0;color:#888;font-size:0.85rem">Overall SEO Score</p>
          </td>
        </tr>
      </table>

      <!-- Category scores -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:24px">
        <tr>
          <td style="padding:20px 24px;border-bottom:2px solid #f0f0f0">
            <h2 style="margin:0;font-size:1.1rem;color:#1e3a5f">📊 Category Scores</h2>
          </td>
        </tr>
        <tr>
          <td>
            <table width="100%" cellpadding="0" cellspacing="0">
              {cat_rows}
            </table>
          </td>
        </tr>
      </table>

      <!-- Key findings -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:24px">
        <tr>
          <td style="padding:20px 24px;border-bottom:2px solid #f0f0f0">
            <h2 style="margin:0;font-size:1.1rem;color:#1e3a5f">🔎 Key Findings</h2>
          </td>
        </tr>
        <tr>
          <td>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr style="background:#f8f9fa">
                <th style="padding:8px 12px;text-align:left;font-size:0.8rem;color:#888;font-weight:600">CHECK</th>
                <th style="padding:8px 12px;text-align:left;font-size:0.8rem;color:#888;font-weight:600">DETAIL</th>
                <th style="padding:8px 12px;text-align:center;font-size:0.8rem;color:#888;font-weight:600">STATUS</th>
              </tr>
              {findings_rows}
            </table>
          </td>
        </tr>
      </table>

      <!-- Recommendations -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:24px">
        <tr>
          <td style="padding:20px 24px;border-bottom:2px solid #f0f0f0">
            <h2 style="margin:0;font-size:1.1rem;color:#1e3a5f">💡 Recommendations</h2>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 24px">
            <ul style="margin:0;padding-left:20px;line-height:1.8">
              {rec_items}
            </ul>
          </td>
        </tr>
      </table>

    </td>
  </tr>
</table>

<!-- Footer -->
<table width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="background:#1e3a5f;padding:16px 40px;text-align:center">
      <p style="color:rgba(255,255,255,0.6);margin:0;font-size:0.8rem">
        ATI &amp; AI · Free SEO Audit Tool · Report generated {timestamp} UTC<br>
        The full structured data (CSV) is attached to this email.
      </p>
    </td>
  </tr>
</table>

</body>
</html>"""
    return html


def send_audit_email(results, score_data):
    """
    Send an HTML audit report + CSV attachment to the configured NOTIFY_EMAIL.
    Returns (True, "") on success or (False, error_message) on failure.
    Silently skips if SMTP is not configured.
    """
    if not _email_configured():
        return False, "SMTP not configured"

    cfg = _get_email_config()
    total = score_data.get("total", 0)
    audited_url = results.get("url", "unknown")
    timestamp_str = results.get("timestamp", datetime.utcnow().isoformat())

    subject = (
        f"🔍 SEO Audit Report — {audited_url} "
        f"(Score: {total}/100) [{timestamp_str[:10]}]"
    )

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = cfg["user"]
    msg["To"]      = cfg["notify"]

    # HTML body
    html_body = build_report_html(results, score_data)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # CSV attachment
    csv_data = _export_csv([results])
    if csv_data:
        ts_file = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        att = MIMEApplication(csv_data.encode("utf-8"), Name=f"seo_audit_{ts_file}.csv")
        att["Content-Disposition"] = f'attachment; filename="seo_audit_{ts_file}.csv"'
        msg.attach(att)

    try:
        port = cfg["port"]
        if port == 465:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(cfg["host"], port, context=ctx) as server:
                server.login(cfg["user"], cfg["password"])
                server.sendmail(cfg["user"], cfg["notify"], msg.as_string())
        else:
            with smtplib.SMTP(cfg["host"], port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(cfg["user"], cfg["password"])
                server.sendmail(cfg["user"], cfg["notify"], msg.as_string())
        return True, ""
    except Exception as exc:
        return False, str(exc)


# ── A/B Testing Module ────────────────────────────────────────────────────────

def run_ab_comparison(url_a, url_b, keyword=None):
    """
    Audit both URLs and return a structured comparison dict.
    Runs both audits (cached independently) and scores them.
    """
    results_a = perform_seo_audit(url_a, keyword or None)
    results_b = perform_seo_audit(url_b, keyword or None)
    score_a = calculate_seo_score(results_a) if not results_a.get("error") else {"total": 0, "categories": {}}
    score_b = calculate_seo_score(results_b) if not results_b.get("error") else {"total": 0, "categories": {}}
    return {
        "url_a": url_a,
        "url_b": url_b,
        "keyword": keyword,
        "timestamp": datetime.utcnow().isoformat(),
        "results_a": results_a,
        "results_b": results_b,
        "score_a": score_a,
        "score_b": score_b,
        "winner": "A" if score_a["total"] >= score_b["total"] else "B",
    }


def _ab_metric_rows(ra, rb):
    """
    Build a list of (metric, val_a, val_b, winner) tuples for every comparable
    SEO dimension.
    """
    rows = []

    def _status(r, key, sub="status"):
        return r.get(key, {}).get(sub, "fail") if isinstance(r.get(key), dict) else "fail"

    def _win(sa, sb):
        order = {"pass": 2, "warn": 1, "fail": 0}
        va, vb = order.get(sa, 0), order.get(sb, 0)
        if va > vb:
            return "A"
        if vb > va:
            return "B"
        return "tie"

    checks = [
        ("SSL / HTTPS",       _status(ra, "ssl"),            _status(rb, "ssl")),
        ("Mobile Viewport",   _status(ra, "mobile"),         _status(rb, "mobile")),
        ("H1 Tag",            _status(ra, "h1"),             _status(rb, "h1")),
        ("Favicon",           _status(ra, "favicon"),        _status(rb, "favicon")),
        ("Open Graph Tags",   _status(ra, "og_tags"),        _status(rb, "og_tags")),
        ("Twitter Cards",     _status(ra, "twitter_tags"),   _status(rb, "twitter_tags")),
        ("Structured Data",   _status(ra, "structured_data"),_status(rb, "structured_data")),
        ("Page Speed",        _status(ra, "page_speed"),     _status(rb, "page_speed")),
    ]

    # robots / sitemap
    rs_a = ra.get("robots_sitemap", {})
    rs_b = rb.get("robots_sitemap", {})
    for key, label in [("robots", "robots.txt"), ("sitemap", "sitemap.xml")]:
        sa = "pass" if rs_a.get(key, {}).get("found") else "fail"
        sb = "pass" if rs_b.get(key, {}).get("found") else "fail"
        checks.append((label, sa, sb))

    # meta title quality
    def _title_status(r):
        t = r.get("title", "")
        if not t:
            return "fail"
        return "pass" if 30 <= len(t) <= 65 else "warn"

    def _desc_status(r):
        d = r.get("description", "")
        if not d:
            return "fail"
        return "pass" if 50 <= len(d) <= 160 else "warn"

    checks.append(("Meta Title",       _title_status(ra), _title_status(rb)))
    checks.append(("Meta Description", _desc_status(ra),  _desc_status(rb)))

    # broken links
    def _link_status(r):
        n = len(r.get("links", {}).get("broken", []))
        return "pass" if n == 0 else ("warn" if n < 3 else "fail")

    checks.append(("Broken Links", _link_status(ra), _link_status(rb)))

    for label, sa, sb in checks:
        rows.append((label, sa, sb, _win(sa, sb)))

    return rows


_STATUS_ICONS = {"pass": "✅", "warn": "⚠️", "fail": "❌"}


def render_ab_comparison(comparison):
    """Render an interactive A/B comparison dashboard."""
    ra = comparison["results_a"]
    rb = comparison["results_b"]
    sa = comparison["score_a"]
    sb = comparison["score_b"]
    winner = comparison["winner"]

    # Top score cards
    col_a, col_mid, col_b = st.columns([5, 2, 5])
    with col_a:
        color_a = _score_color(sa["total"])
        st.markdown(
            f"""<div style="background:#fff;border:2px solid {color_a};border-radius:12px;
            padding:20px;text-align:center">
            <div style="font-size:0.85rem;color:#888;margin-bottom:4px">Version A</div>
            <div style="font-size:0.75rem;color:#555;word-break:break-all;margin-bottom:8px">
              {comparison['url_a']}</div>
            <div style="font-size:3rem;font-weight:bold;color:{color_a}">{sa['total']}</div>
            <div style="color:#888;font-size:0.8rem">/ 100</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col_mid:
        st.markdown(
            """<div style="text-align:center;padding-top:40px;font-size:1.5rem">VS</div>""",
            unsafe_allow_html=True,
        )
    with col_b:
        color_b = _score_color(sb["total"])
        badge = " 🏆 WINNER" if winner == "B" else ""
        badgeA = " 🏆 WINNER" if winner == "A" else ""
        # patch A badge
        col_a.markdown(
            f"""<div style="text-align:center;color:{color_a};font-weight:bold;
            font-size:0.85rem;margin-top:4px">{badgeA}</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div style="background:#fff;border:2px solid {color_b};border-radius:12px;
            padding:20px;text-align:center">
            <div style="font-size:0.85rem;color:#888;margin-bottom:4px">Version B</div>
            <div style="font-size:0.75rem;color:#555;word-break:break-all;margin-bottom:8px">
              {comparison['url_b']}</div>
            <div style="font-size:3rem;font-weight:bold;color:{color_b}">{sb['total']}</div>
            <div style="color:#888;font-size:0.8rem">/ 100</div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div style="text-align:center;color:{color_b};font-weight:bold;
            font-size:0.85rem;margin-top:4px">{badge}</div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Metric-by-metric table
    rows = _ab_metric_rows(ra, rb)
    a_wins = sum(1 for _, _, _, w in rows if w == "A")
    b_wins = sum(1 for _, _, _, w in rows if w == "B")
    ties   = sum(1 for _, _, _, w in rows if w == "tie")

    st.markdown(f"#### Metric Breakdown — A wins **{a_wins}**, B wins **{b_wins}**, Ties **{ties}**")

    header_html = """
    <table style="width:100%;border-collapse:collapse;font-size:0.9rem">
      <thead>
        <tr style="background:#1e3a5f;color:#fff">
          <th style="padding:10px 14px;text-align:left">Metric</th>
          <th style="padding:10px 14px;text-align:center">Version A</th>
          <th style="padding:10px 14px;text-align:center">Version B</th>
          <th style="padding:10px 14px;text-align:center">Winner</th>
        </tr>
      </thead><tbody>"""
    body_html = ""
    winner_colors = {"A": "#e8f4e8", "B": "#e8f4e8", "tie": "#fff"}
    for i, (label, sta, stb, win) in enumerate(rows):
        bg = "#f9f9f9" if i % 2 == 0 else "#fff"
        icon_a = _STATUS_ICONS.get(sta, "❓")
        icon_b = _STATUS_ICONS.get(stb, "❓")
        if win == "A":
            win_cell = '<span style="color:#27ae60;font-weight:bold">⬅ A</span>'
        elif win == "B":
            win_cell = '<span style="color:#2e86ab;font-weight:bold">B ➡</span>'
        else:
            win_cell = '<span style="color:#888">Tie</span>'
        body_html += (
            f'<tr style="background:{bg}">'
            f'<td style="padding:8px 14px;border-bottom:1px solid #eee">{label}</td>'
            f'<td style="padding:8px 14px;border-bottom:1px solid #eee;text-align:center">{icon_a} {sta.upper()}</td>'
            f'<td style="padding:8px 14px;border-bottom:1px solid #eee;text-align:center">{icon_b} {stb.upper()}</td>'
            f'<td style="padding:8px 14px;border-bottom:1px solid #eee;text-align:center">{win_cell}</td>'
            f"</tr>"
        )
    st.markdown(header_html + body_html + "</tbody></table>", unsafe_allow_html=True)

    # Category score side-by-side bar chart
    st.markdown("---")
    cats = list(sa.get("categories", {}).keys())
    pcts_a = [sa["categories"][c]["pct"] for c in cats]
    pcts_b = [sb["categories"][c]["pct"] for c in cats]
    if cats:
        fig = go.Figure(data=[
            go.Bar(name="Version A", x=cats, y=pcts_a, marker_color="#1e3a5f",
                   text=[f"{p}%" for p in pcts_a], textposition="auto"),
            go.Bar(name="Version B", x=cats, y=pcts_b, marker_color="#2e86ab",
                   text=[f"{p}%" for p in pcts_b], textposition="auto"),
        ])
        fig.update_layout(
            barmode="group", title="Category Score Comparison",
            yaxis={"range": [0, 100], "title": "Score (%)"},
            height=320, margin=dict(l=10, r=10, t=50, b=80),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Per-URL recommendations
    with st.expander("💡 Version A — Recommendations"):
        for r in generate_recommendations(ra):
            st.markdown(r)
    with st.expander("💡 Version B — Recommendations"):
        for r in generate_recommendations(rb):
            st.markdown(r)

    # Verdict
    diff = abs(sa["total"] - sb["total"])
    if diff == 0:
        verdict = "Both versions score equally. Review per-metric wins to choose the better candidate."
    elif diff < 10:
        verdict = (
            f"Version **{winner}** has a slight edge (+{diff} pts). "
            "The gap is small — address the recommendations on the losing version to close it."
        )
    else:
        verdict = (
            f"Version **{winner}** is clearly stronger (+{diff} pts). "
            "Adopt its SEO structure as your baseline and apply its fixes to the other."
        )
    st.info(f"**🏁 Verdict:** {verdict}")


# ── Revenue Intelligence Module ───────────────────────────────────────────────

# Industry-average CTR by SERP position (Backlinko 2023 data)
_CTR_BY_POSITION = {
    1: 0.278, 2: 0.152, 3: 0.111,
    4: 0.074, 5: 0.053, 6: 0.041,
    7: 0.032, 8: 0.025, 9: 0.021, 10: 0.018,
}

# Recommendation slugs that map to estimated traffic impact (fraction of monthly traffic)
_REC_TRAFFIC_IMPACT = {
    "HTTPS":           0.20,
    "viewport":        0.18,
    "Meta Title":      0.14,
    "H1":              0.12,
    "Meta Description":0.10,
    "Page Speed":      0.10,
    "Broken Links":    0.08,
    "Structured Data": 0.08,
    "robots.txt":      0.05,
    "sitemap.xml":     0.05,
    "Open Graph":      0.04,
    "Twitter Card":    0.03,
    "Favicon":         0.02,
}


def _score_to_avg_position(score):
    """Map SEO score to an estimated average SERP position (1–20)."""
    if score >= 90:
        return 1.5
    if score >= 80:
        return 3.0
    if score >= 70:
        return 5.5
    if score >= 60:
        return 8.0
    if score >= 50:
        return 12.0
    if score >= 40:
        return 16.0
    return 20.0


def _position_to_ctr(position):
    """Return average CTR for a given (possibly fractional) SERP position."""
    low = int(position)
    high = low + 1
    ctr_low  = _CTR_BY_POSITION.get(low,  0.005)
    ctr_high = _CTR_BY_POSITION.get(high, 0.005)
    frac = position - low
    return ctr_low + frac * (ctr_high - ctr_low)


def calculate_revenue_projections(score_now, recs, monthly_impressions, conversion_rate, aov):
    """
    Return a dict of revenue projections based on current SEO score and
    user-provided business metrics.

    Parameters
    ----------
    score_now          : int   current SEO score (0-100)
    recs               : list  list of recommendation strings
    monthly_impressions: float monthly organic search impressions
    conversion_rate    : float conversion rate as a decimal (e.g., 0.02 = 2%)
    aov                : float average order value in dollars
    """
    pos_now = _score_to_avg_position(score_now)
    ctr_now = _position_to_ctr(pos_now)

    traffic_now     = monthly_impressions * ctr_now
    revenue_now     = traffic_now * conversion_rate * aov

    # Fully optimised (score 95) baseline
    pos_opt = _score_to_avg_position(95)
    ctr_opt = _position_to_ctr(pos_opt)
    traffic_opt     = monthly_impressions * ctr_opt
    revenue_opt     = traffic_opt * conversion_rate * aov
    revenue_delta   = revenue_opt - revenue_now

    # Per-recommendation impact
    rec_impacts = []
    for rec in recs:
        matched_key = next(
            (k for k in _REC_TRAFFIC_IMPACT if k.lower() in rec.lower()), None
        )
        if matched_key:
            traffic_gain   = traffic_now * _REC_TRAFFIC_IMPACT[matched_key]
            revenue_gain   = traffic_gain * conversion_rate * aov
            rec_impacts.append({
                "rec":          rec,
                "traffic_gain": round(traffic_gain),
                "revenue_gain": round(revenue_gain),
                "impact_pct":   round(_REC_TRAFFIC_IMPACT[matched_key] * 100, 1),
            })

    rec_impacts.sort(key=lambda x: x["revenue_gain"], reverse=True)

    # Score improvement curve (score 40 → 100, step 5)
    curve = []
    for s in range(max(40, score_now), 101, 5):
        p = _score_to_avg_position(s)
        c = _position_to_ctr(p)
        t = monthly_impressions * c
        r = t * conversion_rate * aov
        curve.append({"score": s, "traffic": round(t), "revenue": round(r)})

    return {
        "score_now":        score_now,
        "pos_now":          round(pos_now, 1),
        "ctr_now":          round(ctr_now * 100, 2),
        "traffic_now":      round(traffic_now),
        "revenue_now":      round(revenue_now, 2),
        "revenue_optimised":round(revenue_opt, 2),
        "revenue_delta":    round(revenue_delta, 2),
        "rec_impacts":      rec_impacts,
        "curve":            curve,
    }


def render_revenue_dashboard(results, score_data):
    """Render the interactive Revenue Impact calculator."""
    st.markdown("### 💰 Revenue Impact Calculator")
    st.caption(
        "Enter your business metrics below. The calculator projects how improving "
        "your SEO score translates directly to traffic and revenue."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        monthly_impressions = st.number_input(
            "Monthly Organic Impressions",
            min_value=100, max_value=10_000_000,
            value=10_000, step=500,
            help="How many times your site appears in search results per month. "
                 "Find this in Google Search Console.",
        )
    with c2:
        conversion_rate_pct = st.number_input(
            "Conversion Rate (%)",
            min_value=0.1, max_value=100.0,
            value=2.0, step=0.1, format="%.1f",
            help="Percentage of visitors who make a purchase or complete a goal.",
        )
    with c3:
        aov = st.number_input(
            "Average Order / Lead Value ($)",
            min_value=1, max_value=1_000_000,
            value=150, step=10,
            help="Average dollar value of a converted customer.",
        )

    if not st.button("📊 Calculate Revenue Impact", use_container_width=True):
        st.info("Fill in your business metrics above, then click **Calculate Revenue Impact**.")
        return

    recs = generate_recommendations(results)
    proj = calculate_revenue_projections(
        score_now=score_data["total"],
        recs=recs,
        monthly_impressions=float(monthly_impressions),
        conversion_rate=conversion_rate_pct / 100.0,
        aov=float(aov),
    )

    # KPI row
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Current Avg. Position",  f"#{proj['pos_now']}")
    k2.metric("Estimated CTR",          f"{proj['ctr_now']}%")
    k3.metric("Est. Monthly Visitors",  f"{proj['traffic_now']:,}")
    k4.metric("Est. Monthly Revenue",   f"${proj['revenue_now']:,.0f}")

    st.markdown("---")
    opp_col, detail_col = st.columns([1, 2])
    with opp_col:
        delta_color = "normal" if proj["revenue_delta"] >= 0 else "inverse"
        st.metric(
            "Revenue if Fully Optimised (Score 95)",
            f"${proj['revenue_optimised']:,.0f}",
            delta=f"+${proj['revenue_delta']:,.0f}/mo opportunity",
        )
        st.metric(
            "Annual Revenue Opportunity",
            f"${proj['revenue_delta'] * 12:,.0f}",
        )
    with detail_col:
        # Revenue vs Score line chart
        if proj["curve"]:
            fig = go.Figure()
            scores  = [c["score"]   for c in proj["curve"]]
            revs    = [c["revenue"] for c in proj["curve"]]
            traffic = [c["traffic"] for c in proj["curve"]]
            fig.add_trace(go.Scatter(
                x=scores, y=revs, mode="lines+markers",
                name="Monthly Revenue ($)",
                line=dict(color="#27ae60", width=3),
                marker=dict(size=6),
                yaxis="y1",
            ))
            fig.add_trace(go.Scatter(
                x=scores, y=traffic, mode="lines+markers",
                name="Monthly Visitors",
                line=dict(color="#2e86ab", width=2, dash="dot"),
                marker=dict(size=5),
                yaxis="y2",
            ))
            # Mark current score
            fig.add_vline(
                x=proj["score_now"], line_dash="dash", line_color="#e74c3c",
                annotation_text=f"Current ({proj['score_now']})", annotation_position="top right",
            )
            fig.update_layout(
                title="Revenue & Traffic vs SEO Score",
                xaxis_title="SEO Score",
                yaxis=dict(title="Monthly Revenue ($)", tickformat="$,.0f"),
                yaxis2=dict(title="Monthly Visitors", overlaying="y", side="right"),
                height=320,
                margin=dict(l=10, r=60, t=50, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig, use_container_width=True)

    # Priority action table
    if proj["rec_impacts"]:
        st.markdown("---")
        st.markdown("#### 🎯 Priority Actions — Ranked by Revenue Impact")
        st.caption("Fix these issues first to maximise ROI.")
        for i, item in enumerate(proj["rec_impacts"], 1):
            severity = "🔴" if item["revenue_gain"] > proj["revenue_delta"] * 0.15 else "🟡"
            with st.container():
                c_rank, c_rec, c_traffic, c_rev = st.columns([1, 6, 2, 2])
                c_rank.markdown(f"**#{i}** {severity}")
                # Strip leading emoji/bold markers for cleaner display
                clean_rec = item["rec"].lstrip("🔴🟡 ").lstrip("*").strip("*")
                c_rec.markdown(clean_rec)
                c_traffic.metric("Traffic Gain", f"+{item['traffic_gain']:,}/mo")
                c_rev.metric("Revenue Gain", f"+${item['revenue_gain']:,}/mo")
        st.markdown("---")
        total_rec_rev = sum(i["revenue_gain"] for i in proj["rec_impacts"])
        st.success(
            f"💡 Fixing all {len(proj['rec_impacts'])} prioritised issues could unlock "
            f"**+${total_rec_rev:,}/month** in additional revenue."
        )

    # Store projections in session for potential email inclusion
    if "revenue_projections" not in st.session_state:
        st.session_state.revenue_projections = {}
    st.session_state.revenue_projections[results.get("url", "")] = proj


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

        # ── Email status ──────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📧 Email Notifications")
        if _email_configured():
            cfg = _get_email_config()
            st.success(f"✅ Configured → {cfg['notify']}")
            st.caption(
                "Reports are automatically emailed after every audit. "
                "Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, NOTIFY_EMAIL "
                "in Streamlit secrets or environment variables."
            )
            # Test send against the most recent audit in history
            if st.session_state.audit_history:
                if st.button("📤 Send Test Report"):
                    last = st.session_state.audit_history[-1]
                    sd = calculate_seo_score(last)
                    ok, err = send_audit_email(last, sd)
                    if ok:
                        st.success(f"✅ Test report sent to {cfg['notify']}")
                    else:
                        st.error(f"❌ Send failed: {err}")
            else:
                st.info("Run an audit first to enable test send.")
        else:
            st.warning("⚠️ Email not configured")
            with st.expander("Setup instructions"):
                st.markdown("""
Add these to your Streamlit secrets (`.streamlit/secrets.toml`) or as environment variables:

```toml
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "you@gmail.com"
SMTP_PASSWORD = "your-app-password"
NOTIFY_EMAIL  = "you@gmail.com"
```

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833).
""")

        # ── Export ────────────────────────────────────────────────────────────
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
            # Download latest HTML report
            if history:
                last = history[-1]
                last_score = calculate_seo_score(last)
                st.download_button(
                    "⬇️ Download Latest HTML Report",
                    data=build_report_html(last, last_score).encode("utf-8"),
                    file_name=f"seo_report_{ts_str}.html",
                    mime="text/html",
                )

        # ── Batch Audit ───────────────────────────────────────────────────────
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
                sent_count = 0
                for i, u in enumerate(urls):
                    with st.spinner(f"Auditing {u}…"):
                        r = perform_seo_audit(u, batch_kw or None)
                        if not r.get("error"):
                            st.session_state.audit_history.append(r)
                            sd = calculate_seo_score(r)
                            ok, _ = send_audit_email(r, sd)
                            if ok:
                                sent_count += 1
                    prog.progress((i + 1) / len(urls))
                msg = f"✅ Batch complete — {len(urls)} URL(s) audited"
                if sent_count:
                    msg += f", {sent_count} report(s) emailed"
                st.success(msg)
            else:
                st.warning("Enter at least one URL")

        st.markdown("---")
        if st.button("🗑️ Clear Session History"):
            st.session_state.audit_history = []
            st.session_state.ab_history = []
            st.session_state.revenue_projections = {}
            st.success("Session cleared")


# ── Main App ───────────────────────────────────────────────────────────────────

render_admin_panel()

# ── 1. HERO ───────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
  <h1>🔍 ATI &amp; AI SEO Platform</h1>
  <p class="tagline">
    Audit any website, A/B test SEO changes, and calculate the exact revenue<br>
    your rankings are leaving on the table — all in one free tool.
  </p>
  <div class="stats">
    <div class="stat">
      <div class="stat-num">15+</div>
      <div class="stat-label">SEO Checks</div>
    </div>
    <div class="stat">
      <div class="stat-num">0–100</div>
      <div class="stat-label">Scored Instantly</div>
    </div>
    <div class="stat">
      <div class="stat-num">A/B</div>
      <div class="stat-label">Competitor Testing</div>
    </div>
    <div class="stat">
      <div class="stat-num">$ROI</div>
      <div class="stat-label">Revenue Projections</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── 2. SERVICE SELECTION BUTTONS ──────────────────────────────────────────────
st.markdown('<p class="section-label">Select a Service</p>', unsafe_allow_html=True)

SERVICES = [
    {
        "key":   "instant_audit",
        "icon":  "🔍",
        "name":  "Instant Social Audit",
        "desc":  "Is that influencer worth the spend? Enter any Instagram handle for real-time engagement rates, audience authenticity, and growth trends.",
    },
    {
        "key":   "audit",
        "icon":  "🌐",
        "name":  "Free SEO Audit",
        "desc":  "15-point instant analysis of any webpage — score, issues, and fixes.",
    },
    {
        "key":   "ab",
        "icon":  "⚖️",
        "name":  "A/B Testing",
        "desc":  "Compare your page vs a competitor on every SEO metric to find the winner.",
    },
    {
        "key":   "revenue",
        "icon":  "💰",
        "name":  "Revenue Calculator",
        "desc":  "Translate your SEO score into projected traffic and dollar revenue.",
    },
    {
        "key":   "strategy",
        "icon":  "📈",
        "name":  "SEO Strategy Call",
        "desc":  "Book a free consultation with our team to build your growth roadmap.",
    },
    {
        "key":   "technical",
        "icon":  "🛠️",
        "name":  "Technical SEO Fix",
        "desc":  "Audit + prioritised action plan: we show you exactly what to fix first.",
    },
    {
        "key":   "influencer_discovery",
        "icon":  "🔎",
        "name":  "Influencer Discovery",
        "desc":  "Search, filter, and score influencers across Instagram, TikTok, YouTube & LinkedIn.",
    },
    {
        "key":   "influencer_scorecard",
        "icon":  "🏆",
        "name":  "Influencer Scorecard",
        "desc":  "Rate and compare influencers with a weighted authenticity & engagement score.",
    },
    {
        "key":   "audience_analytics",
        "icon":  "👥",
        "name":  "Audience Analytics",
        "desc":  "Demographic breakdown, authenticity analysis, and interests alignment.",
    },
]

# Render cards as columns with Streamlit buttons
svc_cols = st.columns(len(SERVICES))
for col, svc in zip(svc_cols, SERVICES):
    with col:
        is_active = st.session_state.active_service == svc["key"]
        card_class = "svc-card active" if is_active else "svc-card"
        st.markdown(
            f"""<div class="{card_class}">
              <div class="svc-icon">{svc['icon']}</div>
              <div class="svc-name">{svc['name']}</div>
              <div class="svc-desc">{svc['desc']}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button(
            f"{'▶ ' if is_active else ''}{svc['name']}",
            key=f"svc_btn_{svc['key']}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.active_service = svc["key"]
            st.rerun()

st.markdown("---")

# ── 3. ACTIVE SERVICE TOOL ────────────────────────────────────────────────────
active = st.session_state.active_service

# ── Service: Free SEO Audit ───────────────────────────────────────────────────
if active == "audit":
    st.markdown("### 🔍 Free SEO Audit")
    st.caption(
        "Enter any URL to get a full 15-point SEO health check with a 0–100 score, "
        "visual dashboard, and prioritised action list."
    )
    col_url, col_kw, col_btn = st.columns([3, 2, 1])
    with col_url:
        url = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            label_visibility="collapsed",
            key="audit_url",
        )
    with col_kw:
        keyword = st.text_input(
            "Target Keyword (optional)",
            placeholder="e.g., AI tools for SEO",
            label_visibility="collapsed",
            key="audit_kw",
        )
    with col_btn:
        run_audit = st.button("🚀 Run Audit", use_container_width=True, key="btn_audit",
                              type="primary")

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
                        f"❌ Page not accessible "
                        f"(HTTP {results.get('status_code', 'unknown')})"
                    )
                else:
                    score_data = calculate_seo_score(results)
                    progress_bar.progress(95, text="Sending report…")
                    if results not in st.session_state.audit_history:
                        st.session_state.audit_history.append(results)
                    email_ok, _email_err = send_audit_email(results, score_data)
                    progress_bar.progress(100, text="Complete!")
                    progress_bar.empty()
                    if email_ok:
                        cfg = _get_email_config()
                        st.success(
                            f"✅ Audit complete — SEO Score: **{score_data['total']}/100** "
                            f"· Report emailed to {cfg['notify']}"
                        )
                    else:
                        st.success(
                            f"✅ Audit complete — SEO Score: **{score_data['total']}/100**"
                        )
                    display_results(results, score_data)
            except Exception as exc:
                progress_bar.empty()
                st.error(f"An unexpected error occurred: {str(exc)}")

# ── Service: A/B Testing ──────────────────────────────────────────────────────
elif active == "ab":
    st.markdown("### ⚖️ SEO A/B Testing")
    st.caption(
        "Compare your page against a competitor or a revised version on every SEO metric. "
        "See exactly which variant wins and why."
    )
    c_a, c_b, c_kw_ab = st.columns([3, 3, 2])
    with c_a:
        url_a = st.text_input(
            "Your Page (Version A)",
            placeholder="https://your-page.com",
            key="ab_url_a",
        )
    with c_b:
        url_b = st.text_input(
            "Competitor / Version B",
            placeholder="https://competitor.com",
            key="ab_url_b",
        )
    with c_kw_ab:
        ab_keyword = st.text_input(
            "Target Keyword (optional)",
            placeholder="e.g., SEO tools",
            key="ab_kw",
        )
    run_ab = st.button("⚖️ Run Comparison", use_container_width=True,
                       key="btn_ab", type="primary")

    if run_ab:
        if not url_a or not url_b:
            st.error("Please enter both URLs to run a comparison.")
        elif url_a.strip() == url_b.strip():
            st.error("Version A and Version B must be different URLs.")
        else:
            with st.spinner("Auditing both versions — this may take a moment…"):
                comparison = run_ab_comparison(
                    url_a.strip(), url_b.strip(), ab_keyword or None
                )
            ra_err = comparison["results_a"].get("error")
            rb_err = comparison["results_b"].get("error")
            if ra_err:
                st.error(f"❌ Version A failed: {ra_err}")
            elif rb_err:
                st.error(f"❌ Version B failed: {rb_err}")
            else:
                st.session_state.ab_history.append(comparison)
                st.success(
                    f"✅ Comparison complete — "
                    f"A: **{comparison['score_a']['total']}/100** vs "
                    f"B: **{comparison['score_b']['total']}/100** — "
                    f"Winner: **Version {comparison['winner']}**"
                )
                render_ab_comparison(comparison)
    elif st.session_state.ab_history:
        st.info("Showing last comparison. Run a new one above to refresh.")
        render_ab_comparison(st.session_state.ab_history[-1])

# ── Service: Revenue Calculator ───────────────────────────────────────────────
elif active == "revenue":
    history = st.session_state.audit_history
    if not history:
        st.info(
            "💡 Run a **Free SEO Audit** first — click the 🔍 button above — "
            "then return here to calculate the revenue impact of your improvements."
        )
    else:
        url_options = [r.get("url", f"Audit #{i+1}") for i, r in enumerate(history)]
        selected_idx = st.selectbox(
            "Select audited URL",
            range(len(url_options)),
            format_func=lambda i: url_options[i],
            key="rev_url_select",
        )
        selected_result = history[selected_idx]
        selected_score  = calculate_seo_score(selected_result)
        render_revenue_dashboard(selected_result, selected_score)

# ── Service: SEO Strategy Call ────────────────────────────────────────────────
elif active == "strategy":
    st.markdown("### 📈 SEO Strategy Consultation")
    st.markdown(
        "Work directly with the ATI & AI team to build a tailored SEO growth roadmap "
        "for your business. We audit your site, analyse your competitors, and deliver "
        "a prioritised 90-day action plan."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
**What's included:**
- ✅ Full technical SEO audit
- ✅ Competitor landscape analysis
- ✅ Keyword opportunity mapping
- ✅ 90-day SEO action plan
- ✅ Revenue impact forecast
- ✅ Follow-up Q&A session
""")
    with c2:
        st.markdown("""
**Who it's for:**
- 🏢 Businesses wanting more organic traffic
- 🛒 E-commerce stores losing revenue to competitors
- 🚀 Startups entering competitive markets
- 📊 Marketing teams needing a data-driven SEO strategy
""")
    st.markdown("---")
    st.markdown("#### 📅 Book Your Free Strategy Call")
    st.link_button(
        "📅 Schedule on Calendly",
        "https://calendly.com",
        use_container_width=True,
    )
    st.caption(
        "Prefer email? Reach out via the "
        "[Contact Portal](https://automatedtechnicalinsightsandai.github.io/contact) "
        "and we'll get back to you within one business day."
    )

# ── Service: Technical SEO Fix ────────────────────────────────────────────────
elif active == "technical":
    st.markdown("### 🛠️ Technical SEO Fix Plan")
    st.caption(
        "Run an audit on your URL and get a prioritised technical fix list ranked by "
        "expected SEO impact — no guesswork, just clear actions."
    )
    col_url_t, col_btn_t = st.columns([4, 1])
    with col_url_t:
        tech_url = st.text_input(
            "Your Website URL",
            placeholder="https://your-site.com",
            key="tech_url",
        )
    with col_btn_t:
        run_tech = st.button("🛠️ Analyse", use_container_width=True,
                             key="btn_tech", type="primary")

    if run_tech:
        if not tech_url:
            st.error("Please enter a URL to analyse.")
        else:
            with st.spinner("Running technical audit…"):
                tech_results = perform_seo_audit(tech_url)
            if tech_results.get("error"):
                st.error(f"❌ {tech_results['error']}")
            elif not tech_results.get("accessible"):
                st.error(
                    f"❌ Page not accessible "
                    f"(HTTP {tech_results.get('status_code', 'unknown')})"
                )
            else:
                tech_score = calculate_seo_score(tech_results)
                if tech_results not in st.session_state.audit_history:
                    st.session_state.audit_history.append(tech_results)
                send_audit_email(tech_results, tech_score)

                # Show prioritised fix plan
                total = tech_score["total"]
                total_color = _score_color(total)
                st.markdown(
                    f"**SEO Health Score: "
                    f"<span style='color:{total_color};font-size:1.3rem'>"
                    f"{total}/100</span>**",
                    unsafe_allow_html=True,
                )

                recs = generate_recommendations(tech_results)
                critical = [r for r in recs if r.startswith("🔴")]
                warnings  = [r for r in recs if r.startswith("🟡")]

                if critical:
                    st.markdown("#### 🔴 Critical — Fix Immediately")
                    for r in critical:
                        st.error(r.lstrip("🔴 "))
                if warnings:
                    st.markdown("#### 🟡 Recommended — Fix Soon")
                    for r in warnings:
                        st.warning(r.lstrip("🟡 "))
                if not critical and not warnings:
                    st.success(
                        "🎉 No critical issues found. Your technical SEO is in great shape!"
                    )

                st.markdown("---")
                st.markdown("**Full audit results:**")
                display_results(tech_results, tech_score)

# ── Service: Influencer Discovery ────────────────────────────────────────────
elif active == "influencer_discovery":
    from influencer_metrics import (
        build_profile_metrics,
        classify_influencer_tier,
        get_tier_label,
        filter_influencers,
        compare_influencers,
        TIER_NANO, TIER_MICRO, TIER_MACRO, TIER_MEGA,
    )
    import database as _db

    _db.init_db()

    st.markdown("### 🔎 Influencer Discovery")
    st.caption(
        "Search your stored influencer database or add a new influencer profile manually. "
        "Filter by platform, tier, engagement rate, and audience authenticity."
    )

    with st.expander("➕ Add / Update Influencer Profile", expanded=False):
        with st.form("add_influencer_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                inf_username = st.text_input("Username (without @)", placeholder="janedoe")
                inf_platform = st.selectbox(
                    "Platform", ["instagram", "tiktok", "youtube", "linkedin"]
                )
                inf_followers = st.number_input("Follower Count", min_value=0, value=10000)
                inf_engagement = st.number_input(
                    "Engagement Rate (%)", min_value=0.0, max_value=100.0,
                    value=2.5, step=0.1, format="%.2f"
                )
            with col_b:
                inf_growth = st.number_input(
                    "Monthly Growth Rate (%)", min_value=-100.0, max_value=1000.0,
                    value=1.0, step=0.1, format="%.2f"
                )
                inf_bio = st.text_area("Bio / Description", placeholder="About this creator…", height=80)
                inf_url = st.text_input("Profile URL", placeholder="https://instagram.com/janedoe")

            submitted = st.form_submit_button("💾 Save Influencer", type="primary")
            if submitted:
                if not inf_username:
                    st.error("Username is required.")
                else:
                    tier = classify_influencer_tier(int(inf_followers))
                    _db.upsert_influencer(
                        username=inf_username,
                        platform=inf_platform,
                        follower_count=int(inf_followers),
                        engagement_rate=float(inf_engagement),
                        growth_rate=float(inf_growth),
                        audience_tier=tier,
                        bio=inf_bio,
                        profile_url=inf_url,
                    )
                    st.success(
                        f"✅ @{inf_username} saved as a {get_tier_label(tier)} "
                        f"{inf_platform.title()} influencer."
                    )

    st.markdown("#### 🔍 Filter & Search")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        f_platform = st.selectbox(
            "Platform", ["All", "instagram", "tiktok", "youtube", "linkedin"],
            key="disc_platform"
        )
    with f_col2:
        f_tier = st.selectbox(
            "Tier", ["All", TIER_NANO, TIER_MICRO, TIER_MACRO, TIER_MEGA],
            format_func=lambda x: "All" if x == "All" else get_tier_label(x),
            key="disc_tier"
        )
    with f_col3:
        f_min_er = st.number_input(
            "Min Engagement Rate (%)", min_value=0.0, max_value=100.0,
            value=0.0, step=0.1, format="%.1f", key="disc_min_er"
        )
    with f_col4:
        f_min_followers = st.number_input(
            "Min Followers", min_value=0, value=0, step=1000, key="disc_min_fol"
        )

    platform_filter = None if f_platform == "All" else f_platform
    tier_filter = None if f_tier == "All" else f_tier
    all_influencers = _db.get_all_influencers(platform=platform_filter, tier=tier_filter)

    # Convert DB rows to dicts compatible with filter_influencers
    filtered = filter_influencers(
        all_influencers,
        min_followers=int(f_min_followers),
        min_engagement_rate=float(f_min_er),
    )

    if not filtered:
        st.info("No influencers match the current filters.  Add some profiles above to get started.")
    else:
        ranked = compare_influencers(filtered)
        st.markdown(f"**{len(ranked)} influencer(s) found**")
        for inf in ranked:
            sc = inf.get("scorecard", {})
            with st.container():
                cols = st.columns([1, 3, 2, 2, 2, 2])
                cols[0].markdown(f"**#{inf.get('rank', '?')}**")
                cols[1].markdown(
                    f"**@{inf.get('username', '')}** — {inf.get('platform', '').title()}"
                )
                cols[2].metric("Followers", f"{inf.get('follower_count', 0):,}")
                cols[3].metric("Eng. Rate", f"{inf.get('engagement_rate', 0):.2f}%")
                cols[4].metric("Tier", get_tier_label(inf.get('audience_tier') or
                                                       inf.get('tier', '')))
                cols[5].metric("Score", f"{sc.get('overall_score', 0):.1f}/100")

# ── Service: Instant Social Audit ────────────────────────────────────────────
elif active == "instant_audit":
    from instagram_audit import analyze_instagram_profile

    st.markdown("### 🔍 Instant Social Audit")
    st.caption(
        "Analyze any Instagram profile to make data-driven influencer booking decisions. "
        "Stop guessing — get the data."
    )

    username_input = st.text_input(
        "Enter Instagram Handle",
        placeholder="@username_here",
        help="Type the influencer's Instagram username (with or without @)",
    )

    if username_input:
        with st.spinner("🔍 Analyzing profile…"):
            results = analyze_instagram_profile(username_input)

        clean_name = results["username"]
        st.markdown(f"#### 📊 Results Snapshot — @{clean_name}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "🎯 Authenticity",
                f"{results['authenticity_score']}/100",
                delta=f"{results['authenticity_trend']:+.1f}%",
            )
        with col2:
            st.metric(
                "💬 Engagement",
                f"{results['engagement_rate']:.1f}%",
                delta=f"{results['engagement_trend']:+.1f}%",
            )
        with col3:
            st.metric(
                "📈 Growth (90d)",
                f"{results['growth_90d']:.1f}%",
                delta=f"60d: {results['growth_60d']:.1f}%",
            )
        with col4:
            score = results["authenticity_score"]
            score_icon = "🟢" if score > 75 else ("🟡" if score > 50 else "🔴")
            booking_label = "YES" if results["worth_booking"] else "NO"
            st.metric("📊 Worth Booking?", f"{score_icon} {booking_label}")

        st.markdown("---")

        col_f, col_g = st.columns(2)
        with col_f:
            st.metric("👥 Followers", f"{results['followers']:,}")
        with col_g:
            st.metric("📸 Posts", f"{results['posts_count']:,}")

        # Detailed breakdown tabs
        tab_demos, tab_growth, tab_recs = st.tabs(
            ["👥 Audience", "📈 Growth", "💡 Recommendations"]
        )

        with tab_demos:
            st.markdown("**Audience Demographics**")
            demos = results["demographics"]

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.markdown("**Age Groups**")
                for age, pct in demos["age_groups"].items():
                    st.progress(pct / 100, text=f"{age}: {pct}%")
            with d_col2:
                st.markdown("**Gender Split**")
                for gender, pct in demos["gender"].items():
                    st.progress(pct / 100, text=f"{gender}: {pct}%")

            st.markdown("**Top Locations**")
            for country, pct in list(demos["locations"].items())[:4]:
                st.progress(pct / 100, text=f"{country}: {pct}%")

            st.markdown("**Top Interests**")
            interest_tags = "  ".join(
                [f"`{i}`" for i in demos["top_interests"]]
            )
            st.markdown(interest_tags)

        with tab_growth:
            st.markdown("**Follower Growth Timeline (90 Days)**")
            timeline = results["growth_timeline"]
            if timeline:
                import pandas as pd
                df_growth = pd.DataFrame(timeline)
                df_growth = df_growth.rename(
                    columns={"day": "Day", "followers": "Followers"}
                )
                st.line_chart(df_growth.set_index("Day")["Followers"])


# ── Service: Influencer Scorecard ─────────────────────────────────────────────
elif active == "influencer_scorecard":
    import database as _db
    from influencer_metrics import (
        build_influencer_scorecard,
        build_audience_quality,
        build_content_performance,
        get_tier_label,
        compare_influencers,
    )
    from report_generator import (
        generate_influencer_html_report,
        generate_influencer_comparison_html,
    )

    _db.init_db()

    st.markdown("### 🏆 Influencer Scorecard")
    st.caption(
        "Select one or more influencers from your database to generate a weighted "
        "scorecard comparing authenticity, engagement, audience size, and growth."
    )

    all_infs = _db.get_all_influencers()
    if not all_infs:
        st.info(
            "No influencers in the database yet. "
            "Add profiles via the **Influencer Discovery** tool first."
        )
    else:
        inf_options = {
            f"@{i['username']} ({i['platform'].title()})": i["id"]
            for i in all_infs
        }
        selected_names = st.multiselect(
            "Select influencers to score",
            list(inf_options.keys()),
            default=list(inf_options.keys())[:min(3, len(inf_options))],
        )

        if selected_names:
            selected_ids = [inf_options[n] for n in selected_names]
            selected_infs = [i for i in all_infs if i["id"] in selected_ids]

            # Build minimal audience quality / content performance from stored data
            enriched = []
            for inf in selected_infs:
                aq = build_audience_quality(
                    engagement_rate=inf.get("engagement_rate", 2.0),
                    follower_growth_rate=inf.get("growth_rate", 1.0),
                )
                cp = build_content_performance(
                    avg_likes=0.0,
                    avg_comments=0.0,
                    follower_count=inf.get("follower_count", 1),
                )
                cp["engagement_rate"] = inf.get("engagement_rate", 0.0)
                sc = build_influencer_scorecard(inf, aq, cp)
                enriched.append({
                    **inf,
                    "audience_quality": aq,
                    "content_performance": cp,
                    "scorecard": sc,
                })

            ranked = compare_influencers(enriched)

            st.markdown(f"#### Ranked Results ({len(ranked)} influencer(s))")
            for inf in ranked:
                sc = inf["scorecard"]
                rating_colors = {
                    "excellent": "🟢",
                    "above_average": "🔵",
                    "average": "🟡",
                    "below_average": "🟠",
                    "poor": "🔴",
                }
                icon = rating_colors.get(sc.get("rating", ""), "⚪")
                with st.expander(
                    f"{icon} #{inf['rank']} @{inf['username']} — "
                    f"{sc['overall_score']:.1f}/100 ({sc['rating'].replace('_',' ').title()})"
                ):
                    comp = sc.get("components", {})
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Authenticity", f"{comp.get('authenticity', 0):.1f}/30")
                    c2.metric("Engagement", f"{comp.get('engagement', 0):.1f}/30")
                    c3.metric("Audience Size", f"{comp.get('audience_size', 0):.1f}/20")
                    c4.metric("Growth", f"{comp.get('growth', 0):.1f}/20")

                    html_report = generate_influencer_html_report(
                        inf,
                        scorecard=sc,
                        audience_quality=inf["audience_quality"],
                        content_performance=inf["content_performance"],
                    )
                    st.download_button(
                        "⬇️ Download HTML Report",
                        data=html_report,
                        file_name=f"influencer_{inf['username']}_report.html",
                        mime="text/html",
                        key=f"dl_inf_{inf['id']}",
                    )

            if len(ranked) > 1:
                st.markdown("#### Comparison Matrix")
                comparison_html = generate_influencer_comparison_html(ranked)
                st.components.v1.html(comparison_html, height=400, scrolling=True)
                st.download_button(
                    "⬇️ Download Comparison Matrix",
                    data=comparison_html,
                    file_name="influencer_comparison.html",
                    mime="text/html",
                )

# ── Service: Audience Analytics ───────────────────────────────────────────────
elif active == "audience_analytics":
    import database as _db
    from influencer_metrics import (
        build_audience_quality,
        calculate_authenticity_score,
        analyse_growth_trend,
        get_tier_label,
    )

    _db.init_db()

    st.markdown("### 👥 Audience Analytics")
    st.caption(
        "Dive deep into audience demographics, authenticity, geographic distribution, "
        "and growth trends for any influencer in your database."
    )

    all_infs = _db.get_all_influencers()
    if not all_infs:
        st.info(
            "No influencers in the database yet. "
            "Add profiles via the **Influencer Discovery** tool first."
        )
    else:
        inf_map = {
            f"@{i['username']} ({i['platform'].title()})": i
            for i in all_infs
        }
        sel_name = st.selectbox("Select Influencer", list(inf_map.keys()))
        inf = inf_map[sel_name]
        inf_id = inf["id"]

        st.markdown(f"#### @{inf['username']} · {inf['platform'].title()} · {get_tier_label(inf.get('audience_tier', ''))}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Followers", f"{inf.get('follower_count', 0):,}")
        col2.metric("Engagement Rate", f"{inf.get('engagement_rate', 0):.2f}%")
        col3.metric("Growth Rate", f"{inf.get('growth_rate', 0):.2f}%/mo")
        col4.metric("Tier", get_tier_label(inf.get("audience_tier", "")))

        st.markdown("---")
        st.markdown("#### Audience Quality Estimator")
        st.caption(
            "Fill in the audience quality parameters below. "
            "Connect social APIs for real data — manual input available for all platforms."
        )

        aq_col1, aq_col2 = st.columns(2)
        with aq_col1:
            real_pct = st.slider("Real Followers (%)", 0, 100, 80, key="aq_real")
            suspicious_pct = st.slider("Suspicious Followers (%)", 0, 100, 5, key="aq_sus")
        with aq_col2:
            top_country1 = st.text_input("Top Country 1", "United States", key="tc1")
            top_country1_pct = st.number_input("% of audience", 0.0, 100.0, 40.0, key="tc1p")
            top_country2 = st.text_input("Top Country 2", "United Kingdom", key="tc2")
            top_country2_pct = st.number_input("% of audience", 0.0, 100.0, 20.0, key="tc2p")

        interests_input = st.text_input(
            "Top Interests (comma-separated)",
            "Fashion, Lifestyle, Travel",
            key="aq_interests",
        )
        top_interests = [i.strip() for i in interests_input.split(",") if i.strip()]

        gender_f = st.slider("Female Audience (%)", 0, 100, 60, key="aq_gf")
        gender_m = 100 - gender_f

        age_groups = {}
        age_col1, age_col2, age_col3 = st.columns(3)
        with age_col1:
            age_groups["13-17"] = st.number_input("Age 13-17 (%)", 0.0, 100.0, 5.0, key="a1317")
            age_groups["18-24"] = st.number_input("Age 18-24 (%)", 0.0, 100.0, 35.0, key="a1824")
        with age_col2:
            age_groups["25-34"] = st.number_input("Age 25-34 (%)", 0.0, 100.0, 30.0, key="a2534")
            age_groups["35-44"] = st.number_input("Age 35-44 (%)", 0.0, 100.0, 20.0, key="a3544")
        with age_col3:
            age_groups["45-54"] = st.number_input("Age 45-54 (%)", 0.0, 100.0, 7.0, key="a4554")
            age_groups["55+"] = st.number_input("Age 55+ (%)", 0.0, 100.0, 3.0, key="a55")

        aq = build_audience_quality(
            real_follower_pct=float(real_pct),
            engagement_rate=inf.get("engagement_rate", 2.0),
            follower_growth_rate=inf.get("growth_rate", 1.0),
            suspicious_follower_pct=float(suspicious_pct),
            top_countries=[
                {"country": top_country1, "pct": top_country1_pct},
                {"country": top_country2, "pct": top_country2_pct},
            ],
            age_distribution=age_groups,
            gender_split={"female": float(gender_f), "male": float(gender_m)},
            top_interests=top_interests,
        )

        st.markdown("---")
        st.markdown("#### Results")
        r1, r2, r3 = st.columns(3)
        auth = aq["authenticity_score"]
        auth_color = "🟢" if auth >= 70 else "🟡" if auth >= 50 else "🔴"
        r1.metric("Authenticity Score", f"{auth:.1f}/100", delta=f"{auth_color}")
        r2.metric("Real Followers", f"{real_pct}%")
        r3.metric("Suspicious", f"{suspicious_pct}%")

        import plotly.graph_objects as go_aud  # noqa: PLC0415

        # Audience composition pie
        fig_aud = go_aud.Figure(go_aud.Pie(
            labels=["Real Followers", "Suspicious", "Unknown"],
            values=[real_pct, suspicious_pct, max(0, 100 - real_pct - suspicious_pct)],
            marker_colors=["#00d4aa", "#ef4444", "#f59e0b"],
            hole=0.4,
        ))
        fig_aud.update_layout(
            title="Audience Composition",
            paper_bgcolor="#141414",
            plot_bgcolor="#141414",
            font_color="#e5e7eb",
            height=300,
            margin=dict(t=50, b=20, l=20, r=20),
        )

        # Age distribution bar
        fig_age = go_aud.Figure(go_aud.Bar(
            x=list(age_groups.keys()),
            y=list(age_groups.values()),
            marker_color="#00d4ff",
        ))
        fig_age.update_layout(
            title="Age Distribution",
            paper_bgcolor="#141414",
            plot_bgcolor="#141414",
            font_color="#e5e7eb",
            height=300,
            margin=dict(t=50, b=60, l=50, r=20),
            xaxis_title="Age Group",
            yaxis_title="%",
        )

        ch1, ch2 = st.columns(2)
        ch1.plotly_chart(fig_aud, use_container_width=True)
        ch2.plotly_chart(fig_age, use_container_width=True)

        # Growth trend (from stored snapshots)
        history = _db.get_influencer_metrics_history(inf_id, days=90)
        if history:
            trend = analyse_growth_trend(history)
            st.markdown("#### Growth Trend (Last 90 Days)")
            t1, t2, t3 = st.columns(3)
            t1.metric("Total Growth", f"{trend['total_growth_pct']:.2f}%")
            t2.metric("Avg Monthly Growth", f"{trend['avg_monthly_growth']:.2f}%")
            t3.metric("ER Trend", trend["er_trend"].title())

            dates = [s.get("date", "") for s in trend["snapshots"]]
            fol_vals = [s.get("followers", 0) for s in trend["snapshots"]]
            fig_growth = go_aud.Figure(go_aud.Scatter(
                x=dates, y=fol_vals, mode="lines+markers",
                line=dict(color="#00d4ff", width=2),
                marker=dict(color="#00d4ff", size=6),
            ))
            fig_growth.update_layout(
                title="Follower Growth",
                paper_bgcolor="#141414",
                plot_bgcolor="#141414",
                font_color="#e5e7eb",
                height=280,
                margin=dict(t=50, b=60, l=60, r=20),
                xaxis_gridcolor="#222",
                yaxis_gridcolor="#222",
            )
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info(
                "No historical snapshots stored for this influencer.  "
                "Snapshots are recorded automatically when you save metrics via the API integration."
            )

# ── 4. HOW IT WORKS ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-label">How It Works</p>', unsafe_allow_html=True)
st.markdown(
    """
<div class="hiw-grid">
  <div class="hiw-card">
    <div class="hiw-num">1</div>
    <div class="hiw-title">Enter Your URL</div>
    <div class="hiw-body">Paste any webpage URL. No account or login required.</div>
  </div>
  <div class="hiw-card">
    <div class="hiw-num">2</div>
    <div class="hiw-title">We Analyse It</div>
    <div class="hiw-body">15 SEO checks run instantly — technical, on-page, performance & links.</div>
  </div>
  <div class="hiw-card">
    <div class="hiw-num">3</div>
    <div class="hiw-title">Get Your Score</div>
    <div class="hiw-body">Receive a 0–100 SEO health score with a visual breakdown by category.</div>
  </div>
  <div class="hiw-card">
    <div class="hiw-num">4</div>
    <div class="hiw-title">See the Fixes</div>
    <div class="hiw-body">Prioritised recommendations tell you exactly what to change first.</div>
  </div>
  <div class="hiw-card">
    <div class="hiw-num">5</div>
    <div class="hiw-title">Project Revenue</div>
    <div class="hiw-body">Enter your traffic &amp; conversion metrics to see the dollar impact.</div>
  </div>
  <div class="hiw-card">
    <div class="hiw-num">6</div>
    <div class="hiw-title">Get a Report</div>
    <div class="hiw-body">Receive a full HTML report by email and export CSV/JSON data.</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── 5. SOCIAL PROOF / STATS STRIP ─────────────────────────────────────────────
st.markdown(
    """
<div class="proof-strip">
  <div class="proof-item"><div class="proof-num">15+</div><div class="proof-lbl">SEO Checks</div></div>
  <div class="proof-item"><div class="proof-num">Free</div><div class="proof-lbl">No Credit Card</div></div>
  <div class="proof-item"><div class="proof-num">100%</div><div class="proof-lbl">Data Privacy</div></div>
  <div class="proof-item"><div class="proof-num">A/B</div><div class="proof-lbl">Competitor Testing</div></div>
  <div class="proof-item"><div class="proof-num">$ROI</div><div class="proof-lbl">Revenue Forecasting</div></div>
  <div class="proof-item"><div class="proof-num">📧</div><div class="proof-lbl">Email Reports</div></div>
</div>
""",
    unsafe_allow_html=True,
)

# ── 6. FOOTER (About ATI & AI + Contact) ─────────────────────────────────────
st.markdown(
    """
<div class="app-footer">
  <div class="footer-brand">🔍 ATI &amp; AI — Automated Technical Insights &amp; AI</div>
  <div class="footer-links">
    <a href="https://calendly.com/automated-technical-insights/new-meeting" target="_blank">💬 Contact</a>
    <a href="https://automatedtechnicalinsightsandai.github.io/services" target="_blank">📊 Services</a>
    <a href="https://www.linkedin.com/in/orlando-velazquez-borges/" target="_blank">🔗 LinkedIn</a>
  </div>
  <p style="margin:0.5rem 0 0;max-width:560px;margin-left:auto;margin-right:auto">
    ATI &amp; AI bridges the gap between legacy infrastructure and modern intelligence.
    We help businesses grow through data-driven SEO, payment optimisation, and
    AI-powered technical strategy.
  </p>
  <p style="margin:0.8rem 0 0;color:rgba(255,255,255,0.4);font-size:0.75rem">
    © 2026 Automated Technical Insights &amp; AI. All rights reserved.
    &nbsp;·&nbsp; Admin tools available via the sidebar.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

