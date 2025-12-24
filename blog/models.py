import logging
import re
from abc import abstractmethod

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from mdeditor.fields import MDTextField
from uuslug import slugify
from django.utils import timezone
from djangoblog.utils import cache_decorator, cache
from djangoblog.utils import get_current_site

logger = logging.getLogger(__name__)


class LinkShowType(models.TextChoices):
    I = ('i', _('index'))
    L = ('l', _('list'))
    P = ('p', _('post'))
    A = ('a', _('all'))
    S = ('s', _('slide'))


class BaseModel(models.Model):
    id = models.AutoField(primary_key=True)
    creation_time = models.DateTimeField(_('creation time'), default=now)
    last_modify_time = models.DateTimeField(_('modify time'), default=now)

    def save(self, *args, **kwargs):
        is_update_views = isinstance(
            self,
            Article) and 'update_fields' in kwargs and kwargs['update_fields'] == ['views']
        if is_update_views:
            Article.objects.filter(pk=self.pk).update(views=self.views)
        else:
            if 'slug' in self.__dict__:
                slug = getattr(
                    self, 'title') if 'title' in self.__dict__ else getattr(
                    self, 'name')
                setattr(self, 'slug', slugify(slug))
            super().save(*args, **kwargs)

    def get_full_url(self):
        site = get_current_site().domain
        url = "https://{site}{path}".format(site=site,
                                            path=self.get_absolute_url())
        return url

    class Meta:
        abstract = True

    @abstractmethod
    def get_absolute_url(self):
        pass


class Article(BaseModel):
    """文章"""
    STATUS_CHOICES = (
        ('d', _('Draft')),
        ('p', _('Published')),
    )
    COMMENT_STATUS = (
        ('o', _('Open')),
        ('c', _('Close')),
    )
    TYPE = (
        ('a', _('Article')),
        ('p', _('Page')),
    )
    title = models.CharField(_('title'), max_length=200, unique=True)
    body = MDTextField(_('body'))
    pub_time = models.DateTimeField(
        _('publish time'), blank=False, null=False, default=now)
    status = models.CharField(
        _('status'),
        max_length=1,
        choices=STATUS_CHOICES,
        default='p')
    comment_status = models.CharField(
        _('comment status'),
        max_length=1,
        choices=COMMENT_STATUS,
        default='o')
    type = models.CharField(_('type'), max_length=1, choices=TYPE, default='a')
    views = models.PositiveIntegerField(_('views'), default=0)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        blank=False,
        null=False,
        on_delete=models.CASCADE)
    article_order = models.IntegerField(
        _('order'), blank=False, null=False, default=0)
    show_toc = models.BooleanField(_('show toc'), blank=False, null=False, default=False)
    category = models.ForeignKey(
        'Category',
        verbose_name=_('category'),
        on_delete=models.CASCADE,
        blank=False,
        null=False)
    tags = models.ManyToManyField('Tag', verbose_name=_('tag'), blank=True)

    def body_to_string(self):
        return self.body

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-article_order', '-pub_time']
        verbose_name = _('article')
        verbose_name_plural = verbose_name
        get_latest_by = 'id'

    def get_absolute_url(self):
        return reverse('blog:detailbyid', kwargs={
            'article_id': self.id,
            'year': self.creation_time.year,
            'month': self.creation_time.month,
            'day': self.creation_time.day
        })

    @cache_decorator(60 * 60 * 10)
    def get_category_tree(self):
        tree = self.category.get_category_tree()
        names = list(map(lambda c: (c.name, c.get_absolute_url()), tree))

        return names

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def viewed(self):
        self.views += 1
        self.save(update_fields=['views'])

    def comment_list(self):
        cache_key = 'article_comments_{id}'.format(id=self.id)
        value = cache.get(cache_key)
        if value:
            logger.info('get article comments:{id}'.format(id=self.id))
            return value
        else:
            comments = self.comment_set.filter(is_enable=True).order_by('-id')
            cache.set(cache_key, comments, 60 * 100)
            logger.info('set article comments:{id}'.format(id=self.id))
            return comments

    def get_admin_url(self):
        info = (self._meta.app_label, self._meta.model_name)
        return reverse('admin:%s_%s_change' % info, args=(self.pk,))

    @cache_decorator(expiration=60 * 100)
    def next_article(self):
        # 下一篇
        return Article.objects.filter(
            id__gt=self.id, status='p').order_by('id').first()

    @cache_decorator(expiration=60 * 100)
    def prev_article(self):
        # 前一篇
        return Article.objects.filter(id__lt=self.id, status='p').first()

    def get_first_image_url(self):
        """
        Get the first image url from article.body.
        :return:
        """
        match = re.search(r'!\[.*?\]\((.+?)\)', self.body)
        if match:
            return match.group(1)
        return ""

    last_save_type = models.CharField(
        '最后保存类型',
        max_length=10,
        choices=[('auto', '自动'), ('manual', '手动')],
        default='manual'
    )

    # 在现有字段后添加自动保存相关字段
    last_save_type = models.CharField(
        '最后保存类型',
        max_length=10,
        choices=[('auto', '自动'), ('manual', '手动')],
        default='manual'
    )

    # ... 现有的方法 ...

    # 添加自动保存相关方法
    def get_latest_draft(self):
        """获取最新的草稿"""
        return self.drafts.order_by('-saved_at').first()

    def get_draft_count(self):
        """获取草稿数量"""
        return self.drafts.count()

    def save_draft(self, title=None, body=None, save_type='auto', author=None):
        """保存草稿到ArticleDraft"""
        # 获取最新版本号
        latest_draft = self.drafts.order_by('-version').first()
        next_version = (latest_draft.version + 1) if latest_draft else 1

        # 限制版本数量（最多5个自动保存版本）
        auto_drafts = self.drafts.filter(save_type='auto').order_by('-saved_at')
        if auto_drafts.count() >= 5:
            # 删除第5个之后的版本
            drafts_to_delete = auto_drafts[4:]
            for draft in drafts_to_delete:
                draft.delete()

        # 创建新草稿
        draft_data = {
            'article': self,
            'author': author or self.author,
            'title': title or self.title,
            'body': body or self.body,
            'save_type': save_type,
            'version': next_version,
            'status': self.status,
            'comment_status': self.comment_status,
            'article_type': self.type,
            'show_toc': self.show_toc,
            'article_order': self.article_order,
        }

        draft = ArticleDraft.objects.create(**draft_data)
        return draft

    def restore_from_draft(self, draft_id):
        """从指定草稿恢复"""
        try:
            draft = self.drafts.get(id=draft_id)
            # 恢复文章内容
            self.title = draft.title
            self.body = draft.body
            self.status = draft.status
            self.comment_status = draft.comment_status
            self.type = draft.article_type
            self.show_toc = draft.show_toc
            self.article_order = draft.article_order
            self.save()
            return True
        except ArticleDraft.DoesNotExist:
            return False

