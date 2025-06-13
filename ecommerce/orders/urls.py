from django.urls import path
from . import views


urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
    path('vnpay-payment/<int:order_id>/', views.vnpay_payment, name='vnpay_payment'),
    path('vnpay-return/', views.vnpay_return, name='vnpay_return'),
    path('vnpay-ipn/', views.vnpay_ipn, name='vnpay_ipn'),  # Thêm dòng này
    path('payment-success/<str:order_number>/', views.payment_success, name='payment_success'),
    path('payment-failed/<str:order_number>/', views.payment_failed, name='payment_failed'),
    #path('payments/', views.payments, name='payments'),
    #path('order_complete/', views.order_complete, name='order_complete'),
]