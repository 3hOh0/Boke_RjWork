"""
Django management command to create test data for interaction features (like/favorite).
Usage: python manage.py create_interaction_testdata
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from blog.models import Article, Tag, Category
from interaction import models


class Command(BaseCommand):
    help = '创建点赞/收藏功能的测试数据（包括文章、用户、点赞、收藏夹等）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--articles',
            type=int,
            default=10,
            help='要创建的文章数量（默认：10）',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='要创建的用户数量（默认：5）',
        )
        parser.add_argument(
            '--likes',
            type=int,
            default=30,
            help='要创建的点赞数量（默认：30）',
        )
        parser.add_argument(
            '--folders',
            type=int,
            default=8,
            help='要创建的收藏夹数量（默认：8）',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始创建测试数据...\n'))

        # 1. 创建用户
        users = self._create_users(options['users'])
        self.stdout.write(self.style.SUCCESS(f'✓ 创建了 {len(users)} 个用户'))

        # 2. 创建分类和标签
        category = self._create_category()
        tags = self._create_tags()
        self.stdout.write(self.style.SUCCESS(f'✓ 创建了分类和 {len(tags)} 个标签'))

        # 3. 创建文章
        articles = self._create_articles(users, category, tags, options['articles'])
        self.stdout.write(self.style.SUCCESS(f'✓ 创建了 {len(articles)} 篇文章'))

        # 4. 创建点赞
        likes = self._create_likes(users, articles, options['likes'])
        self.stdout.write(self.style.SUCCESS(f'✓ 创建了 {len(likes)} 个点赞'))

        # 5. 创建收藏夹和收藏项
        folders, items = self._create_favorites(users, articles, options['folders'])
        self.stdout.write(self.style.SUCCESS(f'✓ 创建了 {len(folders)} 个收藏夹和 {len(items)} 个收藏项'))

        # 6. 创建一些匿名用户的点赞和收藏
        anonymous_likes, anonymous_items = self._create_anonymous_interactions(articles)
        self.stdout.write(self.style.SUCCESS(
            f'✓ 创建了 {anonymous_likes} 个匿名点赞和 {anonymous_items} 个匿名收藏'))

        self.stdout.write(self.style.SUCCESS('\n✅ 测试数据创建完成！\n'))
        self.stdout.write(self.style.WARNING('测试账号信息：'))
        for i, user in enumerate(users[:3], 1):
            self.stdout.write(f'  用户{i}: {user.username} / 密码: test123456')

    def _create_users(self, count):
        """创建测试用户"""
        User = get_user_model()
        users = []
        for i in range(1, count + 1):
            user, created = User.objects.get_or_create(
                username=f'testuser{i}',
                defaults={
                    'email': f'testuser{i}@example.com',
                    'password': make_password('test123456'),
                }
            )
            users.append(user)
        return users

    def _create_category(self):
        """创建测试分类"""
        category, _ = Category.objects.get_or_create(
            name='测试分类',
            defaults={'parent_category': None}
        )
        return category

    def _create_tags(self):
        """创建测试标签"""
        tag_names = ['Python', 'Django', 'Web开发', '测试', '教程', '技术分享']
        tags = []
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        return tags

    def _create_articles(self, users, category, tags, count):
        """创建测试文章"""
        articles = []
        titles = [
            'Django 入门教程',
            'Python 高级特性详解',
            'Web 开发最佳实践',
            '数据库设计原则',
            'RESTful API 设计指南',
            '前端性能优化技巧',
            'Docker 容器化部署',
            'Git 版本控制实战',
            '测试驱动开发 TDD',
            '微服务架构设计',
            'Redis 缓存策略',
            'Elasticsearch 全文搜索',
            '消息队列应用场景',
            'CI/CD 持续集成',
            '安全编程实践',
        ]

        for i in range(count):
            title = titles[i % len(titles)] + f' (第{i+1}篇)'
            author = random.choice(users)
            
            # 创建不同时间的文章，模拟时间分布
            days_ago = random.randint(0, 30)
            pub_time = timezone.now() - timedelta(days=days_ago)
            
            article, created = Article.objects.get_or_create(
                title=title,
                defaults={
                    'body': f'这是文章《{title}》的正文内容。\n\n' * 5,
                    'category': category,
                    'author': author,
                    'type': 'a',
                    'status': 'p',
                    'pub_time': pub_time,
                }
            )
            
            # 添加随机标签
            article.tags.add(*random.sample(tags, random.randint(1, 3)))
            articles.append(article)
        
        return articles

    def _create_likes(self, users, articles, count):
        """创建点赞记录"""
        likes = []
        actors = [models.InteractionActor.for_user(user) for user in users]
        
        # 确保每篇文章至少有一些点赞
        for article in articles[:min(len(articles), count // 3)]:
            actor = random.choice(actors)
            like, created = models.Like.objects.get_or_create(
                article=article,
                actor=actor,
            )
            if created:
                likes.append(like)
        
        # 随机创建更多点赞
        remaining = count - len(likes)
        for _ in range(remaining):
            article = random.choice(articles)
            actor = random.choice(actors)
            like, created = models.Like.objects.get_or_create(
                article=article,
                actor=actor,
            )
            if created:
                likes.append(like)
        
        return likes

    def _create_favorites(self, users, articles, folder_count):
        """创建收藏夹和收藏项"""
        folders = []
        items = []
        actors = [models.InteractionActor.for_user(user) for user in users]
        
        folder_names = [
            '我的收藏',
            '技术学习',
            '优秀文章',
            '待读列表',
            'Python 相关',
            'Web 开发',
            '数据库',
            'DevOps',
        ]
        
        # 为每个用户创建一些收藏夹
        for i, actor in enumerate(actors):
            num_folders = random.randint(1, 3)
            for j in range(num_folders):
                folder_name = folder_names[(i * 3 + j) % len(folder_names)]
                if j > 0:
                    folder_name += f' {j+1}'
                
                folder, created = models.FavoriteFolder.objects.get_or_create(
                    owner=actor,
                    name=folder_name,
                    defaults={
                        'description': f'这是{folder_name}的描述',
                        'is_public': random.choice([True, False]),
                        'allow_duplicates': random.choice([True, False]),
                        'tags': random.choice(['python,web', 'django', '随笔,阅读', '']),
                        'pinned': random.choice([True, False, False]),
                        'sort_order': random.randint(0, 20),
                    }
                )
                if created:
                    folders.append(folder)
                    
                    # 为每个收藏夹添加一些文章
                    num_items = random.randint(2, 5)
                    selected_articles = random.sample(articles, min(num_items, len(articles)))
                    for article in selected_articles:
                        item, item_created = models.FavoriteItem.objects.get_or_create(
                            folder=folder,
                            article=article,
                            defaults={
                                'added_by': actor,
                                'note': f'收藏于 {timezone.now().strftime("%Y-%m-%d")}',
                            }
                        )
                        if item_created:
                            items.append(item)
        
        return folders, items

    def _create_anonymous_interactions(self, articles):
        """创建匿名用户的点赞和收藏"""
        anonymous_likes = 0
        anonymous_items = 0
        
        # 创建几个匿名用户
        anonymous_keys = ['anon1', 'anon2', 'anon3']
        for key in anonymous_keys:
            actor = models.InteractionActor.for_anonymous(key, f'fp_{key}')
            
            # 匿名点赞
            num_likes = random.randint(2, 5)
            for _ in range(num_likes):
                article = random.choice(articles)
                like, created = models.Like.objects.get_or_create(
                    article=article,
                    actor=actor,
                )
                if created:
                    anonymous_likes += 1
            
            # 匿名收藏（创建公开收藏夹）
            folder, created = models.FavoriteFolder.objects.get_or_create(
                owner=actor,
                name=f'匿名收藏夹 {key}',
                defaults={
                    'description': '这是一个匿名用户的公开收藏夹',
                    'is_public': True,
                    'allow_duplicates': False,
                    'tags': 'anonymous,public',
                    'pinned': False,
                }
            )
            
            if created:
                num_items = random.randint(1, 3)
                for _ in range(num_items):
                    article = random.choice(articles)
                    item, item_created = models.FavoriteItem.objects.get_or_create(
                        folder=folder,
                        article=article,
                        defaults={'added_by': actor}
                    )
                    if item_created:
                        anonymous_items += 1
        
        return anonymous_likes, anonymous_items

