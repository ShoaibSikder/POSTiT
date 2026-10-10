from django.urls import path

from .views import PostSearchView, UserSearchView, UserSuggestionsView

urlpatterns = [
    path("search/suggestions/", UserSuggestionsView.as_view(), name="user-suggestions"),
    path("search/users/", UserSearchView.as_view(), name="search-users"),
    path("search/posts/", PostSearchView.as_view(), name="search-posts"),
]
