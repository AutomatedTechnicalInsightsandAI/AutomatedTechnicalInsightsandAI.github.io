"""
Influencer marketing analytics module for ATI & AI platform.

Tracks influencer profile metrics, campaign performance, audience quality,
content performance, and provides tier classification.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Influencer Tier Classification
# ---------------------------------------------------------------------------

TIER_NANO = "nano"
TIER_MICRO = "micro"
TIER_MACRO = "macro"
TIER_MEGA = "mega"

TIER_THRESHOLDS: Dict[str, Tuple[int, Optional[int]]] = {
    TIER_NANO:  (0,         10_000),
    TIER_MICRO: (10_000,    100_000),
    TIER_MACRO: (100_000,   1_000_000),
    TIER_MEGA:  (1_000_000, None),
}

TIER_LABELS: Dict[str, str] = {
    TIER_NANO:  "Nano (< 10K)",
    TIER_MICRO: "Micro (10K – 100K)",
    TIER_MACRO: "Macro (100K – 1M)",
    TIER_MEGA:  "Mega (1M+)",
}


def classify_influencer_tier(follower_count: int) -> str:
    """Return the tier name for the given follower count."""
    if follower_count >= 1_000_000:
        return TIER_MEGA
    if follower_count >= 100_000:
        return TIER_MACRO
    if follower_count >= 10_000:
        return TIER_MICRO
    return TIER_NANO


def get_tier_label(tier: str) -> str:
    """Return the human-readable label for a tier key."""
    return TIER_LABELS.get(tier, tier.capitalize())


# ---------------------------------------------------------------------------
# Profile Metrics
# ---------------------------------------------------------------------------

def calculate_engagement_rate(
    followers: int,
    avg_likes: float,
    avg_comments: float,
) -> float:
    """
    Return engagement rate as a percentage (0–100).

    Engagement rate = (avg_likes + avg_comments) / followers * 100
    Returns 0.0 when followers is zero.
    """
    if followers <= 0:
        return 0.0
    return round((avg_likes + avg_comments) / followers * 100, 4)


def calculate_growth_rate(
    followers_start: int,
    followers_end: int,
) -> float:
    """
    Return follower growth rate as a percentage.

    Positive = growth, negative = decline, 0 when start is zero.
    """
    if followers_start <= 0:
        return 0.0
    return round((followers_end - followers_start) / followers_start * 100, 4)


def build_profile_metrics(
    username: str,
    platform: str,
    follower_count: int,
    following_count: int = 0,
    avg_likes: float = 0.0,
    avg_comments: float = 0.0,
    post_count: int = 0,
    bio: str = "",
    profile_url: str = "",
) -> Dict[str, Any]:
    """
    Assemble a complete profile metrics dictionary for an influencer.

    Parameters
    ----------
    username:         Social media handle (without @).
    platform:         One of 'instagram', 'tiktok', 'youtube', 'linkedin'.
    follower_count:   Current total followers/subscribers.
    following_count:  Number of accounts the influencer follows.
    avg_likes:        Average likes per post (over recent 30 posts or available).
    avg_comments:     Average comments per post.
    post_count:       Total number of posts/videos published.
    bio:              Profile bio / description.
    profile_url:      Direct link to the profile page.
    """
    engagement_rate = calculate_engagement_rate(follower_count, avg_likes, avg_comments)
    tier = classify_influencer_tier(follower_count)
    follower_to_following = (
        round(follower_count / following_count, 2) if following_count > 0 else None
    )

    return {
        "username": username,
        "platform": platform.lower(),
        "follower_count": follower_count,
        "following_count": following_count,
        "follower_to_following_ratio": follower_to_following,
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "post_count": post_count,
        "engagement_rate": engagement_rate,
        "tier": tier,
        "tier_label": get_tier_label(tier),
        "bio": bio,
        "profile_url": profile_url,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Audience Quality
# ---------------------------------------------------------------------------

def calculate_authenticity_score(
    real_follower_pct: float,
    engagement_rate: float,
    follower_growth_rate: float,
    suspicious_follower_pct: float = 0.0,
) -> float:
    """
    Return an audience authenticity score (0–100).

    Weights:
    - 50 % real-follower percentage
    - 25 % engagement quality (capped at a reasonable ceiling per tier)
    - 15 % organic growth signal
    - 10 % penalty for suspicious followers

    Parameters
    ----------
    real_follower_pct:       Percentage of followers estimated to be real (0–100).
    engagement_rate:         Overall engagement rate (%).
    follower_growth_rate:    Monthly follower growth rate (%).
    suspicious_follower_pct: Percentage of followers flagged as suspicious (0–100).
    """
    # Real followers component (50 pts max)
    real_component = min(real_follower_pct, 100.0) * 0.50

    # Engagement component: 3 % ER → full 25 pts; linear below
    engagement_component = min(engagement_rate / 3.0 * 25.0, 25.0)

    # Growth component: 5 % monthly growth → full 15 pts
    growth_component = min(max(follower_growth_rate, 0.0) / 5.0 * 15.0, 15.0)

    # Suspicious-follower penalty (deducted from 10-pt buffer)
    suspicious_penalty = min(suspicious_follower_pct, 100.0) * 0.10

    score = real_component + engagement_component + growth_component - suspicious_penalty
    return round(max(0.0, min(score, 100.0)), 2)


def build_audience_quality(
    real_follower_pct: float = 80.0,
    engagement_rate: float = 2.0,
    follower_growth_rate: float = 1.0,
    suspicious_follower_pct: float = 5.0,
    top_countries: Optional[List[Dict[str, Any]]] = None,
    age_distribution: Optional[Dict[str, float]] = None,
    gender_split: Optional[Dict[str, float]] = None,
    top_interests: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build a comprehensive audience quality report.

    Parameters
    ----------
    top_countries:       List of {'country': str, 'pct': float}.
    age_distribution:    Dict of age-bracket → percentage (e.g. {'18-24': 35.0}).
    gender_split:        Dict of gender → percentage (e.g. {'female': 60.0, 'male': 40.0}).
    top_interests:       List of interest categories (e.g. ['Fashion', 'Travel']).
    """
    authenticity = calculate_authenticity_score(
        real_follower_pct,
        engagement_rate,
        follower_growth_rate,
        suspicious_follower_pct,
    )
    return {
        "authenticity_score": authenticity,
        "real_follower_pct": real_follower_pct,
        "suspicious_follower_pct": suspicious_follower_pct,
        "top_countries": top_countries or [],
        "age_distribution": age_distribution or {},
        "gender_split": gender_split or {},
        "top_interests": top_interests or [],
    }


