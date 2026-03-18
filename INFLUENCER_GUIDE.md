# Influencer Marketing Guide — ATI & AI Platform

Welcome to the influencer marketing analytics suite built into the ATI & AI platform.  
This guide walks you through every feature, from adding your first influencer to downloading a campaign ROI report.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Getting Started](#2-getting-started)
3. [Influencer Discovery](#3-influencer-discovery)
4. [Campaign Management](#4-campaign-management)
5. [Influencer Scorecard](#5-influencer-scorecard)
6. [Audience Analytics](#6-audience-analytics)
7. [Social API Setup](#7-social-api-setup)
8. [Understanding Scores](#8-understanding-scores)
9. [FAQ](#9-faq)

---

## 1. Overview

The influencer marketing suite adds four new tools to the ATI & AI platform:

| Tool | What It Does |
|---|---|
| **Influencer Discovery** | Build and search your creator database; filter by platform, tier, engagement, and more |
| **Campaign Management** | Create campaigns, link influencers, record performance metrics, and download ROI reports |
| **Influencer Scorecard** | Generate weighted scores and comparison matrices for any set of influencers |
| **Audience Analytics** | Deep-dive into audience demographics, authenticity, and growth trends |

### Target Users

- **Small Businesses** — Validate an influencer partnership before committing budget
- **Social Media Influencers** — Track and showcase your own performance metrics
- **Marketing Agencies** — Manage multiple campaigns and influencer relationships at scale

---

## 2. Getting Started

### Step 1 — Open the app

Navigate to the Streamlit app URL.  The new tools appear in the service selection row as cards:

```
🔎 Influencer Discovery  |  📣 Campaign Management  |  🏆 Influencer Scorecard  |  👥 Audience Analytics
```

### Step 2 — Add your first influencer

Click **Influencer Discovery** → expand **"➕ Add / Update Influencer Profile"** → fill in the form → click **Save Influencer**.

You can always edit a profile later by submitting the form again with the same username + platform combination (the record is upserted automatically).

### Step 3 — Explore the tools

Once you have at least one influencer saved, all four tools become fully functional.

---

## 3. Influencer Discovery

### Adding profiles manually

Use the expandable form to add any creator:

| Field | Description |
|---|---|
| **Username** | Handle without the `@` symbol (e.g. `janedoe`) |
| **Platform** | One of: Instagram, TikTok, YouTube, LinkedIn |
| **Follower Count** | Current follower / subscriber count |
| **Engagement Rate (%)** | (Likes + Comments) ÷ Followers × 100 |
| **Monthly Growth Rate (%)** | Month-over-month follower growth |
| **Bio** | Short description or niche |
| **Profile URL** | Direct link to the creator's profile |

### Adding profiles via API (optional)

If you have configured social API credentials (see [Section 7](#7-social-api-setup)), you can fetch live data programmatically:

```python
from social_api_integration import fetch_influencer_profile
import database as db

db.init_db()
profile = fetch_influencer_profile("instagram", "janedoe")
db.upsert_influencer(
    username=profile["username"],
    platform=profile["platform"],
    follower_count=profile["follower_count"],
    engagement_rate=profile["engagement_rate"],
    audience_tier=profile["tier"],
    bio=profile["bio"],
    profile_url=profile["profile_url"],
)
```

### Filtering influencers

Use the four filter dropdowns above the results list:

- **Platform** — show only creators on a specific network
- **Tier** — Nano / Micro / Macro / Mega (see [Section 8](#8-understanding-scores))
- **Min Engagement Rate** — exclude low-engagement accounts
- **Min Followers** — set a follower floor

### Discovery results

Results are automatically ranked by overall scorecard score (highest first).  Each row shows:
- Rank, handle, platform
- Follower count, engagement rate, tier
- Weighted overall score out of 100

---

## 4. Campaign Management

### Creating a campaign

Click **Campaign Management** → **"➕ New Campaign"** tab → fill in the form:

| Field | Description |
|---|---|
| **Campaign Name** | Descriptive name, e.g. "Summer Launch 2026" |
| **Budget ($)** | Total spend allocated |
| **Start / End Date** | Campaign date range |
| **Expected Reach** | Estimated unique users to be reached |
| **Status** | `draft` → `active` → `paused` → `completed` |

### Linking influencers

Linking is currently done via Python (or a future admin panel enhancement):

```python
import database as db

db.init_db()
db.add_influencer_to_campaign(
    campaign_id=1,          # id returned by create_campaign()
    influencer_id=3,        # id returned by upsert_influencer()
    fee=500.0,              # agreed fee in USD
    expected_impressions=80_000,
)
```

### Updating performance metrics

Open the **"✏️ Update Metrics"** tab, select your campaign, enter the latest numbers, and click **Update Campaign**:

| Metric | Description |
|---|---|
| **Actual Reach** | Unique users who saw at least one post |
| **Impressions** | Total times posts were displayed |
| **Clicks** | Link clicks tracked via UTM / tracking links |
| **Conversions** | Sales, sign-ups, or other goal completions |
| **Revenue Generated ($)** | Attributed revenue for ROI calculation |

### Downloading a campaign report

In the **"📋 All Campaigns"** tab, expand any campaign and click **📊 Download HTML Report** to get a self-contained HTML file with:
- Key metrics (budget, revenue, ROI, CTR, CPM, CPC)
- A conversion funnel chart
- A breakdown table of linked influencers

---

## 5. Influencer Scorecard

### Generating scorecards

1. Click **Influencer Scorecard**
2. Select one or more influencers from the multiselect dropdown
3. Scores are calculated immediately

### Score components

| Component | Weight | Description |
|---|---|---|
| **Authenticity** | 30 % | Estimated real-follower %, engagement quality, and suspicious-follower penalty |
| **Engagement** | 30 % | Engagement rate vs tier benchmark (e.g. 3 % for Micro tier = full marks) |
| **Audience Size** | 20 % | Logarithmic scale; 10M followers = 100 pts, 1K = 43 pts |
| **Growth** | 20 % | Monthly growth rate; 10 %/month = full marks |

### Score ratings

| Score | Rating |
|---|---|
| 80–100 | Excellent 🟢 |
| 65–79 | Above Average 🔵 |
| 50–64 | Average 🟡 |
| 35–49 | Below Average 🟠 |
| 0–34 | Poor 🔴 |

### Downloading reports

Each influencer card has a **⬇️ Download HTML Report** button — a standalone, shareable report with Plotly charts including score gauge, component bars, audience pie, and growth trend.

When two or more influencers are selected, a **Comparison Matrix** renders inline and a **⬇️ Download Comparison Matrix** button appears.

---

## 6. Audience Analytics

### Audience quality estimator

This tool lets you estimate audience quality even without live API data.  
Adjust the sliders and input fields:

- **Real Followers (%)** — estimated percentage of genuine accounts
- **Suspicious Followers (%)** — bots, spam, or purchased followers
- **Top Countries** — primary geographic markets
- **Interests** — comma-separated interest categories
- **Gender Split** — adjust the female/male percentage slider
- **Age Distribution** — fill in percentages for each age bracket

The **Authenticity Score** (0–100) is recalculated in real time as you adjust the inputs.

### Visualisations

| Chart | What it shows |
|---|---|
| **Audience Composition Pie** | Real vs suspicious vs unknown follower breakdown |
| **Age Distribution Bar** | Percentage of audience in each age bracket |
| **Follower Growth Chart** | Historical follower trajectory (requires stored snapshots) |

### Storing metric snapshots

Snapshots power the growth trend chart.  Record them via Python:

```python
import database as db
from datetime import date

db.init_db()
db.record_influencer_metrics_snapshot(
    influencer_id=3,
    date=str(date.today()),      # "YYYY-MM-DD"
    followers=152_000,
    engagement_rate=3.1,
    post_count=280,
    avg_likes=4_500,
    avg_comments=220,
)
```

Call this daily (or weekly) to build up trend data.

---

## 7. Social API Setup

Live data fetching is optional but recommended for accurate, up-to-date metrics.

### Instagram (instagrapi)

1. Create a **secondary / dedicated** Instagram account for API access — never use your main account.
2. Set the credentials in your `.env` file or Streamlit secrets:

```
INSTAGRAM_USERNAME=your_api_account
INSTAGRAM_PASSWORD=your_api_password
```

> ⚠️ Instagram's private API has rate limits and may require CAPTCHA solving or device verification on first login. Use responsibly.

### TikTok (TikTokApi)

1. Open TikTok in a browser, log in, and extract the `ms_token` cookie value (see [TikTokApi README](https://github.com/davidteather/TikTok-Api) for instructions).
2. Set:

```
TIKTOK_MS_TOKEN=<your_ms_token>
```

> ⚠️ `ms_token` values expire. Refresh regularly.

### YouTube Data API v3

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → enable **YouTube Data API v3**
3. Create an **API key** (for read-only public data) and/or an **OAuth 2.0 client** (for authenticated requests)
4. Set:

```
YOUTUBE_API_KEY=AIza...
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
```

> The free quota is 10,000 units/day. Each `channels.list` call costs 1 unit.

### LinkedIn (python-linkedin-v2)

1. Create a LinkedIn app at [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Request the `r_liteprofile` and `r_emailaddress` scopes
3. Complete the OAuth 2.0 flow to obtain an access token
4. Set:

```
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...
LINKEDIN_ACCESS_TOKEN=...
```

---

## 8. Understanding Scores

### Influencer Tiers

| Tier | Range | Typical ER | Best For |
|---|---|---|---|
| **Nano** | < 10K | 5–10 % | Hyper-local, niche communities |
| **Micro** | 10K – 100K | 3–6 % | Targeted campaigns, high authenticity |
| **Macro** | 100K – 1M | 1.5–3.5 % | Brand awareness, broad reach |
| **Mega** | 1M+ | 0.8–2 % | Mass market, premium CPM |

### Engagement Rate Benchmarks

The scorecard uses tier-adjusted benchmarks to determine the engagement component:

| Tier | Low | Average | High (full marks) |
|---|---|---|---|
| Nano | 3 % | 5 % | 10 % |
| Micro | 1.5 % | 3 % | 6 % |
| Macro | 0.5 % | 1.5 % | 3.5 % |
| Mega | 0.2 % | 0.8 % | 2 % |

An influencer at 3 % ER with 500K followers (Macro tier) would score **above average** on engagement (above the 1.5 % average but below the 3.5 % ceiling).

### Estimated Earnings

The `calculate_estimated_earnings()` function uses industry benchmark rates:

| Platform | Content Type | Base Rate (per 10K followers) |
|---|---|---|
| Instagram | Feed post | $10 |
| Instagram | Story | $5 |
| Instagram | Reel | $12 |
| TikTok | Video | $8 |
| YouTube | Video | $20 |
| LinkedIn | Post | $15 |

Rates are multiplied by an engagement rate multiplier (0.5× at 1 % ER → 3× at 6 %+ ER).

---

## 9. FAQ

**Q: Can I use the platform without any social API credentials?**  
A: Yes. All tools work with manually entered data. API credentials are only needed to auto-populate profiles from live social media data.

**Q: Is my influencer data shared with anyone?**  
A: No. All data is stored locally in your SQLite database. Nothing is transmitted to third parties.

**Q: How do I back up my influencer database?**  
A: Copy the `.db` file (default: `seo_audits.db`) to a safe location. For cloud deployments, consider migrating to Supabase or another hosted PostgreSQL database.

**Q: Can I import a CSV of influencers?**  
A: Not yet via the UI. You can do it programmatically using `database.upsert_influencer()` in a loop over your CSV rows.

**Q: The scorecard shows 0/100 — what's wrong?**  
A: This typically happens when follower count is 0 or growth rate is negative. Update the influencer's profile with accurate metrics.

**Q: How do I track changes in an influencer's followers over time?**  
A: Call `database.record_influencer_metrics_snapshot()` once a day (e.g. via a cron job or Streamlit scheduled rerun). The Audience Analytics tool will then display a growth chart.

---

© ATI & AI. All rights reserved.
