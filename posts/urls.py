from django.urls import path
from posts import views

urlpatterns = [
    path('posts/', views.PostListView.as_view(), name='post_list'),
    path('posts/create/', views.PostCreateView.as_view(), name='post_create'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/<int:pk>/edit/', views.PostEditView.as_view(), name='post_edit'),
    path('posts/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('posts/comments/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
    path('posts/images/<int:pk>/delete/', views.PostImageDeleteView.as_view(), name='post_image_delete'),
    path('search/', views.SearchView.as_view(), name='search'),
]
