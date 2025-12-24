import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from .models import ArticleDraft
try:
    from blog.models import Article
except Exception:
    Article = None


@csrf_exempt
@require_POST
def save_autosave(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'authentication required'}, status=403)
    article_id = payload.get('article_id')
    title = payload.get('title', '')
    content = payload.get('content', '')
    version = int(payload.get('version', 1) or 1)
    article = None
    if article_id and Article:
        try:
            article = Article.objects.get(pk=article_id)
        except Article.DoesNotExist:
            article = None
    draft = ArticleDraft.objects.create(article=article, user=request.user, title=title, content=content, version=version)
    return JsonResponse({'id': draft.pk, 'updated_at': draft.updated_at.isoformat(), 'version': draft.version})


@require_GET
def list_versions(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'authentication required'}, status=403)
    drafts = ArticleDraft.objects.filter(user=request.user).values('id', 'article', 'title', 'version', 'updated_at')[:50]
    # convert QuerySet to list and isoformat datetime
    results = []
    for d in drafts:
        d['updated_at'] = d['updated_at'].isoformat() if d.get('updated_at') else None
        results.append(d)
    return JsonResponse({'drafts': results})
