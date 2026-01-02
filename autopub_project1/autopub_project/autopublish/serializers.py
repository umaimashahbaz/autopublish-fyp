from rest_framework import serializers
from .models import PublishedPost

class PublishedPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishedPost
        fields = [
            "id",
            "user",
            "wp_post_id",
            "wp_link",
            "title",
            "keyword",
            "image_id",
            "word_count",
            "created_at",
        ]
