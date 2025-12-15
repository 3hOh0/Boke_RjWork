from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from blog.models import Article, Category, Tag
from . import models


class InteractionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='tester', email='tester@example.com', password='pass1234')
        category = Category.objects.create(name='TestCat')
        tag = Tag.objects.create(name='Tag1')
        self.article = Article.objects.create(
            title='Hello',
            body='content',
            category=category,
            author=self.user)
        self.article.tags.add(tag)

    def test_toggle_like_anonymous(self):
        response = self.client.post(reverse('interaction:toggle_like'), {'article_id': self.article.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(models.Like.objects.count(), 1)

    def test_favorite_folder_creation(self):
        self.client.login(username='tester', password='pass1234')
        response = self.client.post(reverse('interaction:folder_list'), {
            'name': 'My Folder',
            'description': 'desc',
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('id', data)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('interaction:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.client.login(username='tester', password='pass1234')
        response = self.client.get(reverse('interaction:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_public_share_page(self):
        self.client.login(username='tester', password='pass1234')
        folder = models.FavoriteFolder.objects.create(owner=models.InteractionActor.for_user(self.user), name='Public', is_public=True)
        response = self.client.get(reverse('interaction:folder_share', args=[folder.share_token]))
        self.assertEqual(response.status_code, 200)

    def test_quick_save_creates_folder(self):
        response = self.client.post(reverse('interaction:quick_save'), {
            'article_id': self.article.id,
            'folder_name': 'QuickBox',
            'folder_description': 'desc'
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['created'])
        self.assertTrue(models.FavoriteFolder.objects.filter(name='QuickBox').exists())

    def test_folder_detail_update(self):
        actor = models.InteractionActor.for_user(self.user)
        folder = models.FavoriteFolder.objects.create(owner=actor, name='OldName')
        self.client.login(username='tester', password='pass1234')
        response = self.client.post(reverse('interaction:folder_detail', args=[folder.id]), {
            'name': 'NewName',
            'description': 'Updated'
        })
        self.assertEqual(response.status_code, 200)
        folder.refresh_from_db()
        self.assertEqual(folder.name, 'NewName')

    def test_toggle_like_authenticated(self):
        """Test like toggle for authenticated users."""
        self.client.login(username='tester', password='pass1234')
        response = self.client.post(reverse('interaction:toggle_like'), {'article_id': self.article.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)
        
        # Toggle again to unlike
        response = self.client.post(reverse('interaction:toggle_like'), {'article_id': self.article.id})
        data = response.json()
        self.assertFalse(data['liked'])
        self.assertEqual(data['like_count'], 0)

    def test_favorite_item_add_remove(self):
        """Test adding and removing favorite items."""
        self.client.login(username='tester', password='pass1234')
        actor = models.InteractionActor.for_user(self.user)
        folder = models.FavoriteFolder.objects.create(owner=actor, name='TestFolder')
        
        # Add item
        response = self.client.post(reverse('interaction:favorite_item'), {
            'folder_id': folder.id,
            'article_id': self.article.id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['created'])
        self.assertEqual(models.FavoriteItem.objects.filter(folder=folder).count(), 1)
        
        # Remove item
        item_id = data['item_id']
        response = self.client.delete(reverse('interaction:favorite_item_detail', args=[item_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.FavoriteItem.objects.filter(folder=folder).count(), 0)

    def test_leaderboard_api(self):
        """Test leaderboard API endpoint."""
        # Create multiple likes
        actor1 = models.InteractionActor.for_anonymous('key1', 'fp1')
        actor2 = models.InteractionActor.for_anonymous('key2', 'fp2')
        models.Like.objects.create(article=self.article, actor=actor1)
        models.Like.objects.create(article=self.article, actor=actor2)
        
        response = self.client.get(reverse('interaction:leaderboard'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('articles', data)
        self.assertGreaterEqual(len(data['articles']), 1)

    def test_leaderboard_with_time_filter(self):
        """Test leaderboard with time-based filtering."""
        from django.utils import timezone
        from datetime import timedelta
        
        actor = models.InteractionActor.for_anonymous('key1', 'fp1')
        models.Like.objects.create(
            article=self.article,
            actor=actor,
            created_time=timezone.now() - timedelta(days=5)
        )
        
        since = (timezone.now() - timedelta(days=7)).isoformat()
        response = self.client.get(reverse('interaction:leaderboard'), {'since': since})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('articles', data)

    def test_folder_items_list(self):
        """Test listing items in a folder."""
        self.client.login(username='tester', password='pass1234')
        actor = models.InteractionActor.for_user(self.user)
        folder = models.FavoriteFolder.objects.create(owner=actor, name='TestFolder')
        models.FavoriteItem.objects.create(folder=folder, article=self.article, added_by=actor)
        
        response = self.client.get(reverse('interaction:folder_items', args=[folder.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['folder'], 'TestFolder')
        self.assertEqual(len(data['items']), 1)

    def test_private_folder_not_accessible(self):
        """Test that private folders are not accessible via share link."""
        self.client.login(username='tester', password='pass1234')
        actor = models.InteractionActor.for_user(self.user)
        folder = models.FavoriteFolder.objects.create(owner=actor, name='Private', is_public=False)
        
        response = self.client.get(reverse('interaction:folder_share', args=[folder.share_token]))
        self.assertEqual(response.status_code, 404)

    def test_duplicate_favorite_prevention(self):
        """Test that duplicate favorites are prevented when allow_duplicates=False."""
        self.client.login(username='tester', password='pass1234')
        actor = models.InteractionActor.for_user(self.user)
        folder = models.FavoriteFolder.objects.create(owner=actor, name='NoDupes', allow_duplicates=False)
        
        # Add first item
        response = self.client.post(reverse('interaction:favorite_item'), {
            'folder_id': folder.id,
            'article_id': self.article.id
        })
        self.assertEqual(response.status_code, 200)
        
        # Try to add duplicate
        response = self.client.post(reverse('interaction:favorite_item'), {
            'folder_id': folder.id,
            'article_id': self.article.id
        })
        self.assertEqual(response.status_code, 400)

    def test_public_folders_list(self):
        """Test listing public folders."""
        actor = models.InteractionActor.for_user(self.user)
        models.FavoriteFolder.objects.create(owner=actor, name='Public1', is_public=True)
        models.FavoriteFolder.objects.create(owner=actor, name='Private1', is_public=False)
        
        response = self.client.get(reverse('interaction:public_folders'))
        self.assertEqual(response.status_code, 200)
        # Should only show public folders

    def test_folder_delete(self):
        """Test deleting a folder."""
        self.client.login(username='tester', password='pass1234')
        actor = models.InteractionActor.for_user(self.user)
        folder = models.FavoriteFolder.objects.create(owner=actor, name='ToDelete')
        
        response = self.client.delete(reverse('interaction:folder_detail', args=[folder.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(models.FavoriteFolder.objects.filter(id=folder.id).exists())

    def test_share_token_regeneration(self):
        """Test regenerating share token."""
        self.client.login(username='tester', password='pass1234')
        actor = models.InteractionActor.for_user(self.user)
        folder = models.FavoriteFolder.objects.create(owner=actor, name='TestFolder')
        old_token = folder.share_token
        
        response = self.client.post(reverse('interaction:folder_detail', args=[folder.id]), {
            'name': 'TestFolder',
            'regenerate_share_token': True
        })
        self.assertEqual(response.status_code, 200)
        folder.refresh_from_db()
        self.assertNotEqual(folder.share_token, old_token)

    def test_notification_creation(self):
        """Test that notifications are created on like/favorite."""
        actor = models.InteractionActor.for_user(self.article.author)
        like_actor = models.InteractionActor.for_anonymous('key1', 'fp1')
        
        models.Like.objects.create(article=self.article, actor=like_actor)
        models.InteractionNotification.notify_like(self.article, like_actor)
        
        notification = models.InteractionNotification.objects.filter(
            recipient=self.article.author,
            notification_type='like'
        ).first()
        self.assertIsNotNone(notification)
        self.assertFalse(notification.is_read)

    def test_actor_for_user_creates_once(self):
        """Test that InteractionActor.for_user creates only one actor per user."""
        actor1 = models.InteractionActor.for_user(self.user)
        actor2 = models.InteractionActor.for_user(self.user)
        self.assertEqual(actor1.id, actor2.id)

    def test_anonymous_actor_creation(self):
        """Test anonymous actor creation and uniqueness."""
        actor1 = models.InteractionActor.for_anonymous('key1', 'fp1')
        actor2 = models.InteractionActor.for_anonymous('key1', 'fp1')
        self.assertEqual(actor1.id, actor2.id)
        
        actor3 = models.InteractionActor.for_anonymous('key2', 'fp1')
        self.assertNotEqual(actor1.id, actor3.id)

# Create your tests here.
