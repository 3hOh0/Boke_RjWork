"""
生成统计仪表盘测试数据

使用方法:
    python manage.py generate_dashboard_testdata
    
可选参数:
    --articles N    生成N篇文章 (默认: 50)
    --users N       生成N个用户 (默认: 10)
    --comments N    每篇文章生成N个评论 (默认: 5)
    --clear         清除现有测试数据
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from blog.models import Article, Category, Tag
from comments.models import Comment
from interaction.models import Like, FavoriteItem, FavoriteFolder, InteractionActor

User = get_user_model()


class Command(BaseCommand):
    help = '生成统计仪表盘测试数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--articles',
            type=int,
            default=50,
            help='生成文章数量 (默认: 50)'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='生成用户数量 (默认: 10)'
        )
        parser.add_argument(
            '--comments',
            type=int,
            default=5,
            help='每篇文章的评论数量 (默认: 5)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除现有测试数据'
        )

    def handle(self, *args, **options):
        article_count = options['articles']
        user_count = options['users']
        comment_count = options['comments']
        clear_data = options['clear']

        if clear_data:
            self.stdout.write(self.style.WARNING('清除现有测试数据...'))
            self.clear_test_data()

        self.stdout.write(self.style.SUCCESS('开始生成测试数据...\n'))

        # 1. 生成用户
        users = self.create_users(user_count)
        
        # 2. 生成分类和标签
        categories = self.create_categories()
        tags = self.create_tags()
        
        # 3. 生成文章
        articles = self.create_articles(article_count, users, categories, tags)
        
        # 4. 生成评论
        self.create_comments(articles, users, comment_count)
        
        # 5. 生成点赞
        self.create_likes(articles, users)
        
        # 6. 生成收藏
        self.create_favorites(articles, users)
        
        # 清除缓存
        from django.core.cache import cache
        cache.clear()
        
        self.stdout.write(self.style.SUCCESS('\n✓ 测试数据生成完成！'))
        self.print_summary(users, articles)

    def clear_test_data(self):
        """清除测试数据"""
        Like.objects.filter(article__title__startswith='测试文章').delete()
        FavoriteItem.objects.filter(article__title__startswith='测试文章').delete()
        Comment.objects.filter(article__title__startswith='测试文章').delete()
        Article.objects.filter(title__startswith='测试文章').delete()
        User.objects.filter(username__startswith='test_user_').delete()
        Tag.objects.filter(name__startswith='测试标签').delete()
        Category.objects.filter(name__startswith='测试分类').delete()
        self.stdout.write(self.style.SUCCESS('✓ 测试数据已清除\n'))

    def create_users(self, count):
        """创建测试用户"""
        self.stdout.write('1. 生成用户...')
        users = []
        
        for i in range(1, count + 1):
            user, created = User.objects.get_or_create(
                username=f'test_user_{i}',
                defaults={
                    'email': f'test_user_{i}@example.com',
                    'nickname': f'测试用户{i}',
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建了 {len(users)} 个用户'))
        return users

    def create_categories(self):
        """创建测试分类"""
        self.stdout.write('2. 生成分类...')
        categories = []
        
        category_names = [
            '测试分类-技术', '测试分类-生活', '测试分类-随笔',
            '测试分类-教程', '测试分类-笔记'
        ]
        
        for name in category_names:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'slug': name.lower().replace(' ', '-')}
            )
            categories.append(category)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建了 {len(categories)} 个分类'))
        return categories

    def create_tags(self):
        """创建测试标签"""
        self.stdout.write('3. 生成标签...')
        tags = []
        
        tag_names = [
            '测试标签Python', '测试标签Django', '测试标签Web',
            '测试标签数据库', '测试标签前端', '测试标签后端',
            '测试标签算法', '测试标签设计', '测试标签运维',
            '测试标签DevOps', '测试标签云计算', '测试标签AI'
        ]
        
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(
                name=name,
                defaults={'slug': name.lower().replace(' ', '-')}
            )
            tags.append(tag)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建了 {len(tags)} 个标签'))
        return tags

    def create_articles(self, count, users, categories, tags):
        """创建测试文章"""
        self.stdout.write('4. 生成文章...')
        articles = []
        
        titles = [
            'Django开发实战', 'Python高级编程', 'Web性能优化',
            '数据库设计原则', '前端框架对比', 'RESTful API设计',
            '微服务架构', '容器化部署', 'CI/CD实践',
            '代码重构技巧', '设计模式详解', '算法与数据结构'
        ]
        
        for i in range(1, count + 1):
            # 随机选择发布时间（最近30天内）
            days_ago = random.randint(0, 30)
            pub_time = timezone.now() - timedelta(days=days_ago)
            
            # 随机选择状态（90%已发布，10%草稿）
            status = 'p' if random.random() > 0.1 else 'd'
            
            article, created = Article.objects.get_or_create(
                title=f'测试文章{i:03d} - {random.choice(titles)}',
                defaults={
                    'body': f'这是测试文章{i}的内容。' * random.randint(10, 50),
                    'author': random.choice(users),
                    'category': random.choice(categories),
                    'status': status,
                    'pub_time': pub_time,
                    'views': random.randint(10, 1000),
                }
            )
            
            if created:
                # 添加1-4个随机标签
                article_tags = random.sample(tags, random.randint(1, 4))
                article.tags.set(article_tags)
                article.save()
            
            articles.append(article)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建了 {len(articles)} 篇文章'))
        return articles

    def create_comments(self, articles, users, count_per_article):
        """创建测试评论"""
        self.stdout.write('5. 生成评论...')
        total_comments = 0
        
        comment_texts = [
            '写得很好！', '学到了很多', '感谢分享',
            '非常实用的内容', '期待更多文章', '收藏了',
            '讲解得很清楚', '有深度的文章', '赞一个',
            '很有帮助', '继续加油', '支持作者'
        ]
        
        # 只为已发布的文章生成评论
        published_articles = [a for a in articles if a.status == 'p']
        
        for article in published_articles:
            # 随机生成0到count_per_article个评论
            num_comments = random.randint(0, count_per_article)
            
            for i in range(num_comments):
                days_ago = random.randint(0, 30)
                submit_date = timezone.now() - timedelta(
                    days=days_ago,
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                Comment.objects.create(
                    body=random.choice(comment_texts),
                    author=random.choice(users),
                    article=article,
                    submit_date=submit_date,
                )
                total_comments += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建了 {total_comments} 条评论'))

    def create_likes(self, articles, users):
        """创建测试点赞"""
        self.stdout.write('6. 生成点赞...')
        total_likes = 0
        
        # 只为已发布的文章生成点赞
        published_articles = [a for a in articles if a.status == 'p']
        
        for article in published_articles:
            # 随机选择一些用户点赞（30%-80%的用户）
            like_users = random.sample(
                users,
                random.randint(int(len(users) * 0.3), int(len(users) * 0.8))
            )
            
            for user in like_users:
                # 获取或创建InteractionActor
                actor, _ = InteractionActor.objects.get_or_create(user=user)
                
                # 创建点赞记录
                days_ago = random.randint(0, 30)
                created_time = timezone.now() - timedelta(
                    days=days_ago,
                    hours=random.randint(0, 23)
                )
                
                Like.objects.get_or_create(
                    article=article,
                    actor=actor,
                    defaults={'created_time': created_time}
                )
                total_likes += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建了 {total_likes} 个点赞'))

    def create_favorites(self, articles, users):
        """创建测试收藏"""
        self.stdout.write('7. 生成收藏...')
        total_favorites = 0
        
        # 只为已发布的文章生成收藏
        published_articles = [a for a in articles if a.status == 'p']
        
        for user in users:
            # 每个用户创建1-3个收藏夹
            num_folders = random.randint(1, 3)
            folders = []
            
            for i in range(num_folders):
                folder, _ = FavoriteFolder.objects.get_or_create(
                    user=user,
                    name=f'{user.username}的收藏夹{i+1}',
                    defaults={'description': f'测试收藏夹{i+1}'}
                )
                folders.append(folder)
            
            # 随机收藏一些文章（20%-50%的文章）
            favorite_articles = random.sample(
                published_articles,
                random.randint(int(len(published_articles) * 0.2), 
                             int(len(published_articles) * 0.5))
            )
            
            for article in favorite_articles:
                folder = random.choice(folders)
                days_ago = random.randint(0, 30)
                created_time = timezone.now() - timedelta(
                    days=days_ago,
                    hours=random.randint(0, 23)
                )
                
                FavoriteItem.objects.get_or_create(
                    article=article,
                    folder=folder,
                    defaults={'created_time': created_time}
                )
                total_favorites += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建了 {total_favorites} 个收藏'))

    def print_summary(self, users, articles):
        """打印统计摘要"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('数据生成摘要'))
        self.stdout.write('='*50)
        
        published_count = Article.objects.filter(status='p', title__startswith='测试文章').count()
        draft_count = Article.objects.filter(status='d', title__startswith='测试文章').count()
        comment_count = Comment.objects.filter(article__title__startswith='测试文章').count()
        like_count = Like.objects.filter(article__title__startswith='测试文章').count()
        favorite_count = FavoriteItem.objects.filter(article__title__startswith='测试文章').count()
        folder_count = FavoriteFolder.objects.filter(user__username__startswith='test_user_').count()
        
        self.stdout.write(f'用户数量: {len(users)}')
        self.stdout.write(f'文章总数: {len(articles)} (已发布: {published_count}, 草稿: {draft_count})')
        self.stdout.write(f'评论总数: {comment_count}')
        self.stdout.write(f'点赞总数: {like_count}')
        self.stdout.write(f'收藏总数: {favorite_count}')
        self.stdout.write(f'收藏夹数: {folder_count}')
        self.stdout.write('='*50)
        self.stdout.write(self.style.SUCCESS('\n现在可以访问 /dashboard/ 查看统计数据！'))
