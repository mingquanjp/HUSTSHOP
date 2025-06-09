from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('', views.dashboard, name='dashboard'),
    path('logout/', views.logout, name='logout'),
    path('register/',views.register, name ='register'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
]