from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Follow


User = get_user_model()


class FollowAPITests(TestCase):
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
        self.client = APIClient()
        self.client.force_authenticate(self.alice)

    def test_follow_is_idempotent_and_self_follow_is_rejected(self):
        first = self.client.post("/api/v1/users/bob/follow/")
        second = self.client.post("/api/v1/users/bob/follow/")

        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(second.data["follower_count"], 1)
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(
            self.client.post("/api/v1/users/alice/follow/").status_code,
            400,
        )

    def test_unfollow_and_public_relationship_lists(self):
        Follow.objects.create(follower=self.alice, following=self.bob)
        Follow.objects.create(follower=self.carol, following=self.bob)

        followers = self.client.get("/api/v1/users/bob/followers/")
        self.assertEqual(followers.status_code, 200)
        self.assertEqual(
            {entry["username"] for entry in followers.data["results"]},
            {"alice", "carol"},
        )
        following = self.client.get("/api/v1/users/alice/following/")
        self.assertEqual(following.data["results"][0]["username"], "bob")

        self.assertEqual(
            self.client.delete("/api/v1/users/bob/follow/").status_code,
            200,
        )
        self.assertEqual(
            self.client.delete("/api/v1/users/bob/follow/").data[
                "follower_count"
            ],
            1,
        )
        self.assertFalse(Follow.objects.filter(follower=self.alice).exists())

    def test_profile_counts_only_active_follow_relationships(self):
        Follow.objects.create(follower=self.alice, following=self.bob)
        Follow.objects.create(follower=self.carol, following=self.bob)
        Follow.objects.create(follower=self.bob, following=self.carol)

        profile = self.client.get("/api/v1/users/bob/")
        self.assertEqual(profile.data["follower_count"], 2)
        self.assertEqual(profile.data["following_count"], 1)

        self.carol.is_active = False
        self.carol.save(update_fields=("is_active",))
        bob_profile = self.client.get("/api/v1/users/bob/")
        self.assertEqual(bob_profile.data["follower_count"], 1)
        self.assertEqual(
            self.client.get("/api/v1/users/carol/followers/").status_code,
            404,
        )
