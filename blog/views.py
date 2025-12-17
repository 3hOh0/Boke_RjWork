import logging
import os
import uuid
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from haystack.views import SearchView

from blog.models import Article, Category, LinkShowType, Links, Tag
try:
    from autosave.models import ArticleDraft
except Exception:
    ArticleDraft = None
from comments.forms import CommentForm
from djangoblog.plugin_manage import hooks
from djangoblog.plugin_manage.hook_constants import ARTICLE_CONTENT_HOOK_NAME
from djangoblog.utils import cache, get_blog_setting, get_sha256

logger = logging.getLogger(__name__)


class ArticleListView(ListView):
    # template_name属性用于指定使用哪个模板进行渲染
    template_name = 'blog/article_index.html'

    # context_object_name属性用于给上下文变量取名（在模板中使用该名字）
    context_object_name = 'article_list'

    # 页面类型，分类目录或标签列表等
    page_type = ''
    paginate_by = settings.PAGINATE_BY
    page_kwarg = 'page'
    link_type = LinkShowType.L

    def get_view_cache_key(self):
        return self.request.get['pages']

    @property
    def page_number(self):
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(
            page_kwarg) or self.request.GET.get(page_kwarg) or 1
        return page

    def get_queryset_cache_key(self):
        """
        子类重写.获得queryset的缓存key
        """
        raise NotImplementedError()

    def get_queryset_data(self):
        """
        子类重写.获取queryset的数据
        """
        raise NotImplementedError()

    def get_queryset_from_cache(self, cache_key):
        '''
        缓存页面数据
        :param cache_key: 缓存key
        :return:
        '''
        value = cache.get(cache_key)
        if value:
            logger.info('get view cache.key:{key}'.format(key=cache_key))
            return value
        else:
            article_list = self.get_queryset_data()
            cache.set(cache_key, article_list)
            logger.info('set view cache.key:{key}'.format(key=cache_key))
            return article_list

    def get_queryset(self):
        '''
        重写默认，从缓存获取数据
        :return:
        '''
        key = self.get_queryset_cache_key()
        value = self.get_queryset_from_cache(key)
        return value

    def get_context_data(self, **kwargs):
        kwargs['linktype'] = self.link_type
        return super(ArticleListView, self).get_context_data(**kwargs)


class IndexView(ArticleListView):
    '''
    首页
    '''
    # 友情链接类型
    link_type = LinkShowType.I

    def get_queryset_data(self):
        article_list = Article.objects.filter(type='a', status='p')
        return article_list

    def get_queryset_cache_key(self):
        cache_key = 'index_{page}'.format(page=self.page_number)
        return cache_key


class ArticleDetailView(DetailView):
    '''
    文章详情页面
    '''
    template_name = 'blog/article_detail.html'
    model = Article
    pk_url_kwarg = 'article_id'
    context_object_name = "article"

    def get_context_data(self, **kwargs):
        comment_form = CommentForm()

        article_comments = self.object.comment_list()
        parent_comments = article_comments.filter(parent_comment=None)
        blog_setting = get_blog_setting()
        paginator = Paginator(parent_comments, blog_setting.article_comment_count)
        page = self.request.GET.get('comment_page', '1')
        if not page.isnumeric():
            page = 1
        else:
            page = int(page)
            if page < 1:
                page = 1
            if page > paginator.num_pages:
                page = paginator.num_pages

        p_comments = paginator.page(page)
        next_page = p_comments.next_page_number() if p_comments.has_next() else None
        prev_page = p_comments.previous_page_number() if p_comments.has_previous() else None

        if next_page:
            kwargs[
                'comment_next_page_url'] = self.object.get_absolute_url() + f'?comment_page={next_page}#commentlist-container'
        if prev_page:
            kwargs[
                'comment_prev_page_url'] = self.object.get_absolute_url() + f'?comment_page={prev_page}#commentlist-container'
        kwargs['form'] = comment_form
        kwargs['article_comments'] = article_comments
        kwargs['p_comments'] = p_comments
        kwargs['comment_count'] = len(
            article_comments) if article_comments else 0

        kwargs['next_article'] = self.object.next_article
        kwargs['prev_article'] = self.object.prev_article

        context = super(ArticleDetailView, self).get_context_data(**kwargs)
        article = self.object
        
        # 触发文章详情加载钩子，让插件可以添加额外的上下文数据
        from djangoblog.plugin_manage.hook_constants import ARTICLE_DETAIL_LOAD
        hooks.run_action(ARTICLE_DETAIL_LOAD, article=article, context=context, request=self.request)
        
        # Action Hook, 通知插件"文章详情已获取"
        hooks.run_action('after_article_body_get', article=article, request=self.request)
        return context


