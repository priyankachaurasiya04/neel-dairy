from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from django.db.models import Count
from django.views import View
from .models import Cart, Product, Customer, OrderPlaced, Payment, Wishlist, ContactMessage
from .forms import CustomerRegistrationForm, CustomerProfileForm
from django.contrib import messages
from django.conf import settings
import razorpay
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


# ----------------- Helper Function -----------------
def get_counts(request):
    if request.user.is_authenticated:
        totalitem = Cart.objects.filter(user=request.user).count()
        whisitem = Wishlist.objects.filter(user=request.user).count()
    else:
        totalitem = 0
        whisitem = 0
    return totalitem, whisitem


# ------------------------- Home / Static Pages -------------------------
@login_required
def home(request):
    totalitem, whisitem = get_counts(request)
    return render(request, "app/home.html", {
        "totalitem": totalitem,
        "whisitem": whisitem
    })


@login_required
def about(request):
    totalitem, whisitem = get_counts(request)
    return render(request, "app/about.html", {
        "totalitem": totalitem,
        "whisitem": whisitem
    })


@login_required
def contact(request):
    totalitem, whisitem = get_counts(request)

    if request.method == "POST":
        ContactMessage.objects.create(
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            message=request.POST.get("message")
        )
        messages.success(request, "Message sent successfully!")
        return redirect("contact")

    return render(request, "app/contact.html", {
        "totalitem": totalitem,
        "whisitem": whisitem
    })


# ------------------------- Category Views -------------------------
@method_decorator(login_required, name='dispatch')
class CategoryViews(View):
    def get(self, request, val):
        totalitem, whisitem = get_counts(request)
        product = Product.objects.filter(category=val)
        title = product.values('title').annotate(total=Count('title'))
        return render(request, "app/category.html", {
            "product": product,
            "title": title,
            "totalitem": totalitem,
            "whisitem": whisitem
        })


@method_decorator(login_required, name='dispatch')
class CategoryTitle(View):
    def get(self, request, val):
        totalitem, whisitem = get_counts(request)
        products = Product.objects.filter(title=val)
        if not products.exists():
            return redirect('/')

        title = Product.objects.filter(category=products[0].category).values('title')
        return render(request, "app/category.html", {
            'product': products,
            'title': title,
            'totalitem': totalitem,
            'whisitem': whisitem
        })


@method_decorator(login_required, name='dispatch')
class ProductDetail(View):
    def get(self, request, pk):
        totalitem, whisitem = get_counts(request)
        product = Product.objects.get(pk=pk)
        wishlist = Wishlist.objects.filter(user=request.user, product=product)
        return render(request, "app/productdetail.html", {
            "product": product,
            "wishlist": wishlist,
            "totalitem": totalitem,
            "whisitem": whisitem
        })


