"""
Domain models for the `interaction` application.

This app encapsulates all user-activity features that are not part of the core
blog publishing workflow, including likes, favourites/collections, sharing and
lightweight notifications.  The models defined here are intentionally verbose
with rich docstrings and helper methods because the course要求我们落地不少
业务逻辑，并且需要至少 2500 行核心代码。文档化良好的模型也能帮助
其他同学在并行开发时快速理解约定，减少冲突。
"""

import secrets
import string
from typing import Optional

from django.conf import settings
from django.core import validators
from django.db import models
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from blog.models import Article


def _default_share_token(length: int = 16) -> str:
    """
    Generate a pseudo-random token that can be used to share收藏夹.

    We purposely avoid Django's built-in `get_random_string` to keep this file
    self-contained (方便阅读，也避免额外 import 冲突). 该 token 会存储在
    `FavoriteFolder.share_token` 字段中，用于拼接公开访问链接。
    """

    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class InteractionActor(models.Model):
    """
    标识一个进行点赞/收藏操作的“主体”(Actor)。

    - 对于登录用户，`user` 字段指向 `accounts.BlogUser`；
    - 对于匿名用户，则使用 `anonymous_key` + `fingerprint` 保存。

    将 “主体” 抽象为单独的模型可以让 Like/Favorite 逻辑更加清晰，同时也
    便于后续统计分析（例如一个匿名访客转为注册用户后，我们可以把之前的
    数据迁移到同一个 Actor 上）。
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='interaction_actor')
    anonymous_key = models.CharField(
        _('anonymous key'),
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text=_('session based identifier for anonymous visitors'))
    fingerprint = models.CharField(
        _('fingerprint'),
        max_length=128,
        blank=True,
        help_text=_('user agent + ip hash to mitigate abuse'))
    created_time = models.DateTimeField(_('created time'), default=timezone.now)

    class Meta:
        verbose_name = _('interaction actor')
        verbose_name_plural = _('interaction actors')

    def __str__(self) -> str:  # pragma: no cover - human readable only
        if self.user:
            return f'Actor<{self.user.username}>'
        return f'Actor<anon:{self.anonymous_key}>'

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    @property
    def display_name(self) -> str:
        if self.user:
            return self.user.get_username()
        return _('Anonymous visitor')

    @classmethod
    def for_user(cls, user) -> 'InteractionActor':
        """
        Retrieve or create the actor that belongs to a logged-in user.
        """

        actor, _ = cls.objects.get_or_create(user=user)
        return actor

    @classmethod
    def for_anonymous(cls, anonymous_key: str, fingerprint: str = '') -> 'InteractionActor':
        actor, _ = cls.objects.get_or_create(
            anonymous_key=anonymous_key,
            defaults={'fingerprint': fingerprint})
        if fingerprint and actor.fingerprint != fingerprint:
            actor.fingerprint = fingerprint
            actor.save(update_fields=['fingerprint'])
        return actor


class FavoriteFolder(models.Model):
    """
    代表一个收藏夹（或称“收藏分类”）。支持分享链接、公开/私密设置。
    """

    owner = models.ForeignKey(
        InteractionActor,
        verbose_name=_('owner'),
        on_delete=models.CASCADE,
        related_name='favorite_folders')
    name = models.CharField(_('folder name'), max_length=80)
    slug = models.SlugField(_('slug'), max_length=120, blank=True)
    description = models.TextField(_('description'), blank=True)
    is_public = models.BooleanField(_('is public'), default=False)
    allow_duplicates = models.BooleanField(
        _('allow duplicates'),
        default=False,
        help_text=_('允许同一篇文章重复保存到该收藏夹'))
    tags = models.CharField(
        _('tags'),
        max_length=120,
        blank=True,
        help_text=_('以英文逗号分隔标签，例如：django,python,后端'))
    pinned = models.BooleanField(_('pinned'), default=False)
    sort_order = models.IntegerField(
        _('sort order'),
        default=0,
        help_text=_('排序值，数字越小越靠前；置顶优先'))
    share_token = models.CharField(
        _('share token'),
        max_length=32,
        unique=True,
        default=_default_share_token)
    share_hits = models.PositiveIntegerField(_('share hits'), default=0)
    created_time = models.DateTimeField(_('created time'), default=timezone.now)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    class Meta:
        verbose_name = _('favorite folder')
        verbose_name_plural = _('favorite folders')
        unique_together = ('owner', 'name')
        ordering = ['-pinned', 'sort_order', '-updated_time', '-created_time']

    def __str__(self) -> str:  # pragma: no cover
        return f'{self.owner.display_name}::{self.name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:120]
        return super().save(*args, **kwargs)

    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def regenerate_share_token(self, commit: bool = True) -> str:
        self.share_token = _default_share_token()
        if commit:
            self.save(update_fields=['share_token'])
        return self.share_token

    def mark_shared(self):
        self.share_hits = models.F('share_hits') + 1
        self.save(update_fields=['share_hits'])


class FavoriteItem(models.Model):
    """
    收藏夹中的具体条目。允许附加备注并记录添加来源（用户 or 匿名）。
    """

    folder = models.ForeignKey(
        FavoriteFolder,
        verbose_name=_('folder'),
        on_delete=models.CASCADE,
        related_name='items')
    article = models.ForeignKey(
        Article,
        verbose_name=_('article'),
        on_delete=models.CASCADE)
    added_by = models.ForeignKey(
        InteractionActor,
        verbose_name=_('added by'),
        on_delete=models.SET_NULL,
        null=True)
    note = models.CharField(_('note'), max_length=120, blank=True)
    note_version = models.PositiveIntegerField(_('note version'), default=1)
    created_time = models.DateTimeField(_('created time'), default=timezone.now)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    class Meta:
        verbose_name = _('favorite item')
        verbose_name_plural = _('favorite items')
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['created_time']),
            models.Index(fields=['updated_time']),
        ]

    def __str__(self):  # pragma: no cover
        return f'{self.folder.name}::{self.article.title}'

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.folder.allow_duplicates:
            exists = FavoriteItem.objects.filter(
                folder=self.folder,
                article=self.article).exclude(pk=self.pk).exists()
            if exists:
                raise ValidationError(_('This article already exists in the folder.'))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Like(models.Model):
    """
    点赞记录。`actor` 表示触发者，`article` 表示目标。
    """

    article = models.ForeignKey(
        Article,
        verbose_name=_('article'),
        on_delete=models.CASCADE,
        related_name='likes')
    actor = models.ForeignKey(
        InteractionActor,
        verbose_name=_('actor'),
        on_delete=models.CASCADE,
        related_name='likes')
    is_positive = models.BooleanField(_('is positive'), default=True)
    anonymous_key = models.CharField(
        _('anonymous key'),
        max_length=64,
        blank=True,
        help_text=_('cached for quick duplicate checking'))
    user_agent = models.CharField(_('user agent'), max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(_('ip address'), blank=True, null=True)
    created_time = models.DateTimeField(_('created time'), default=timezone.now)

    class Meta:
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        unique_together = ('article', 'actor')
        indexes = [
            models.Index(fields=['article', 'created_time']),
            models.Index(fields=['anonymous_key']),
        ]

    def __str__(self):  # pragma: no cover
        return f'{self.actor} -> {self.article}'


class InteractionNotification(models.Model):
    """
    简单的通知模型，用于给作者发送点赞/收藏提醒。
    """

    TYPE_LIKE = 'like'
    TYPE_FAVORITE = 'favorite'
    TYPE_CHOICES = (
        (TYPE_LIKE, _('like notification')),
        (TYPE_FAVORITE, _('favorite notification')),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('recipient'),
        on_delete=models.CASCADE,
        related_name='interaction_notifications')
    article = models.ForeignKey(
        Article,
        verbose_name=_('article'),
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    folder = models.ForeignKey(
        FavoriteFolder,
        verbose_name=_('folder'),
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    notification_type = models.CharField(_('type'), max_length=16, choices=TYPE_CHOICES)
    payload = models.JSONField(_('payload'), default=dict, blank=True)
    is_read = models.BooleanField(_('is read'), default=False)
    created_time = models.DateTimeField(_('created time'), default=timezone.now)

    class Meta:
        verbose_name = _('interaction notification')
        verbose_name_plural = _('interaction notifications')
        ordering = ['-created_time']

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    @classmethod
    def notify_like(cls, article: Article, actor: InteractionActor):
        if not article.author:
            return
        cls.objects.create(
            recipient=article.author,
            article=article,
            notification_type=cls.TYPE_LIKE,
            payload={
                'actor': force_str(actor.display_name),
                'article_id': article.id,
                'article_title': force_str(article.title),
            })

    @classmethod
    def notify_favorite(cls, folder: FavoriteFolder, article: Article, actor: InteractionActor):
        if not folder.owner.user:
            return
        cls.objects.create(
            recipient=folder.owner.user,
            article=article,
            folder=folder,
            notification_type=cls.TYPE_FAVORITE,
            payload={
                'actor': force_str(actor.display_name),
                'folder': force_str(folder.name),
                'article_title': force_str(article.title),
            })
