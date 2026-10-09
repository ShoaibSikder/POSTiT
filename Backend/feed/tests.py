from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from follows.models import Follow
from likes.models import Like
from posts.models import Post


User = get_user_model()


class FeedAPITests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="unique-test-password-123",
        )
        self.bob = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="unique-test-password-123",
        )
        self.carol = User.objects.create_user(
            username="carol",
            email="carol@example.com",
            password="unique-test-password-123",
        )
        self.alice_post = Post.objects.create(author=self.alice, content="Alice post")
        self.bob_post = Post.objects.create(author=self.bob, content="Bob post")
        self.carol_post = Post.objects.create(author=self.carol, content="Carol post")
        self.client = APIClient()
        self.client.force_authenticate(self.alice)

    def test_feed_is_private_to_authenticated_users_and_includes_followed_users(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/v1/feed/").status_code, 403)

        self.client.force_authenticate(self.alice)
        Follow.objects.create(follower=self.alice, following=self.bob)
        Like.objects.create(post=self.bob_post, user=self.alice)

        response = self.client.get("/api/v1/feed/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {entry["author"] for entry in response.data["results"]},
            {"alice", "bob"},
        )
        bob_entry = next(
            entry for entry in response.data["results"] if entry["author"] == "bob"
        )
        self.assertTrue(bob_entry["liked_by_user"])
        self.assertEqual(bob_entry["likes_count"], 1)

    def test_feed_is_chronological_and_excludes_deactivated_users(self):
        Follow.objects.create(follower=self.alice, following=self.bob)
        Follow.objects.create(follower=self.alice, following=self.carol)
        self.carol.is_active = False
        self.carol.save(update_fields=("is_active",))

        response = self.client.get("/api/v1/feed/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [entry["author"] for entry in response.data["results"]],
            ["bob", "alice"],
        )
