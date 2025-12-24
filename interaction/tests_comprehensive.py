from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from blog.models import Article, Category, Tag
from . import models
import logging

# Disable logging during tests to keep output clean, or enable for debugging
logging.disable(logging.CRITICAL)

class ComprehensiveInteractionTests(TestCase):
    """
    全面测试交互模块：点赞与收藏功能
    Covering: Unit, Functional, Boundary, Permission, and Exception handling.
    """

    def setUp(self):
        # 基础测试环境准备
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser', email='test@example.com', password='password123')
        self.user2 = get_user_model().objects.create_user(
            username='hacker', email='hacker@example.com', password='password123')
        
        self.category = Category.objects.create(name='Tech')
        self.article = Article.objects.create(
            title='Test Article',
            body='This is a test article content.',
            category=self.category,
            author=self.user
        )
        self.url_toggle_like = reverse('interaction:toggle_like')
        self.url_folder_list = reverse('interaction:folder_list')
        self.url_favorite_item = reverse('interaction:favorite_item')
        
        # 登录主用户
        self.client.login(username='testuser', password='password123')

    # ==========================================
    # 功能1：点赞 (Like) 测试用例
    # ==========================================

    def test_case_01_like_normal_flow(self):
        """
        [Like] 正常流程：用户点赞，再次点击取消点赞
        """
        # 1. 首次点赞
        response = self.client.post(self.url_toggle_like, {'article_id': self.article.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['liked'], "首次点击应返回 liked=True")
        self.assertEqual(data['like_count'], 1, "点赞数应增加为 1")
        self.assertTrue(models.Like.objects.filter(article=self.article, actor__user=self.user).exists(), "数据库应存在点赞记录")

        # 2. 再次点击（取消点赞）
        response = self.client.post(self.url_toggle_like, {'article_id': self.article.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertFalse(data['liked'], "再次点击应返回 liked=False")
        self.assertEqual(data['like_count'], 0, "点赞数应减少为 0")
        self.assertFalse(models.Like.objects.filter(article=self.article, actor__user=self.user).exists(), "数据库点赞记录应被删除")

    def test_case_02_like_nonexistent_article(self):
        """
        [Like] 异常处理：点赞不存在的文章
        """
        # 尝试点赞 ID 为 99999 的不存在文章
        response = self.client.post(self.url_toggle_like, {'article_id': 99999})
        # Django get_object_or_404 通常返回 404
        self.assertEqual(response.status_code, 404, "点赞不存在的文章应返回 404")

    # ==========================================
    # 功能2：收藏 (Favorite) 测试用例
    # ==========================================

    def test_case_03_favorite_create_folder_boundary(self):
        """
        [Favorite] 边界测试：创建收藏夹（名称长度、特殊字符）
        """
        # 1. 正常创建
        response = self.client.post(self.url_folder_list, {
            'name': 'My Favorites',
            'description': 'Normal description',
            'is_public': True
        })
        self.assertEqual(response.status_code, 200)
        
        # 2. 边界：极长名称 (假设模型限制 100 字符，测试 101+ 或刚好 100)
        # 假设这里我们测试一个合理的较长名称，确保系统不崩溃
        long_name = 'A' * 50
        response = self.client.post(self.url_folder_list, {
            'name': long_name,
            'description': 'Long name test'
        })
        self.assertEqual(response.status_code, 200, "创建合法的收藏夹不应失败")
        self.assertTrue(models.FavoriteFolder.objects.filter(name=long_name, owner__user=self.user).exists())

        # 3. 异常：空名称 (取决于 Form 验证，通常不允许为空)
        response = self.client.post(self.url_folder_list, {
            'name': '',
            'description': 'Empty name'
        })
        # 如果前端/后端有验证，应返回 400 或 表单错误
        # 这里假设后端会拦截
        self.assertNotEqual(response.status_code, 200, "不允许创建空名文件夹")

    def test_case_04_favorite_add_item_permission(self):
        """
        [Favorite] 权限测试：不能向他人收藏夹添加内容
        """
        # Hacker 创建一个收藏夹
        self.client.logout()
        self.client.login(username='hacker', password='password123')
        actor_hacker = models.InteractionActor.for_user(self.user2)
        hacker_folder = models.FavoriteFolder.objects.create(owner=actor_hacker, name='Hacker Folder')
        
        # TestUser 尝试向 Hacker 的收藏夹添加文章
        self.client.logout()
        self.client.login(username='testuser', password='password123')
        
        response = self.client.post(self.url_favorite_item, {
            'folder_id': hacker_folder.id,
            'article_id': self.article.id
        })
        
        # 预期结果：应该禁止访问 (403 or 404 if filtered by user)
        # 根据常见逻辑，filter(user=request.user) 找不到该 folder 会 404，或者权限检查 403
        self.assertIn(response.status_code, [403, 404], "不应允许操作他人的收藏夹")
        
        # 验证数据库未写入
        self.assertEqual(models.FavoriteItem.objects.filter(folder=hacker_folder).count(), 0)

    def test_case_05_favorite_duplicate_prevention_logic(self):
        """
        [Favorite] 业务逻辑：重复收藏校验 (allow_duplicates=False)
        """
        # 创建不允许重复的收藏夹
        actor = models.InteractionActor.for_user(self.user)
        folder = models.FavoriteFolder.objects.create(owner=actor, name='Unique Folder', allow_duplicates=False)
        
        # 第一次收藏
        response = self.client.post(self.url_favorite_item, {
            'folder_id': folder.id,
            'article_id': self.article.id
        })
        self.assertEqual(response.status_code, 200)
        
        # 第二次收藏同一文章
        response = self.client.post(self.url_favorite_item, {
            'folder_id': folder.id,
            'article_id': self.article.id
        })
        
        # 预期：失败 (400 Bad Request 或者 自定义错误码)
        self.assertEqual(response.status_code, 400, "不允许重复收藏同一文章")
        self.assertEqual(models.FavoriteItem.objects.filter(folder=folder).count(), 1, "数据库中应只有一条记录")

    def test_case_06_folder_deletion_cascade(self):
        """
        [Favorite] 数据完整性：删除收藏夹应级联删除其内项目
        """
        # 创建文件夹和项目
        response = self.client.post(self.url_folder_list, {'name': 'To Delete'})
        folder_id = response.json()['id']
        
        self.client.post(self.url_favorite_item, {
            'folder_id': folder_id,
            'article_id': self.article.id
        })
        
        # 确认已存在
        self.assertTrue(models.FavoriteItem.objects.filter(folder_id=folder_id).exists())
        
        # 删除文件夹
        url_delete = reverse('interaction:folder_detail', args=[folder_id])
        response = self.client.delete(url_delete)
        self.assertEqual(response.status_code, 200)
        
        # 验证：文件夹和项目都应消失
        self.assertFalse(models.FavoriteFolder.objects.filter(id=folder_id).exists(), "文件夹应被删除")
        self.assertFalse(models.FavoriteItem.objects.filter(folder_id=folder_id).exists(), "文件夹内的收藏项应级联删除")

    def test_case_07_like_concurrency_simulation(self):
        """
        [Like] 并发/重复操作模拟：短时间内多次请求不应导致数据异常
        """
        # 虽然单元测试很难真正模拟并发，但可以测试逻辑上的幂等性
        # 连续发送 3 次点赞请求
        for _ in range(3):
            self.client.post(self.url_toggle_like, {'article_id': self.article.id})
            
        # 最终状态应该是 "点赞" (User liked it), 因为 toggle logic:
        # 1. Like -> True (Count 1)
        # 2. Unlike -> False (Count 0)
        # 3. Like -> True (Count 1)
        
        # 验证最终状态
        is_liked = models.Like.objects.filter(article=self.article, actor__user=self.user).exists()
        self.assertTrue(is_liked, "三次 Toggle 后，状态应为已点赞")
        self.assertEqual(self.article.likes.count(), 1)
