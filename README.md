# ATI & AI — Automated Technical Insights & AI

**Professional SEO Audit Platform** | Built with Streamlit · Plotly · ReportLab · SQLite

> A fully automated, self-service SEO audit platform where customers submit a URL, receive a comprehensive interactive HTML dashboard and PDF report via email, and every result is persisted in a local SQLite database — all with zero manual intervention.

---

## What Is This Repository?

This is the source code for **[AutomatedTechnicalInsightsandAI.github.io](https://automatedtechnicalinsightsandai.github.io)** — the web presence and tooling for **ATI & AI**, a consulting practice specialising in:

- **Merchant POS Optimization** — payment infrastructure and Beacon Payments integrations
- **VMS Lifecycle Management** — video management system maintenance and legacy-to-modern migrations
- **Intelligence Layer R&D** — computer vision, behavioral analytics, and AI integrations

The centrepiece of the repository is a **free, professional SEO audit tool** hosted on Streamlit Cloud. It serves as both a standalone utility and a lead-generation engine for the consulting services above.

---

## Live Links

| Resource | URL |
|---|---|
| GitHub Pages site | <https://automatedtechnicalinsightsandai.github.io> |
| Streamlit audit app | <https://automatedtechnicalinsightsandaiappio-csbpdxg8nrnc5nfp3v9nmn.streamlit.app> |

---

## Features

### Customer-facing (public)
- **Audit request form** — URL, email, optional business name, contact name, and target keyword
- **Real-time progress bar** — live status from "fetching content" → "sending email" → "complete"
- **30+ automated SEO checks** across four categories (see [Audit Engine](#audit-engine) below)
- **Completion screen** — overall SEO score, pass/warning/fail breakdown, download buttons
- **Interactive HTML dashboard** — standalone file with embedded Plotly charts (gauge, pie, bar)
- **PDF report** — professional, printable documentation with cover page and recommendations
- **Automated email** — report PDF + interactive dashboard delivered automatically via SMTP

### Admin dashboard (password-protected)
| Tab | What you see |
|---|---|
| **Pending Queue** | All audits currently `pending` or `processing`, with customer info and status badges |
| **Audit History** | Searchable table of every completed audit; view dashboard, download HTML, or resend email |
| **Monthly Analytics** | Audits per month (bar), average SEO score (line), status distribution (pie), top failing checks (bar) |
| **Database Status** | Live SQLite connection check, version, file path, file size, and per-table row counts |

---

## Audit Engine

`seo_audit.py` runs the following checks and returns a structured JSON result with a weighted score (0–100):

| Category | Checks |
|---|---|
| **Technical** | HTTPS/SSL, `robots.txt`, `sitemap.xml`, mobile viewport meta tag, JSON-LD structured data, canonical tag |
| **On-Page** | Meta title (length), meta description (length), H1 (presence + uniqueness), H2 presence, Open Graph tags, Twitter Card, favicon, keyword-in-title/description/H1 |
| **Performance** | Page size (<1 MB pass / <3 MB warn / >3 MB fail), image alt-tag coverage, estimated load time |
| **Links** | Internal link count, external link count, broken links (samples up to 10) |

SSRF protection is enforced on every outbound request — private IPs, loopback addresses, link-local ranges, and non-HTTP(S) schemes are all rejected before any network call is made.

---

## Project Structure

```
.
├── streamlit_app.py        # Main Streamlit application (customer form + admin dashboard)
├── seo_audit.py            # SEO audit engine (30+ checks, SSRF protection, scoring)
├── report_generator.py     # HTML dashboard (Plotly) and PDF report (ReportLab) generation
├── database.py             # SQLite data layer (CRUD, analytics, diagnostics)
├── email_service.py        # SMTP email automation with PDF + HTML attachments
│
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template (copy to .env to configure)
│
├── _config.yml             # Jekyll / GitHub Pages configuration (Midnight theme)
├── _data/navigation.yml    # Site navigation menu
├── index.md                # Homepage content
├── services.md             # Enterprise services page
├── contact.md              # Calendly booking + LinkedIn links
├── assets/css/style.scss   # Custom CSS overrides for the Jekyll theme
│
└── .gitignore              # Excludes .env, *.db, __pycache__, generated PDFs, etc.
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI framework | [Streamlit](https://streamlit.io) |
| HTML parsing | [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) + `requests` |
| Interactive charts | [Plotly](https://plotly.com/python/) |
| PDF generation | [ReportLab](https://www.reportlab.com/) |
| HTML templates | [Jinja2](https://jinja.palletsprojects.com/) |
| Database | SQLite3 (stdlib) |
| Email | `smtplib` (stdlib) — Gmail SMTP-ready |
| Config | [python-dotenv](https://github.com/theskumar/python-dotenv) |
| Static site | Jekyll + GitHub Pages (Midnight theme) |

---

## Local Setup

### Prerequisites
- Python 3.11+

### 1. Clone and install dependencies
```bash
git clone https://github.com/AutomatedTechnicalInsightsandAI/AutomatedTechnicalInsightsandAI.github.io.git
cd AutomatedTechnicalInsightsandAI.github.io
pip install -r requirements.txt
```

### 2. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your values (see Environment Variables below)
```

### 3. Run the app
```bash
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501`.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values. None are required to run the app locally — missing values are handled gracefully.

| Variable | Description | Default |
|---|---|---|
| `EMAIL_SENDER` | Gmail address to send reports from | — |
| `EMAIL_PASSWORD` | Gmail [App Password](https://support.google.com/accounts/answer/185833) (not your regular password) | — |
| `EMAIL_SMTP_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | SMTP port | `587` |
| `ADMIN_PASSWORD` | Password to unlock the admin dashboard | `admin123` |
| `APP_URL` | Public URL of the deployed Streamlit app | — |
| `DATABASE_PATH` | Path to the SQLite database file | `seo_audits.db` |

> **Note:** Never commit `.env` — it is listed in `.gitignore`. The database file (`*.db`) is also excluded and is created automatically at runtime.

---

## Streamlit Cloud Deployment

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app pointing to `streamlit_app.py`.
3. In **Settings → Secrets**, add your environment variables (same keys as `.env`).
4. Deploy.

The SQLite database is ephemeral on Streamlit Cloud (resets on each deployment). For persistent storage, set `DATABASE_PATH` to a volume mount or switch to a hosted database.

---

## Module Reference

### `streamlit_app.py`
Entry point. Renders the customer audit request form and the password-protected admin dashboard. Imports all other modules and degrades gracefully if any import fails (errors are shown inline rather than crashing the app).

### `seo_audit.py`
`run_full_audit(url, keyword=None) → dict`  
Fetches the target URL, runs all checks, computes a weighted score, and returns a structured result dictionary. All outbound requests go through `_validated_url()` which enforces SSRF protection.

### `report_generator.py`
- `generate_html_dashboard(audit_data, audit_id) → str` — Returns a self-contained HTML file with embedded Plotly charts.
- `generate_pdf_report(audit_data, customer_name, business_name) → bytes` — Returns a PDF as raw bytes (not written to disk).

### `database.py`
Thin SQLite wrapper. Tables: `audit_requests`, `admin_notifications`. Key functions: `init_db()`, `create_audit_request()`, `update_audit_status()`, `get_all_audits()`, `get_pending_audits()`, `get_monthly_analytics()`, `get_db_stats()`.

### `email_service.py`
`send_audit_report(to_email, customer_name, website_url, seo_score, html_dashboard_content, pdf_bytes, business_name) → (bool, str)`  
Sends a branded HTML email with the PDF and HTML dashboard as attachments. Returns `(True, "Sent")` on success or `(False, reason)` on failure. Silently skips if `EMAIL_SENDER` / `EMAIL_PASSWORD` are not set.

---

## Security Notes

- **SSRF protection** — `_validated_url()` in `seo_audit.py` blocks requests to private/loopback/reserved IPs and non-HTTP(S) schemes before any network call.
- **SQL injection prevention** — all database queries use parameterised statements. `get_db_stats()` validates table names against a whitelist.
- **No secrets in source** — `.env`, `*.db`, and Streamlit secrets are all excluded from git via `.gitignore`.
- **Admin access** — the admin dashboard requires a password stored in `ADMIN_PASSWORD`; change the default (`admin123`) before deploying to production.

---

## Roadmap — What to Do Next

Below is a prioritised list of improvements. Items higher in the list have more immediate impact.

### 🔴 High priority

| # | Task | Why it matters |
|---|---|---|
| 1 | **Change `ADMIN_PASSWORD`** — update the default value (`admin123`) in your deployment secrets. A startup warning is now logged if the default is detected | The default password is public knowledge and must be changed before production use |
| 2 | **Configure email delivery** — set `EMAIL_SENDER` and `EMAIL_PASSWORD` in Streamlit Cloud secrets | Without this, audit reports are generated but never delivered to customers |
| 3 | **Persistent database** — the SQLite file resets on every Streamlit Cloud deployment; consider [Supabase](https://supabase.com) (free tier, Postgres) or [Streamlit Community Cloud file persistence](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-storage) | Without persistence, audit history and analytics are lost on each redeploy |

### 🟡 Medium priority

| # | Task | Why it matters |
|---|---|---|
| 4 | **Add a Portfolio page** (`portfolio.md`) — the navigation already has a "Portfolio" link pointing to `/portfolio` but the page doesn't exist yet | Clicking Portfolio in the site nav currently 404s |
| 5 | **Rate limiting on the audit form** — a single IP can currently spam unlimited audit requests; add a per-session or per-email cooldown | Protects the Streamlit Cloud resource quota and prevents abuse |
| 6 | **Unit tests** — add a `tests/` directory with `pytest` tests for `seo_audit.py` (at minimum: SSRF rejection, scoring algorithm, check categories) | Catches regressions when editing the audit engine |
| 7 | **CAPTCHA / bot protection** on the audit form | Prevents automated form submissions |

### 🟢 Lower priority / future ideas

| # | Task | Notes |
|---|---|---|
| 8 | **Intelligence Layer page** — flesh out the R&D computer vision project with technical details and a progress update | Currently only mentioned in passing on the homepage |
| 9 | **Webhook / Zapier integration** — send a notification to Slack or email when a new audit is submitted | Useful once request volume increases |
| 10 | **Audit comparison view** — let customers compare two audit results side-by-side (re-audit a URL after making fixes) | High-value UX feature that demonstrates improvement over time |
| 11 | **Export analytics to CSV** — add a download button in the Monthly Analytics tab | Makes reporting easier for client calls |
| 12 | **Dark/light theme toggle** on the Jekyll GitHub Pages site | Accessibility improvement |

---

## License

© ATI & AI. All rights reserved.