class CategoryDetailView(ArticleListView):
    '''
    分类目录列表
    '''
    page_type = "分类目录归档"

    def get_queryset_data(self):
        slug = self.kwargs['category_name']
        category = get_object_or_404(Category, slug=slug)

        categoryname = category.name
        self.categoryname = categoryname
        categorynames = list(
            map(lambda c: c.name, category.get_sub_categorys()))
        article_list = Article.objects.filter(
            category__name__in=categorynames, status='p')
        return article_list

    def get_queryset_cache_key(self):
        slug = self.kwargs['category_name']
        category = get_object_or_404(Category, slug=slug)
        categoryname = category.name
        self.categoryname = categoryname
        cache_key = 'category_list_{categoryname}_{page}'.format(
            categoryname=categoryname, page=self.page_number)
        return cache_key

    def get_context_data(self, **kwargs):

        categoryname = self.categoryname
        try:
            categoryname = categoryname.split('/')[-1]
        except BaseException:
            pass
        kwargs['page_type'] = CategoryDetailView.page_type
        kwargs['tag_name'] = categoryname
        return super(CategoryDetailView, self).get_context_data(**kwargs)


class AuthorDetailView(ArticleListView):
    '''
    作者详情页
    '''
    page_type = '作者文章归档'

    def get_queryset_cache_key(self):
        from uuslug import slugify
        author_name = slugify(self.kwargs['author_name'])
        cache_key = 'author_{author_name}_{page}'.format(
            author_name=author_name, page=self.page_number)
        return cache_key

    def get_queryset_data(self):
        author_name = self.kwargs['author_name']
        article_list = Article.objects.filter(
            author__username=author_name, type='a', status='p')
        return article_list

    def get_context_data(self, **kwargs):
        author_name = self.kwargs['author_name']
        kwargs['page_type'] = AuthorDetailView.page_type
        kwargs['tag_name'] = author_name
        return super(AuthorDetailView, self).get_context_data(**kwargs)


class TagDetailView(ArticleListView):
    '''
    标签列表页面
    '''
    page_type = '分类标签归档'

    def get_queryset_data(self):
        slug = self.kwargs['tag_name']
        tag = get_object_or_404(Tag, slug=slug)
        tag_name = tag.name
        self.name = tag_name
        article_list = Article.objects.filter(
            tags__name=tag_name, type='a', status='p')
        return article_list

    def get_queryset_cache_key(self):
        slug = self.kwargs['tag_name']
        tag = get_object_or_404(Tag, slug=slug)
        tag_name = tag.name
        self.name = tag_name
        cache_key = 'tag_{tag_name}_{page}'.format(
            tag_name=tag_name, page=self.page_number)
        return cache_key

    def get_context_data(self, **kwargs):
        # tag_name = self.kwargs['tag_name']
        tag_name = self.name
        kwargs['page_type'] = TagDetailView.page_type
        kwargs['tag_name'] = tag_name
        return super(TagDetailView, self).get_context_data(**kwargs)


class ArchivesView(ArticleListView):
    '''
    文章归档页面
    '''
    page_type = '文章归档'
    paginate_by = None
    page_kwarg = None
    template_name = 'blog/article_archives.html'

    def get_queryset_data(self):
        return Article.objects.filter(status='p').all()

    def get_queryset_cache_key(self):
        cache_key = 'archives'
        return cache_key


class LinkListView(ListView):
    model = Links
    template_name = 'blog/links_list.html'

    def get_queryset(self):
        return Links.objects.filter(is_enable=True)


