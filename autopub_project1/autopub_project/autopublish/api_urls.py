# autopublish/api_urls.py

from django.urls import path
from . import api_views

urlpatterns = [
    path("posts/", api_views.api_list_published_posts, name="api_list_published_posts"),
]
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

path("social/generate/", api_views.api_generate_social_post, name="api_generate_social_post"),
