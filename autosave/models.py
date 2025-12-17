from django.db import models
from django.conf import settings
from django.utils import timezone

try:
    from blog.models import Article
except Exception:
    Article = None


class ArticleDraft(models.Model):
    # ArticleFK (if blog.Article is available) or store as integer otherwise
    article = models.ForeignKey(Article, null=True, blank=True, on_delete=models.CASCADE, related_name='autosave_drafts') if Article else models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='article_drafts')
    title = models.CharField(max_length=255, blank=True)
    # use `body` to match blog.views expectations, keep `content` as alias
    body = models.TextField(blank=True)
    content = models.TextField(blank=True)
    # additional metadata expected by blog.views
    save_type = models.CharField(max_length=10, choices=(('auto', 'auto'), ('manual', 'manual')), default='auto')
    status = models.CharField(max_length=10, default='d')
    comment_status = models.CharField(max_length=10, default='o')
    article_type = models.CharField(max_length=10, default='a')
    show_toc = models.BooleanField(default=False)
    article_order = models.IntegerField(default=0)

    version = models.IntegerField(default=1)
    saved_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-saved_at']

    def __str__(self):
        return f"Draft {self.pk} ({self.title})"

    def get_human_time(self):
        # simple human-readable time for compatibility with blog.views
        return self.saved_at.strftime('%Y-%m-%d %H:%M:%S')
