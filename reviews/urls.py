from django.urls import path
from reviews import views

urlpatterns = [
    path('games/<slug:slug>/review/', views.ReviewCreateView.as_view(), name='review_create'),
    path('reviews/<int:pk>/edit/', views.ReviewEditView.as_view(), name='review_edit'),
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),
]
