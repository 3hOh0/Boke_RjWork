"""
HTTP/API views for the interaction application.
"""

from __future__ import annotations

import csv
import io

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import Count
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from blog.models import Article
from . import forms, models, services
from .utils import build_share_url, identity_from_request
from djangoblog.utils import send_email


class InteractionActorMixin:
    """
    Resolve the InteractionActor for the incoming request.
    """

    actor: models.InteractionActor

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            self.actor = models.InteractionActor.for_user(request.user)
        else:
            anonymous_key, fingerprint = identity_from_request(request)
            self.actor = models.InteractionActor.for_anonymous(
                anonymous_key=anonymous_key,
                fingerprint=fingerprint)
        return super().dispatch(request, *args, **kwargs)


class ToggleLikeView(InteractionActorMixin, View):
    """
    Toggle like/unlike for an article. Allows anonymous visitors.
    """

    http_method_names = ['post']

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        article = get_object_or_404(Article, pk=request.POST.get('article_id'))
        existing = models.Like.objects.filter(article=article, actor=self.actor)
        created = False
        if existing.exists():
            existing.delete()
            liked = False
        else:
            models.Like.objects.create(
                article=article,
                actor=self.actor,
                anonymous_key=self.actor.anonymous_key or '',
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                ip_address=request.META.get('REMOTE_ADDR'),
                created_time=timezone.now())
            models.InteractionNotification.notify_like(article, self.actor)
            liked = True
            created = True
        like_count = models.Like.objects.filter(article=article).count()
        return JsonResponse({
            'liked': liked,
            'created': created,
            'like_count': like_count,
        })


class LikeLeaderboardView(View):
    """
    点赞排行榜页面，显示最受欢迎文章TOP20
    """

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # 获取点赞数最多的20篇文章
        top_articles = Article.objects.filter(
            status='p',
            likes__isnull=False
        ).annotate(
            like_count=Count('likes')
        ).order_by('-like_count', '-pub_time')[:20]
        
        # 获取当前用户的点赞状态
        user_likes = set()
        if request.user.is_authenticated:
            actor = models.InteractionActor.for_user(request.user)
            user_likes = set(models.Like.objects.filter(
                actor=actor,
                article__in=top_articles
            ).values_list('article_id', flat=True))
        
        context = {
            'top_articles': top_articles,
            'user_likes': user_likes,
            'title': _('Most Liked Articles')
        }
        return render(request, 'interaction/like_leaderboard.html', context)


