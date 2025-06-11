import datetime

from django.shortcuts import render, redirect

from carts.models import CartItem

from orders.forms import OrderForm
from orders.models import Order


# Create your views here.
def place_order(request, total = 0, quantity = 0,):
    current_user = request.user

    cart_items = CartItem.objects.filter(user = current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
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

            order = Order.objects.get(user = current_user, is_ordered = False, order_number = order_number)

            context = {
                'order' : order,
                'cart_items': cart_items,
                'total' : total,
                'grand_total' : grand_total,
            }
            return render(request,'payments.html',context)

        else:
            return redirect('checkout')
