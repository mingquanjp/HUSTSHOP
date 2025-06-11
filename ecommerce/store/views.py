from decimal import Decimal, InvalidOperation

from django.forms import FloatField
from unicodedata import category

from django.contrib import messages
from django.shortcuts import render, redirect

# Create your views here.
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from store.forms import ReviewForm
from django.db.models import Q, Avg, Case, When, Count

from store.models import Category, Product

from orders.models import OrderProduct

from reviews.models import Review

from carts.models import Cart, CartItem

from carts.views import _cart_id

from store.models import Variation


def store(request, category_slug=None):
    products = Product.objects.filter(is_available=True)

    # Filter theo category
    if category_slug is not None:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Lấy các tham số filter từ URL
    size_filter = request.GET.getlist('size')
    color_filter = request.GET.getlist('color')
    min_price = request.GET.get('min_price', '0')
    max_price = request.GET.get('max_price', '500000')
    star_filter = request.GET.get('star_rating', '')

    # Áp dụng các filters
    if size_filter:
        products = products.filter(
            variations__variation_category='size',
            variations__variation_value__in=size_filter,
            variations__is_active=True
        ).distinct()

    if color_filter:
        products = products.filter(
            variations__variation_category='color',
            variations__variation_value__in=color_filter,
            variations__is_active=True
        ).distinct()

    # Filter theo giá
    if min_price and min_price != '0':
        try:
            min_price_decimal = Decimal(str(min_price))
            products = products.filter(price__gte=min_price_decimal)
        except (ValueError, TypeError, InvalidOperation):
            pass

    if max_price and max_price != '500000':
        try:
            max_price_decimal = Decimal(str(max_price))
            products = products.filter(price__lte=max_price_decimal)
        except (ValueError, TypeError, InvalidOperation):
            pass

    # Filter theo rating
    if star_filter:
        try:
            star_rating = float(star_filter)
            products = products.annotate(
                avg_rating=Avg('review__rating', filter=Q(review__status=True)),
                review_count=Count('review', filter=Q(review__status=True))
            ).filter(
                Q(avg_rating__gte=star_rating) | Q(review_count=0)
            )
        except (ValueError, TypeError):
            pass

    all_products_for_variations = Product.objects.filter(is_available=True)
    if category_slug:
        all_products_for_variations = all_products_for_variations.filter(category__slug=category_slug)

    # Lấy danh sách sizes và colors có sẵn
    variations = Variation.objects.filter(
        product__in=products,
        is_active=True
    ).values('variation_category', 'variation_value').distinct()

    available_sizes = set()
    available_colors = set()

    for var in variations:
        if var['variation_category'] == 'size':
            available_sizes.add(var['variation_value'])
        elif var['variation_category'] == 'color':
            available_colors.add(var['variation_value'])

    # Pagination
    paginator = Paginator(products.order_by('-created_at'), 6)
    page = request.GET.get('page', 1)
    paged_products = paginator.get_page(page)

    context = {
        'products': paged_products,
        'product_count': products.count(),
        'categories': Category.objects.all(),
        'current_category_slug': category_slug,
        'available_sizes': sorted(available_sizes),
        'available_colors': sorted(available_colors),
        'selected_sizes': size_filter,
        'selected_colors': color_filter,
        'current_min_price': min_price or '0',
        'current_max_price': max_price or '2000+',
        'current_star_rating': star_filter or '',
    }

    return render(request, 'store.html', context)


def product_detail(request, category_slug, product_slug=None):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        cart = Cart.objects.get(cart_id=_cart_id(request=request))
        in_cart = CartItem.objects.filter(
            cart=cart,
            product=single_product
        ).exists()
    except Exception as e:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )

    try:
        orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
    except Exception:
        orderproduct = None

    reviews = Review.objects.filter(product_id=single_product.id, status=True)

    context = {
        'single_product': single_product,
        'in_cart': in_cart if 'in_cart' in locals() else False,
        'orderproduct': orderproduct,
        'reviews': reviews,
    }
    return render(request, 'product_detail.html', context=context)


def search(request):
    products = Product.objects.none()
    q = ''
    product_count = 0

    if 'q' in request.GET:
        q = request.GET.get('q')
        if q:
            products = Product.objects.order_by('-created_at').filter(
                Q(name__icontains=q) | Q(description__icontains=q),
                is_available=True
            )
            product_count = products.count()

    # Apply same filtering logic as store view
    size_filter = request.GET.getlist('size')
    color_filter = request.GET.getlist('color')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    star_filter = request.GET.get('star_rating')

    # Apply filters if products exist
    if products.exists():
        if size_filter:
            products = products.filter(
                variations__variation_category='size',
                variations__variation_value__in=size_filter,
                variations__is_active=True
            ).distinct()

        if color_filter:
            products = products.filter(
                variations__variation_category='color',
                variations__variation_value__in=color_filter,
                variations__is_active=True
            ).distinct()

        if min_price and min_price != '0':
            try:
                products = products.filter(price__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass

        if max_price and max_price not in ['500000', '']:
            try:
                products = products.filter(price__lte=Decimal(max_price))
            except (ValueError, TypeError):
                pass

        if star_filter:
            try:
                star_rating = float(star_filter)
                products = products.annotate(
                    avg_rating=Avg('review__rating', filter=Q(review__status=True)),
                    review_count=Count('review', filter=Q(review__status=True))
                ).filter(
                    Q(avg_rating__gte=star_rating) | Q(review_count=0)
                )
            except (ValueError, TypeTypeError):
                pass

        product_count = products.count()

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 6)
    paged_products = paginator.get_page(page)

    context = {
        'products': paged_products,
        'q': q,
        'product_count': product_count,
        'categories': Category.objects.all(),
        'selected_sizes': size_filter,
        'selected_colors': color_filter,
        'current_min_price': min_price or '0',
        'current_max_price': max_price or '500000',
        'current_star_rating': star_filter or '',
    }
    return render(request, 'store.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        try:
            review = Review.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=review)
            form.save()
            messages.success(request, "Thank you! Your review has been updated.")
            return redirect(url)
        except Exception:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = Review()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, "Thank you! Your review has been submitted.")
                return redirect(url)
