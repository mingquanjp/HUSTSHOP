from django.urls import path
from . import views


urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
    path('process-cod/<int:order_id>/', views.process_cod_payment, name='process_cod_payment'),
    path('order-success/<str:order_number>/', views.order_success, name='order_success'),
]