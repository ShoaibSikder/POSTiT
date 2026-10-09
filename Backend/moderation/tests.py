from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from audit.models import AdminAuditLog
from posts.models import Post


User = get_user_model()


class ModerationAPITests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="test-moderation-admin-password-123",
            is_staff=True,
            role=User.Role.ADMIN,
        )
        self.member = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="test-moderation-user-password-123",
        )
        self.post = Post.objects.create(author=self.member, content="Moderate me")
        self.client = APIClient()

    def test_regular_users_cannot_access_admin_apis(self):
        self.client.force_authenticate(self.member)
        response = self.client.get("/api/v1/admin/dashboard/")

        self.assertEqual(response.status_code, 403)

    def test_admin_role_without_staff_permission_cannot_access_admin_apis(self):
        non_staff_admin = User.objects.create_user(
            username="nonstaffadmin",
            email="nonstaffadmin@example.com",
            password="unique-test-password-123",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(non_staff_admin)
        response = self.client.get("/api/v1/admin/dashboard/")

        self.assertEqual(response.status_code, 403)

    def test_dashboard_and_moderation_actions_are_audited(self):
        self.client.force_authenticate(self.admin)
        dashboard = self.client.get("/api/v1/admin/dashboard/")

        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.data["counts"]["users"], 2)

        removed = self.client.delete(
            f"/api/v1/admin/posts/{self.post.pk}/",
            {"reason": "Violates platform content rules"},
            format="json",
        )
        self.assertEqual(removed.status_code, 204)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())
        self.assertTrue(
            AdminAuditLog.objects.filter(
                admin=self.admin,
                action="remove_post",
                target_id=self.post.pk,
            ).exists()
        )

    def test_last_active_admin_cannot_be_deactivated(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            f"/api/v1/admin/users/{self.admin.pk}/deactivate/",
            {"reason": "Testing last administrator protection"},
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertFalse(AdminAuditLog.objects.exists())

    def test_ban_requires_reason_and_unban_restores_access(self):
        self.client.force_authenticate(self.admin)
        url = f"/api/v1/admin/users/{self.member.pk}"
        rejected = self.client.post(f"{url}/ban/", {}, format="json")
        self.assertEqual(rejected.status_code, 400)

        banned = self.client.post(
            f"{url}/ban/",
            {"reason": "Repeated abuse"},
            format="json",
        )
        self.assertEqual(banned.status_code, 200)
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_banned)
        self.assertFalse(self.member.is_active)

        blocked_activation = self.client.post(
            f"{url}/activate/",
            {"reason": "Checking ban enforcement"},
            format="json",
        )
        self.assertEqual(blocked_activation.status_code, 409)

        unbanned = self.client.post(
            f"{url}/unban/",
            {"reason": "Appeal accepted"},
            format="json",
        )
        self.assertEqual(unbanned.status_code, 200)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_banned)
        self.assertTrue(self.member.is_active)

    def test_setting_change_updates_configured_limits_and_is_audited(self):
        self.client.force_authenticate(self.admin)
        response = self.client.put(
            "/api/v1/admin/settings/",
            {
                "key": "POSTIT_MAX_POST_IMAGES",
                "value": 8,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["value"], 8)
        self.assertTrue(
            AdminAuditLog.objects.filter(action="update_system_setting").exists()
        )

    def test_admin_can_review_paginated_media_lists(self):
        self.client.force_authenticate(self.admin)
        for media_type in ("post", "profile"):
            response = self.client.get(f"/api/v1/admin/media/{media_type}/")
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["results"], [])

        invalid = self.client.get("/api/v1/admin/media/unknown/")
        self.assertEqual(invalid.status_code, 400)

    def test_moderation_delete_requires_an_explanation(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(f"/api/v1/admin/posts/{self.post.pk}/")

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
        self.assertFalse(AdminAuditLog.objects.exists())
