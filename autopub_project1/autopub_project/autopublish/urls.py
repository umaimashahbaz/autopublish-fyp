from django.urls import path
from . import views

urlpatterns = [
    path("accounts/register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("ask/", views.ask_keyword, name="ask_keyword"),
    path("generate/", views.generate_content_view, name="generate_content"),
    path("publish/", views.publish_content, name="publish_content"),
]
