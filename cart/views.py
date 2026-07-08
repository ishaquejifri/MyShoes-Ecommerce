from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from products.models import Product
from .models import Cart,CartItem
from django.http import JsonResponse
from django.contrib import messages
from category.models import Category
from products.models import ProductVariant
from wishlist.models import Wishlist
from django.views.decorators.cache import never_cache


# Create your views here.
@never_cache
@login_required(login_url='login')
def add_to_cart(request,product_id):
    if not request.user.is_authenticated:
        messages.warning(request,"⚠️ Please Login to purchase the Product")
        return redirect(f'/user/login/?next=/cart/add/{product_id}/')

    product = get_object_or_404(Product,id=product_id)

    variant_id = request.POST.get('variant_id')
    
    if not variant_id:
        messages.error(request,'Please select size and color.')
        return redirect(request.META.get('HTTP_REFERER', 'wishlist'))

    variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

    # Product availability check
    if not product.is_available or product.is_blocked:
        messages.error(request, "This product is unavailable.")
        return redirect('user_product_list')
    
    # Variant stock check
    if variant.stock <= 0:
        messages.error(request,'Selected variant is out of stock.')
        return redirect('wishlist')

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant,
        defaults={
            'quantity': 1,
            'price': product.offer_price or product.base_price
                  })

    #already exists in cart
    if not item_created:
        
        #max quantity check
        if cart_item.quantity >= CartItem.MAX_QUANTITY_PER_PRODUCT:
            messages.error(request,'Maximum quantity reached.')
            return redirect('cart:view_cart')
        
        #variant stock limit check
        if cart_item.quantity >= variant.stock:
            messages.error(request,'No More stock available.')
            return redirect('cart:view_cart')
        cart_item.quantity += 1
        cart_item.save()

        messages.success(request,'Quantity increased in cart')
    else:
        messages.success(request,'Product added to the cart') 

    #remove from wishlist
    if request.POST.get('from_wishlist') == 'true':
        Wishlist.objects.filter(
        user=request.user,
        product=product
    ).delete()
    return redirect('cart:view_cart')       


@never_cache
@login_required(login_url='login')
def view_cart(request):
    categories = Category.objects.filter(is_active=True)  
    cart, created = Cart.objects.get_or_create(user = request.user)
    cart_items = cart.items.all()

    cart_count = sum(item.quantity for item in cart.items.all())
    total = sum(item.subtotal() for item in cart_items)

    return render(request,'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
        'categories': categories,
    })  

@never_cache
@login_required(login_url='login')
def update_cart(request,item_id, action):
    cart_item = get_object_or_404(CartItem,id=item_id,cart__user=request.user)

    if action == 'increase' and cart_item.quantity < cart_item.product.stock:
        cart_item.quantity += 1

    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            cart_item.delete()
            return redirect('cart:view_cart')

    cart_item.save()
    return redirect('cart:view_cart')  

@login_required(login_url='login')
def ajax_update_cart(request):
    if request.method == "POST":
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')

        cart_item = get_object_or_404(CartItem,id=item_id,cart__user=request.user)

        message = ""

        if action == 'increase':
            if cart_item.quantity < cart_item.variant.stock:
                cart_item.quantity += 1
                cart_item.save()
            else:
                message = f'Only {cart_item.variant.stock} items available in stock.'   
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()

        cart = cart_item.cart
        total = sum(item.subtotal() for item in cart_item.cart.items.all())

        return JsonResponse({
            'success': True,
            'message': message,
            'quantity': cart_item.quantity,
            'subtotal': float(cart_item.subtotal()),
            'total': float(total),
            'cart_count': cart_item.cart.items.count()
        })
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})                

@never_cache
@login_required(login_url='login')
def remove_from_cart(request,item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()

    return redirect('cart:view_cart')
                    




