from django.contrib import admin

from .models import Post, PostImage


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("content", "author__username")
    list_select_related = ("author",)
    readonly_fields = ("created_at", "updated_at")
    inlines = (PostImageInline,)


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "created_at")
    list_select_related = ("post",)
    search_fields = ("post__author__username", "post__content")
    readonly_fields = ("created_at",)
