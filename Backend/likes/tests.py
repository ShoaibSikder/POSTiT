from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from posts.models import Post

from .models import Like


User = get_user_model()


class LikeAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="liker",
            email="liker@example.com",
            password="unique-test-password-123",
        )
        self.author = User.objects.create_user(
            username="author",
            email="author@example.com",
            password="unique-test-password-123",
        )
        self.post = Post.objects.create(author=self.author, content="A post")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.like_url = f"/api/v1/posts/{self.post.pk}/like/"

    def test_like_and_unlike_are_idempotent_and_visible_on_post(self):
        first = self.client.post(self.like_url)
        second = self.client.post(self.like_url)

        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.data["liked"])
        self.assertEqual(second.data["likes_count"], 1)
        self.assertEqual(Like.objects.filter(post=self.post).count(), 1)

        post = self.client.get(f"/api/v1/posts/{self.post.pk}/")
        self.assertEqual(post.data["likes_count"], 1)
        self.assertTrue(post.data["liked_by_user"])

        self.assertEqual(self.client.delete(self.like_url).data["likes_count"], 0)
        self.assertFalse(self.client.delete(self.like_url).data["liked"])
        self.assertFalse(Like.objects.filter(post=self.post).exists())

    def test_likes_require_authentication(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(self.like_url).status_code, 403)
