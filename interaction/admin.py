from django.contrib import admin

from . import models


@admin.register(models.InteractionActor)
class InteractionActorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'anonymous_key', 'created_time')
    search_fields = ('user__username', 'anonymous_key')
    list_filter = ('created_time',)


@admin.register(models.FavoriteFolder)
class FavoriteFolderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'is_public', 'pinned', 'sort_order', 'tags', 'share_hits', 'created_time')
    list_filter = ('is_public', 'pinned', 'created_time')
    search_fields = ('name', 'owner__user__username', 'share_token', 'tags')
    ordering = ('-pinned', 'sort_order', '-updated_time')
    readonly_fields = ('share_hits', 'share_token', 'created_time', 'updated_time')


@admin.register(models.FavoriteItem)
class FavoriteItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'folder', 'article', 'added_by', 'note_version', 'created_time')
    search_fields = ('folder__name', 'article__title', 'note')
    list_filter = ('created_time', 'updated_time')


@admin.register(models.Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'article', 'actor', 'is_positive', 'created_time')
    list_filter = ('is_positive', 'created_time')
    search_fields = ('article__title', 'actor__user__username', 'anonymous_key')


@admin.register(models.InteractionNotification)
class InteractionNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'notification_type', 'is_read', 'created_time')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('recipient__username',)