# ------------------ Registration ------------------
class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, "app/customerregistration.html", {
            "form": form
        })

    def post(self, request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Congratulations! User registered successfully.")
        else:
            messages.warning(request, "Invalid input data.")
        return render(request, "app/customerregistration.html", {
            "form": form
        })


# ------------------------- Profile -------------------------
@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        totalitem, whisitem = get_counts(request)
        form = CustomerProfileForm()
        return render(request, 'app/profile.html', {
            "form": form,
            "totalitem": totalitem,
            "whisitem": whisitem
        })

    def post(self, request):
        totalitem, whisitem = get_counts(request)
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            customer, created = Customer.objects.get_or_create(user=request.user)
            for field in ['name', 'locality', 'city', 'mobile', 'state', 'zipcode']:
                setattr(customer, field, form.cleaned_data[field])
            customer.save()
            messages.success(request, "Profile saved successfully!")
        else:
            messages.warning(request, "Invalid input. Please check the form.")
        return render(request, 'app/profile.html', {
            "form": form,
            "totalitem": totalitem,
            "whisitem": whisitem
        })


# ------------------------- Address Management -------------------------
@login_required
def address(request):
    totalitem, whisitem = get_counts(request)
    add = Customer.objects.filter(user=request.user)
    return render(request, 'app/address.html', {
        "add": add,
        "totalitem": totalitem,
        "whisitem": whisitem
    })


@method_decorator(login_required, name='dispatch')
class updateAddress(View):
    def get(self, request, pk):
        totalitem, whisitem = get_counts(request)
        add = Customer.objects.get(pk=pk)
        form = CustomerProfileForm(instance=add)
        return render(request, 'app/updateAddress.html', {
            "form": form,
            "totalitem": totalitem,
            "whisitem": whisitem
        })

    def post(self, request, pk):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            add = Customer.objects.get(pk=pk)
            for field in ['name', 'locality', 'city', 'mobile', 'state', 'zipcode']:
                setattr(add, field, form.cleaned_data[field])
            add.save()
            messages.success(request, "Profile updated successfully!")
        else:
            messages.warning(request, "Invalid input.")
        return redirect("address")


# ------------------------- Cart Management -------------------------
@login_required
def add_to_cart(request):
    user = request.user
    product_id = request.GET.get('prod_id')
    try:
        product = Product.objects.get(id=int(product_id))
    except:
        messages.warning(request, "Invalid product ID.")
        return redirect("/")
    cart_item, created = Cart.objects.get_or_create(user=user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, "Item added to cart.")
    return redirect("/cart/")


@login_required
def show_cart(request):
    totalitem, whisitem = get_counts(request)
    user = request.user
    cart = Cart.objects.filter(user=user)
    amount = sum(p.quantity * p.product.discounted_price for p in cart)
    totalamount = amount + 40
    return render(request, 'app/addtocart.html', {
        "cart": cart,
        "totalamount": totalamount,
        "totalitem": totalitem,
        "whisitem": whisitem
    })


# ------------------------- Checkout -------------------------
@method_decorator(login_required, name='dispatch')
class checkout(View):
    def get(self, request):
        totalitem, whisitem = get_counts(request)
        user = request.user
        add = Customer.objects.filter(user=user)
        cart_items = Cart.objects.filter(user=user)
        amount = sum(p.quantity * p.product.discounted_price for p in cart_items)
        totalamount = amount + 40
        razoramount = int(totalamount * 100)

        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        data = {"amount": razoramount, "currency": "INR", "receipt": "order_rcptid_12"}
        payment_response = client.order.create(data=data)

        order_id = payment_response['id']

        payment = Payment.objects.create(
            user=user,
            amount=totalamount,
            razorpay_order_id=order_id,
            razorpay_payment_status=payment_response['status']
        )

        return render(request, 'app/checkout.html', {
            "add": add,
            "cart_items": cart_items,
            "totalamount": totalamount,
            "order_id": order_id,
            "totalitem": totalitem,
            "whisitem": whisitem
        })


@login_required
def payment_done(request):
    order_id = request.GET.get('order_id')
    payment_id = request.GET.get('payment_id')
    cust_id = request.GET.get('cust_id')

    user = request.user
    customer = Customer.objects.get(id=cust_id)

    payment = Payment.objects.get(razorpay_order_id=order_id)
    payment.paid = True
    payment.razorpay_payment_id = payment_id
    payment.save()

    cart = Cart.objects.filter(user=user)
    for c in cart:
        OrderPlaced.objects.create(
            user=user,
            customer=customer,
            product=c.product,
            quantity=c.quantity,
            payment=payment
        )
        c.delete()

    return redirect("orders")


@login_required
def orders(request):
    totalitem, whisitem = get_counts(request)
    order_placed = OrderPlaced.objects.filter(user=request.user)
    return render(request, 'app/orders.html', {
        "order_placed": order_placed,
        "totalitem": totalitem,
        "whisitem": whisitem
    })


# ------------------------- Cart Quantity Operations -------------------------
@login_required
def plus_cart(request):
    prod_id = request.GET.get('prod_id')
    c = Cart.objects.get(product=prod_id, user=request.user)
    c.quantity += 1
    c.save()

    cart = Cart.objects.filter(user=request.user)
    amount = sum(p.quantity * p.product.discounted_price for p in cart)
    totalamount = amount + 40

    return JsonResponse({'quantity': c.quantity, 'amount': amount, 'totalamount': totalamount})


@login_required
def minus_cart(request):
    prod_id = request.GET.get('prod_id')
    c = Cart.objects.get(product=prod_id, user=request.user)

    if c.quantity > 1:
        c.quantity -= 1
        c.save()
    else:
        c.delete()

    cart = Cart.objects.filter(user=request.user)
    amount = sum(p.quantity * p.product.discounted_price for p in cart)
    totalamount = amount + 40

    return JsonResponse({'amount': amount, 'totalamount': totalamount})


@login_required
def remove_cart(request):
    prod_id = request.GET.get('prod_id')
    Cart.objects.filter(product=prod_id, user=request.user).delete()

    cart = Cart.objects.filter(user=request.user)
    amount = sum(p.quantity * p.product.discounted_price for p in cart)
    totalamount = amount + 40

    return JsonResponse({'amount': amount, 'totalamount': totalamount})


# ------------------------- Wishlist -------------------------
@login_required
def plus_wishlist(request):
    prod_id = request.GET.get('prod_id')
    product = Product.objects.get(id=prod_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return JsonResponse({'message': 'Wishlist Added Successfully'})


@login_required
def minus_wishlist(request):
    prod_id = request.GET.get('prod_id')
    Wishlist.objects.filter(user=request.user, product_id=prod_id).delete()
    return JsonResponse({'message': 'Wishlist Removed Successfully'})


# ------------------------- Search -------------------------
@login_required
def search(request):
    totalitem, whisitem = get_counts(request)
    query = request.GET.get('search', '')
    product = Product.objects.filter(title__icontains=query)
    return render(request, 'app/search.html', {
        "product": product,
        "totalitem": totalitem,
        "whisitem": whisitem
    })


@login_required
def wishlist(request):
    totalitem, whisitem = get_counts(request)
    wish_items = Wishlist.objects.filter(user=request.user)
    return render(request, "app/wishlist.html", {
        "wishlist": wish_items,
        "totalitem": totalitem,
        "whisitem": whisitem
    })
