from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from posts.models import Post

from .models import Comment


User = get_user_model()


class CommentAPITests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="post-author",
            email="author@example.com",
            password="unique-test-password-123",
        )
        self.commenter = User.objects.create_user(
            username="commenter",
            email="commenter@example.com",
            password="unique-test-password-123",
        )
        self.other_user = User.objects.create_user(
            username="other-user",
            email="other@example.com",
            password="unique-test-password-123",
        )
        self.post = Post.objects.create(author=self.author, content="A post")
        self.client = APIClient()
        self.client.force_authenticate(self.commenter)
        self.comments_url = f"/api/v1/posts/{self.post.pk}/comments/"

    def test_comment_create_list_update_delete_and_post_count(self):
        created = self.client.post(
            self.comments_url,
            {"content": "  Nice post!  "},
            format="json",
        )

        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["content"], "Nice post!")
        self.assertEqual(created.data["author"], "commenter")
        comment_id = created.data["id"]

        listed = self.client.get(self.comments_url)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data["count"], 1)
        self.assertEqual(
            self.client.get(f"/api/v1/posts/{self.post.pk}/").data["comments_count"],
            1,
        )

        updated = self.client.patch(
            f"/api/v1/comments/{comment_id}/",
            {"content": "Updated comment"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["content"], "Updated comment")

        deleted = self.client.delete(f"/api/v1/comments/{comment_id}/")
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(Comment.objects.filter(pk=comment_id).exists())

    def test_blank_comment_and_non_owner_mutations_are_rejected(self):
        blank = self.client.post(
            self.comments_url,
            {"content": "  "},
            format="json",
        )
        self.assertEqual(blank.status_code, 400)

        comment = Comment.objects.create(
            post=self.post,
            author=self.commenter,
            content="Original text",
        )
        self.client.force_authenticate(self.other_user)
        update = self.client.patch(
            f"/api/v1/comments/{comment.pk}/",
            {"content": "Changed"},
            format="json",
        )
        deletion = self.client.delete(f"/api/v1/comments/{comment.pk}/")

        self.assertEqual(update.status_code, 403)
        self.assertEqual(deletion.status_code, 403)
        comment.refresh_from_db()
        self.assertEqual(comment.content, "Original text")
