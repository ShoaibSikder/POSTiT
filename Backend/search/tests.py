from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from follows.models import Follow
from posts.models import Post
from .models import SearchActivity


User = get_user_model()


class SearchAPITests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="test-search-user-password-123",
            first_name="Alice",
        )
        self.bob = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="test-search-user-password-123",
            first_name="Bob",
        )
        self.post = Post.objects.create(author=self.bob, content="A searchable note")
        self.client = APIClient()

    def test_user_search_matches_username_and_name_and_paginates(self):
        response = self.client.get("/api/v1/search/users/?q=ali")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([entry["username"] for entry in response.data["results"]], ["alice"])
        self.assertEqual(
            SearchActivity.objects.filter(search_type=SearchActivity.SearchType.USERS).count(),
            1,
        )

    def test_empty_user_search_lists_everyone_except_the_signed_in_user(self):
        self.client.force_authenticate(self.alice)

        response = self.client.get("/api/v1/search/users/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [entry["username"] for entry in response.data["results"]],
            ["bob"],
        )

    def test_empty_user_search_requires_authentication(self):
        response = self.client.get("/api/v1/search/users/")

        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(SearchActivity.objects.count(), 0)

    def test_suggestions_exclude_the_current_user_and_existing_follows(self):
        charlie = User.objects.create_user(
            username="charlie",
            email="charlie@example.com",
            ******,
        )
        Follow.objects.create(follower=self.alice, following=self.bob)
        self.client.force_authenticate(self.alice)

        response = self.client.get("/api/v1/search/suggestions/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [entry["username"] for entry in response.data["results"]],
            ["charlie"],
        )

    def test_suggestions_require_authentication(self):
        response = self.client.get("/api/v1/search/suggestions/")

        self.assertIn(response.status_code, (401, 403))

    def test_post_search_supports_term_author_and_inclusive_dates(self):
        response = self.client.get(
            f"/api/v1/search/posts/?q=searchable&author=bob&from={date.today().isoformat()}&to={date.today().isoformat()}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.post.pk)

    def test_post_search_rejects_inverted_date_range(self):
        response = self.client.get("/api/v1/search/posts/?from=2026-05-02&to=2026-05-01")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(SearchActivity.objects.count(), 0)
