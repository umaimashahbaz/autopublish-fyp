from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.utils import timezone

from bs4 import BeautifulSoup
from markdown2 import markdown
from dotenv import load_dotenv
from newspaper import Article

import os
import json
import re
import requests

from .models import PublishedPost, UserProfile
from .generator import generate_article
from .utils import fetch_pexels_image_bytes, upload_image_to_wordpress

# ---------------- ENV ---------------- #
load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
WP_SITE_URL = os.getenv("WP_SITE_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")


# ---------------- COMPETITOR FETCH ---------------- #
def fetch_competitors(keyword: str):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": keyword,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "num": 5,
    }

    try:
        res = requests.get(url, params=params, timeout=20)
        if res.status_code != 200:
            return []

        data = res.json()
        competitors = []

        for result in data.get("organic_results", []):
            competitors.append({
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet"),
            })

        return competitors

    except Exception:
        return []


def scrape_competitor_content(competitors, max_articles=10, max_chars=3000):
    texts = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for comp in competitors[:max_articles]:
        url = comp.get("link")
        if not url:
            continue

        text = ""
        try:
            article = Article(url)
            article.download()
            article.parse()
            text = article.text
        except:
            pass

        if not text:
            try:
                r = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                text = "\n".join(p.get_text() for p in soup.find_all("p"))
            except:
                continue

        if text:
            texts.append(text[:max_chars])

    return "\n\n".join(texts)


# ---------------- CLEAN GPT OUTPUT ---------------- #
def clean_output(raw):
    bad_keys = ["meta_title", "meta_description", "title", "body_markdown"]
    cleaned = "\n".join(
        l for l in raw.splitlines() if not any(k in l for k in bad_keys)
    )
    return re.sub(r"^[\{\}\[\]]+$", "", cleaned).strip()


# ---------------- AUTH ---------------- #
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            auth_login(request, user)
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})


# ---------------- DASHBOARD ---------------- #
@login_required
def dashboard(request):
    posts = PublishedPost.objects.filter(user=request.user).order_by("-created_at")
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    today = timezone.now().date()
    used_today = posts.filter(created_at__date=today).count()

    return render(
        request,
        "dashboard.html",
        {
            "posts": posts,
            "profile": profile,
            "remaining": max(profile.daily_post_limit - used_today, 0),
        },
    )


# ---------------- KEYWORD ---------------- #
@login_required
def ask_keyword(request):
    if request.method == "POST":
        request.session["keyword"] = request.POST.get("keyword")
        return render(request, "loading.html")
    return render(request, "ask_keyword.html")


# ---------------- GENERATE BLOG ---------------- #
@login_required
def generate_content_view(request):
    keyword = request.session.get("keyword")
    if not keyword:
        return redirect("ask_keyword")

    competitors = fetch_competitors(keyword)
    competitors_for_ui = competitors.copy()
    competitor_content = scrape_competitor_content(competitors)

    raw_output = generate_article(
        keyword,
        competitors,
        competitor_content,
        900,
    )

    try:
        data = json.loads(raw_output)
    except:
        cleaned = clean_output(raw_output)
        data = {
            "meta_title": keyword,
            "meta_description": f"Guide to {keyword}",
            "title": f"Complete Guide to {keyword}",
            "body_markdown": cleaned,
        }

    content_html = markdown(f"# {data['title']}\n\n{data['body_markdown']}")

    request.session["content_data"] = data
    request.session["content_html"] = content_html
    request.session["slug"] = keyword.lower().replace(" ", "-")

    return render(
        request,
        "preview_content.html",
        {
            "keyword": keyword,
            "competitors": competitors_for_ui,
            "meta_title": data["meta_title"],
            "meta_description": data["meta_description"],
            "title": data["title"],
            "content": content_html,
        },
    )


# ---------------- PUBLISH WORDPRESS ---------------- #
@login_required
def publish_content(request):
    data = request.session.get("content_data")
    html = request.session.get("content_html")
    slug = request.session.get("slug")

    if not data:
        return HttpResponse("No content", status=400)

    auth = (WP_USERNAME, WP_APP_PASSWORD)
    posts_url = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

    res = requests.post(
        posts_url,
        auth=auth,
        json={
            "title": data["title"],
            "content": html,
            "status": "publish",
            "slug": slug,
        },
    )

    if res.status_code not in (200, 201):
        return HttpResponse(res.text)

    post = res.json()
    post_id = post["id"]
    post_link = post["link"]

    featured_id = None
    img = fetch_pexels_image_bytes(data["title"])
    if img:
        featured_id = upload_image_to_wordpress(
            img,
            f"{slug}.jpg",
            WP_SITE_URL,
            WP_USERNAME,
            WP_APP_PASSWORD,
            post_id,
        )

    if featured_id:
        requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}",
            auth=auth,
            json={"featured_media": featured_id},
        )

    PublishedPost.objects.create(
        user=request.user,
        wp_post_id=post_id,
        wp_link=post_link,
        title=data["title"],
        keyword=request.session.get("keyword", ""),
        image_id=featured_id,
        word_count=len(data["body_markdown"].split()),
    )

    return render(
        request,
        "publish_result.html",
        {
            "success": True,
            "response": post_link,
        },
    )
