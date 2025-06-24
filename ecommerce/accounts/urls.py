from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('', views.dashboard, name='dashboard'),
    path('logout/', views.logout, name='logout'),
    path('register/',views.register, name ='register'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('order-detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
]