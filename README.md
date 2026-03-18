# ATI & AI — Automated Technical Insights & AI

**Professional SEO & Influencer Marketing Analytics Platform** | Built with Streamlit · Plotly · ReportLab · SQLite

> A fully automated, self-service SEO audit and influencer marketing analytics platform. Customers submit a URL for a comprehensive SEO health check; social media influencers and marketing teams use the built-in analytics suite to discover creators, track campaigns, and measure ROI — all with zero manual intervention.

---

## What Is This Repository?

This is the source code for **[AutomatedTechnicalInsightsandAI.github.io](https://automatedtechnicalinsightsandai.github.io)** — the web presence and tooling for **ATI & AI**, a consulting practice specialising in:

- **Merchant POS Optimization** — payment infrastructure and Beacon Payments integrations
- **VMS Lifecycle Management** — video management system maintenance and legacy-to-modern migrations
- **Intelligence Layer R&D** — computer vision, behavioral analytics, and AI integrations
- **Influencer Marketing Analytics** — Modash-style discovery, scoring, and campaign management

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

### Influencer Marketing (new)
| Tool | Description |
|---|---|
| **Influencer Discovery** | Search, filter, and rank influencers by platform, tier, engagement rate, follower count, and authenticity |
| **Campaign Management** | Create campaigns, link influencers, update performance metrics (reach, impressions, CTR, ROI) |
| **Influencer Scorecard** | Weighted scoring system (authenticity 30 % + engagement 30 % + size 20 % + growth 20 %) |
| **Audience Analytics** | Demographic breakdown, authenticity analysis, geographic distribution, interest alignment, growth trends |
| **Influencer Reports** | Self-contained HTML reports with Plotly charts — downloadable and shareable |
| **Campaign ROI Reports** | Funnel chart, CPM/CPC/CVR metrics, influencer contribution breakdown |
| **Comparison Matrix** | Side-by-side comparison of multiple influencers with ranking |

### Admin dashboard (password-protected)
| Tab | What you see |
|---|---|
| **Pending Queue** | All audits currently `pending` or `processing`, with customer info and status badges |
| **Audit History** | Searchable table of every completed audit; view dashboard, download HTML, or resend email |
| **Monthly Analytics** | Audits per month (bar), average SEO score (line), status distribution (pie), top failing checks (bar) |
| **Database Status** | Live SQLite connection check, version, file path, file size, and per-table row counts (including influencer tables) |

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

## Influencer Tier System

| Tier | Follower Range | Description |
|---|---|---|
| **Nano** | < 10K | High authenticity, niche audiences, low cost |
| **Micro** | 10K – 100K | Strong engagement, targeted reach |
| **Macro** | 100K – 1M | Broad reach, brand credibility |
| **Mega** | 1M+ | Mass awareness, premium pricing |

---

## Project Structure

```
.
├── streamlit_app.py            # Main Streamlit app (SEO audit + influencer marketing tools)
├── seo_audit.py                # SEO audit engine (30+ checks, SSRF protection, scoring)
├── report_generator.py         # HTML dashboard & PDF reports for SEO + influencer analytics
├── database.py                 # SQLite data layer (SEO audits + influencer tables)
├── email_service.py            # SMTP email automation with PDF + HTML attachments
├── influencer_metrics.py       # Influencer analytics engine (tiers, scoring, trends)
├── social_api_integration.py   # Instagram / TikTok / YouTube / LinkedIn API adapters
│
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── INFLUENCER_GUIDE.md         # User guide for influencer marketing features
│
├── _config.yml                 # Jekyll / GitHub Pages configuration
├── _data/navigation.yml        # Site navigation menu
├── index.md / services.md / contact.md / portfolio.md
└── assets/css/style.scss       # Custom CSS for Jekyll theme
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
| Instagram API | [instagrapi](https://github.com/subzeroid/instagrapi) |
| TikTok API | [TikTokApi](https://github.com/davidteather/TikTok-Api) |
| YouTube API | [google-api-python-client](https://github.com/googleapis/google-api-python-client) + [google-auth-oauthlib](https://github.com/googleapis/google-auth-library-python-oauthlib) |
| LinkedIn API | [python-linkedin-v2](https://github.com/ozgur/python-linkedin) |
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

### Core / SEO
| Variable | Description | Default |
|---|---|---|
| `EMAIL_SENDER` | Gmail address to send reports from | — |
| `EMAIL_PASSWORD` | Gmail [App Password](https://support.google.com/accounts/answer/185833) | — |
| `EMAIL_SMTP_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | SMTP port | `587` |
| `ADMIN_PASSWORD` | Password to unlock the admin dashboard | `admin123` |
| `APP_URL` | Public URL of the deployed Streamlit app | — |
| `DATABASE_PATH` | Path to the SQLite database file | `seo_audits.db` |

### Social Media API (optional — only needed for live data fetching)
| Variable | Description |
|---|---|
| `INSTAGRAM_USERNAME` | Instagram account username for instagrapi login |
| `INSTAGRAM_PASSWORD` | Instagram account password for instagrapi login |
| `TIKTOK_MS_TOKEN` | TikTok `ms_token` cookie value — see [TikTokApi docs](https://github.com/davidteather/TikTok-Api) |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key — create at [console.cloud.google.com](https://console.cloud.google.com) |
| `YOUTUBE_CLIENT_ID` | OAuth 2.0 client ID (required for authenticated YouTube calls) |
| `YOUTUBE_CLIENT_SECRET` | OAuth 2.0 client secret |
| `LINKEDIN_CLIENT_ID` | LinkedIn app client ID |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn app client secret |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn OAuth 2.0 access token with `r_liteprofile` scope |

> **Note:** The app runs fully without social API credentials. Manual profile entry is supported via the Influencer Discovery form. See `INFLUENCER_GUIDE.md` for a step-by-step walkthrough.

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
Entry point. Renders the customer audit form, all influencer marketing tools, and the password-protected admin dashboard. All new tool sections are guarded with `elif active == "<key>":` routing — adding a new service is as simple as appending an entry to `SERVICES` and adding a matching `elif` block.

### `seo_audit.py`
`run_full_audit(url, keyword=None) → dict`  
Fetches the target URL, runs all checks, computes a weighted score, and returns a structured result dictionary. All outbound requests go through `_validated_url()` which enforces SSRF protection.

### `report_generator.py`
- `generate_html_dashboard(audit_data, audit_id) → str` — SEO audit HTML dashboard with Plotly charts.
- `generate_pdf_report(audit_data, customer_name, business_name) → bytes` — SEO audit PDF as raw bytes.
- `generate_influencer_html_report(influencer_data, scorecard, audience_quality, content_performance, growth_trend) → str` — Influencer profile HTML report.
- `generate_campaign_roi_report(campaign, influencers) → str` — Campaign ROI HTML report with funnel chart.
- `generate_influencer_comparison_html(influencers) → str` — Side-by-side comparison matrix for multiple influencers.

### `database.py`
SQLite wrapper. SEO tables: `audit_requests`, `admin_notifications`. Influencer tables: `influencers`, `social_accounts`, `influencer_campaigns`, `campaign_influencers`, `influencer_metrics`. Key functions: `init_db()`, `upsert_influencer()`, `get_all_influencers()`, `create_campaign()`, `update_campaign_metrics()`, `get_campaign_influencers()`, `record_influencer_metrics_snapshot()`.

### `influencer_metrics.py`
Pure analytics engine — no I/O. Key functions:
- `classify_influencer_tier(follower_count)` — returns tier string.
- `calculate_engagement_rate(followers, avg_likes, avg_comments)` — percentage.
- `calculate_authenticity_score(real_pct, er, growth, suspicious_pct)` — 0–100 score.
- `build_profile_metrics(...)` — assemble complete profile dict.
- `build_audience_quality(...)` — audience demographic and quality dict.
- `build_campaign_performance(...)` — CTR, CPM, CPC, ROI, CVR.
- `build_influencer_scorecard(profile, audience_quality, content)` — weighted 0–100 score.
- `compare_influencers(list)` — sort and rank by scorecard.
- `filter_influencers(list, **kwargs)` — filter by platform, tier, ER, followers.
- `analyse_growth_trend(history)` — growth rate, ER trend, peak followers.

### `social_api_integration.py`
API adapters for Instagram (`instagrapi`), TikTok (`TikTokApi`), YouTube (Data API v3), and LinkedIn (`python-linkedin-v2`). All credentials are loaded from environment variables or Streamlit secrets. Key functions:
- `fetch_influencer_profile(platform, identifier)` — unified dispatcher.
- `fetch_multiple_profiles(requests)` — batch fetch with graceful error handling.
- `normalise_cross_platform_metrics(profiles)` — fill missing keys for safe table rendering.

### `email_service.py`
`send_audit_report(to_email, customer_name, website_url, seo_score, html_dashboard_content, pdf_bytes, business_name) → (bool, str)`  
Sends branded HTML email with PDF and HTML dashboard as attachments.

---

## Security Notes

- **SSRF protection** — `_validated_url()` in `seo_audit.py` blocks requests to private/loopback/reserved IPs and non-HTTP(S) schemes before any network call.
- **SQL injection prevention** — all database queries use parameterised statements; `get_db_stats()` validates table names against a whitelist that now includes all influencer tables.
- **No secrets in source** — `.env`, `*.db`, and Streamlit secrets are all excluded from git via `.gitignore`.
- **Admin access** — the admin dashboard requires a password stored in `ADMIN_PASSWORD`; change the default (`admin123`) before deploying to production.
- **Social API credentials** — stored only in environment variables or Streamlit secrets; never logged or exposed in the UI.

---

## Roadmap — What to Do Next

### 🔴 High priority

| # | Task | Why it matters |
|---|---|---|
| 1 | **Change `ADMIN_PASSWORD`** — update the default value in your deployment secrets | The default password is public knowledge |
| 2 | **Configure email delivery** — set `EMAIL_SENDER` and `EMAIL_PASSWORD` | Without this, audit reports are generated but never delivered |
| 3 | **Persistent database** — SQLite resets on Streamlit Cloud redeploy; consider Supabase or Streamlit file persistence | Influencer and campaign data is lost on redeploy otherwise |

### 🟡 Medium priority

| # | Task | Why it matters |
|---|---|---|
| 4 | **Connect social APIs** — add Instagram/TikTok/YouTube/LinkedIn credentials in Streamlit secrets | Enables live follower/engagement data instead of manual entry |
| 5 | **Add a Portfolio page** (`portfolio.md`) | Navigation link currently 404s |
| 6 | **Rate limiting** on the audit form | Prevents abuse of Streamlit Cloud quota |
| 7 | **Unit tests** — `pytest` tests for `seo_audit.py` and `influencer_metrics.py` | Catches regressions |
| 8 | **CAPTCHA / bot protection** on the audit form | Prevents automated submissions |

### 🟢 Lower priority / future ideas

| # | Task | Notes |
|---|---|---|
| 9 | **Sentiment analysis** — analyse comment sentiment for influencer audience quality | Requires NLP library (e.g. `transformers`, `textblob`) |
| 10 | **Hashtag performance tracking** — store and trend hashtag reach over time | Useful for campaign optimisation |
| 11 | **Audience overlap detection** — identify shared audiences between two influencers | Prevents over-targeting the same users |
| 12 | **Webhook / Zapier integration** — post notifications on new audit or campaign event | Useful for team workflows |
| 13 | **Dark/light theme toggle** on the Jekyll site | Accessibility improvement |

---

## License

© ATI & AI. All rights reserved.

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
