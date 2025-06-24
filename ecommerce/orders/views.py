from django.contrib.auth.decorators import login_required
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

from orders.models import Payment, OrderProduct

from store.models import Product


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
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.shipping_address = form.cleaned_data['shipping_address']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.ip = request.META.get('REMOTE_ADDR')
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

        else:
            print(f"Error saving order: {e}")
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



@login_required(login_url='login')
def process_cod_payment(request, order_id):
    """Xử lý thanh toán COD"""
    try:
        order = Order.objects.get(id=order_id, user=request.user, is_ordered=False)
        cart = _get_cart(request)
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        # Tạo payment record cho COD
        payment = Payment(
            user=request.user,
            payment_id=f"COD_{order.order_number}",
            payment_method="Cash on Delivery",
            amount_paid=order.order_total,
            status="Pending"
        )
        payment.save()

        # Cập nhật order
        order.payment = payment
        order.is_ordered = True
        order.order_status = "Accepted"
        order.save()

        # Tạo OrderProduct cho từng sản phẩm
        for cart_item in cart_items:
            # Create OrderProduct first
            order_product = OrderProduct(
                order=order,
                payment=payment,
                user=request.user,
                product=cart_item.product,
                quantity=cart_item.quantity,
                product_price=cart_item.product.price,
                ordered=True,
                subtotal=cart_item.quantity * cart_item.product.price
            )
            # Explicitly save to ensure it has an ID
            order_product.save()

            # Now add variations after the object is definitely saved
            cart_item_variations = cart_item.variations.all()
            if cart_item_variations.exists():
                for variation in cart_item_variations:
                    order_product.variations.add(variation)

            # Giảm số lượng sản phẩm trong kho
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()

        # Xóa cart items
        CartItem.objects.filter(cart=cart).delete()

        messages.success(request, 'Đặt hàng thành công! Bạn sẽ thanh toán khi nhận hàng.')
        return redirect('order_success', order_number=order.order_number)

    except Order.DoesNotExist:
        messages.error(request, 'Đơn hàng không tồn tại')
        return redirect('checkout')
    except Exception as e:
        print(f"Error in process_cod_payment: {e}")
        messages.error(request, 'Có lỗi xảy ra khi xử lý đơn hàng. Vui lòng thử lại.')
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