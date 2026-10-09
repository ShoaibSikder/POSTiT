from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from .models import Profile, ProfileMedia


User = get_user_model()


def image_upload(name="profile.jpg", image_format="JPEG", content_type="image/jpeg"):
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color="blue").save(buffer, format=image_format)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


@override_settings(POSTIT_MAX_PROFILE_MEDIA=1)
class ProfileAPITests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="unique-test-password-123",
        )
        self.other_user = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="unique-test-password-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_user_creation_creates_profile_and_profile_can_be_edited(self):
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
        response = self.client.patch(
            "/api/v1/users/alice/",
            {"bio": "Hello Postit", "first_name": "Alice"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["bio"], "Hello Postit")
        self.assertEqual(response.data["first_name"], "Alice")
        self.assertEqual(response.data["follower_count"], 0)

    def test_profile_is_publicly_readable(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/users/alice/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "alice")
        self.assertNotIn("email", response.data)

    def test_user_cannot_edit_another_users_profile(self):
        response = self.client.patch(
            "/api/v1/users/bob/",
            {"bio": "Changed"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.other_user.profile.refresh_from_db()
        self.assertEqual(self.other_user.profile.bio, "")

    def test_profile_uploads_are_validated_and_owner_scoped(self):
        response = self.client.patch(
            "/api/v1/profiles/me/",
            {"avatar": image_upload()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["avatar"].endswith(".jpg"))
        self.assertTrue(self.user.profile.avatar.storage.exists(self.user.profile.avatar.name))

        response = self.client.post(
            "/api/v1/users/alice/media/",
            {"image": image_upload("gallery.png", "PNG", "image/png")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ProfileMedia.objects.filter(profile=self.user.profile).count(), 1)

        response = self.client.post(
            "/api/v1/users/alice/media/",
            {"image": image_upload("second.png", "PNG", "image/png")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

        self.client.force_authenticate(self.other_user)
        response = self.client.post(
            "/api/v1/users/alice/media/",
            {"image": image_upload("unauthorized.png", "PNG", "image/png")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 403)

    def test_upload_rejects_mismatched_image_extension(self):
        response = self.client.patch(
            "/api/v1/profiles/me/",
            {"avatar": image_upload("not-really.png")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

    def test_profile_media_can_only_be_deleted_by_its_owner(self):
        media = ProfileMedia.objects.create(
            profile=self.user.profile,
            image=image_upload("gallery.png", "PNG", "image/png"),
        )
        self.client.force_authenticate(self.other_user)
        response = self.client.delete(f"/api/v1/profile-media/{media.pk}/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProfileMedia.objects.filter(pk=media.pk).exists())

        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/v1/profile-media/{media.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProfileMedia.objects.filter(pk=media.pk).exists())
