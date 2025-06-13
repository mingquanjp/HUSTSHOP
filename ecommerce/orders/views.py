import datetime
from cmath import e

from django.http import HttpResponse
from django.shortcuts import render, redirect

from carts.models import CartItem
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from orders.forms import OrderForm
from orders.models import Order
from pyexpat.errors import messages
from raven.utils.wsgi import get_client_ip

from orders.models import Payment, OrderProduct
from vnpay.vnpay_config import VNPayConfig, VNPay


# Create your views here.
def place_order(request, total = 0, quantity = 0,):
    current_user = request.user

    cart_items = CartItem.objects.filter(user = current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        messages.error(request,"Your cart is empty")
        return redirect('store')

    grand_total = 0

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity

    #discount
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

            #generate order number

            year = int(datetime.date.today().strftime("%Y"))
            date = int(datetime.date.today().strftime("%d"))
            month = int(datetime.date.today().strftime("%m"))
            day = datetime.date(year,month,date)
            current_date = day.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            return redirect('payment_page', order_id=data.id)
          #  order = Order.objects.get(user = current_user, is_ordered = False, order_number = order_number)

           # context = {
            #    'order' : order,
             #   'cart_items': cart_items,
              #  'total' : total,
              #  'grand_total' : grand_total,
            #}



        else:
            print(f"Error saving order: {e}")
            return redirect('checkout')

#Chon phuong thuc thanh toan
def payment_page(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user, is_ordered=False)
        cart_items = CartItem.objects.filter(user=request.user)

        context = {
            'order': order,
            'cart_items': cart_items,
        }
        return render(request, 'payment_page.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Order does not exist')
        return redirect('checkout')


def vnpay_payment(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user, is_ordered=False)
    except Order.DoesNotExist:
        return redirect('store')

    vnpay = VNPay()
    client_ip = get_client_ip(request)

    vnpay.request_data['vnp_Version'] = '2.1.0'
    vnpay.request_data['vnp_Command'] = 'pay'
    vnpay.request_data['vnp_TmnCode'] = VNPayConfig.VNPAY_TMN_CODE
    vnpay.request_data['vnp_Amount'] = str(int(order.order_total * 100))
    vnpay.request_data['vnp_CurrCode'] = 'VND'
    vnpay.request_data['vnp_TxnRef'] = str(order.order_number)
    vnpay.request_data['vnp_OrderInfo'] = f'Payment for order {order.order_number}'  # Không dấu
    vnpay.request_data['vnp_OrderType'] = 'other'
    vnpay.request_data['vnp_Locale'] = 'vn'
    vnpay.request_data['vnp_CreateDate'] = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    vnpay.request_data['vnp_IpAddr'] = client_ip
    vnpay.request_data['vnp_ReturnUrl'] = VNPayConfig.VNPAY_RETURN_URL

    try:
        payment_url = vnpay.get_payment_url(VNPayConfig.VNPAY_URL, VNPayConfig.VNPAY_HASH_SECRET)
        print(f"Final payment URL: {payment_url}")
        return redirect(payment_url)
    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, 'Có lỗi khi tạo URL thanh toán')
        return redirect('payment_page', order_id=order.id)

@csrf_exempt
def vnpay_return(request):
    """Xử lý khi VNPAY trả về kết quả thanh toán"""
    vnpay = VNPay()
    vnpay.request_data = dict(request.GET)
    print("VNPay Return Data:", vnpay.request_data)



    # Flatten QueryDict values (Django trả về list)
    for key, value in vnpay.request_data.items():
        if isinstance(value, list):
            vnpay.request_data[key] = value[0]

    # Lấy thông tin từ response
    vnp_ResponseCode = vnpay.request_data.get('vnp_ResponseCode')
    vnp_TxnRef = vnpay.request_data.get('vnp_TxnRef')
    vnp_Amount = int(vnpay.request_data.get('vnp_Amount', 0)) / 100
    vnp_TransactionNo = vnpay.request_data.get('vnp_TransactionNo', '')

    print(f"Response Code: {vnp_ResponseCode}")
    print(f"Transaction Ref: {vnp_TxnRef}")
    print(f"Amount: {vnp_Amount}")

    #vnp_PayDate = vnpay.request_data.get('vnp_PayDate', '')

    if vnpay.validate_response(VNPayConfig.VNPAY_HASH_SECRET):
        try:
            order = Order.objects.get(order_number=vnp_TxnRef, is_ordered=False)

            if vnp_ResponseCode == '00':  # Thanh toán thành công
                # Tạo Payment record
                payment = Payment.objects.create(
                    user=order.user,
                    payment_id=vnp_TransactionNo,
                    payment_method='VNPAY',
                    amount_paid=vnp_Amount,
                    status='completed'
                )

                # Cập nhật order
                order.payment = payment
                order.is_ordered = True
                order.order_status = 'processing'
                order.save()

                # Tạo OrderProduct cho từng item trong cart
                cart_items = CartItem.objects.filter(user=order.user)
                for cart_item in cart_items:
                    order_product = OrderProduct.objects.create(
                        order=order,
                        payment=payment,
                        user=order.user,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        product_price=cart_item.product.price,
                        subtotal=cart_item.product.price * cart_item.quantity,
                        ordered=True
                    )
                    # Thêm variations nếu có
                    order_product.variations.set(cart_item.variations.all())

                # Xóa giỏ hàng
                cart_items.delete()

                messages.success(request, 'Thanh toán thành công!')
                return redirect('payment_success', order_number=order.order_number)

            else:  # Thanh toán thất bại
                # Tạo payment record với status failed
                Payment.objects.create(
                    user=order.user,
                    payment_id=vnp_TransactionNo if vnp_TransactionNo else f"FAILED_{vnp_TxnRef}",
                    payment_method='VNPAY',
                    amount_paid=vnp_Amount,
                    status='failed'
                )

                messages.error(request, 'Thanh toán thất bại! Vui lòng thử lại.')
                return redirect('payment_failed', order_number=order.order_number)

        except Order.DoesNotExist:
            messages.error(request, 'Đơn hàng không tồn tại!')
            return redirect('store')
    else:

        return redirect('store')

