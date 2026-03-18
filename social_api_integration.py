"""
Social media API integration layer for ATI & AI platform.

Provides a unified interface for fetching influencer data from
Instagram, TikTok, YouTube, and LinkedIn, then normalises it
into the common profile schema used by influencer_metrics.py.

All API credentials are read from environment variables or
Streamlit secrets — no secrets are stored in source code.

NOTE: This module uses optional dependencies.  When an SDK is not
installed the corresponding platform simply raises an ImportError
which is caught gracefully, allowing the app to run without every
SDK present.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from influencer_metrics import build_profile_metrics

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported platforms
# ---------------------------------------------------------------------------

SUPPORTED_PLATFORMS = ["instagram", "tiktok", "youtube", "linkedin"]


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------

def _env_or_secret(key: str, default: str = "") -> str:
    """
    Return the value of *key* from Streamlit secrets (if available) or from
    the process environment.  Falls back to *default*.
    """
    try:
        import streamlit as st  # noqa: PLC0415
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


def get_instagram_credentials() -> Dict[str, str]:
    return {
        "username": _env_or_secret("INSTAGRAM_USERNAME"),
        "password": _env_or_secret("INSTAGRAM_PASSWORD"),
    }


def get_tiktok_credentials() -> Dict[str, str]:
    return {
        "ms_token": _env_or_secret("TIKTOK_MS_TOKEN"),
    }


def get_youtube_credentials() -> Dict[str, str]:
    return {
        "api_key":       _env_or_secret("YOUTUBE_API_KEY"),
        "client_id":     _env_or_secret("YOUTUBE_CLIENT_ID"),
        "client_secret": _env_or_secret("YOUTUBE_CLIENT_SECRET"),
    }


def get_linkedin_credentials() -> Dict[str, str]:
    return {
        "client_id":     _env_or_secret("LINKEDIN_CLIENT_ID"),
        "client_secret": _env_or_secret("LINKEDIN_CLIENT_SECRET"),
        "access_token":  _env_or_secret("LINKEDIN_ACCESS_TOKEN"),
    }


# ---------------------------------------------------------------------------
# Data normalisation
# ---------------------------------------------------------------------------

def _normalise_number(value: Any, default: int = 0) -> int:
    """Safely convert a value to int, returning *default* on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalise_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning *default* on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------

def fetch_instagram_profile(username: str) -> Dict[str, Any]:
    """
    Fetch an Instagram influencer's public profile via instagrapi.

    Returns a normalised profile dict (same schema as build_profile_metrics).
    Raises RuntimeError if the SDK is not installed or credentials are missing.
    """
    try:
        from instagrapi import Client  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "instagrapi is required for Instagram integration.  "
            "Install it with: pip install instagrapi"
        ) from exc

    creds = get_instagram_credentials()
    if not creds["username"] or not creds["password"]:
        raise RuntimeError(
            "INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD must be set to fetch Instagram data."
        )

    cl = Client()
    cl.login(creds["username"], creds["password"])

    user_id = cl.user_id_from_username(username)
    info = cl.user_info(user_id)

    follower_count = _normalise_number(info.follower_count)
    following_count = _normalise_number(info.following_count)
    media_count = _normalise_number(info.media_count)

    # Approximate averages from recent 20 media items
    medias = cl.user_medias(user_id, amount=20)
    avg_likes = 0.0
    avg_comments = 0.0
    if medias:
        avg_likes = sum(m.like_count for m in medias) / len(medias)
        avg_comments = sum(m.comment_count for m in medias) / len(medias)

    return build_profile_metrics(
        username=username,
        platform="instagram",
        follower_count=follower_count,
        following_count=following_count,
        avg_likes=avg_likes,
        avg_comments=avg_comments,
        post_count=media_count,
        bio=info.biography or "",
        profile_url=f"https://www.instagram.com/{username}/",
    )


# ---------------------------------------------------------------------------
# TikTok
# ---------------------------------------------------------------------------

