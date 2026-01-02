# autopublish/utils.py

import os
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# ---------- API Keys ---------- #

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
api_key = os.getenv("PEXELS_API_KEY")


# ---------- SERP via SerpApi ---------- #

def fetch_serp_links_serpapi(query: str, serpapi_key: str, num: int = 5) -> List[Dict]:
    """Return list of dicts: {title, link, snippet} using SerpApi."""
    params = {
        "engine": "google",
        "q": query,
        "api_key": serpapi_key,
        "num": num,
    }
    r = requests.get("https://serpapi.com/search", params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    results = []
    for item in data.get("organic_results", [])[:num]:
        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet"),
        })
    return results


# ---------- Fallback: Bing HTML scraping ---------- #

def fetch_serp_links_bing(query: str, num: int = 5, pause: float = 1.0) -> List[Dict]:
    """Return list of dicts: {title, link, snippet} using Bing HTML."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AutoContentBot/1.0; +https://example.com/bot)"
    }
    params = {"q": query}
    url = "https://www.bing.com/search"

    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    results = []

    for el in soup.select("li.b_algo")[:num]:
        a = el.find("a")
        title = a.get_text(strip=True) if a else None
        link = a["href"] if a and a.has_attr("href") else None

        snippet = None
        p = el.find("p")
        if p:
            snippet = p.get_text(strip=True)

        results.append({"title": title, "link": link, "snippet": snippet})

    time.sleep(pause)
    return results


# ---------- Pexels Image Fetch ---------- #

def fetch_pexels_image_bytes(keyword: str) -> Optional[bytes]:
    """
    Search Pexels for a photo matching the keyword.
    Returns the image bytes (JPEG) for the first result, or None on failure.
    """
    api_key = os.getenv("PEXELS_API_KEY")
    print("🔍 [PEXELS] Fetching image for:", keyword)
    print("🔑 [PEXELS] PEXELS_API_KEY present?:", bool(api_key))

    if not api_key:
        print("❌ [PEXELS] No PEXELS_API_KEY found inside utils.py")
        return None

    headers = {
        "Authorization": api_key
    }
    params = {
        "query": keyword,
        "per_page": 1,
        "orientation": "landscape",
    }

    try:
        # Search Pexels
        search_resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params=params,
            timeout=15,
        )
        print("📡 [PEXELS] Search status:", search_resp.status_code)

        if search_resp.status_code != 200:
            print("❌ [PEXELS] Search failed:", search_resp.status_code, search_resp.text[:200])
            return None

        data = search_resp.json()
        photos = data.get("photos", [])
        print("🖼 [PEXELS] Photos found:", len(photos))

        if not photos:
            print("❌ [PEXELS] No photos found for:", keyword)
            return None

        photo = photos[0]
        src = photo.get("src", {})
        img_url = src.get("large2x") or src.get("large") or src.get("medium")
        print("🔗 [PEXELS] Chosen img_url:", img_url)

        if not img_url:
            print("❌ [PEXELS] No suitable image URL")
            return None

        # Download image
        img_resp = requests.get(img_url, timeout=15)
        print("⬇️ [PEXELS] Download status:", img_resp.status_code)

        if img_resp.status_code != 200:
            print("❌ [PEXELS] Failed to download image:", img_resp.status_code)
            return None

        print("📏 [PEXELS] Downloaded image size:", len(img_resp.content))
        return img_resp.content

    except Exception as e:
        print("🔥 [PEXELS] Error while fetching image:", e)
        return None


# ---------- WordPress media upload ---------- #

def upload_image_to_wordpress(
    img_bytes: bytes,
    filename: str,
    wp_site_url: str,
    wp_user: str,
    wp_app_pass: str,
    post_id: Optional[int] = None,
) -> Optional[int]:
    """
    Uploads image bytes to WordPress Media Library.
    If post_id is provided, attaches image to that post.
    Returns the media ID on success, or None on failure.
    """
    if not img_bytes:
        print("⚠️ [WP] No img_bytes passed")
        return None

    media_url = wp_site_url.rstrip("/") + "/wp-json/wp/v2/media"
    if post_id:
        media_url += f"?post={post_id}"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/jpeg",
    }

    print("🌐 [WP] Uploading image to:", media_url)

    try:
        r = requests.post(
            media_url,
            headers=headers,
            data=img_bytes,
            auth=(wp_user, wp_app_pass),
            timeout=30,
        )
        print("📡 [WP] Status:", r.status_code)

        if r.status_code not in (200, 201):
            print("❌ [WP] Media upload failed:", r.status_code, r.text[:300])
            return None

        media_data = r.json()
        media_id = media_data.get("id")
        print("✅ [WP] Uploaded media ID:", media_id)
        return media_id

    except Exception as e:
        print("🔥 [WP] Error uploading image:", e)
        return None


# ---------- WordPress post publish helper ---------- #

def publish_to_wordpress(
    title: str,
    content: str,
    status: str,
    wp_site_url: str,
    wp_user: str,
    wp_app_pass: str,
) -> Dict:

    wp_api = wp_site_url.rstrip("/") + "/wp-json/wp/v2/posts"
    auth = (wp_user, wp_app_pass)

    payload = {
        "title": title,
        "content": content,
        "status": status,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "identity",
    }

    r = requests.post(wp_api, auth=auth, json=payload, headers=headers, timeout=30)

    if r.status_code not in (200, 201):
        r.raise_for_status()

    return r.json()