def payment_success(request, order_number):
    """Trang hiển thị khi thanh toán thành công"""
    try:
        order = Order.objects.get(order_number=order_number, user=request.user, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order=order)

        context = {
            'order': order,
            'ordered_products': ordered_products,
        }
        return render(request, 'orders/payment_success.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Đơn hàng không tồn tại!')
        return redirect('store')


def payment_failed(request, order_number):
    """Trang hiển thị khi thanh toán thất bại"""
    try:
        order = Order.objects.get(order_number=order_number, user=request.user)
        context = {
            'order': order,
        }
        return render(request, 'orders/payment_failed.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Đơn hàng không tồn tại!')
        return redirect('store')


def get_client_ip(request):
    """Lấy IP của client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip if ip else '127.0.0.1'


@csrf_exempt
def vnpay_ipn(request):
    """IPN endpoint để VNPay gọi thông báo kết quả thanh toán"""
    vnpay = VNPay()
    vnpay.request_data = dict(request.GET)

    # Flatten QueryDict values
    for key, value in vnpay.request_data.items():
        if isinstance(value, list):
            vnpay.request_data[key] = value[0]

    print("=== VNPay IPN Data ===")
    for key, value in vnpay.request_data.items():
        print(f"{key}: {value}")

    # Validate hash
    if vnpay.validate_response(VNPayConfig.VNPAY_HASH_SECRET):
        vnp_ResponseCode = vnpay.request_data.get('vnp_ResponseCode')
        vnp_TxnRef = vnpay.request_data.get('vnp_TxnRef')
        vnp_Amount = int(vnpay.request_data.get('vnp_Amount', 0)) / 100
        vnp_TransactionNo = vnpay.request_data.get('vnp_TransactionNo', '')

        try:
            order = Order.objects.get(order_number=vnp_TxnRef)

            if vnp_ResponseCode == '00' and not order.is_ordered:
                # Thanh toán thành công - cập nhật order
                payment = Payment.objects.create(
                    user=order.user,
                    payment_id=vnp_TransactionNo,
                    payment_method='VNPAY',
                    amount_paid=vnp_Amount,
                    status='completed'
                )

                order.payment = payment
                order.is_ordered = True
                order.order_status = 'processing'
                order.save()

                # Tạo OrderProduct
                cart_items = CartItem.objects.filter(user=order.user)
                for cart_item in cart_items:
                    OrderProduct.objects.create(
                        order=order,
                        payment=payment,
                        user=order.user,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        product_price=cart_item.product.price,
                        subtotal=cart_item.product.price * cart_item.quantity,
                        ordered=True
                    )

                # Xóa giỏ hàng
                cart_items.delete()

                print(f"Order {vnp_TxnRef} processed successfully via IPN")
                return HttpResponse("RspCode=00&Message=Confirm Success")

            else:
                print(f"Order {vnp_TxnRef} payment failed via IPN")
                return HttpResponse("RspCode=00&Message=Confirm Success")

        except Order.DoesNotExist:
            print(f"Order {vnp_TxnRef} not found")
            return HttpResponse("RspCode=01&Message=Order not found")

    else:
        print("Invalid signature in IPN")
        return HttpResponse("RspCode=97&Message=Invalid signature")