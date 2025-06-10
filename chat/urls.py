from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/<str:username>/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout'),  # Add logout URL
    path('chat/<str:room_name>/', views.room, name='room'),
]