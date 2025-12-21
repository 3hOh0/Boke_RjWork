from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from . import utils

@staff_member_required
def index(request):
    # 默认重定向到概览页面
    return render(request, "dashboard/pages/overview.html")

@staff_member_required
def overview(request):
    """概览页面 - 关键指标总览"""
    return render(request, "dashboard/pages/overview.html")

@staff_member_required
def content_analysis(request):
    """内容分析页面 - 文章、分类、标签统计"""
    return render(request, "dashboard/pages/content.html")

@staff_member_required
def engagement_analysis(request):
    """用户互动页面 - 点赞、评论、收藏趋势"""
    return render(request, "dashboard/pages/engagement.html")

@staff_member_required
def user_statistics(request):
    """用户统计页面 - 热门文章和作者排行"""
    return render(request, "dashboard/pages/users.html")

@staff_member_required
def recent_activities(request):
    """最近活动页面 - 实时活动流"""
    return render(request, "dashboard/pages/activities.html")

@staff_member_required
def metrics_api(request):
    return JsonResponse(utils.get_metrics(), safe=False)

@staff_member_required
def trend_api(request):
    days = int(request.GET.get("range", "7"))
    return JsonResponse(utils.get_trend(days), safe=False)

@staff_member_required
def top_api(request):
    limit = int(request.GET.get("limit", "10"))
    return JsonResponse(utils.get_top_articles(limit), safe=False)

@staff_member_required
def top_authors_api(request):
    limit = int(request.GET.get("limit", "10"))
    return JsonResponse(utils.get_top_authors(limit), safe=False)

@staff_member_required
def category_distribution_api(request):
    return JsonResponse(utils.get_category_distribution(), safe=False)

@staff_member_required
def like_trend_api(request):
    days = int(request.GET.get("range", "7"))
    return JsonResponse(utils.get_like_trend(days), safe=False)

@staff_member_required
def tag_distribution_api(request):
    limit = int(request.GET.get("limit", "10"))
    return JsonResponse(utils.get_tag_distribution(limit), safe=False)

@staff_member_required
def favorite_trend_api(request):
    days = int(request.GET.get("range", "7"))
    return JsonResponse(utils.get_favorite_trend(days), safe=False)

@staff_member_required
def comment_trend_api(request):
    days = int(request.GET.get("range", "7"))
    return JsonResponse(utils.get_comment_trend(days), safe=False)

@staff_member_required
def recent_activities_api(request):
    limit = int(request.GET.get("limit", "20"))
    return JsonResponse(utils.get_recent_activities(limit), safe=False)