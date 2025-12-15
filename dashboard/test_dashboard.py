"""
Dashboard功能测试脚本

使用方法:
    python manage.py shell < dashboard/test_dashboard.py
    
或者在Django shell中:
    python manage.py shell
    >>> exec(open('dashboard/test_dashboard.py').read())
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from blog.models import Article, Category, Tag
from comments.models import Comment
from interaction.models import Like, FavoriteItem, FavoriteFolder, InteractionActor
from dashboard import utils
import json

User = get_user_model()

def test_dashboard_access():
    """测试仪表盘访问权限"""
    print("\n=== 测试1: 仪表盘访问权限 ===")
    client = Client()
    
    # 创建测试用户
    admin_user = User.objects.create_superuser(
        username='test_admin',
        email='admin@test.com',
        password='testpass123'
    )
    normal_user = User.objects.create_user(
        username='test_user',
        email='user@test.com',
        password='testpass123'
    )
    
    # 测试未登录访问
    response = client.get('/dashboard/')
    print(f"未登录访问: {response.status_code} (期望: 302重定向)")
    
    # 测试普通用户访问
    client.login(username='test_user', password='testpass123')
    response = client.get('/dashboard/')
    print(f"普通用户访问: {response.status_code} (期望: 302重定向)")
    client.logout()
    
    # 测试管理员访问
    client.login(username='test_admin', password='testpass123')
    response = client.get('/dashboard/')
    print(f"管理员访问: {response.status_code} (期望: 200成功)")
    
    print("✓ 权限测试完成\n")
    return admin_user, normal_user

def test_metrics_api():
    """测试关键指标API"""
    print("=== 测试2: 关键指标API ===")
    
    try:
        metrics = utils.get_metrics()
        print(f"文章总数: {metrics.get('article_total', 0)}")
        print(f"已发布文章: {metrics.get('article_published', 0)}")
        print(f"草稿数: {metrics.get('article_draft', 0)}")
        print(f"总浏览量: {metrics.get('pv_total', 0)}")
        print(f"评论总数: {metrics.get('comment_total', 0)}")
        print(f"点赞总数: {metrics.get('like_total', 0)}")
        print(f"收藏总数: {metrics.get('favorite_total', 0)}")
        print(f"用户总数: {metrics.get('user_total', 0)}")
        print(f"活跃用户: {metrics.get('active_users', 0)}")
        print(f"标签总数: {metrics.get('tag_total', 0)}")
        print(f"分类总数: {metrics.get('category_total', 0)}")
        print("✓ 指标API测试完成\n")
        return True
    except Exception as e:
        print(f"✗ 指标API测试失败: {str(e)}\n")
        return False

def test_trend_api():
    """测试趋势分析API"""
    print("=== 测试3: 趋势分析API ===")
    
    try:
        # 文章发布趋势
        trend = utils.get_trend(days=7)
        print(f"文章发布趋势(7天): {len(trend)} 条记录")
        
        # 点赞趋势
        like_trend = utils.get_like_trend(days=7)
        print(f"点赞趋势(7天): {len(like_trend)} 条记录")
        
        # 收藏趋势
        favorite_trend = utils.get_favorite_trend(days=7)
        print(f"收藏趋势(7天): {len(favorite_trend)} 条记录")
        
        # 评论趋势
        comment_trend = utils.get_comment_trend(days=7)
        print(f"评论趋势(7天): {len(comment_trend)} 条记录")
        
        print("✓ 趋势API测试完成\n")
        return True
    except Exception as e:
        print(f"✗ 趋势API测试失败: {str(e)}\n")
        return False

def test_distribution_api():
    """测试分布统计API"""
    print("=== 测试4: 分布统计API ===")
    
    try:
        # 分类分布
        category_dist = utils.get_category_distribution()
        print(f"分类分布: {len(category_dist)} 个分类")
        for cat in category_dist[:3]:
            print(f"  - {cat['name']}: {cat['article_count']} 篇文章")
        
        # 标签分布
        tag_dist = utils.get_tag_distribution(limit=10)
        print(f"标签分布(TOP10): {len(tag_dist)} 个标签")
        for tag in tag_dist[:3]:
            print(f"  - {tag['name']}: {tag['article_count']} 篇文章")
        
        print("✓ 分布API测试完成\n")
        return True
    except Exception as e:
        print(f"✗ 分布API测试失败: {str(e)}\n")
        return False

def test_ranking_api():
    """测试排行榜API"""
    print("=== 测试5: 排行榜API ===")
    
    try:
        # 热门文章
        top_articles = utils.get_top_articles(limit=10)
        print(f"热门文章(TOP10): {len(top_articles)} 篇")
        for i, article in enumerate(top_articles[:3], 1):
            print(f"  {i}. {article['title']}: {article['views']} 浏览")
        
        # 热门作者
        top_authors = utils.get_top_authors(limit=10)
        print(f"热门作者(TOP10): {len(top_authors)} 位")
        for i, author in enumerate(top_authors[:3], 1):
            print(f"  {i}. {author['username']}: {author['article_count']} 篇文章, {author['total_views']} 总浏览")
        
        print("✓ 排行榜API测试完成\n")
        return True
    except Exception as e:
        print(f"✗ 排行榜API测试失败: {str(e)}\n")
        return False

def test_recent_activities():
    """测试最近活动API"""
    print("=== 测试6: 最近活动API ===")
    
    try:
        activities = utils.get_recent_activities(limit=20)
        print(f"最近活动: {len(activities)} 条记录")
        
        activity_types = {}
        for activity in activities:
            activity_type = activity['type']
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        print("活动类型统计:")
        for activity_type, count in activity_types.items():
            print(f"  - {activity_type}: {count} 条")
        
        print("✓ 最近活动API测试完成\n")
        return True
    except Exception as e:
        print(f"✗ 最近活动API测试失败: {str(e)}\n")
        return False

def test_cache_performance():
    """测试缓存性能"""
    print("=== 测试7: 缓存性能 ===")
    
    import time
    from django.core.cache import cache
    
    # 清除缓存
    cache.clear()
    print("已清除缓存")
    
    # 第一次调用（无缓存）
    start = time.time()
    metrics1 = utils.get_metrics()
    time1 = time.time() - start
    print(f"第一次调用(无缓存): {time1*1000:.2f}ms")
    
    # 第二次调用（有缓存）
    start = time.time()
    metrics2 = utils.get_metrics()
    time2 = time.time() - start
    print(f"第二次调用(有缓存): {time2*1000:.2f}ms")
    
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"性能提升: {speedup:.1f}x")
    
    print("✓ 缓存性能测试完成\n")
    return True

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*50)
    print("Dashboard功能测试套件")
    print("="*50)
    
    results = []
    
    # 测试1: 访问权限（需要在测试环境中运行）
    # admin_user, normal_user = test_dashboard_access()
    
    # 测试2: 关键指标API
    results.append(("关键指标API", test_metrics_api()))
    
    # 测试3: 趋势分析API
    results.append(("趋势分析API", test_trend_api()))
    
    # 测试4: 分布统计API
    results.append(("分布统计API", test_distribution_api()))
    
    # 测试5: 排行榜API
    results.append(("排行榜API", test_ranking_api()))
    
    # 测试6: 最近活动API
    results.append(("最近活动API", test_recent_activities()))
    
    # 测试7: 缓存性能
    results.append(("缓存性能", test_cache_performance()))
    
    # 输出测试结果
    print("="*50)
    print("测试结果汇总")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print("="*50 + "\n")
    
    return passed == total

if __name__ == "__main__":
    # 在Django shell中运行
    run_all_tests()
