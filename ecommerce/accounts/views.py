from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail.message import EmailMessage
from django.http import HttpResponse
from django.shortcuts import render, redirect

from carts.models import Cart, CartItem

from carts.views import _cart_id
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from accounts.forms import RegistrationForm
from accounts.models import Account

import requests



# Create your views here.
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                 password=password,
                phone_number=phone_number)
            user.is_active = False
            user.save()
            current_site = get_current_site(request=request)
            mail_subject = 'Activate your blog account.'
            message = render_to_string('active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            send_email = EmailMessage(mail_subject, message, to=[email])
            send_email.send()
            messages.success(
                request=request,
                message="Please confirm your email address to complete the registration"
            )
            return redirect('register')
        else:
            messages.error(request=request, message="Register failed!")
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'register.html', context)


def login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = auth.authenticate(email=email, password=password)
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart)
                if cart_items.exists():
                    product_variation = []
                    for cart_item in cart_items:
                        variations = cart_item.variations.all()
                        product_variation.append(list(variations))
                        # cart_item.user = user
                        # cart_item.save()
                    cart_items = CartItem.objects.filter(user=user)
                    existing_variation_list = [list(item.variations.all()) for item in cart_items]
                    id = [item.id for item in cart_items]

                    for product in product_variation:
                        if product in existing_variation_list:
                            index = existing_variation_list.index(product)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_items = CartItem.objects.filter(cart=cart)
                            for item in cart_items:
                                item.user = user
                                item.save()
            except Exception:
                pass
            auth.login(request=request, user=user)
            messages.success(request=request, message="Login successful!")

            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split("=") for x in query.split("&"))
                if "next" in params:
                    next_page = params["next"]
                    return redirect(next_page)
            except Exception:
                return redirect('dashboard')
        else:
            messages.error(request=request, message="Login failed!")
    context = {
        'email': email if 'email' in locals() else '',
        'password': password if 'password' in locals() else '',
    }
    return render(request, 'login.html', context=context)




@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    messages.success(request=request, message="You are logged out!")
    return redirect('login')



def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except Exception:
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request=request, message="Your account is activated, please login!")
        return render(request, 'login.html')
    else:
        messages.error(request=request, message="Activation link is invalid!")
        return redirect('home')




@login_required(login_url="login")
def dashboard(request):
    return render(request, "dashboard.html")



