from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from posts.models import Post


User = get_user_model()


class SocialInteractionsIntegrationTests(TestCase):
    def test_follow_like_comment_and_feed_work_together(self):
        alice = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="unique-test-password-123",
        )
        bob = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="unique-test-password-123",
        )
        bob_post = Post.objects.create(author=bob, content="A post for the feed")
        client = APIClient()
        client.force_authenticate(alice)

        follow = client.post("/api/v1/users/bob/follow/")
        like = client.post(f"/api/v1/posts/{bob_post.pk}/like/")
        comment = client.post(
            f"/api/v1/posts/{bob_post.pk}/comments/",
            {"content": "Looks good"},
            format="json",
        )
        feed = client.get("/api/v1/feed/")

        self.assertEqual(follow.status_code, 200)
        self.assertEqual(like.data["likes_count"], 1)
        self.assertEqual(comment.status_code, 201)
        self.assertEqual(feed.status_code, 200)
        self.assertEqual(feed.data["results"][0]["author"], "bob")
        self.assertEqual(feed.data["results"][0]["likes_count"], 1)
        self.assertEqual(feed.data["results"][0]["comments_count"], 1)