class EsSearchView(SearchView):
    def get_context(self):
        paginator, page = self.build_page()
        context = {
            "query": self.query,
            "form": self.form,
            "page": page,
            "paginator": paginator,
            "suggestion": None,
        }
        if hasattr(self.results, "query") and self.results.query.backend.include_spelling:
            context["suggestion"] = self.results.query.get_spelling_suggestion()
        context.update(self.extra_context())

        return context


@csrf_exempt
def fileupload(request):
    """
    该方法需自己写调用端来上传图片，该方法仅提供图床功能
    :param request:
    :return:
    """
    if request.method == 'POST':
        sign = request.GET.get('sign', None)
        if not sign:
            return HttpResponseForbidden()
        if not sign == get_sha256(get_sha256(settings.SECRET_KEY)):
            return HttpResponseForbidden()
        response = []
        for filename in request.FILES:
            timestr = timezone.now().strftime('%Y/%m/%d')
            imgextensions = ['jpg', 'png', 'jpeg', 'bmp']
            fname = u''.join(str(filename))
            isimage = len([i for i in imgextensions if fname.find(i) >= 0]) > 0
            base_dir = os.path.join(settings.STATICFILES, "files" if not isimage else "image", timestr)
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)
            savepath = os.path.normpath(os.path.join(base_dir, f"{uuid.uuid4().hex}{os.path.splitext(filename)[-1]}"))
            if not savepath.startswith(base_dir):
                return HttpResponse("only for post")
            with open(savepath, 'wb+') as wfile:
                for chunk in request.FILES[filename].chunks():
                    wfile.write(chunk)
            if isimage:
                from PIL import Image
                image = Image.open(savepath)
                image.save(savepath, quality=20, optimize=True)
            url = static(savepath)
            response.append(url)
        return HttpResponse(response)

    else:
        return HttpResponse("only for post")


def page_not_found_view(
        request,
        exception,
        template_name='blog/error_page.html'):
    if exception:
        logger.error(exception)
    url = request.get_full_path()
    return render(request,
                  template_name,
                  {'message': _('Sorry, the page you requested is not found, please click the home page to see other?'),
                   'statuscode': '404'},
                  status=404)


def server_error_view(request, template_name='blog/error_page.html'):
    return render(request,
                  template_name,
                  {'message': _('Sorry, the server is busy, please click the home page to see other?'),
                   'statuscode': '500'},
                  status=500)


def permission_denied_view(
        request,
        exception,
        template_name='blog/error_page.html'):
    if exception:
        logger.error(exception)
    return render(
        request, template_name, {
            'message': _('Sorry, you do not have permission to access this page?'),
            'statuscode': '403'}, status=403)


def clean_cache_view(request):
    cache.clear()
    return HttpResponse('ok')


# ======================= 自动保存功能相关视图 =======================

