from django.urls import path
from . import views

app_name = 'autosave'

urlpatterns = [
    path('', views.save_autosave, name='save'),
    path('versions/', views.list_versions, name='versions'),
]
