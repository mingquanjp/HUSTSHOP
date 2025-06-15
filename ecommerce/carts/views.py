from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required

from store.models import Product, Variation
from carts.models import Cart, CartItem
from django.http import HttpResponse

def _get_cart(request):
    """Helper function để lấy cart cho cả authenticated user và anonymous user"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'cart_id': ''}  # cart_id không cần thiết cho authenticated user
        )
    else:
        cart_id = _cart_id(request)
        cart, created = Cart.objects.get_or_create(
            cart_id=cart_id,
            user=None,  # Anonymous user
            defaults={'cart_id': cart_id}
        )
    return cart


def _cart_id(request):
    cart_id = request.session.session_key
    if not cart_id:
        cart_id = request.session.create()
    return cart_id

def add_cart(request, product_id):

    product = Product.objects.get(id=product_id)
    cart = _get_cart(request)# Get object product

    product_variations = []
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST.get(key)
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variations.append(variation)
            except ObjectDoesNotExist:
                pass

        is_exists_cart_item = CartItem.objects.filter(product=product, cart=cart).exists()


        if is_exists_cart_item:
            cart_items = CartItem.objects.filter(product=product, cart=cart)
            existing_variation_list = [list(item.variations.all()) for item in cart_items]
            cart_item_ids = [item.id for item in cart_items]

            if product_variations in existing_variation_list:
            # Tăng quantity nếu variation đã tồn tại
                index = existing_variation_list.index(product_variations)
                cart_item = CartItem.objects.get(id=cart_item_ids[index])
                cart_item.quantity += 1
                cart_item.save()
            else:
            # Tạo cart item mới với variation khác
                cart_item = CartItem.objects.create(
                    product=product,
                    cart=cart,
                    quantity=1
            )
                if product_variations:
                    cart_item.variations.set(product_variations)
        else:
            cart_item = CartItem.objects.create(
                product=product,
                cart=cart,
                quantity=1
            )
            if product_variations:
                cart_item.variations.set(product_variations)

        return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        cart = _get_cart(request)
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity
        tax = total * 2 / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass    # Chỉ bỏ qua
    print(request.user)
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax if "tax" in locals() else "",
        'grand_total': grand_total if "tax" in locals() else 0,
    }
    return render(request, 'cart.html', context=context)


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    cart = _get_cart(request)
    try:
        cart_item = CartItem.objects.get(
            id=cart_item_id,
            product=product,
            cart=cart
        )
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()

        else:
            cart_item.delete()
    except Exception:
        pass
    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    cart = _get_cart(request)

    try:
        cart_item = CartItem.objects.get(
            id=cart_item_id,
            product=product,
            cart=cart
        )
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')


@login_required(login_url='login')
def checkout(request, total = 0, quantity = 0, cart_items = None):
    try:
        user = request.user
        cart = _get_cart(request)
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity

        grand_total = total
    except ObjectDoesNotExist:
        pass


    context = {
        'total' : total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'grand_total': grand_total,
        'first_name' : user.first_name,
        'last_name' : user.last_name,
        'email' : user.email,
        'phone_number': user.phone_number,
    }
    return render(request, 'checkout.html',context)