@login_required
@require_POST
@csrf_exempt
def autosave_draft(request, article_id=None):
    """
    自动保存草稿API
    POST /api/autosave/draft/              # 新文章
    POST /api/autosave/draft/<article_id>/ # 已有文章
    """
    try:
        data = json.loads(request.body)
        title = data.get('title', '')
        body = data.get('body', '')  # 注意：原Article模型使用body字段
        save_type = data.get('save_type', 'auto')

        # 获取其他可选字段
        category_id = data.get('category_id')
        tags = data.get('tags', [])
        show_toc = data.get('show_toc', False)
        article_order = data.get('article_order', 0)
        comment_status = data.get('comment_status', 'o')
        article_type = data.get('type', 'a')  # 注意：原字段名是type

        with transaction.atomic():
            if article_id:
                # 更新已有文章
                article = get_object_or_404(Article, id=article_id, author=request.user)

                # 更新文章字段
                if title:
                    article.title = title
                if body:
                    article.body = body

                # 更新分类
                if category_id:
                    try:
                        category = Category.objects.get(id=category_id)
                        article.category = category
                    except Category.DoesNotExist:
                        pass

                # 更新标签
                if tags and isinstance(tags, list):
                    tag_objects = []
                    for tag_name in tags:
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        tag_objects.append(tag)
                    article.tags.set(tag_objects)

                article.show_toc = show_toc
                article.article_order = article_order
                article.comment_status = comment_status
                article.type = article_type
                article.status = 'd'  # 确保是草稿状态
                article.save()

            else:
                # 创建新文章（草稿）
                category = None
                if category_id:
                    try:
                        category = Category.objects.get(id=category_id)
                    except Category.DoesNotExist:
                        pass

                article = Article.objects.create(
                    title=title or '未命名文章',
                    body=body,
                    author=request.user,
                    status='d',  # 草稿状态
                    comment_status=comment_status,
                    type=article_type,
                    show_toc=show_toc,
                    article_order=article_order,
                    category=category if category else Category.objects.first()  # 默认分类
                )

                # 设置标签
                if tags and isinstance(tags, list):
                    for tag_name in tags:
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        article.tags.add(tag)

            # 获取最新版本号
            latest_draft = article.drafts.order_by('-version').first()
            next_version = (latest_draft.version + 1) if latest_draft else 1

            # 限制版本数量（最多5个自动保存版本）
            auto_drafts = article.drafts.filter(save_type='auto').order_by('-saved_at')
            if auto_drafts.count() >= 5:
                # 删除第5个之后的版本
                drafts_to_delete = auto_drafts[4:]
                for draft in drafts_to_delete:
                    draft.delete()

            # 创建新草稿
            draft_data = {
                'article': article,
                'user': request.user,
                'title': title or article.title,
                'body': body or article.body,
                'save_type': save_type,
                'version': next_version,
                'status': article.status,
                'comment_status': article.comment_status,
                'article_type': article.type,
                'show_toc': article.show_toc,
                'article_order': article.article_order,
            }

            draft = ArticleDraft.objects.create(**draft_data)

        return JsonResponse({
            'success': True,
            'message': '草稿已保存',
            'data': {
                'article_id': article.id,
                'draft_id': draft.id,
                'version': draft.version,
                'saved_at': draft.saved_at.strftime('%Y-%m-%d %H:%M:%S'),
                'human_time': draft.get_human_time(),
                'save_type': save_type,
                'is_draft': article.status == 'd',
                'title': article.title,
            }
        })

    except Exception as e:
        logger.error(f"自动保存失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }, status=500)


@login_required
@require_GET
def get_draft_versions(request, article_id):
    """
    获取草稿版本列表
    GET /api/autosave/versions/<article_id>/
    """
    try:
        article = get_object_or_404(Article, id=article_id, author=request.user)

        # 获取所有版本（最近10个）
        drafts = article.drafts.order_by('-saved_at')[:10]

        versions = []
        for draft in drafts:
            versions.append({
                'id': draft.id,
                'title': draft.title,
                'body_preview': draft.body[:200] + '...' if len(draft.body) > 200 else draft.body,
                'version': draft.version,
                'save_type': draft.save_type,
                'saved_at': draft.saved_at.strftime('%Y-%m-%d %H:%M:%S'),
                'human_time': draft.get_human_time(),
                'status': draft.status,
                'status_display': dict(Article.STATUS_CHOICES).get(draft.status, '未知'),
            })

        return JsonResponse({
            'success': True,
            'versions': versions,
            'article_title': article.title,
            'current_version': article.drafts.order_by('-version').first().version if article.drafts.exists() else 0,
            'is_draft': article.status == 'd',
        })

    except Exception as e:
        logger.error(f"获取版本历史失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }, status=500)


@login_required
@require_POST
@csrf_exempt
def restore_version(request, draft_id):
    """
    恢复指定版本
    POST /api/autosave/restore/<draft_id>/
    """
    try:
        draft = get_object_or_404(ArticleDraft, id=draft_id, user=request.user)
        article = draft.article

        with transaction.atomic():
            # 恢复文章内容
            article.title = draft.title
            article.body = draft.body
            article.status = draft.status
            article.comment_status = draft.comment_status
            article.type = draft.article_type
            article.show_toc = draft.show_toc
            article.article_order = draft.article_order
            article.save()

            # 创建恢复记录
            latest_draft = article.drafts.order_by('-version').first()
            next_version = (latest_draft.version + 1) if latest_draft else 1

            restore_draft = ArticleDraft.objects.create(
                article=article,
                user=request.user,
                title=draft.title,
                body=draft.body,
                save_type='manual',
                version=next_version,
                status=draft.status,
                comment_status=draft.comment_status,
                article_type=draft.article_type,
                show_toc=draft.show_toc,
                article_order=draft.article_order,
            )

        return JsonResponse({
            'success': True,
            'message': '已恢复到指定版本',
            'data': {
                'title': draft.title,
                'body': draft.body,
                'version': restore_draft.version,
                'status': draft.status,
            }
        })

    except Exception as e:
        logger.error(f"恢复版本失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'恢复失败: {str(e)}'
        }, status=500)


@login_required
@require_POST
@csrf_exempt
def publish_article(request, article_id):
    """
    发布文章（将状态改为已发布）
    POST /api/autosave/publish/<article_id>/
    """
    try:
        article = get_object_or_404(Article, id=article_id, author=request.user)

        # 检查是否有内容
        if not article.title.strip() or not article.body.strip():
            return JsonResponse({
                'success': False,
                'message': '标题和内容不能为空'
            }, status=400)

        # 更新状态为已发布
        article.status = 'p'
        article.pub_time = timezone.now()
        article.save()

        # 清除缓存（如果使用了缓存）
        try:
            from djangoblog.utils import cache
            cache.clear()
        except:
            pass

        return JsonResponse({
            'success': True,
            'message': '文章已发布',
            'data': {
                'article_id': article.id,
                'title': article.title,
                'status': article.status,
                'pub_time': article.pub_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
        })

    except Exception as e:
        logger.error(f"发布文章失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'发布失败: {str(e)}'
        }, status=500)


@login_required
@require_GET
def get_draft_status(request, article_id):
    """
    获取草稿状态
    GET /api/autosave/status/<article_id>/
    """
    try:
        article = get_object_or_404(Article, id=article_id, author=request.user)

        latest_draft = article.drafts.order_by('-saved_at').first()

        data = {
            'article_id': article.id,
            'title': article.title,
            'status': article.status,
            'last_modify_time': article.last_modify_time.strftime('%Y-%m-%d %H:%M:%S'),
            'is_draft': article.status == 'd',
            'draft_count': article.drafts.count(),
            'latest_draft': None,
        }

        if latest_draft:
            data['latest_draft'] = {
                'id': latest_draft.id,
                'title': latest_draft.title,
                'version': latest_draft.version,
                'save_type': latest_draft.save_type,
                'saved_at': latest_draft.saved_at.strftime('%Y-%m-%d %H:%M:%S'),
                'human_time': latest_draft.get_human_time(),
            }

        return JsonResponse({
            'success': True,
            'data': data
        })

    except Exception as e:
        logger.error(f"获取草稿状态失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }, status=500)


@login_required
@require_GET
def get_article_drafts(request):
    """
    获取用户的所有草稿文章
    GET /api/autosave/drafts/
    """
    try:
        # 获取用户的草稿文章
        drafts = Article.objects.filter(author=request.user, status='d').order_by('-last_modify_time')

        draft_list = []
        for article in drafts:
            latest_draft = article.drafts.order_by('-saved_at').first()

            draft_list.append({
                'id': article.id,
                'title': article.title,
                'body_preview': article.body[:100] + '...' if len(article.body) > 100 else article.body,
                'last_modify_time': article.last_modify_time.strftime('%Y-%m-%d %H:%M'),
                'draft_count': article.drafts.count(),
                'latest_draft_time': latest_draft.saved_at.strftime('%Y-%m-%d %H:%M') if latest_draft else None,
            })

        return JsonResponse({
            'success': True,
            'drafts': draft_list,
            'count': len(draft_list)
        })

    except Exception as e:
        logger.error(f"获取草稿列表失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }, status=500)