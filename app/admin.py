from django.contrib import admin
from .models import OrderPlaced, Payment, Cart, Customer, Product ,Wishlist
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import Group
from .models import ContactMessage


# Register your models here.
@admin.register(Product)
class productModelAdmin(admin.ModelAdmin):
    list_display=['id','title','discounted_price','category','product_image']
    
@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id','user','locality','city','state','zipcode']
    

    
@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product_link', 'quantity']

    def product_link(self, obj):
        link = reverse("admin:app_product_change", args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', link, obj.product.title)

    product_link.short_description = "Product"

@admin.register(Payment)   
class PaymentModelAdmin(admin.ModelAdmin):
    list_display = ['id','user','amount','razorpay_order_id','razorpay_payment_status','razorpay_payment_id','paid']
    

@admin.register(OrderPlaced)
class OrderPlacedModeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'customer_link', 'product_link',
        'quantity', 'ordered_date', 'status', 'payment_link'
    ]

    def customer_link(self, obj):
        link = reverse("admin:app_customer_change", args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', link, obj.customer.name)
    customer_link.short_description = "Customer"

    def product_link(self, obj):
        link = reverse("admin:app_product_change", args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', link, obj.product.title)
    product_link.short_description = "Product"

    def payment_link(self, obj):
        link = reverse("admin:app_payment_change", args=[obj.payment.pk])
        return format_html('<a href="{}">{}</a>', link, obj.payment.razorpay_payment_id)
    payment_link.short_description = "Payment"


@admin.register(Wishlist)
class WishlistModelAdmin(admin.ModelAdmin):
     list_display = ['id','user','product_link']
     def product_link(self, obj):
        link = reverse("admin:app_product_change", args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', link, obj.product.title)

     product_link.short_description = "Product"
     
admin.site.unregister(Group)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')

#success@razorpay