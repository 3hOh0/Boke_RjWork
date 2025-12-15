"""
Forms used by the interaction app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from blog.models import Article
from .models import FavoriteFolder, FavoriteItem


class FavoriteFolderForm(forms.ModelForm):
    class Meta:
        model = FavoriteFolder
        fields = ['name', 'description', 'is_public', 'allow_duplicates', 'tags', 'pinned', 'sort_order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'name': '收藏夹名称',
            'description': '描述',
            'is_public': '是否公开',
            'allow_duplicates': '允许重复文章',
            'tags': '标签',
            'pinned': '置顶',
            'sort_order': '排序值',
        }
        help_texts = {
            'allow_duplicates': '允许同一篇文章重复保存到该收藏夹',
            'tags': '以英文逗号分隔标签，例如：django,python,后端',
            'sort_order': '数字越小越靠前；置顶优先',
        }


class FavoriteFolderUpdateForm(FavoriteFolderForm):
    regenerate_share_token = forms.BooleanField(
        required=False,
        initial=False,
        label='重新生成分享链接',
        help_text='勾选后将刷新公开分享链接')

    class Meta(FavoriteFolderForm.Meta):
        fields = FavoriteFolderForm.Meta.fields + ['regenerate_share_token']


class FavoriteItemForm(forms.ModelForm):
    article = forms.ModelChoiceField(
        queryset=Article.objects.filter(status='p'),
        label=_('article'),
        help_text=_('select the article you want to save')
    )

    class Meta:
        model = FavoriteItem
        fields = ['article', 'note']


class QuickFavoriteForm(forms.Form):
    folder = forms.ModelChoiceField(
        queryset=FavoriteFolder.objects.none(),
        label='选择收藏夹',
        required=False,
    )
    folder_name = forms.CharField(
        label='新建收藏夹名称',
        max_length=80,
        required=False)
    folder_description = forms.CharField(
        label='新建收藏夹描述',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}))
    folder_is_public = forms.BooleanField(
        label='公开收藏夹',
        required=False,
        initial=False)
    allow_duplicates = forms.BooleanField(
        label='允许重复文章',
        required=False,
        initial=False)
    note = forms.CharField(
        label='备注',
        required=False,
        max_length=120)
    article_id = forms.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        self.actor = kwargs.pop('actor', None)
        super().__init__(*args, **kwargs)
        if self.actor is not None:
            self.fields['folder'].queryset = self.actor.favorite_folders.all()

    def clean(self):
        cleaned = super().clean()
        folder = cleaned.get('folder')
        if folder and self.actor and folder.owner != self.actor:
            raise forms.ValidationError(_('invalid folder selection'))
        if not folder and not cleaned.get('folder_name'):
            raise forms.ValidationError(_('please choose or create a folder'))
        return cleaned