def fetch_tiktok_profile(username: str) -> Dict[str, Any]:
    """
    Fetch a TikTok creator's profile via TikTokApi.

    Returns a normalised profile dict.
    Raises RuntimeError if the SDK is not installed or ms_token is missing.
    """
    try:
        from TikTokApi import TikTokApi  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "TikTokApi is required for TikTok integration.  "
            "Install it with: pip install TikTokApi"
        ) from exc

    creds = get_tiktok_credentials()
    if not creds["ms_token"]:
        raise RuntimeError(
            "TIKTOK_MS_TOKEN must be set to fetch TikTok data.  "
            "See https://github.com/davidteather/TikTok-Api for instructions."
        )

    import asyncio  # noqa: PLC0415

    async def _fetch() -> Dict[str, Any]:
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[creds["ms_token"]],
                num_sessions=1,
                sleep_after=3,
            )
            user = api.user(username=username)
            user_data = await user.info()

            stats = user_data.get("stats", {})
            user_info = user_data.get("userInfo", {}).get("user", {})

            follower_count = _normalise_number(stats.get("followerCount", 0))
            following_count = _normalise_number(stats.get("followingCount", 0))
            video_count = _normalise_number(stats.get("videoCount", 0))

            # Approximate averages from recent videos
            avg_likes = 0.0
            avg_comments = 0.0
            videos = []
            async for video in user.videos(count=20):
                videos.append(video)
            if videos:
                avg_likes = sum(
                    _normalise_number(v.as_dict.get("stats", {}).get("diggCount", 0))
                    for v in videos
                ) / len(videos)
                avg_comments = sum(
                    _normalise_number(v.as_dict.get("stats", {}).get("commentCount", 0))
                    for v in videos
                ) / len(videos)

            return build_profile_metrics(
                username=username,
                platform="tiktok",
                follower_count=follower_count,
                following_count=following_count,
                avg_likes=avg_likes,
                avg_comments=avg_comments,
                post_count=video_count,
                bio=user_info.get("signature", ""),
                profile_url=f"https://www.tiktok.com/@{username}",
            )

    return asyncio.run(_fetch())


# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------

def fetch_youtube_channel(channel_id: str) -> Dict[str, Any]:
    """
    Fetch a YouTube channel's profile via the YouTube Data API v3.

    *channel_id* may be a channel ID (UCxxxxxx) or a custom handle (@handle).
    Requires YOUTUBE_API_KEY.
    Raises RuntimeError if google-auth-oauthlib or the API key is missing.
    """
    try:
        import googleapiclient.discovery  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "google-api-python-client is required for YouTube integration.  "
            "Install it with: pip install google-api-python-client google-auth-oauthlib"
        ) from exc

    creds = get_youtube_credentials()
    if not creds["api_key"]:
        raise RuntimeError("YOUTUBE_API_KEY must be set to fetch YouTube data.")

    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=creds["api_key"]
    )

    # Support both @handle and UC... channel IDs
    if channel_id.startswith("@"):
        search_kwargs = {"forHandle": channel_id.lstrip("@")}
    elif channel_id.startswith("UC"):
        search_kwargs = {"id": channel_id}
    else:
        search_kwargs = {"forUsername": channel_id}

    response = youtube.channels().list(
        part="snippet,statistics",
        **search_kwargs,
    ).execute()

    items = response.get("items", [])
    if not items:
        raise RuntimeError(f"No YouTube channel found for: {channel_id}")

    item = items[0]
    snippet = item.get("snippet", {})
    statistics = item.get("statistics", {})

    subscriber_count = _normalise_number(statistics.get("subscriberCount", 0))
    video_count = _normalise_number(statistics.get("videoCount", 0))
    view_count = _normalise_number(statistics.get("viewCount", 0))

    avg_views = round(view_count / max(video_count, 1), 2)

    handle = snippet.get("customUrl", channel_id)
    return build_profile_metrics(
        username=handle,
        platform="youtube",
        follower_count=subscriber_count,
        avg_likes=0.0,        # Likes hidden by default in YT API
        avg_comments=0.0,
        post_count=video_count,
        bio=snippet.get("description", ""),
        profile_url=f"https://www.youtube.com/{handle}",
    ) | {"avg_video_views": avg_views, "total_views": view_count}


# ---------------------------------------------------------------------------
# LinkedIn
# ---------------------------------------------------------------------------