class MyFavoritesView(LoginRequiredMixin, View):
    """
    我的收藏页面，显示用户的收藏列表和收藏夹
    """

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        actor = models.InteractionActor.for_user(request.user)
        
        # 获取所有收藏夹
        folders = models.FavoriteFolder.objects.filter(owner=actor)
        
        # 获取默认收藏夹中的文章（按添加时间倒序）
        default_folder = folders.filter(name='默认收藏夹').first()
        if not default_folder:
            default_folder = models.FavoriteFolder.objects.create(
                owner=actor,
                name='默认收藏夹',
                description='默认收藏夹'
            )
        
        # 分页显示收藏文章
        favorite_items = models.FavoriteItem.objects.filter(
            folder__owner=actor
        ).select_related('article', 'folder').order_by('-created_time')
        
        paginator = Paginator(favorite_items, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context = {
            'folders': folders,
            'page_obj': page_obj,
            'title': _('My Favorites')
        }
        return render(request, 'interaction/my_favorites.html', context)


class UserLikeHistoryView(LoginRequiredMixin, View):
    """
    用户点赞历史记录页面
    """

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        actor = models.InteractionActor.for_user(request.user)
        
        # 获取用户的点赞记录
        likes = models.Like.objects.filter(
            actor=actor
        ).select_related('article').order_by('-created_time')
        
        # 分页显示
        paginator = Paginator(likes, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'title': _('My Like History')
        }
        return render(request, 'interaction/like_history.html', context)


class FavoriteSearchView(LoginRequiredMixin, View):
    """
    收藏文章搜索和筛选
    """

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        actor = models.InteractionActor.for_user(request.user)
        
        # 获取查询参数
        query = request.GET.get('q', '')
        folder_id = request.GET.get('folder_id')
        category = request.GET.get('category')
        
        # 构建查询
        favorite_items = models.FavoriteItem.objects.filter(
            folder__owner=actor
        ).select_related('article', 'folder')
        
        if query:
            favorite_items = favorite_items.filter(
                models.Q(article__title__icontains=query) |
                models.Q(note__icontains=query)
            )
        
        if folder_id:
            favorite_items = favorite_items.filter(folder_id=folder_id)
        
        if category:
            favorite_items = favorite_items.filter(article__category__name=category)
        
        # 排序和分页
        sort_by = request.GET.get('sort_by', 'created_time')
        if sort_by == 'title':
            favorite_items = favorite_items.order_by('article__title')
        else:
            favorite_items = favorite_items.order_by('-created_time')
        
        paginator = Paginator(favorite_items, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # 构建响应数据
        items_data = []
        for item in page_obj:
            items_data.append({
                'id': item.id,
                'article_id': item.article.id,
                'title': item.article.title,
                'url': item.article.get_absolute_url(),
                'folder_name': item.folder.name,
                'note': item.note,
                'created_time': item.created_time.strftime('%Y-%m-%d %H:%M'),
                'category': item.article.category.name
            })
        
        return JsonResponse({
            'items': items_data,
            'total_pages': paginator.num_pages,
            'current_page': page_number,
            'total_count': paginator.count
        })


class FavoriteFolderListView(InteractionActorMixin, View):
    """
    List or create favorite folders.
    """

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        folders = []
        for folder in self.actor.favorite_folders.all():
            share_url = build_share_url(request, folder.share_token)
            folders.append({
            'id': folder.id,
            'name': folder.name,
            'description': folder.description,
            'is_public': folder.is_public,
            'share_token': folder.share_token,
            'share_url': share_url,
            'allow_duplicates': folder.allow_duplicates,
            'tags': folder.tag_list(),
            'pinned': folder.pinned,
            'sort_order': folder.sort_order,
        })
        return JsonResponse({'folders': folders})

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        form = forms.FavoriteFolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.owner = self.actor
            folder.save()
            return JsonResponse({'id': folder.id, 'share_token': folder.share_token})
        return JsonResponse({'errors': form.errors}, status=400)


class FavoriteItemView(InteractionActorMixin, View):
    """
    Add or remove favorite items.
    """

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        # Support method override for clients that cannot send DELETE
        if request.POST.get('_method') == 'delete' or request.POST.get('action') == 'delete':
            item_id = kwargs.get('item_id') or request.POST.get('item_id')
            if not item_id:
                return JsonResponse({'deleted': False, 'error': 'item_id missing'}, status=400)
            deleted, _ = models.FavoriteItem.objects.filter(
                pk=item_id,
                folder__owner=self.actor).delete()
            return JsonResponse({'deleted': bool(deleted)})

        folder = get_object_or_404(
            models.FavoriteFolder,
            pk=request.POST.get('folder_id'),
            owner=self.actor)
        article = get_object_or_404(Article, pk=request.POST.get('article_id'))
        
        # Check if item already exists
        existing_item = models.FavoriteItem.objects.filter(
            folder=folder,
            article=article
        ).first()
        
        if existing_item:
            # If duplicates are not allowed, return error
            if not folder.allow_duplicates:
                return JsonResponse({
                    'created': False,
                    'error': 'duplicate not allowed',
                    'item_id': existing_item.id
                }, status=400)
            # If duplicates are allowed, return existing item
            return JsonResponse({
                'created': False,
                'item_id': existing_item.id,
                'message': 'Item already exists in folder'
            })
        
        # Create new item
        item = models.FavoriteItem.objects.create(
            folder=folder,
            article=article,
            added_by=self.actor
        )
        models.InteractionNotification.notify_favorite(folder, article, self.actor)
        return JsonResponse({'created': True, 'item_id': item.id})

    def delete(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        item_id = kwargs.get('item_id')
        deleted, _ = models.FavoriteItem.objects.filter(
            pk=item_id,
            folder__owner=self.actor).delete()
        return JsonResponse({'deleted': bool(deleted)})


class FavoriteFolderDetailView(InteractionActorMixin, View):
    """
    Retrieve/update/delete a specific folder.
    """

    def _get_folder(self, pk: int) -> models.FavoriteFolder:
        return get_object_or_404(models.FavoriteFolder, pk=pk, owner=self.actor)

    def get(self, request: HttpRequest, folder_id: int, *args, **kwargs) -> JsonResponse:
        folder = self._get_folder(folder_id)
        return JsonResponse({
            'id': folder.id,
            'name': folder.name,
            'description': folder.description,
            'is_public': folder.is_public,
            'share_token': folder.share_token,
            'share_url': build_share_url(request, folder.share_token),
            'allow_duplicates': folder.allow_duplicates,
            'tags': folder.tag_list(),
            'pinned': folder.pinned,
            'sort_order': folder.sort_order,
        })

    def post(self, request: HttpRequest, folder_id: int, *args, **kwargs) -> JsonResponse:
        folder = self._get_folder(folder_id)
        form = forms.FavoriteFolderUpdateForm(request.POST, instance=folder)
        if form.is_valid():
            updated_folder = form.save()
            if form.cleaned_data.get('regenerate_share_token'):
                updated_folder.regenerate_share_token()
            return JsonResponse({
                'id': updated_folder.id,
                'share_token': updated_folder.share_token,
                'share_url': build_share_url(request, updated_folder.share_token),
            })
        return JsonResponse({'errors': form.errors}, status=400)

    def delete(self, request: HttpRequest, folder_id: int, *args, **kwargs) -> JsonResponse:
        folder = self._get_folder(folder_id)
        folder.delete()
        return JsonResponse({'deleted': True})


class QuickFavoriteView(InteractionActorMixin, View):
    """
    Save article to folder via modal.
    """

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        form = forms.QuickFavoriteForm(request.POST, actor=self.actor)
        if not form.is_valid():
            return JsonResponse({'errors': form.errors}, status=400)
        folder: models.FavoriteFolder = form.cleaned_data['folder']
        if folder is None:
            folder = models.FavoriteFolder.objects.create(
                owner=self.actor,
                name=form.cleaned_data['folder_name'],
                description=form.cleaned_data.get('folder_description', ''),
                is_public=form.cleaned_data.get('folder_is_public', False),
                allow_duplicates=form.cleaned_data.get('allow_duplicates', False),
            )
        article = get_object_or_404(Article, pk=form.cleaned_data['article_id'])
        item, created = models.FavoriteItem.objects.get_or_create(
            folder=folder,
            article=article,
            defaults={'added_by': self.actor, 'note': form.cleaned_data.get('note', '')})
        if not created and form.cleaned_data.get('note'):
            item.note = form.cleaned_data['note']
            item.note_version += 1
            item.save(update_fields=['note', 'note_version'])
        status_code = 201 if created else 200
        if created:
            models.InteractionNotification.notify_favorite(folder, article, self.actor)
        return JsonResponse({
            'created': created,
            'item_id': item.id,
            'folder_id': folder.id,
            'share_url': build_share_url(request, folder.share_token),
        }, status=status_code)


class FavoriteItemListView(InteractionActorMixin, View):
    """
    Return all items within a folder.
    """

    def get(self, request: HttpRequest, folder_id: int, *args, **kwargs) -> JsonResponse:
        folder = get_object_or_404(models.FavoriteFolder, pk=folder_id, owner=self.actor)
        items = [{
            'id': item.id,
            'article_id': item.article_id,
            'title': item.article.title,
            'url': item.article.get_absolute_url(),
            'note': item.note,
            'created_time': item.created_time.isoformat(),
        } for item in folder.items.select_related('article').all()]
        return JsonResponse({'folder': folder.name, 'items': items})


class FavoriteBatchActionView(LoginRequiredMixin, InteractionActorMixin, View):
    """
    Handle batch operations for favorites to reduce front-end roundtrips.

    Supported actions (POST):
    - delete_items: item_ids[]
    - move_items: item_ids[] + target_folder_id
    - pin_folders / unpin_folders: folder_ids[]
    - sort_folders: folder_ids[] + sort_order[] (parallel lists)
    """

    http_method_names = ['post']

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        action = request.POST.get('action')
        if not action:
            return JsonResponse({'error': 'action required'}, status=400)

        item_ids = request.POST.getlist('item_ids[]') or request.POST.getlist('item_ids')
        folder_ids = request.POST.getlist('folder_ids[]') or request.POST.getlist('folder_ids')

        if action == 'delete_items':
            deleted, _ = models.FavoriteItem.objects.filter(
                pk__in=item_ids,
                folder__owner=self.actor).delete()
            return JsonResponse({'deleted': deleted})

        if action == 'move_items':
            target_folder_id = request.POST.get('target_folder_id')
            if not target_folder_id:
                return JsonResponse({'error': 'target_folder_id required'}, status=400)
            target_folder = get_object_or_404(
                models.FavoriteFolder,
                pk=target_folder_id,
                owner=self.actor)
            moved = models.FavoriteItem.objects.filter(
                pk__in=item_ids,
                folder__owner=self.actor).update(folder=target_folder)
            return JsonResponse({'moved': moved})

        if action in ('pin_folders', 'unpin_folders'):
            pinned = action == 'pin_folders'
            updated = models.FavoriteFolder.objects.filter(
                pk__in=folder_ids,
                owner=self.actor).update(pinned=pinned)
            return JsonResponse({'updated': updated})

        if action == 'sort_folders':
            sort_orders = request.POST.getlist('sort_order[]')
            if len(folder_ids) != len(sort_orders):
                return JsonResponse({'error': 'folder_ids and sort_order length mismatch'}, status=400)
            
            updated = 0
            for folder_id, sort_order in zip(folder_ids, sort_orders):
                try:
                    folder = models.FavoriteFolder.objects.get(
                        pk=folder_id,
                        owner=self.actor)
                    folder.sort_order = int(sort_order)
                    folder.save(update_fields=['sort_order'])
                    updated += 1
                except (models.FavoriteFolder.DoesNotExist, ValueError):
                    continue
            return JsonResponse({'updated': updated})

        return JsonResponse({'error': 'unsupported action'}, status=400)


class FavoriteExportView(LoginRequiredMixin, InteractionActorMixin, View):
    """
    Export folder items as CSV or JSON for personal use.
    """

    def get(self, request: HttpRequest, folder_id: int, *args, **kwargs) -> HttpResponse:
        fmt = (request.GET.get('format') or 'json').lower()
        folder = get_object_or_404(models.FavoriteFolder, pk=folder_id, owner=self.actor)
        items = list(folder.items.select_related('article').all())
        if fmt == 'csv':
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(['id', 'article_id', 'title', 'url', 'note', 'note_version', 'created_time'])
            for item in items:
                writer.writerow([
                    item.id,
                    item.article_id,
                    force_str(getattr(item.article, 'title', '')),
                    item.article.get_absolute_url(),
                    item.note,
                    item.note_version,
                    item.created_time.isoformat(),
                ])
            response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename=folder_{folder_id}.csv'
            return response
        data = []
        for item in items:
            data.append({
                'id': item.id,
                'article_id': item.article_id,
                'title': force_str(getattr(item.article, 'title', '')),
                'url': item.article.get_absolute_url(),
                'note': item.note,
                'note_version': item.note_version,
                'created_time': item.created_time.isoformat(),
            })
        return JsonResponse({'folder': folder.name, 'items': data})


class FavoriteShareView(View):
    """
    Render a public favorite folder page.
    """

    template_name = 'interaction/folder_share.html'

    def get(self, request: HttpRequest, token: str, *args, **kwargs) -> HttpResponse:
        folder = get_object_or_404(models.FavoriteFolder, share_token=token, is_public=True)
        folder.mark_shared()
        return render(request, self.template_name, {'folder': folder})


class FavoriteDashboardView(LoginRequiredMixin, InteractionActorMixin, View):
    """
    Render a dashboard for managing folders & saved items.
    """

    template_name = 'interaction/dashboard.html'

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        folders = list(self.actor.favorite_folders.prefetch_related('items', 'items__article'))
        folder_count = len(folders)
        item_count = sum(f.items.count() for f in folders)
        public_count = sum(1 for f in folders if f.is_public)
        pinned_count = sum(1 for f in folders if f.pinned)
        paginator = Paginator(folders, 5)
        page_obj = paginator.get_page(request.GET.get('page'))
        for folder in folders:
            folder.share_url = build_share_url(request, folder.share_token)
        return render(request, self.template_name, {
            'folders': page_obj.object_list,
            'page_obj': page_obj,
            'folder_form': forms.FavoriteFolderForm(),
            'item_form': forms.FavoriteItemForm(),
            'folder_count': folder_count,
            'item_count': item_count,
            'public_count': public_count,
            'pinned_count': pinned_count,
        })


class LeaderboardView(View):
    """
    Return like leaderboard, optionally filtered by date range.
    """

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        since = request.GET.get('since')
        service = services.LeaderboardService()
        if since:
            try:
                since_dt = timezone.datetime.fromisoformat(since)
            except ValueError:
                return JsonResponse({'error': 'invalid since parameter'}, status=400)
        else:
            since_dt = None
        entries = service.top_articles(limit=20, since=since_dt)
        data = []
        for entry in entries:
            data.append({
                'article_id': entry.article_id,
                'title': entry.title,
                'url': entry.url,
                'total_likes': entry.total_likes,
                'delta_7d': entry.delta_7d,
                'delta_30d': entry.delta_30d,
            })
        return JsonResponse({'articles': data})


class LeaderboardPage(View):
    """
    Render leaderboard page with filters.
    """

    template_name = 'interaction/leaderboard.html'

    def get(self, request: HttpRequest, *args, **kwargs):
        since = request.GET.get('since')
        since_dt = None
        if since:
            try:
                since_dt = timezone.datetime.fromisoformat(since)
            except ValueError:
                since_dt = None
        service = services.LeaderboardService()
        entries = service.top_articles(limit=20, since=since_dt)
        return render(request, self.template_name, {
            'entries': entries,
            'since': since or '',
        })


class PublicFavoriteListView(View):
    """
    List public folders for discovery.
    """

    template_name = 'interaction/public_folders.html'

    def get(self, request: HttpRequest, *args, **kwargs):
        folders = models.FavoriteFolder.objects.filter(is_public=True).select_related('owner__user')[:50]
        for folder in folders:
            folder.share_url = build_share_url(request, folder.share_token)
        return render(request, self.template_name, {'folders': folders})


@method_decorator(csrf_exempt, name='dispatch')
class SwaggerView(View):
    """
    Provide a minimal JSON schema describing the interaction API.
    """

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        base = request.build_absolute_uri(reverse_lazy('interaction:toggle_like'))
        return JsonResponse({
            'info': {
                'title': 'Interaction API',
                'version': '1.0.0',
            },
            'paths': {
                '/interaction/like/': {
                    'post': {
                        'description': 'toggle like for an article',
                        'parameters': [{'name': 'article_id', 'in': 'formData', 'required': True}],
                    }
                },
                '/interaction/folders/': {
                    'get': {'description': 'list favorite folders'},
                    'post': {'description': 'create favorite folder'},
                },
                '/interaction/folders/{id}/': {
                    'get': {'description': 'retrieve folder'},
                    'post': {'description': 'update folder'},
                    'delete': {'description': 'delete folder'},
                },
                '/interaction/quick-save/': {
                    'post': {'description': 'quick save article to folder'}
                },
            },
            'base_like_endpoint': base,
        })