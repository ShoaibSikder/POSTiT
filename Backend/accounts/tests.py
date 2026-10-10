from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


User = get_user_model()


class UserManagerTests(TestCase):
    def test_create_user_normalizes_username_and_email(self):
        user = User.objects.create_user(
            username="  Alice  ",
            email="ALICE@EXAMPLE.COM",
            password="unique-test-password-123",
        )

        self.assertEqual(user.username, "alice")
        self.assertEqual(user.email, "alice@example.com")
        self.assertTrue(user.check_password("unique-test-password-123"))
        self.assertEqual(user.role, User.Role.USER)
        self.assertFalse(user.is_staff)

    def test_create_superuser_assigns_admin_role(self):
        user = User.objects.create_superuser(
            username="siteadmin",
            email="admin@example.com",
            password="unique-admin-password-123",
        )

        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class AuthenticationAPITests(TestCase):
    csrf_url = "/api/v1/auth/csrf/"
    registration_url = "/api/v1/auth/register/"
    login_url = "/api/v1/auth/login/"
    logout_url = "/api/v1/auth/logout/"
    current_user_url = "/api/v1/auth/me/"

    def registration_data(self, **overrides):
        data = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "unique-test-password-123",
            "password_confirmation": "unique-test-password-123",
        }
        data.update(overrides)
        return data

    def test_registration_creates_user_and_starts_session(self):
        response = self.client.post(
            self.registration_url,
            self.registration_data(role="admin"),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["role"], User.Role.USER)
        self.assertNotIn("password", response.data)
        self.assertNotIn("is_superuser", response.data)
        self.assertEqual(User.objects.get().username, "alice")

        current_user = self.client.get(self.current_user_url)
        self.assertEqual(current_user.status_code, 200)
        self.assertEqual(current_user.data["username"], "alice")

    def test_registration_requires_matching_passwords(self):
        response = self.client.post(
            self.registration_url,
            self.registration_data(password_confirmation="different-password"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        User.objects.create_user(
            username="existing",
            email="alice@example.com",
            password="unique-test-password-123",
        )

        response = self.client.post(
            self.registration_url,
            self.registration_data(email="ALICE@example.com"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_login_accepts_email_and_logout_ends_session(self):
        User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="unique-test-password-123",
        )

        login_response = self.client.post(
            self.login_url,
            {
                "identifier": "ALICE@example.com",
                "password": "unique-test-password-123",
            },
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.data["username"], "alice")

        logout_response = self.client.post(self.logout_url)
        self.assertEqual(logout_response.status_code, 204)
        self.assertEqual(self.client.get(self.current_user_url).status_code, 403)

    def test_login_remember_option_controls_session_lifetime(self):
        User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="unique-test-password-123",
        )

        response = self.client.post(
            self.login_url,
            {
                "identifier": "alice",
                "password": "unique-test-password-123",
                "remember": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_error_does_not_disclose_account_existence(self):
        response = self.client.post(
            self.login_url,
            {"identifier": "missing@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"][0],
            "Invalid username/email or password.",
        )

    def test_current_user_requires_authentication(self):
        self.assertEqual(self.client.get(self.current_user_url).status_code, 403)

    def test_development_frontend_origin_is_allowed_by_cors(self):
        response = self.client.get(
            self.csrf_url,
            HTTP_ORIGIN="http://127.0.0.1:3002",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "http://127.0.0.1:3002",
        )
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")

    def test_registration_requires_csrf_for_anonymous_requests(self):
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(self.registration_url, self.registration_data())
        self.assertEqual(response.status_code, 403)

        csrf_response = client.get(self.csrf_url)
        token = csrf_response.data["csrfToken"]
        response = client.post(
            self.registration_url,
            self.registration_data(),
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)

    def test_login_and_logout_require_csrf(self):
        User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="unique-test-password-123",
        )
        client = APIClient(enforce_csrf_checks=True)
        credentials = {
            "identifier": "alice",
            "password": "unique-test-password-123",
        }

        self.assertEqual(client.post(self.login_url, credentials).status_code, 403)

        csrf_token = client.get(self.csrf_url).data["csrfToken"]
        self.assertEqual(
            client.post(
                self.login_url,
                credentials,
                HTTP_X_CSRFTOKEN=csrf_token,
            ).status_code,
            200,
        )
        self.assertEqual(client.post(self.logout_url).status_code, 403)

        csrf_token = client.get(self.csrf_url).data["csrfToken"]
        self.assertEqual(
            client.post(
                self.logout_url,
                HTTP_X_CSRFTOKEN=csrf_token,
            ).status_code,
            204,
        )
