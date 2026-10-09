from .models import Comment


def get_active_post_comments(post):
    return Comment.objects.filter(
        post=post,
        author__is_active=True,
    ).select_related("author")
