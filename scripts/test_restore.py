import os
import sys
import django
import requests
import pathlib

# ensure project root on sys.path
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoblog.settings')
django.setup()

from django.contrib.auth import get_user_model
from autosave.models import ArticleDraft
from blog.models import Article

User = get_user_model()
admin = User.objects.get(username='admin')

# get latest draft for admin
draft = ArticleDraft.objects.filter(user=admin).order_by('-id').first()
if not draft:
    print('No draft found for admin')
    sys.exit(1)

print('Found draft id=', draft.id, 'article=', draft.article_id)

s = requests.Session()
# login to admin
login_get = s.get('http://127.0.0.1:8000/admin/login/?next=/admin/')
csrftoken = s.cookies.get('csrftoken')
login_data = {'username': 'admin', 'password': 'admin', 'csrfmiddlewaretoken': csrftoken, 'next': '/admin/'}
headers = {'Referer': 'http://127.0.0.1:8000/admin/login/?next=/admin/'}
resp = s.post('http://127.0.0.1:8000/admin/login/?next=/admin/', data=login_data, headers=headers)
print('Admin login status:', resp.status_code)

# call restore endpoint
restore_url = f'http://127.0.0.1:8000/api/autosave/restore/{draft.id}/'
resp2 = s.post(restore_url)
print('Restore POST status:', resp2.status_code, 'response:', resp2.text)

# reload article from DB
if draft.article_id:
    article = Article.objects.get(pk=draft.article_id)
    print('Article after restore: id=', article.id, 'title=', article.title)
    # print small preview of body
    print('Body preview:', article.body[:200])

# list drafts for article
drafts = list(ArticleDraft.objects.filter(article_id=draft.article_id).order_by('-version').values('id','version','save_type','title'))
print('Drafts for article:', drafts)
