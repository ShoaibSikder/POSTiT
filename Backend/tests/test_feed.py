from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from follows.models import Follow
from posts.models import Post


User = get_user_model()


class FeedIntegrationTests(TestCase):
    def test_feed_is_page_number_paginated(self):
        viewer = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="unique-test-password-123",
        )
        followed = User.objects.create_user(
            username="followed",
            email="followed@example.com",
            password="unique-test-password-123",
        )
        Follow.objects.create(follower=viewer, following=followed)
        for index in range(21):
            Post.objects.create(author=followed, content=f"Post {index}")

        client = APIClient()
        client.force_authenticate(viewer)
        first_page = client.get("/api/v1/feed/")
        second_page = client.get("/api/v1/feed/?page=2")

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data["count"], 21)
        self.assertEqual(len(first_page.data["results"]), 20)
        self.assertEqual(len(second_page.data["results"]), 1)
        self.assertEqual(first_page.data["results"][0]["content"], "Post 20")
        self.assertFalse(first_page.data["results"][0]["is_own_post"])
