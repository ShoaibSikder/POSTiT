from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from .models import Post, PostImage


User = get_user_model()


def image_upload(name="post.jpg", image_format="JPEG", content_type="image/jpeg"):
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color="green").save(buffer, format=image_format)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


@override_settings(POSTIT_MAX_POST_IMAGES=2)
class PostAPITests(TestCase):
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

    def test_create_post_with_images_and_retrieve_it(self):
        response = self.client.post(
            "/api/v1/posts/",
            {
                "content": "A post with two images",
                "images": [
                    image_upload("first.jpg"),
                    image_upload("second.webp", "WEBP", "image/webp"),
                ],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["author"], "alice")
        self.assertEqual(len(response.data["images"]), 2)
        self.assertEqual(PostImage.objects.filter(post_id=response.data["id"]).count(), 2)

        detail = self.client.get(f"/api/v1/posts/{response.data['id']}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["content"], "A post with two images")

    def test_image_only_post_is_allowed(self):
        response = self.client.post(
            "/api/v1/posts/",
            {"images": [image_upload()]},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["content"], "")

    def test_post_requires_content_or_image_and_obeys_image_limit(self):
        empty_response = self.client.post(
            "/api/v1/posts/",
            {"content": ""},
            format="json",
        )
        self.assertEqual(empty_response.status_code, 400)

        too_many_response = self.client.post(
            "/api/v1/posts/",
            {
                "content": "Too many images",
                "images": [
                    image_upload("first.jpg"),
                    image_upload("second.jpg"),
                    image_upload("third.jpg"),
                ],
            },
            format="multipart",
        )
        self.assertEqual(too_many_response.status_code, 400)
        self.assertFalse(Post.objects.exists())

    @override_settings(POSTIT_MAX_POST_LENGTH=10)
    def test_post_content_obeys_configured_character_limit(self):
        response = self.client.post(
            "/api/v1/posts/",
            {"content": "This is too long"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_post_adds_and_removes_images(self):
        post = Post.objects.create(author=self.user, content="Before edit")
        image = PostImage.objects.create(post=post, image=image_upload())

        response = self.client.patch(
            f"/api/v1/posts/{post.pk}/",
            {
                "content": "After edit",
                "images": [image_upload("added.png", "PNG", "image/png")],
                "remove_image_ids": [image.pk],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["content"], "After edit")
        self.assertEqual(len(response.data["images"]), 1)
        self.assertFalse(PostImage.objects.filter(pk=image.pk).exists())

    def test_cannot_edit_or_delete_another_users_post(self):
        post = Post.objects.create(author=self.other_user, content="Bob's post")

        update = self.client.patch(
            f"/api/v1/posts/{post.pk}/",
            {"content": "Tampered"},
            format="json",
        )
        self.assertEqual(update.status_code, 403)

        deletion = self.client.delete(f"/api/v1/posts/{post.pk}/")
        self.assertEqual(deletion.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_post_deletion_cascades_to_image_records(self):
        post = Post.objects.create(author=self.user, content="Remove me")
        image = PostImage.objects.create(post=post, image=image_upload())

        response = self.client.delete(f"/api/v1/posts/{post.pk}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(PostImage.objects.filter(pk=image.pk).exists())

    def test_invalid_image_content_is_rejected(self):
        response = self.client.post(
            "/api/v1/posts/",
            {
                "content": "Not an image",
                "images": [
                    SimpleUploadedFile(
                        "fake.jpg",
                        b"not an image",
                        content_type="image/jpeg",
                    )
                ],
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
