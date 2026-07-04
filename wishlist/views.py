from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wishlist
from products.models import Product
from category.models import Category
from decimal import Decimal
from cart.models import Cart,CartItem

# Create your views here.


@never_cache
@login_required
def wishlist(request):
    categories = Category.objects.filter(is_active=True)

    if not request.user.is_authenticated:
        return redirect('login')
    
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')

    total_price = sum(
        (
            item.product.offer_price or item.product.base_price or Decimal('0.00')
        )
           for item in wishlist_items
    )

    context = {
        'wishlist_items': wishlist_items,
        'total_price': total_price,
        'categories': categories,
    }

    return render(request,'wishlist.html', context)

@never_cache
@login_required
def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        messages.warning(request,'Please Login First')
        return redirect('login')
    
    product = get_object_or_404(Product, id=product_id)

    wishlist_item,created = Wishlist.objects.get_or_create(user = request.user,product=product)

    if created:
        messages.success(request,'Product Added to the Wishlist')
    else:
        messages.info(request,'Product Already in Wishlist')

    return redirect('wishlist')  

@never_cache
@login_required
def remove_wishlist(request,wishlist_id):
    wishlist_item = get_object_or_404(Wishlist, id=wishlist_id,user=request.user)
    wishlist_item.delete()

    messages.success(request,'Item Removed from Wishlist')

    return redirect('wishlist') 

@never_cache
@login_required
def clear_wishlist(request):
    if request.method == 'POST':
        Wishlist.objects.filter(user=request.user).delete()
        messages.success(request, 'Wishlist Cleared Successfully.')
    return redirect('wishlist')    


# @never_cache
# @login_required
# def move_all_to_cart(request):

#     if request.method == "POST":

#         wishlist_items = Wishlist.objects.filter(
#             user=request.user
#         ).select_related('product')

#         cart, created = Cart.objects.get_or_create(
#             user=request.user
#         )

#         moved_count = 0

#         for item in wishlist_items:

#             variants = item.product.variants.filter(stock__gt=0)

#             if variants.count() == 1:

#                 variant = variants.first()

#                 cart_item, created = CartItem.objects.get_or_create(
#                     cart=cart,
#                     product_variant=variant,
#                     defaults={'quantity': 1}
#                 )

#                 if not created:
#                     cart_item.quantity += 1
#                     cart_item.save()

#                 item.delete()
#                 moved_count += 1

#         messages.success(
#             request,
#             f"{moved_count} item(s) moved to cart."
#         )

#     return redirect('wishlist')
