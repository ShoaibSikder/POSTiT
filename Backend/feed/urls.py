from django.urls import path

from .views import FeedView

urlpatterns = [
    path("feed/", FeedView.as_view(), name="feed"),
]
