"""
ATI & AI — Professional SEO Audit Platform
Streamlit multi-section application.
"""

import logging
import os
import time

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---- Module imports (graceful degradation) --------------------------------
_db_ok = False
_db_error = ""
try:
    import database as db

    db.init_db()
    _db_ok = True
except Exception as _e:
    _db_error = str(_e)
    logging.error("Database init failed: %s", _e)

try:
    from seo_audit import run_full_audit
except Exception as _e:
    logging.error("seo_audit import failed: %s", _e)

    def run_full_audit(url, keyword=None):  # type: ignore[misc]
        return {"score": 0, "url": url, "error": str(_e), "checks": [], "summary": {}, "categories": {}, "page_info": {}}


try:
    from report_generator import generate_html_dashboard, generate_pdf_report
except Exception as _e:
    logging.error("report_generator import failed: %s", _e)

    def generate_html_dashboard(audit_data, audit_id=0):  # type: ignore[misc]
        return "<html><body>Dashboard unavailable</body></html>"

    def generate_pdf_report(audit_data, customer_name="", business_name=""):  # type: ignore[misc]
        return b""


try:
    from email_service import send_audit_report
except Exception as _e:
    logging.error("email_service import failed: %s", _e)

    def send_audit_report(*args, **kwargs):  # type: ignore[misc]
        return False, "Email service unavailable"


# ---------------------------------------------------------------------------
# Config / constants
# ---------------------------------------------------------------------------
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or "admin123"
if ADMIN_PASSWORD == "admin123":
    import warnings
    warnings.warn(
        "ADMIN_PASSWORD is not set — using insecure default 'admin123'. "
        "Set the ADMIN_PASSWORD environment variable before deploying to production.",
        stacklevel=1,
    )
