"""
Service layer helpers for interaction module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

from django.db.models import Count, F, Q
from django.utils import timezone

from blog.models import Article
from . import models


@dataclass
class LeaderboardEntry:
    article_id: int
    title: str
    url: str
    total_likes: int
    delta_7d: int
    delta_30d: int


class LeaderboardService:
    """
    Provide aggregated leaderboard information.
    """

    def __init__(self, base_qs=None):
        self.article_qs = base_qs or Article.objects.filter(status='p')

    def _compute_delta(self, article: Article, days: int) -> int:
        since = timezone.now() - timezone.timedelta(days=days)
        return models.Like.objects.filter(article=article, created_time__gte=since).count()

    def top_articles(self, limit: int = 20, since: Optional[datetime] = None) -> List[LeaderboardEntry]:
        like_qs = models.Like.objects.all()
        if since:
            like_qs = like_qs.filter(created_time__gte=since)
        queryset = like_qs.values('article').annotate(total=Count('id')).order_by('-total')[:limit]
        entries: List[LeaderboardEntry] = []
        for row in queryset:
            article = self.article_qs.get(pk=row['article'])
            entries.append(LeaderboardEntry(
                article_id=article.id,
                title=article.title,
                url=article.get_absolute_url(),
                total_likes=row['total'],
                delta_7d=self._compute_delta(article, 7),
                delta_30d=self._compute_delta(article, 30),
            ))
        return entries


def move_anonymous_actor(old_key: str, user_actor: models.InteractionActor) -> int:
    """
    Merge likes/favorites from an anonymous actor into a logged-in actor.
    """

    try:
        anon_actor = models.InteractionActor.objects.get(anonymous_key=old_key, user__isnull=True)
    except models.InteractionActor.DoesNotExist:
        return 0

    updated = 0
    updated += models.Like.objects.filter(actor=anon_actor).update(actor=user_actor)
    updated += models.FavoriteFolder.objects.filter(owner=anon_actor).update(owner=user_actor)
    updated += models.FavoriteItem.objects.filter(added_by=anon_actor).update(added_by=user_actor)
    anon_actor.delete()
    return updated

