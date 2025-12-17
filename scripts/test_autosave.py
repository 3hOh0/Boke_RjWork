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
from blog.models import Category, Article

User = get_user_model()
admin = User.objects.get(username='admin')

cat = Category.objects.first()
if not cat:
    cat = Category.objects.create(name='TestCategory', slug='test-category', index=0)

# ensure unique title
base_title = 'Test Autosave'
count = 1
while Article.objects.filter(title=base_title if count == 1 else base_title + str(count)).exists():
    count += 1

title = base_title if count == 1 else base_title + str(count)
article = Article.objects.create(title=title, body='Initial body for autosave testing', author=admin, category=cat, article_order=0)
print('Created article id=', article.pk)

# login via requests session to admin
s = requests.Session()
login_get = s.get('http://127.0.0.1:8000/admin/login/?next=/admin/')
csrftoken = s.cookies.get('csrftoken')
login_data = {'username': 'admin', 'password': 'admin', 'csrfmiddlewaretoken': csrftoken, 'next': '/admin/'}
headers = {'Referer': 'http://127.0.0.1:8000/admin/login/?next=/admin/'}
resp = s.post('http://127.0.0.1:8000/admin/login/?next=/admin/', data=login_data, headers=headers)
print('Admin login status:', resp.status_code)

# post autosave
payload = {'article_id': article.pk, 'title': 'Draft via script', 'content': 'Draft content from automated test', 'version': 1}
resp2 = s.post('http://127.0.0.1:8000/autosave/', json=payload)
print('Autosave POST status:', resp2.status_code, 'response:', resp2.text)

from autosave.models import ArticleDraft

drafts = list(ArticleDraft.objects.filter(user=admin).values('id', 'article', 'title', 'version', 'updated_at'))
print('Drafts for admin:', drafts)
