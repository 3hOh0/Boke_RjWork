from django.urls import path
from django.views.decorators.cache import cache_page

from . import views

app_name = "blog"
urlpatterns = [
    # ==================== 主要页面路由 ====================
    # 首页
    path(
        r'',
        views.IndexView.as_view(),
        name='index'),
    path(
        r'page/<int:page>/',
        views.IndexView.as_view(),
        name='index_page'),

    # 文章详情页
    path(
        r'article/<int:year>/<int:month>/<int:day>/<int:article_id>.html',
        views.ArticleDetailView.as_view(),
        name='detailbyid'),

    # 分类目录页
    path(
        r'category/<slug:category_name>.html',
        views.CategoryDetailView.as_view(),
        name='category_detail'),
    path(
        r'category/<slug:category_name>/<int:page>.html',
        views.CategoryDetailView.as_view(),
        name='category_detail_page'),

    # 作者文章页
    path(
        r'author/<author_name>.html',
        views.AuthorDetailView.as_view(),
        name='author_detail'),
    path(
        r'author/<author_name>/<int:page>.html',
        views.AuthorDetailView.as_view(),
        name='author_detail_page'),

    # 标签文章页
    path(
        r'tag/<slug:tag_name>.html',
        views.TagDetailView.as_view(),
        name='tag_detail'),
    path(
        r'tag/<slug:tag_name>/<int:page>.html',
        views.TagDetailView.as_view(),
        name='tag_detail_page'),

    # 文章归档页
    path(
        'archives.html',
        cache_page(
            60 * 60)(
            views.ArchivesView.as_view()),
        name='archives'),

    # 友情链接页
    path(
        'links.html',
        views.LinkListView.as_view(),
        name='links'),

    # 文件上传
    path(
        r'upload',
        views.fileupload,
        name='upload'),

    # 清理缓存
    path(
        r'clean',
        views.clean_cache_view,
        name='clean'),

    # ==================== 自动保存功能路由 ====================
    # 保存草稿（新文章和已有文章）
    path(
        r'api/autosave/draft/',
        views.autosave_draft,
        name='autosave_draft'),
    path(
        r'api/autosave/draft/<int:article_id>/',
        views.autosave_draft,
        name='autosave_draft_update'),

    # 获取草稿版本列表
    path(
        r'api/autosave/versions/<int:article_id>/',
        views.get_draft_versions,
        name='get_draft_versions'),

    # 恢复指定版本
    path(
        r'api/autosave/restore/<int:draft_id>/',
        views.restore_version,
        name='restore_version'),

    # 发布文章
    path(
        r'api/autosave/publish/<int:article_id>/',
        views.publish_article,
        name='publish_article'),

    # 获取草稿状态
    path(
        r'api/autosave/status/<int:article_id>/',
        views.get_draft_status,
        name='get_draft_status'),

    # 获取用户的所有草稿文章
    path(
        r'api/autosave/drafts/',
        views.get_article_drafts,
        name='get_article_drafts'),
]