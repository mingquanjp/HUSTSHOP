from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import datetime
from django.http import HttpResponseRedirect

from carts.models import CartItem, Cart
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from orders.forms import OrderForm
from orders.models import Order
# Thay đổi import này - raven.utils.wsgi có thể không tồn tại
# from raven.utils.wsgi import get_client_ip

from orders.models import Payment, OrderProduct




def get_client_ip(request):
    """Lấy IP address của client - Di chuyển function lên đầu"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def _get_cart(request):
    """Helper function để lấy cart cho cả authenticated user và anonymous user"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'cart_id': ''}
        )
    else:
        cart_id = request.session.session_key
        if not cart_id:
            cart_id = request.session.create()
        cart, created = Cart.objects.get_or_create(
            cart_id=cart_id,
            user=None,
            defaults={'cart_id': cart_id}
        )
    return cart


def place_order(request, total=0, quantity=0):
    current_user = request.user

    # Lấy cart của user hiện tại
    cart = _get_cart(request)
    cart_items = CartItem.objects.filter(cart=cart, is_active=True)
    cart_count = cart_items.count()

    if cart_count <= 0:
        messages.error(request, "Your cart is empty")
        return redirect('store')

    grand_total = 0

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity

    # discount
    grand_total = total

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                data = Order()
                data.user = current_user
                data.first_name = form.cleaned_data['first_name']
                data.last_name = form.cleaned_data['last_name']
                data.phone = form.cleaned_data['phone']
                data.email = form.cleaned_data['email']
                data.shipping_address = form.cleaned_data['shipping_address']
                data.order_note = form.cleaned_data['order_note']
                data.order_total = grand_total
                data.save()

                # generate order number
                year = int(datetime.date.today().strftime("%Y"))
                date = int(datetime.date.today().strftime("%d"))
                month = int(datetime.date.today().strftime("%m"))
                day = datetime.date(year, month, date)
                current_date = day.strftime("%Y%m%d")
                order_number = current_date + str(data.id)
                data.order_number = order_number
                data.save()

                return redirect('payment_page', order_id=data.id)

            except Exception as e:
                print(f"Error saving order: {e}")
                messages.error(request, f"Error creating order: {str(e)}")
                return redirect('checkout')
        else:
            messages.error(request, "Form validation error")
            return redirect('checkout')


def payment_page(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user, is_ordered=False)
        cart = _get_cart(request)
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        context = {
            'order': order,
            'cart_items': cart_items,
        }
        return render(request, 'payment_page.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Order does not exist')
        return redirect('checkout')

def order_success(request, order_number):
    """Trang thành công sau khi đặt hàng"""
    try:
        order = Order.objects.get(order_number=order_number, user=request.user, is_ordered=True)
        order_products = OrderProduct.objects.filter(order=order)

        context = {
            'order': order,
            'order_products': order_products,
        }
        return render(request, 'order_success.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('home')