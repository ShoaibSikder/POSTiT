from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from notifications.models import Notification
from posts.models import Post


User = get_user_model()


class NotificationAPITests(TestCase):
    def setUp(self):
        self.actor = User.objects.create_user(
            username="actor",
            email="actor@example.com",
            password="test-notification-user-password-123",
        )
        self.recipient = User.objects.create_user(
            username="recipient",
            email="recipient@example.com",
            password="test-notification-user-password-123",
        )
        self.post = Post.objects.create(author=self.recipient, content="Hello")
        self.client = APIClient()
        self.client.force_authenticate(self.actor)

    def test_follow_like_and_comment_create_notifications_once(self):
        self.client.post("/api/v1/users/recipient/follow/")
        self.client.post("/api/v1/users/recipient/follow/")
        self.client.post(f"/api/v1/posts/{self.post.pk}/like/")
        self.client.post(f"/api/v1/posts/{self.post.pk}/like/")
        self.client.post(
            f"/api/v1/posts/{self.post.pk}/comments/",
            {"content": "Nice post"},
            format="json",
        )

        self.assertEqual(
            Notification.objects.filter(recipient=self.recipient).count(),
            3,
        )
        self.assertEqual(
            set(
                Notification.objects.filter(recipient=self.recipient).values_list(
                    "type", flat=True
                )
            ),
            {"follow", "like", "comment"},
        )

    def test_notification_lists_and_mark_read_are_recipient_scoped(self):
        notification = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            type=Notification.Type.LIKE,
            post=self.post,
        )
        response = self.client.get("/api/v1/notifications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["unread"], 0)

        self.client.force_authenticate(self.recipient)
        response = self.client.get("/api/v1/notifications/")
        self.assertEqual(response.data["unread"], 1)
        marked = self.client.post(f"/api/v1/notifications/{notification.pk}/read/")
        self.assertEqual(marked.status_code, 200)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

        self.client.force_authenticate(self.actor)
        forbidden = self.client.post(f"/api/v1/notifications/{notification.pk}/read/")
        self.assertEqual(forbidden.status_code, 404)

    def test_own_social_activity_does_not_notify_the_actor(self):
        self.client.force_authenticate(self.recipient)
        own_post = Post.objects.create(author=self.recipient, content="Mine")
        self.client.post(f"/api/v1/posts/{own_post.pk}/like/")
        self.client.post(
            f"/api/v1/posts/{own_post.pk}/comments/",
            {"content": "My own comment"},
            format="json",
        )
        self.assertFalse(Notification.objects.filter(recipient=self.recipient).exists())