# ---------------------------------------------------------------------------
# Campaign Performance
# ---------------------------------------------------------------------------

def calculate_ctr(clicks: int, impressions: int) -> float:
    """Return click-through rate as a percentage."""
    if impressions <= 0:
        return 0.0
    return round(clicks / impressions * 100, 4)


def calculate_cpm(budget: float, impressions: int) -> float:
    """Return cost per thousand impressions (CPM)."""
    if impressions <= 0:
        return 0.0
    return round(budget / impressions * 1000, 4)


def calculate_cpc(budget: float, clicks: int) -> float:
    """Return cost per click (CPC)."""
    if clicks <= 0:
        return 0.0
    return round(budget / clicks, 4)


def calculate_roi(revenue: float, cost: float) -> float:
    """Return campaign ROI as a percentage."""
    if cost <= 0:
        return 0.0
    return round((revenue - cost) / cost * 100, 2)


def calculate_estimated_earnings(
    follower_count: int,
    engagement_rate: float,
    platform: str = "instagram",
    post_type: str = "post",
) -> float:
    """
    Estimate per-post earnings using industry benchmarks (USD).

    Benchmarks (approximate):
    - Instagram feed post:   $10 per 10K followers × ER multiplier
    - Instagram Story:       $5 per 10K followers
    - TikTok video:          $8 per 10K followers × ER multiplier
    - YouTube video:         $20 per 10K subscribers (CPM-based estimate)
    - LinkedIn post:         $15 per 10K followers (B2B premium)
    """
    base_rate_per_10k = {
        "instagram": {"post": 10.0, "story": 5.0, "reel": 12.0},
        "tiktok":    {"video": 8.0, "live": 4.0},
        "youtube":   {"video": 20.0, "short": 5.0},
        "linkedin":  {"post": 15.0, "article": 20.0},
    }
    platform_rates = base_rate_per_10k.get(platform.lower(), {"post": 10.0})
    base = platform_rates.get(post_type.lower(), list(platform_rates.values())[0])

    # ER multiplier: 1× at 2 % baseline, up to 3× at 6 %+
    er_multiplier = min(max(engagement_rate / 2.0, 0.5), 3.0)
    estimated = base * (follower_count / 10_000) * er_multiplier
    return round(estimated, 2)


def build_campaign_performance(
    campaign_name: str,
    budget: float,
    reach: int,
    impressions: int,
    clicks: int,
    conversions: int,
    revenue: float,
    start_date: str = "",
    end_date: str = "",
) -> Dict[str, Any]:
    """
    Build a complete campaign performance metrics dictionary.
    """
    ctr = calculate_ctr(clicks, impressions)
    cpm = calculate_cpm(budget, impressions)
    cpc = calculate_cpc(budget, clicks)
    roi = calculate_roi(revenue, budget)
    conversion_rate = round(conversions / clicks * 100, 4) if clicks > 0 else 0.0

    return {
        "campaign_name": campaign_name,
        "budget": budget,
        "reach": reach,
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "revenue": revenue,
        "ctr": ctr,
        "cpm": cpm,
        "cpc": cpc,
        "roi": roi,
        "conversion_rate": conversion_rate,
        "start_date": start_date,
        "end_date": end_date,
    }


