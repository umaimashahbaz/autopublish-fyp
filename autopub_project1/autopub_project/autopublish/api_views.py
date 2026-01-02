from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PublishedPost, SocialPost
from .serializers import PublishedPostSerializer
from .social_generator import generate_social_caption


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_list_published_posts(request):
    posts = PublishedPost.objects.filter(user=request.user).order_by("-created_at")
    serializer = PublishedPostSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_generate_social_post(request):
    user = request.user
    post_id = request.data.get("post_id")
    platform = request.data.get("platform")

    try:
        published_post = PublishedPost.objects.get(id=post_id, user=user)
    except PublishedPost.DoesNotExist:
        return Response({"error": "Post not found"}, status=404)

    caption = generate_social_caption(
        platform=platform,
        title=published_post.title,
        keyword=published_post.keyword,
        wp_link=published_post.wp_link,
        article_text=published_post.title,  # replace with full text if stored
    )

    sp = SocialPost.objects.create(
        user=user,
        published_post=published_post,
        platform=platform,
        caption=caption,
        status="scheduled",
    )

    return Response({
        "message": "Social post generated",
        "social_post_id": sp.id,
        "caption": caption
    })
