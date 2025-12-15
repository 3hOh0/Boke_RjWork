from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.core.cache import cache
from blog.models import Article, Category, Tag
from comments.models import Comment
from accounts.models import BlogUser
from interaction.models import Like, FavoriteItem, FavoriteFolder

CACHE_TTL = 600  # 10 分钟

def get_metrics():
    key = "dashboard:metrics:v2"
    cached = cache.get(key)
    if cached:
        return cached
    qs_article = Article.objects
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    active_users = BlogUser.objects.filter(
        Q(article__pub_time__gte=thirty_days_ago) |
        Q(comment__creation_time__gte=thirty_days_ago) |
        Q(interaction_actor__likes__created_time__gte=thirty_days_ago)
    ).distinct().count()
    
    data = {
        "article_total": qs_article.count(),
        "article_published": qs_article.filter(status="p").count(),
        "article_draft": qs_article.filter(status="d").count(),
        "comment_total": Comment.objects.count(),
        "user_total": BlogUser.objects.count(),
        "active_users": active_users,
        "pv_total": qs_article.aggregate(total=Sum("views"))["total"] or 0,
        "like_total": Like.objects.count(),
        "favorite_total": FavoriteItem.objects.count(),
        "folder_total": FavoriteFolder.objects.count(),
        "tag_total": Tag.objects.count(),
        "category_total": Category.objects.count(),
    }
    cache.set(key, data, CACHE_TTL)
    return data

def get_trend(days=7):
    key = f"dashboard:trend:{days}"
    cached = cache.get(key)
    if cached:
        return cached
    since = timezone.now() - timedelta(days=days)
    # 示例：按天统计 PV（假设 Article 有 views_log 表则替换）
    rows = (
        Article.objects.filter(pub_time__gte=since)
        .extra(select={"day": "date(pub_time)"})
        .values("day")
        .annotate(published_count=Count("id"))
        .order_by("day")
    )
    data = list(rows)
    cache.set(key, data, CACHE_TTL)
    return data

def get_top_articles(limit=10):
    key = f"dashboard:top_articles:{limit}"
    cached = cache.get(key)
    if cached:
        return cached
    rows = (
        Article.objects
        .annotate(comment_count=Count("comment"))  # 视你的 related_name 调整
        .order_by("-views")[:limit]
        .values("id", "title", "views", "comment_count")
    )
    data = list(rows)
    cache.set(key, data, CACHE_TTL)
    return data

def get_top_authors(limit=10):
    key = f"dashboard:top_authors:{limit}"
    cached = cache.get(key)
    if cached:
        return cached
    rows = (
        BlogUser.objects
        .annotate(article_count=Count("article"))
        .annotate(total_views=Sum("article__views"))
        .order_by("-total_views")[:limit]
        .values("id", "username", "article_count", "total_views")
    )
    data = list(rows)
    cache.set(key, data, CACHE_TTL)
    return data

def get_category_distribution():
    key = "dashboard:category_distribution"
    cached = cache.get(key)
    if cached:
        return cached
    rows = (
        Category.objects
        .annotate(article_count=Count("article"))
        .filter(article_count__gt=0)
        .order_by("-article_count")
        .values("name", "article_count")
    )
    data = list(rows)
    cache.set(key, data, CACHE_TTL)
    return data

def get_like_trend(days=7):
    key = f"dashboard:like_trend:{days}"
    cached = cache.get(key)
    if cached:
        return cached
    since = timezone.now() - timedelta(days=days)
    rows = (
        Like.objects.filter(created_time__gte=since)
        .extra(select={"day": "date(created_time)"})
        .values("day")
        .annotate(like_count=Count("id"))
        .order_by("day")
    )
    data = list(rows)
    cache.set(key, data, CACHE_TTL)
    return data

def get_tag_distribution(limit=10):
    """获取标签分布统计"""
    key = f"dashboard:tag_distribution:{limit}"
    cached = cache.get(key)
    if cached:
        return cached
    rows = (
        Tag.objects
        .annotate(article_count=Count("article"))
        .filter(article_count__gt=0)
        .order_by("-article_count")[:limit]
        .values("name", "article_count")
    )
    data = list(rows)
    cache.set(key, data, CACHE_TTL)
    return data

def get_favorite_trend(days=7):
    """获取收藏趋势统计"""
    key = f"dashboard:favorite_trend:{days}"
    cached = cache.get(key)
    if cached:
        return cached
    since = timezone.now() - timedelta(days=days)
    rows = (
        FavoriteItem.objects.filter(created_time__gte=since)
        .extra(select={"day": "date(created_time)"})
        .values("day")
        .annotate(favorite_count=Count("id"))
        .order_by("day")
    )
    data = list(rows)
    cache.set(key, data, CACHE_TTL)
    return data

def get_comment_trend(days=7):
    """获取评论趋势统计"""
    key = f"dashboard:comment_trend:{days}"
    cached = cache.get(key)
    if cached:
        return cached
    since = timezone.now() - timedelta(days=days)
    rows = (
        Comment.objects.filter(creation_time__gte=since)
        .extra(select={"day": "date(creation_time)"})
        .values("day")
        .annotate(comment_count=Count("id"))
        .order_by("day")
    )
    data = list(rows)
    cache.set(key, data, CACHE_TTL)
    return data

def get_recent_activities(limit=20):
    """获取最近活动记录"""
    key = f"dashboard:recent_activities:{limit}"
    cached = cache.get(key)
    if cached:
        return cached
    
    activities = []
    
    recent_articles = Article.objects.filter(status="p").order_by("-pub_time")[:limit//4]
    for article in recent_articles:
        author = article.author.username if article.author else "Unknown"
        activities.append({
            "type": "article",
            "title": article.title,
            "author": author,
            "time": article.pub_time.isoformat(),
            "url": article.get_absolute_url(),
            "description": f"{author} 发布了文章《{article.title}》",
        })
    
    recent_comments = Comment.objects.order_by("-creation_time")[:limit//4]
    for comment in recent_comments:
        author = comment.author.username if comment.author else "Anonymous"
        content = comment.body[:50] + "..." if len(comment.body) > 50 else comment.body
        activities.append({
            "type": "comment",
            "content": content,
            "author": author,
            "time": comment.creation_time.isoformat(),
            "description": f"{author} 发表了评论: {content}",
        })
    
    recent_likes = Like.objects.select_related("article", "actor__user").order_by("-created_time")[:limit//4]
    for like in recent_likes:
        user = like.actor.display_name
        article_title = like.article.title
        activities.append({
            "type": "like",
            "article": article_title,
            "user": user,
            "time": like.created_time.isoformat(),
            "description": f"{user} 点赞了文章《{article_title}》",
        })
    
    recent_favorites = FavoriteItem.objects.select_related("article", "folder").order_by("-created_time")[:limit//4]
    for fav in recent_favorites:
        article_title = fav.article.title
        folder_name = fav.folder.name
        activities.append({
            "type": "favorite",
            "article": article_title,
            "folder": folder_name,
            "time": fav.created_time.isoformat(),
            "description": f"收藏了文章《{article_title}》到收藏夹《{folder_name}》",
        })
    
    activities.sort(key=lambda x: x["time"], reverse=True)
    data = activities[:limit]
    cache.set(key, data, CACHE_TTL)
    return data