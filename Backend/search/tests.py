from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

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
