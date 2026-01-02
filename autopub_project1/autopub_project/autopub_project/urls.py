from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect


def home_redirect(request):
    """Redirect / to dashboard if logged in, otherwise to login."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


urlpatterns = [
    path("admin/", admin.site.urls),

    # Root redirect
    path("", home_redirect, name="home"),

    # Auth
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),

    # App views (HTML)
    path("", include("autopublish.urls")),

    # API endpoints (JSON)
    path("api/", include("autopublish.api_urls")),
]
