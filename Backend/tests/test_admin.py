from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from audit.models import AdminAuditLog
from moderation.models import SystemSetting


User = get_user_model()


class DjangoAdminControlTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            username="siteadmin",
            email="siteadmin@example.com",
            password="Strong-test-password-123!",
        )
        cls.member = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="Strong-test-password-123!",
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_admin_site_is_available_and_branded(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "POSTiT Administration")
        self.assertContains(response, "Platform management")

    def test_admin_can_ban_an_account_with_a_reason_and_audit_it(self):
        response = self.client.post(
            reverse("admin:accounts_user_changelist"),
            {
                "action": "ban_selected_users",
                "_selected_action": [str(self.member.pk)],
                "reason": "Repeated abuse",
            },
            follow=True,
        )

        self.member.refresh_from_db()
        self.assertTrue(self.member.is_banned)
        self.assertFalse(self.member.is_active)
        self.assertTrue(
            AdminAuditLog.objects.filter(
                admin=self.admin_user,
                action="ban_user",
                target_id=self.member.pk,
                details__reason="Repeated abuse",
            ).exists()
        )
        self.assertContains(response, "Ban completed for 1 account")

    def test_admin_moderation_action_requires_a_reason(self):
        response = self.client.post(
            reverse("admin:accounts_user_changelist"),
            {
                "action": "ban_selected_users",
                "_selected_action": [str(self.member.pk)],
                "reason": "",
            },
            follow=True,
        )

        self.member.refresh_from_db()
        self.assertFalse(self.member.is_banned)
        self.assertFalse(AdminAuditLog.objects.exists())
        self.assertContains(response, "Enter a reason")

    def test_admin_moderation_action_preserves_the_last_active_admin(self):
        response = self.client.post(
            reverse("admin:accounts_user_changelist"),
            {
                "action": "deactivate_selected_users",
                "_selected_action": [str(self.admin_user.pk)],
                "reason": "Routine account review",
            },
            follow=True,
        )

        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)
        self.assertContains(response, "last active administrator")
        self.assertFalse(AdminAuditLog.objects.exists())

    def test_admin_can_create_a_bounded_platform_setting_and_audit_it(self):
        response = self.client.post(
            reverse("admin:moderation_systemsetting_add"),
            {
                "key": SystemSetting.Key.MAX_POST_IMAGES,
                "value": "8",
                "_save": "Save",
            },
            follow=True,
        )

        setting = SystemSetting.objects.get(key=SystemSetting.Key.MAX_POST_IMAGES)
        self.assertEqual(setting.value, 8)
        self.assertEqual(setting.updated_by, self.admin_user)
        self.assertTrue(
            AdminAuditLog.objects.filter(
                admin=self.admin_user,
                action="update_system_setting",
                target_id=setting.pk,
                details__created=True,
            ).exists()
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_can_update_a_platform_setting_and_audit_it(self):
        setting = SystemSetting.objects.create(
            key=SystemSetting.Key.MAX_POST_IMAGES,
            value=4,
            updated_by=self.admin_user,
        )

        response = self.client.post(
            reverse("admin:moderation_systemsetting_change", args=(setting.pk,)),
            {
                "key": SystemSetting.Key.MAX_POST_IMAGES,
                "value": "7",
                "_save": "Save",
            },
            follow=True,
        )

        setting.refresh_from_db()
        self.assertEqual(setting.value, 7)
        self.assertEqual(setting.updated_by, self.admin_user)
        self.assertTrue(
            AdminAuditLog.objects.filter(
                admin=self.admin_user,
                action="update_system_setting",
                target_id=setting.pk,
                details__created=False,
                details__value=7,
            ).exists()
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_cannot_exceed_a_platform_setting_limit(self):
        response = self.client.post(
            reverse("admin:moderation_systemsetting_add"),
            {
                "key": SystemSetting.Key.MAX_POST_IMAGES,
                "value": "11",
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SystemSetting.objects.exists())
        self.assertFalse(AdminAuditLog.objects.exists())
        self.assertContains(response, "maximum supported value")