class Category(BaseModel):
    """文章分类"""
    name = models.CharField(_('category name'), max_length=30, unique=True)
    parent_category = models.ForeignKey(
        'self',
        verbose_name=_('parent category'),
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    slug = models.SlugField(default='no-slug', max_length=60, blank=True)
    index = models.IntegerField(default=0, verbose_name=_('index'))

    class Meta:
        ordering = ['-index']
        verbose_name = _('category')
        verbose_name_plural = verbose_name

    def get_absolute_url(self):
        return reverse(
            'blog:category_detail', kwargs={
                'category_name': self.slug})

    def __str__(self):
        return self.name

    @cache_decorator(60 * 60 * 10)
    def get_category_tree(self):
        """
        递归获得分类目录的父级
        :return:
        """
        categorys = []

        def parse(category):
            categorys.append(category)
            if category.parent_category:
                parse(category.parent_category)

        parse(self)
        return categorys

    @cache_decorator(60 * 60 * 10)
    def get_sub_categorys(self):
        """
        获得当前分类目录所有子集
        :return:
        """
        categorys = []
        all_categorys = Category.objects.all()

        def parse(category):
            if category not in categorys:
                categorys.append(category)
            childs = all_categorys.filter(parent_category=category)
            for child in childs:
                if category not in categorys:
                    categorys.append(child)
                parse(child)

        parse(self)
        return categorys


class Tag(BaseModel):
    """文章标签"""
    name = models.CharField(_('tag name'), max_length=30, unique=True)
    slug = models.SlugField(default='no-slug', max_length=60, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:tag_detail', kwargs={'tag_name': self.slug})

    @cache_decorator(60 * 60 * 10)
    def get_article_count(self):
        return Article.objects.filter(tags__name=self.name).distinct().count()

    class Meta:
        ordering = ['name']
        verbose_name = _('tag')
        verbose_name_plural = verbose_name


class Links(models.Model):
    """友情链接"""

    name = models.CharField(_('link name'), max_length=30, unique=True)
    link = models.URLField(_('link'))
    sequence = models.IntegerField(_('order'), unique=True)
    is_enable = models.BooleanField(
        _('is show'), default=True, blank=False, null=False)
    show_type = models.CharField(
        _('show type'),
        max_length=1,
        choices=LinkShowType.choices,
        default=LinkShowType.I)
    creation_time = models.DateTimeField(_('creation time'), default=now)
    last_mod_time = models.DateTimeField(_('modify time'), default=now)

    class Meta:
        ordering = ['sequence']
        verbose_name = _('link')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SideBar(models.Model):
    """侧边栏,可以展示一些html内容"""
    name = models.CharField(_('title'), max_length=100)
    content = models.TextField(_('content'))
    sequence = models.IntegerField(_('order'), unique=True)
    is_enable = models.BooleanField(_('is enable'), default=True)
    creation_time = models.DateTimeField(_('creation time'), default=now)
    last_mod_time = models.DateTimeField(_('modify time'), default=now)

    class Meta:
        ordering = ['sequence']
        verbose_name = _('sidebar')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class BlogSettings(models.Model):
    """blog的配置"""
    site_name = models.CharField(
        _('site name'),
        max_length=200,
        null=False,
        blank=False,
        default='')
    site_description = models.TextField(
        _('site description'),
        max_length=1000,
        null=False,
        blank=False,
        default='')
    site_seo_description = models.TextField(
        _('site seo description'), max_length=1000, null=False, blank=False, default='')
    site_keywords = models.TextField(
        _('site keywords'),
        max_length=1000,
        null=False,
        blank=False,
        default='')
    article_sub_length = models.IntegerField(_('article sub length'), default=300)
    sidebar_article_count = models.IntegerField(_('sidebar article count'), default=10)
    sidebar_comment_count = models.IntegerField(_('sidebar comment count'), default=5)
    article_comment_count = models.IntegerField(_('article comment count'), default=5)
    show_google_adsense = models.BooleanField(_('show adsense'), default=False)
    google_adsense_codes = models.TextField(
        _('adsense code'), max_length=2000, null=True, blank=True, default='')
    open_site_comment = models.BooleanField(_('open site comment'), default=True)
    global_header = models.TextField("公共头部", null=True, blank=True, default='')
    global_footer = models.TextField("公共尾部", null=True, blank=True, default='')
    beian_code = models.CharField(
        '备案号',
        max_length=2000,
        null=True,
        blank=True,
        default='')
    analytics_code = models.TextField(
        "网站统计代码",
        max_length=1000,
        null=False,
        blank=False,
        default='')
    show_gongan_code = models.BooleanField(
        '是否显示公安备案号', default=False, null=False)
    gongan_beiancode = models.TextField(
        '公安备案号',
        max_length=2000,
        null=True,
        blank=True,
        default='')
    comment_need_review = models.BooleanField(
        '评论是否需要审核', default=False, null=False)

    class Meta:
        verbose_name = _('Website configuration')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.site_name

    def clean(self):
        if BlogSettings.objects.exclude(id=self.id).count():
            raise ValidationError(_('There can only be one configuration'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from djangoblog.utils import cache
        cache.clear()


class ArticleDraft(models.Model):
    """文章草稿模型"""
    SAVE_TYPE_CHOICES = [
        ('auto', '自动保存'),
        ('manual', '手动保存'),
    ]

    article = models.ForeignKey(
        'Article',
        on_delete=models.CASCADE,
        related_name='drafts',
        null=True,
        blank=True,
        verbose_name='关联文章'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='作者'
    )

    # 草稿内容 - 与Article模型保持一致
    title = models.CharField(_('title'), max_length=200, default='', blank=True)
    body = MDTextField(_('body'), default='', blank=True)  # 改为MDTextField，与Article一致
    summary = models.TextField(_('summary'), default='', blank=True)  # 添加翻译

    # 元数据
    save_type = models.CharField(
        '保存类型',
        max_length=10,
        choices=SAVE_TYPE_CHOICES,
        default='auto'
    )
    version = models.IntegerField('版本号', default=1)
    saved_at = models.DateTimeField('保存时间', default=timezone.now)

    # 添加与原Article模型相同的字段，用于恢复时保持一致性
    status = models.CharField(
        _('status'),
        max_length=1,
        choices=Article.STATUS_CHOICES,  # 使用Article的选项
        default='d'
    )
    comment_status = models.CharField(
        _('comment status'),
        max_length=1,
        choices=Article.COMMENT_STATUS,
        default='o'
    )
    article_type = models.CharField(
        _('type'),
        max_length=1,
        choices=Article.TYPE,
        default='a'
    )
    show_toc = models.BooleanField(_('show toc'), default=False)
    article_order = models.IntegerField(_('order'), default=0)

    class Meta:
        verbose_name = '文章草稿'
        verbose_name_plural = verbose_name
        ordering = ['-saved_at']
        indexes = [
            models.Index(fields=['article', 'saved_at']),
            models.Index(fields=['author', 'saved_at']),
        ]

    def __str__(self):
        article_title = self.article.title if self.article else '新文章'
        return f"{article_title} - 版本{self.version} ({self.save_type})"

    def get_human_time(self):
        """获取人性化时间显示"""
        now = timezone.now()
        diff = now - self.saved_at

        if diff.days > 7:
            return self.saved_at.strftime('%Y-%m-%d')
        elif diff.days > 0:
            return f'{diff.days}天前'
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f'{hours}小时前'
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f'{minutes}分钟前'
        else:
            return '刚刚'

    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'summary': self.summary,
            'version': self.version,
            'save_type': self.save_type,
            'saved_at': self.saved_at.strftime('%Y-%m-%d %H:%M:%S'),
            'human_time': self.get_human_time(),
            'status': self.status,
            'comment_status': self.comment_status,
            'article_type': self.article_type,
            'show_toc': self.show_toc,
            'article_order': self.article_order,
        }