from django.urls import path

from . import views

app_name = 'interaction'

urlpatterns = [
    path('like/', views.ToggleLikeView.as_view(), name='toggle_like'),
    path('like-history/', views.UserLikeHistoryView.as_view(), name='like_history'),
    path('folders/', views.FavoriteFolderListView.as_view(), name='folder_list'),
    path('folders/<int:folder_id>/', views.FavoriteFolderDetailView.as_view(), name='folder_detail'),
    path('items/', views.FavoriteItemView.as_view(), name='favorite_item'),
    path('items/<int:item_id>/', views.FavoriteItemView.as_view(), name='favorite_item_detail'),
    path('folders/<int:folder_id>/items/', views.FavoriteItemListView.as_view(), name='folder_items'),
    path('folders/<int:folder_id>/export/', views.FavoriteExportView.as_view(), name='folder_export'),
    path('batch/', views.FavoriteBatchActionView.as_view(), name='batch_action'),
    path('quick-save/', views.QuickFavoriteView.as_view(), name='quick_save'),
    path('share/<str:token>/', views.FavoriteShareView.as_view(), name='folder_share'),
    path('dashboard/', views.FavoriteDashboardView.as_view(), name='dashboard'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('leaderboard/page/', views.LeaderboardPage.as_view(), name='leaderboard_page'),
    path('leaderboard/top/', views.LikeLeaderboardView.as_view(), name='like_leaderboard'),
    path('my-favorites/', views.MyFavoritesView.as_view(), name='my_favorites'),
    path('search/', views.FavoriteSearchView.as_view(), name='favorite_search'),
    path('public/', views.PublicFavoriteListView.as_view(), name='public_folders'),
    path('swagger.json', views.SwaggerView.as_view(), name='swagger'),
]

