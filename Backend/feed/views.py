from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .pagination import FeedPagination
from .serializers import FeedPostSerializer
from .services import get_feed_posts


class FeedView(generics.ListAPIView):
    serializer_class = FeedPostSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = FeedPagination

    def get_queryset(self):
        return get_feed_posts(self.request.user)