# ---------------------------------------------------------------------------
# Content Performance
# ---------------------------------------------------------------------------

def get_engagement_benchmark(tier: str) -> Dict[str, float]:
    """
    Return industry-average engagement rate benchmarks by tier (%).

    Sources: industry reports (approximate medians).
    """
    benchmarks = {
        TIER_NANO:  {"low": 3.0, "average": 5.0, "high": 10.0},
        TIER_MICRO: {"low": 1.5, "average": 3.0, "high": 6.0},
        TIER_MACRO: {"low": 0.5, "average": 1.5, "high": 3.5},
        TIER_MEGA:  {"low": 0.2, "average": 0.8, "high": 2.0},
    }
    return benchmarks.get(tier, benchmarks[TIER_MICRO])


def rate_engagement(engagement_rate: float, tier: str) -> str:
    """
    Compare an influencer's ER against tier benchmarks.

    Returns one of: 'excellent', 'above_average', 'average', 'below_average', 'poor'.
    """
    benchmarks = get_engagement_benchmark(tier)
    if engagement_rate >= benchmarks["high"]:
        return "excellent"
    if engagement_rate >= benchmarks["average"]:
        return "above_average"
    if engagement_rate >= benchmarks["low"]:
        return "average"
    if engagement_rate >= benchmarks["low"] * 0.5:
        return "below_average"
    return "poor"


