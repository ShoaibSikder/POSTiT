from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from .permissions import IsOwnerOrReadOnly


class IsOwnerOrReadOnlyTests(SimpleTestCase):
    def test_safe_methods_are_public(self):
        request = APIRequestFactory().get("/")

        self.assertTrue(IsOwnerOrReadOnly().has_object_permission(request, None, object()))

