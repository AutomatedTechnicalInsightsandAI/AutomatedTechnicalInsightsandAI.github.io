import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

MAX_LINKS_TO_CHECK = 10

st.set_page_config(page_title="Free SEO Audit Tool | ATI & AI", page_icon="🔍")

st.title("🔍 Free SEO Audit Tool")
st.markdown(
    "Uncover low-hanging SEO opportunities for your website. "
    "Enter your URL below to get instant insights on meta tags, "
    "keyword usage, and broken links."
)

url = st.text_input("Website URL", placeholder="https://example.com")
keyword = st.text_input(
    "Target Keyword (optional)",
    placeholder="e.g., AI tools for SEO",
)
run_audit = st.button("Run SEO Audit")


HEADERS = {"User-Agent": "ATI-SEO-AuditBot/1.0 (+https://automatedtechnicalinsightsandai.github.io)"}


def perform_seo_audit(website, keyword=None):
    try:
        response = requests.get(website, timeout=10, headers=HEADERS)
    except requests.RequestException as exc:
        return {"Error": f"Failed to reach {website}. Reason: {str(exc)}"}

    accessible = response.status_code == 200
    insights = {
        "Website Accessibility": "✅ Accessible" if accessible else "❌ Not Accessible",
        "HTTP Status Code": response.status_code,
    }

    if not accessible:
        insights["Note"] = "Page returned a non-200 status; meta and link checks skipped."
        return insights

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""

    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc_text = desc_tag.get("content", "").strip() if desc_tag else ""

    insights["Meta Title"] = title_text or "⚠️ No <title> tag found"
    insights["Meta Description"] = desc_text or "⚠️ No meta description found"

    if keyword:
        kw = keyword.lower()
        insights["Keyword in Title"] = (
            "✅ Yes" if kw in title_text.lower() else "❌ No — consider adding it"
        )
        insights["Keyword in Description"] = (
            "✅ Yes" if kw in desc_text.lower() else "❌ No — consider adding it"
        )

    # Check top MAX_LINKS_TO_CHECK http/https links for broken ones (free-tier limit)
    raw_links = [
        urljoin(website, a["href"])
        for a in soup.find_all("a", href=True)
        if a["href"]
        and not a["href"].startswith(("#", "mailto:", "javascript:", "tel:"))
    ]
    # Deduplicate while preserving order, then keep only absolute http(s) URLs
    seen: set = set()
    sampled_links = []
    for link in raw_links:
        if link not in seen and link.startswith(("http://", "https://")):
            seen.add(link)
            sampled_links.append(link)
            if len(sampled_links) == MAX_LINKS_TO_CHECK:
                break

    broken = []
    for link in sampled_links:
        try:
            link_resp = requests.head(link, timeout=5, allow_redirects=True, headers=HEADERS)
            if link_resp.status_code == 405:
                # Some servers don't support HEAD; fall back to GET
                link_resp = requests.get(link, timeout=5, allow_redirects=True, headers=HEADERS)
            if link_resp.status_code >= 400:
                broken.append(f"{link}  (HTTP {link_resp.status_code})")
        except requests.RequestException as exc:
            broken.append(f"{link}  (unreachable: {str(exc)})")

    insights[f"Broken Links (top {MAX_LINKS_TO_CHECK} sampled)"] = (
        broken if broken else "✅ None found"
    )

    return insights


if run_audit:
    if url:
        with st.spinner(f"Auditing {url} …"):
            results = perform_seo_audit(url, keyword or None)
        if "Error" in results:
            st.error(results["Error"])
        else:
            st.success("Audit complete — here are your SEO insights:")
            for key, value in results.items():
                if isinstance(value, list):
                    st.markdown(f"**{key}:**")
                    for item in value:
                        st.markdown(f"- {item}")
                else:
                    st.markdown(f"**{key}:** {value}")
    else:
        st.error("Please enter a valid URL before running the audit.")
