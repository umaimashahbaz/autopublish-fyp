from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    daily_post_limit = models.PositiveIntegerField(default=5)

    def __str__(self):
        return f"Profile for {self.user.username}"


class PublishedPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    wp_post_id = models.IntegerField()
    wp_link = models.URLField()

    title = models.CharField(max_length=255)
    keyword = models.CharField(max_length=255, blank=True)

    image_id = models.IntegerField(null=True, blank=True)
    word_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class SocialPost(models.Model):
    PLATFORM_CHOICES = [
        ("instagram", "Instagram"),
        ("facebook", "Facebook"),
        ("linkedin", "LinkedIn"),
        ("medium", "Medium"),
        ("pinterest", "Pinterest"),
    ]

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("posted", "Posted"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    published_post = models.ForeignKey(
        PublishedPost,
        on_delete=models.CASCADE,
        related_name="social_posts"
    )

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)

    caption = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)

    # Pinterest-specific (ONLY used if platform == pinterest)
    pinterest_url = models.URLField(blank=True, null=True)

    scheduled_for = models.DateTimeField(blank=True, null=True)
    posted_at = models.DateTimeField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled"
    )

    response_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} → {self.published_post.title}"