COLOR_ACCENT = "#00d4ff"
COLOR_BG = "#0a0a0a"
COLOR_CARD = "#141414"
COLOR_PASS = "#00d4aa"
COLOR_WARN = "#f59e0b"
COLOR_FAIL = "#ef4444"
COLOR_TEXT = "#e5e7eb"
COLOR_SUB = "#9ca3af"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Professional SEO Audit | ATI & AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{
        background: {COLOR_BG} !important;
        color: {COLOR_TEXT} !important;
    }}
    [data-testid="stSidebar"] {{
        background: #0d1117 !important;
        border-right: 1px solid #1a1a1a;
    }}
    h1, h2, h3, h4 {{ color: {COLOR_TEXT} !important; }}
    .stButton > button {{
        background: {COLOR_ACCENT} !important;
        color: #000 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
    }}
    .stButton > button:hover {{ opacity: 0.85 !important; }}
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: #141414 !important;
        color: {COLOR_TEXT} !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }}
    [data-testid="metric-container"] {{
        background: {COLOR_CARD} !important;
        border: 1px solid #222 !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        background: #0d0d0d !important;
        border-radius: 8px !important;
        gap: 4px !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {COLOR_SUB} !important;
        background: transparent !important;
        border-radius: 6px !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLOR_ACCENT}22 !important;
        color: {COLOR_ACCENT} !important;
    }}
    hr {{ border-color: #222 !important; }}
    .ati-card {{
        background:{COLOR_CARD};border:1px solid #222;border-radius:12px;
        padding:20px 24px;margin-bottom:16px;
    }}
    .score-ring {{
        display:inline-flex;align-items:center;justify-content:center;
        width:120px;height:120px;border-radius:50%;
        font-size:2.4rem;font-weight:800;border:6px solid;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _score_color(score: int) -> str:
    if score >= 70:
        return COLOR_PASS
    if score >= 40:
        return COLOR_WARN
    return COLOR_FAIL


def _score_label(score: int) -> str:
    if score >= 70:
        return "Good"
    if score >= 40:
        return "Needs Improvement"
    return "Poor"


def _brand_header(subtitle: str = "") -> None:
    sub_html = (
        f"<p style='color:{COLOR_SUB};margin:4px 0 0;font-size:1rem;'>{subtitle}</p>"
        if subtitle
        else ""
    )
    st.markdown(
        f"""
        <div style="padding:24px 0 16px">
          <span style="font-size:2rem;font-weight:800;color:{COLOR_ACCENT}">ATI &amp;</span>
          <span style="font-size:2rem;font-weight:800;color:{COLOR_TEXT}"> AI</span>
          {sub_html}
        </div>
        <hr>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"<div style='font-size:1.4rem;font-weight:800;color:{COLOR_ACCENT};padding:12px 0 4px'>ATI &amp; AI</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='color:{COLOR_SUB};font-size:0.8rem;margin-bottom:16px'>Professional SEO Platform</div>",
        unsafe_allow_html=True,
    )
    nav = st.radio(
        "Navigate to",
        ["🚀 Request Audit", "📊 Admin Dashboard"],
        label_visibility="collapsed",
    )
    st.divider()

    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False

    if nav == "📊 Admin Dashboard":
        st.markdown(
            f"<div style='color:{COLOR_SUB};font-size:0.85rem;font-weight:600;margin-bottom:8px'>🔐 Admin Access</div>",
            unsafe_allow_html=True,
        )
        if not st.session_state["admin_authenticated"]:
            admin_pw = st.text_input("Password", type="password", key="admin_pw_input")
            if st.button("Login"):
                if admin_pw == ADMIN_PASSWORD:
                    st.session_state["admin_authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            st.success("✅ Authenticated")
            if st.button("Logout"):
                st.session_state["admin_authenticated"] = False
                st.rerun()

    if not _db_ok:
        st.warning(f"⚠️ Database error:\n{_db_error}")

    email_configured = bool(os.getenv("EMAIL_SENDER") and os.getenv("EMAIL_PASSWORD"))
    if not email_configured:
        with st.expander("⚙️ Email Setup Required"):
            st.code(
                "EMAIL_SENDER=your@gmail.com\n"
                "EMAIL_PASSWORD=app-password\n"
                "EMAIL_SMTP_HOST=smtp.gmail.com\n"
                "EMAIL_SMTP_PORT=587",
                language="bash",
            )


# ===========================================================================
# Section 1 — Customer Audit Request Form
# ===========================================================================
if nav == "🚀 Request Audit":
    _brand_header("Uncover your website's SEO opportunities with an instant professional audit.")

    col_form, col_info = st.columns([3, 2], gap="large")

    with col_info:
        st.markdown(
            f"""
            <div class="ati-card">
              <div style="color:{COLOR_ACCENT};font-weight:700;margin-bottom:12px">✨ What You'll Get</div>
              <ul style="color:{COLOR_SUB};font-size:0.9rem;line-height:2;padding-left:18px">
                <li>Technical SEO analysis (HTTPS, robots.txt, sitemap…)</li>
                <li>On-page checks (title, description, headings, OG tags…)</li>
                <li>Performance assessment (page size, load time, images…)</li>
                <li>Link health audit (internal, external, broken links)</li>
                <li>Score 0–100 with actionable recommendations</li>
                <li>Interactive HTML dashboard + PDF report via email</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_form:
        with st.form("audit_request_form", clear_on_submit=False):
            st.markdown(
                f"<div style='font-size:1.1rem;font-weight:700;color:{COLOR_TEXT};margin-bottom:16px'>"
                "Request Your Professional SEO Audit</div>",
                unsafe_allow_html=True,
            )

            website_url = st.text_input(
                "Website URL *",
                placeholder="https://example.com",
                help="The full URL of the website you want audited.",
            )
            email = st.text_input(
                "Email Address *",
                placeholder="you@example.com",
                help="Your report will be delivered to this address.",
            )
            c1, c2 = st.columns(2)
            with c1:
                business_name = st.text_input("Business Name", placeholder="Acme Corp")
            with c2:
                contact_name = st.text_input("Contact Name", placeholder="Jane Smith")
            keyword = st.text_input(
                "Target Keyword (optional)",
                placeholder="e.g., AI tools for SEO",
                help="We'll check whether your keyword appears in key on-page elements.",
            )

            submitted = st.form_submit_button(
                "🚀 Request Professional Audit", use_container_width=True
            )

        # ---- Process submission -------------------------------------------
        if submitted:
            errors = []
            if not website_url.strip():
                errors.append("Website URL is required.")
            elif not website_url.strip().startswith(("http://", "https://")):
                errors.append("Website URL must start with http:// or https://")
            if not email.strip() or "@" not in email:
                errors.append("A valid email address is required.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                audit_id = None
                if _db_ok:
                    try:
                        audit_id = db.create_audit_request(
                            url=website_url.strip(),
                            email=email.strip(),
                            business_name=business_name.strip(),
                            contact_name=contact_name.strip(),
                            keyword=keyword.strip(),
                        )
                        db.update_audit_status(audit_id, "processing")
                    except Exception as exc:
                        st.warning(f"Database record error (continuing anyway): {exc}")

                progress_bar = st.progress(0, text="Initialising audit…")
                status_ph = st.empty()

                def _update(pct: int, msg: str) -> None:
                    progress_bar.progress(pct, text=msg)
                    status_ph.markdown(
                        f"<div style='color:{COLOR_SUB};font-size:0.9rem'>{msg}</div>",
                        unsafe_allow_html=True,
                    )

                try:
                    _update(10, "🔍 Fetching website content…")
                    audit_results = run_full_audit(
                        website_url.strip(),
                        keyword=keyword.strip() or None,
                    )
                    _update(50, "📊 Generating interactive dashboard…")
                    html_dashboard = generate_html_dashboard(audit_results, audit_id or 0)
                    _update(65, "📄 Generating PDF report…")
                    pdf_bytes = generate_pdf_report(
                        audit_results,
                        customer_name=contact_name.strip(),
                        business_name=business_name.strip(),
                    )
                    _update(80, "📧 Sending report to your email…")
                    email_ok, email_msg = send_audit_report(
                        to_email=email.strip(),
                        customer_name=contact_name.strip(),
                        website_url=website_url.strip(),
                        seo_score=audit_results.get("score", 0),
                        html_dashboard_content=html_dashboard,
                        pdf_bytes=pdf_bytes,
                        business_name=business_name.strip(),
                    )
                    _update(95, "💾 Saving results…")

                    if _db_ok and audit_id:
                        db.update_audit_status(
                            audit_id,
                            "completed",
                            seo_score=audit_results.get("score"),
                            audit_results=audit_results,
                            report_html=html_dashboard,
                        )

                    _update(100, "✅ Audit complete!")
                    time.sleep(0.4)
                    progress_bar.empty()
                    status_ph.empty()

                    score = audit_results.get("score", 0)
                    sc = _score_color(score)
                    summary = audit_results.get("summary", {})

                    if audit_results.get("error"):
                        st.error(f"Audit failed: {audit_results['error']}")
                    else:
                        st.markdown(
                            f"""
                            <div class="ati-card" style="border-color:{sc}33">
                              <div style="font-size:1.1rem;font-weight:700;color:{COLOR_PASS};margin-bottom:16px">
                                ✅ Audit Complete!
                              </div>
                              <div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap">
                                <div class="score-ring" style="color:{sc};border-color:{sc}">{score}</div>
                                <div>
                                  <div style="font-size:1.5rem;font-weight:700;color:{sc}">{_score_label(score)}</div>
                                  <div style="color:{COLOR_SUB};font-size:0.9rem;margin-top:4px">{website_url}</div>
                                </div>
                              </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("✅ Passed", summary.get("passed", 0))
                        m2.metric("⚠️ Warnings", summary.get("warnings", 0))
                        m3.metric("❌ Failed", summary.get("failed", 0))
                        m4.metric("📋 Total Checks", summary.get("total", 0))

                        if email_ok:
                            st.success(f"📧 Full report (PDF + interactive dashboard) sent to **{email}**")
                        else:
                            st.info(
                                f"ℹ️ Email not sent ({email_msg}). "
                                "Download your dashboard below instead."
                            )

                        with st.expander("🔍 Preview Interactive Dashboard", expanded=False):
                            st.components.v1.html(html_dashboard, height=900, scrolling=True)

                        dcol1, dcol2 = st.columns(2)
                        with dcol1:
                            st.download_button(
                                "⬇️ Download HTML Dashboard",
                                data=html_dashboard,
                                file_name="SEO_Dashboard.html",
                                mime="text/html",
                                use_container_width=True,
                            )
                        with dcol2:
                            if pdf_bytes:
                                st.download_button(
                                    "⬇️ Download PDF Report",
                                    data=pdf_bytes,
                                    file_name="SEO_Audit_Report.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                )

                except Exception as exc:
                    progress_bar.empty()
                    status_ph.empty()
                    st.error(f"An unexpected error occurred: {exc}")
                    if _db_ok and audit_id:
                        try:
                            db.update_audit_status(audit_id, "failed", error_message=str(exc))
                        except Exception:
                            pass
                    logging.error("Audit pipeline error", exc_info=True)


# ===========================================================================
# Section 2 — Admin Dashboard
# ===========================================================================
elif nav == "📊 Admin Dashboard":
    _brand_header("Admin Dashboard")

    if not st.session_state.get("admin_authenticated"):
        st.warning("🔐 Please log in via the sidebar to access the admin dashboard.")
        st.stop()

    if not _db_ok:
        st.error(f"Database unavailable: {_db_error}")
        st.stop()

    tabs = st.tabs(["📋 Pending Queue", "📁 Audit History", "📈 Monthly Analytics", "🗄️ Database Status"])

    # -----------------------------------------------------------------------
    # Tab 1: Pending Queue
    # -----------------------------------------------------------------------
    with tabs[0]:
        st.markdown(
            f"<div style='font-size:1.1rem;font-weight:700;color:{COLOR_TEXT};margin-bottom:16px'>"
            "Pending &amp; Processing Audits</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔄 Refresh", key="refresh_pending"):
            st.rerun()

        pending = db.get_pending_audits()
        if not pending:
            st.info("No pending or processing audits.")
        else:
            for audit in pending:
                status = audit.get("status", "pending")
                badge_color = COLOR_WARN if status == "pending" else COLOR_ACCENT
                st.markdown(
                    f"""
                    <div class="ati-card">
                      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
                        <div>
                          <div style="font-weight:700;color:{COLOR_TEXT}">{audit.get('website_url','')}</div>
                          <div style="color:{COLOR_SUB};font-size:0.85rem">
                            {audit.get('customer_name') or 'Anonymous'} — {audit.get('customer_email','')}
                          </div>
                          <div style="color:{COLOR_SUB};font-size:0.8rem;margin-top:4px">
                            Submitted: {(audit.get('created_at') or '')[:19]}
                          </div>
                        </div>
                        <span style="background:{badge_color}22;color:{badge_color};border:1px solid {badge_color}44;
                              padding:4px 14px;border-radius:20px;font-size:0.8rem;font-weight:700">
                          {status.upper()}
                        </span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -----------------------------------------------------------------------
    # Tab 2: Audit History
    # -----------------------------------------------------------------------
    with tabs[1]:
        st.markdown(
            f"<div style='font-size:1.1rem;font-weight:700;color:{COLOR_TEXT};margin-bottom:16px'>"
            "Audit History</div>",
            unsafe_allow_html=True,
        )

        search_col, btn_col = st.columns([4, 1])
        with search_col:
            search_term = st.text_input(
                "Search by URL or email",
                placeholder="example.com or user@email.com",
                label_visibility="collapsed",
            )
        with btn_col:
            if st.button("�� Refresh", key="refresh_history"):
                st.rerun()

        all_audits = db.get_all_audits(limit=200)
        if search_term:
            q = search_term.lower()
            all_audits = [
                a for a in all_audits
                if q in (a.get("website_url") or "").lower()
                or q in (a.get("customer_email") or "").lower()
            ]

        if not all_audits:
            st.info("No audits found.")
        else:
            import pandas as pd  # noqa: PLC0415

            df = pd.DataFrame(all_audits)
            want = ["id", "customer_name", "customer_email", "website_url", "status", "seo_score", "created_at"]
            display_cols = [c for c in want if c in df.columns]
            st.dataframe(
                df[display_cols].rename(columns={
                    "id": "ID", "customer_name": "Name", "customer_email": "Email",
                    "website_url": "URL", "status": "Status", "seo_score": "Score",
                    "created_at": "Created",
                }),
                use_container_width=True,
                height=400,
            )

            st.markdown("---")
            st.markdown(
                f"<div style='font-weight:700;color:{COLOR_TEXT};margin-bottom:8px'>Audit Actions</div>",
                unsafe_allow_html=True,
            )
            audit_ids = [str(a["id"]) for a in all_audits]
            if audit_ids:
                sel_id = st.selectbox("Select Audit ID", audit_ids, key="sel_audit_id")
                if sel_id:
                    audit_record = db.get_audit_by_id(int(sel_id))
                    if audit_record:
                        act1, act2, act3 = st.columns(3)
                        with act1:
                            if audit_record.get("report_html"):
                                if st.button("👁 View Dashboard", key="view_dash"):
                                    st.components.v1.html(
                                        audit_record["report_html"], height=700, scrolling=True
                                    )
                        with act2:
                            if audit_record.get("report_html"):
                                st.download_button(
                                    "⬇️ Download Dashboard",
                                    data=audit_record["report_html"],
                                    file_name=f"SEO_Dashboard_{sel_id}.html",
                                    mime="text/html",
                                    key="dl_html",
                                )
                        with act3:
                            if st.button("📧 Resend Email", key="resend_email"):
                                if audit_record.get("audit_results"):
                                    res = audit_record["audit_results"]
                                    html_d = audit_record.get("report_html") or generate_html_dashboard(
                                        res, int(sel_id)
                                    )
                                    pdf_b = generate_pdf_report(
                                        res,
                                        customer_name=audit_record.get("customer_name", ""),
                                        business_name=audit_record.get("business_name", ""),
                                    )
                                    ok, msg = send_audit_report(
                                        to_email=audit_record["customer_email"],
                                        customer_name=audit_record.get("customer_name", ""),
                                        website_url=audit_record["website_url"],
                                        seo_score=audit_record.get("seo_score", 0),
                                        html_dashboard_content=html_d,
                                        pdf_bytes=pdf_b,
                                        business_name=audit_record.get("business_name", ""),
                                    )
                                    if ok:
                                        st.success(f"Email resent: {msg}")
                                    else:
                                        st.error(f"Failed: {msg}")
                                else:
                                    st.warning("No audit results stored for this record.")

    # -----------------------------------------------------------------------
    # Tab 3: Monthly Analytics
    # -----------------------------------------------------------------------
    with tabs[2]:
        st.markdown(
            f"<div style='font-size:1.1rem;font-weight:700;color:{COLOR_TEXT};margin-bottom:16px'>"
            "Monthly Analytics</div>",
            unsafe_allow_html=True,
        )

        analytics = db.get_monthly_analytics()

        audits_pm = analytics.get("audits_per_month", [])
        if audits_pm:
            months = [r["month"] for r in audits_pm]
            counts = [r["count"] for r in audits_pm]
            fig_audits = go.Figure(
                go.Bar(
                    x=months, y=counts,
                    marker_color=COLOR_ACCENT,
                    hovertemplate="%{x}: %{y} audits<extra></extra>",
                )
            )
            fig_audits.update_layout(
                title="Audits per Month",
                paper_bgcolor=COLOR_CARD, plot_bgcolor=COLOR_BG,
                font={"color": COLOR_TEXT},
                xaxis={"tickfont": {"color": COLOR_TEXT}},
                yaxis={"gridcolor": "#222", "tickfont": {"color": COLOR_SUB}},
                margin={"t": 50, "b": 30, "l": 40, "r": 20},
                height=300,
            )
            st.plotly_chart(fig_audits, use_container_width=True)
        else:
            st.info("No monthly audit data available yet.")

        avg_scores = analytics.get("avg_score_per_month", [])
        if avg_scores:
            months_s = [r["month"] for r in avg_scores]
            scores_s = [r["avg_score"] for r in avg_scores]
            fig_scores = go.Figure(
                go.Scatter(
                    x=months_s, y=scores_s,
                    mode="lines+markers",
                    line={"color": COLOR_PASS, "width": 3},
                    marker={"size": 8, "color": COLOR_PASS},
                    hovertemplate="%{x}: avg %{y}<extra></extra>",
                )
            )
            fig_scores.update_layout(
                title="Average SEO Score per Month",
                paper_bgcolor=COLOR_CARD, plot_bgcolor=COLOR_BG,
                font={"color": COLOR_TEXT},
                xaxis={"tickfont": {"color": COLOR_TEXT}},
                yaxis={"range": [0, 100], "gridcolor": "#222", "tickfont": {"color": COLOR_SUB}},
                margin={"t": 50, "b": 30, "l": 40, "r": 20},
                height=300,
            )
            st.plotly_chart(fig_scores, use_container_width=True)

        col_a, col_b = st.columns(2, gap="large")

        with col_a:
            status_dist = analytics.get("status_distribution", {})
            if status_dist:
                status_color_map = {
                    "completed": COLOR_PASS, "failed": COLOR_FAIL,
                    "pending": COLOR_WARN, "processing": COLOR_ACCENT,
                }
                fig_status = go.Figure(
                    go.Pie(
                        labels=list(status_dist.keys()),
                        values=list(status_dist.values()),
                        marker={"colors": [status_color_map.get(k, COLOR_SUB) for k in status_dist]},
                        hole=0.45,
                        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
                        textfont={"color": "#fff"},
                    )
                )
                fig_status.update_layout(
                    title="Audit Status Distribution",
                    paper_bgcolor=COLOR_CARD,
                    font={"color": COLOR_TEXT},
                    legend={"font": {"color": COLOR_TEXT}},
                    margin={"t": 50, "b": 20, "l": 20, "r": 20},
                    height=320,
                )
                st.plotly_chart(fig_status, use_container_width=True)

        with col_b:
            top_issues = analytics.get("top_issues", [])
            if top_issues:
                issue_names = [i["issue"] for i in top_issues]
                issue_counts = [i["count"] for i in top_issues]
                fig_issues = go.Figure(
                    go.Bar(
                        x=issue_counts, y=issue_names,
                        orientation="h",
                        marker_color=COLOR_FAIL,
                        hovertemplate="%{y}: %{x}<extra></extra>",
                    )
                )
                fig_issues.update_layout(
                    title="Top Failing Checks",
                    paper_bgcolor=COLOR_CARD, plot_bgcolor=COLOR_BG,
                    font={"color": COLOR_TEXT},
                    xaxis={"gridcolor": "#222", "tickfont": {"color": COLOR_SUB}},
                    yaxis={"tickfont": {"color": COLOR_TEXT}, "autorange": "reversed"},
                    margin={"t": 50, "b": 20, "l": 20, "r": 20},
                    height=320,
                )
                st.plotly_chart(fig_issues, use_container_width=True)
            else:
                st.info("No issue data available yet.")

    # -----------------------------------------------------------------------
    # Tab 4: Database Status
    # -----------------------------------------------------------------------
    with tabs[3]:
        st.markdown(
            f"<div style='font-size:1.1rem;font-weight:700;color:{COLOR_TEXT};margin-bottom:16px'>"
            "Database Status</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔄 Refresh DB Status", key="refresh_db"):
            st.rerun()

        db_stats = db.get_db_stats()

        # Connection status banner
        if db_stats.get("connected"):
            st.success("✅ SQLite is running and connected")
        else:
            st.error(f"❌ Database connection failed: {db_stats.get('error', 'Unknown error')}")

        # Key metrics
        s1, s2, s3 = st.columns(3)
        s1.metric("SQLite Version", db_stats.get("sqlite_version", "—"))
        s2.metric("File Size", f"{db_stats.get('file_size_kb', 0)} KB")
        total_rows = sum(
            v for v in db_stats.get("tables", {}).values() if isinstance(v, int)
        )
        s3.metric("Total Rows", total_rows)

        # DB path
        st.markdown(
            f"<div style='color:{COLOR_SUB};font-size:0.85rem;margin-top:12px;margin-bottom:16px'>"
            f"<b style='color:{COLOR_TEXT}'>Database Path:</b> "
            f"<code style='background:#1a1a1a;padding:2px 8px;border-radius:4px;color:{COLOR_ACCENT}'>"
            f"{db_stats.get('db_path', '—')}</code></div>",
            unsafe_allow_html=True,
        )

        # Table row counts
        tables = db_stats.get("tables", {})
        if tables:
            st.markdown(
                f"<div style='font-weight:700;color:{COLOR_TEXT};margin-bottom:8px'>Table Row Counts</div>",
                unsafe_allow_html=True,
            )
            for tbl_name, row_count in tables.items():
                st.markdown(
                    f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                background:{COLOR_CARD};border:1px solid #2a2a2a;border-radius:8px;
                                padding:12px 18px;margin-bottom:8px">
                      <div>
                        <span style="color:{COLOR_ACCENT};font-family:monospace;font-size:0.95rem">
                          {tbl_name}
                        </span>
                      </div>
                      <div style="background:{COLOR_ACCENT}22;color:{COLOR_ACCENT};
                                  border:1px solid {COLOR_ACCENT}44;padding:2px 14px;
                                  border-radius:16px;font-size:0.85rem;font-weight:700">
                        {row_count} rows
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.warning("No tables found — the database may not have been initialised.")