def fetch_linkedin_profile(profile_id: str) -> Dict[str, Any]:
    """
    Fetch a LinkedIn member or company profile.

    Requires LINKEDIN_ACCESS_TOKEN.  The token must have at least the
    r_liteprofile and r_emailaddress scopes for personal profiles, or
    r_organization_social for company pages.

    Raises RuntimeError if python-linkedin-v2 or the token is missing.
    """
    try:
        from linkedin import linkedin as li  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "python-linkedin-v2 is required for LinkedIn integration.  "
            "Install it with: pip install python-linkedin-v2"
        ) from exc

    creds = get_linkedin_credentials()
    if not creds["access_token"]:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN must be set to fetch LinkedIn data.")

    authentication = li.LinkedInAuthentication(
        creds["client_id"],
        creds["client_secret"],
        redirect_uri="",
    )
    authentication.token = li.AccessToken(
        access_token=creds["access_token"],
        expires_in=3600,
        token_type="Bearer",
    )
    application = li.LinkedInApplication(authentication)

    profile = application.get_profile(
        member_id=profile_id,
        selectors=["id", "firstName", "lastName", "headline", "summary", "numConnections"],
    )

    full_name = " ".join(
        filter(
            None,
            [
                profile.get("firstName", {}).get("localized", {}).get("en_US", ""),
                profile.get("lastName", {}).get("localized", {}).get("en_US", ""),
            ],
        )
    )
    connections = _normalise_number(profile.get("numConnections", 0))

    return build_profile_metrics(
        username=full_name or profile_id,
        platform="linkedin",
        follower_count=connections,
        bio=profile.get("summary", ""),
        profile_url=f"https://www.linkedin.com/in/{profile_id}/",
    )


# ---------------------------------------------------------------------------
# Unified fetch dispatcher
# ---------------------------------------------------------------------------

def fetch_influencer_profile(
    platform: str,
    identifier: str,
) -> Dict[str, Any]:
    """
    Dispatch a profile fetch to the correct platform handler.

    Parameters
    ----------
    platform:   One of 'instagram', 'tiktok', 'youtube', 'linkedin'.
    identifier: Platform-specific username / channel ID / profile ID.

    Returns the normalised profile dict or raises RuntimeError on failure.
    """
    platform = platform.lower().strip()
    dispatchers = {
        "instagram": lambda: fetch_instagram_profile(identifier),
        "tiktok":    lambda: fetch_tiktok_profile(identifier),
        "youtube":   lambda: fetch_youtube_channel(identifier),
        "linkedin":  lambda: fetch_linkedin_profile(identifier),
    }
    if platform not in dispatchers:
        raise ValueError(
            f"Unsupported platform '{platform}'.  "
            f"Choose from: {', '.join(SUPPORTED_PLATFORMS)}"
        )
    return dispatchers[platform]()


# ---------------------------------------------------------------------------
# Batch helpers
# ---------------------------------------------------------------------------

def fetch_multiple_profiles(
    requests: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    """
    Fetch profiles for a list of requests in sequence.

    Each request dict must have 'platform' and 'identifier' keys.

    Returns a list of result dicts, each containing either the profile
    data or an 'error' key with the failure message.
    """
    results = []
    for req in requests:
        platform = req.get("platform", "")
        identifier = req.get("identifier", "")
        try:
            profile = fetch_influencer_profile(platform, identifier)
            results.append({"success": True, **profile})
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to fetch %s/%s: %s", platform, identifier, exc
            )
            results.append({
                "success": False,
                "platform": platform,
                "identifier": identifier,
                "error": str(exc),
            })
    return results


def normalise_cross_platform_metrics(
    profiles: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Ensure all profiles share the same key set so they can be safely
    compared or rendered in a table.

    Missing numeric keys are filled with 0 / 0.0; missing string keys
    are filled with empty strings.
    """
    baseline_int = {
        "follower_count": 0,
        "following_count": 0,
        "post_count": 0,
    }
    baseline_float = {
        "avg_likes": 0.0,
        "avg_comments": 0.0,
        "engagement_rate": 0.0,
    }
    baseline_str = {
        "username": "",
        "platform": "",
        "tier": "",
        "tier_label": "",
        "bio": "",
        "profile_url": "",
        "last_updated": "",
    }
    normalised = []
    for p in profiles:
        merged = {**baseline_int, **baseline_float, **baseline_str, **p}
        normalised.append(merged)
    return normalised