def build_content_performance(
    avg_likes: float,
    avg_comments: float,
    avg_shares: float = 0.0,
    avg_saves: float = 0.0,
    avg_video_views: float = 0.0,
    follower_count: int = 0,
    top_hashtags: Optional[List[Dict[str, Any]]] = None,
    best_posting_times: Optional[List[str]] = None,
    content_themes: Optional[List[str]] = None,
    recent_posts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Build a content performance summary.

    Parameters
    ----------
    top_hashtags:       List of {'hashtag': str, 'avg_reach': int, 'usage_count': int}.
    best_posting_times: List of strings like 'Tuesday 18:00 UTC'.
    content_themes:     List of recurring theme labels.
    recent_posts:       List of recent post dicts with engagement data.
    """
    tier = classify_influencer_tier(follower_count)
    engagement_rate = calculate_engagement_rate(follower_count, avg_likes, avg_comments)
    engagement_rating = rate_engagement(engagement_rate, tier)
    benchmark = get_engagement_benchmark(tier)

    return {
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "avg_shares": avg_shares,
        "avg_saves": avg_saves,
        "avg_video_views": avg_video_views,
        "engagement_rate": engagement_rate,
        "engagement_rating": engagement_rating,
        "engagement_benchmark": benchmark,
        "top_hashtags": top_hashtags or [],
        "best_posting_times": best_posting_times or [],
        "content_themes": content_themes or [],
        "recent_posts": recent_posts or [],
    }


# ---------------------------------------------------------------------------
# Influencer Scorecard
# ---------------------------------------------------------------------------

def build_influencer_scorecard(
    profile: Dict[str, Any],
    audience_quality: Dict[str, Any],
    content: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute an overall influencer score (0–100) and component ratings.

    Weights:
    - 30 % audience authenticity
    - 30 % engagement quality vs tier benchmark
    - 20 % audience size (logarithmic; mega→100, nano→10)
    - 20 % growth momentum
    """
    import math

    auth_score = audience_quality.get("authenticity_score", 50.0)
    engagement_rate = content.get("engagement_rate", 0.0)
    tier = profile.get("tier", TIER_MICRO)
    follower_count = profile.get("follower_count", 1)

    # Engagement vs benchmark (0–100)
    benchmark = get_engagement_benchmark(tier)
    er_score = min(engagement_rate / benchmark["high"] * 100.0, 100.0)

    # Audience size score (logarithmic)
    size_score = min(math.log10(max(follower_count, 1)) / math.log10(10_000_000) * 100.0, 100.0)

    # Growth score (0–100 based on 0–10 % monthly growth)
    growth_rate = profile.get("growth_rate", 0.0)
    growth_score = min(max(growth_rate, 0.0) / 10.0 * 100.0, 100.0)

    overall = round(
        auth_score * 0.30
        + er_score * 0.30
        + size_score * 0.20
        + growth_score * 0.20,
        2,
    )

    rating = "poor"
    if overall >= 80:
        rating = "excellent"
    elif overall >= 65:
        rating = "above_average"
    elif overall >= 50:
        rating = "average"
    elif overall >= 35:
        rating = "below_average"

    return {
        "overall_score": overall,
        "rating": rating,
        "components": {
            "authenticity": round(auth_score * 0.30, 2),
            "engagement": round(er_score * 0.30, 2),
            "audience_size": round(size_score * 0.20, 2),
            "growth": round(growth_score * 0.20, 2),
        },
    }


# ---------------------------------------------------------------------------
# Comparison & Discovery Helpers
# ---------------------------------------------------------------------------

def compare_influencers(
    influencers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Accept a list of influencer profile dicts and return them sorted by
    overall scorecard score (highest first), with rank added.
    """
    scored = []
    for inf in influencers:
        audience_quality = inf.get("audience_quality", {})
        content = inf.get("content_performance", {})
        scorecard = build_influencer_scorecard(inf, audience_quality, content)
        scored.append({**inf, "scorecard": scorecard})

    scored.sort(key=lambda x: x["scorecard"]["overall_score"], reverse=True)
    for rank, item in enumerate(scored, start=1):
        item["rank"] = rank
    return scored


def filter_influencers(
    influencers: List[Dict[str, Any]],
    min_followers: int = 0,
    max_followers: Optional[int] = None,
    min_engagement_rate: float = 0.0,
    platforms: Optional[List[str]] = None,
    tiers: Optional[List[str]] = None,
    min_authenticity: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Filter a list of influencer dicts by discovery criteria.
    All parameters are optional; omitting them applies no filter on that dimension.
    """
    result = []
    for inf in influencers:
        fc = inf.get("follower_count", 0)
        if fc < min_followers:
            continue
        if max_followers is not None and fc > max_followers:
            continue
        er = inf.get("engagement_rate") or inf.get(
            "content_performance", {}
        ).get("engagement_rate", 0.0)
        if er < min_engagement_rate:
            continue
        if platforms:
            plat = inf.get("platform", "").lower()
            if plat not in [p.lower() for p in platforms]:
                continue
        if tiers:
            tier = inf.get("tier") or classify_influencer_tier(fc)
            if tier not in tiers:
                continue
        auth = inf.get("audience_quality", {}).get("authenticity_score", 100.0)
        if auth < min_authenticity:
            continue
        result.append(inf)
    return result


# ---------------------------------------------------------------------------
# Growth Trend Analysis
# ---------------------------------------------------------------------------

def analyse_growth_trend(
    historical_metrics: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Analyse a chronological list of metric snapshots.

    Each snapshot should contain:
    - 'date':            ISO date string
    - 'followers':       int
    - 'engagement_rate': float
    - 'post_count':      int (optional)

    Returns:
    - total_growth_pct:   Follower growth from first to last snapshot.
    - avg_monthly_growth: Average month-over-month growth rate.
    - er_trend:           'improving', 'stable', or 'declining'.
    - peak_followers:     Maximum follower count observed.
    - snapshots:          The input list, unchanged.
    """
    if not historical_metrics:
        return {
            "total_growth_pct": 0.0,
            "avg_monthly_growth": 0.0,
            "er_trend": "stable",
            "peak_followers": 0,
            "snapshots": [],
        }

    # Sort by date ascending
    snapshots = sorted(historical_metrics, key=lambda x: x.get("date", ""))

    first_followers = snapshots[0].get("followers", 0)
    last_followers = snapshots[-1].get("followers", 0)
    peak_followers = max(s.get("followers", 0) for s in snapshots)

    total_growth = calculate_growth_rate(first_followers, last_followers)

    # Average month-over-month growth
    mo_growths = []
    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1].get("followers", 0)
        curr = snapshots[i].get("followers", 0)
        if prev > 0:
            mo_growths.append((curr - prev) / prev * 100)
    avg_monthly = round(sum(mo_growths) / len(mo_growths), 4) if mo_growths else 0.0

    # ER trend — compare first half vs second half average
    mid = len(snapshots) // 2
    if mid > 0:
        first_half_er = [s.get("engagement_rate", 0.0) for s in snapshots[:mid]]
        second_half_er = [s.get("engagement_rate", 0.0) for s in snapshots[mid:]]
        avg_first = sum(first_half_er) / len(first_half_er)
        avg_second = sum(second_half_er) / len(second_half_er)
        if avg_second > avg_first * 1.05:
            er_trend = "improving"
        elif avg_second < avg_first * 0.95:
            er_trend = "declining"
        else:
            er_trend = "stable"
    else:
        er_trend = "stable"

    return {
        "total_growth_pct": total_growth,
        "avg_monthly_growth": avg_monthly,
        "er_trend": er_trend,
        "peak_followers": peak_followers,
        "snapshots": snapshots,
    }
