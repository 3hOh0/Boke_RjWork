from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    # 分页式仪表盘 - 独立页面
    path("overview/", views.overview, name="overview"),
    path("content/", views.content_analysis, name="content"),
    path("engagement/", views.engagement_analysis, name="engagement"),
    path("users/", views.user_statistics, name="users"),
    path("activities/", views.recent_activities, name="activities"),
    # API端点
    path("api/metrics/", views.metrics_api, name="metrics_api"),
    path("api/trend/", views.trend_api, name="trend_api"),
    path("api/top/", views.top_api, name="top_api"),
    path("api/top_authors/", views.top_authors_api, name="top_authors_api"),
    path("api/category_distribution/", views.category_distribution_api, name="category_distribution_api"),
    path("api/like_trend/", views.like_trend_api, name="like_trend_api"),
    path("api/tag_distribution/", views.tag_distribution_api, name="tag_distribution_api"),
    path("api/favorite_trend/", views.favorite_trend_api, name="favorite_trend_api"),
    path("api/comment_trend/", views.comment_trend_api, name="comment_trend_api"),
    path("api/recent_activities/", views.recent_activities_api, name="recent_activities_api"),
]