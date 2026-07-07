from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from products.models import Product
from category.models import Category
from django.core.paginator import Paginator
from wishlist.models import Wishlist
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from banner.models import Banner
from django.utils import timezone
from coupons.models import Coupon




def home_page(request):

    categories = Category.objects.filter(is_active=True)
    banners = Banner.objects.filter(is_active=True)
    products = Product.objects.select_related('category').filter(
        is_deleted=False,
        is_available=True,
        is_blocked=False,
        is_listed=True
    ).order_by('-id')[:8]

    return render(request,'home.html', {
        'categories' : categories,
        'products' : products,
        'banners': banners,  
    })


@never_cache
@login_required
def user_product_list(request, category_id=None):
    products = Product.objects.filter(
        is_deleted=False,
        is_available=True,
        is_blocked=False,
        is_listed=True
    )
    categories = Category.objects.filter(is_active=True)
    
    category = None
    category_id = request.GET.get('category')

    if category_id:
        category = Category.objects.filter(id=category_id, is_active=True).first()

        if category:
            products = products.filter(category=category)
        else:
            messages.warning(request, 'No More.')    

    wishlist_product_ids = []

    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(
            user = request.user,
        ).values_list('product_id',flat=True)

    search_query = request.GET.get('search','')
    sort_option = request.GET.get('sort','')
    min_price = request.GET.get('min_price','')
    max_price = request.GET.get('max_price','')

    if search_query:
        products = products.filter(product_name__icontains=search_query)

    if min_price:
        products = products.filter(base_price__gte=min_price)

    if max_price:
        products = products.filter(base_price__lte=max_price) 

    if sort_option == 'price_low':
        products = products.order_by('base_price') 
    elif sort_option == 'price_high':
        products = products.order_by('-base_price')
    elif sort_option == 'a_z':
        products = products.order_by('product_name') 
    elif sort_option == 'z_a':
        products = products.order_by('-product_name')                     

     
    paginator = Paginator(products,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

        
    return render(request,'user_product_list.html', {
        'page_obj': page_obj,
        'category': category,
        'search_query': search_query,
        'sort_option': sort_option,
        'min_price': min_price,
        'max_price': max_price,
        'categories': categories,
        'wishlist_product_ids': wishlist_product_ids,

    })


@never_cache
@login_required
def user_product_details(request,pk):
    categories = Category.objects.filter(is_active=True)
    coupons = Coupon.objects.filter(is_active=True) 
    try:
        product = get_object_or_404(Product,
                                 pk=pk,
                                 is_deleted=False
                                 )
    except Product.DoesNotExist:
        return render(request, '404.html', status=404)    
    
    if ( not product.is_listed  or not product.is_available or product.is_blocked ):
        return render(
        request,
        'product_unavailable.html',
        {'product': product},
        status=404
    )

    variants = product.variants.all()

    sizes = variants.values_list('size', flat=True).distinct()
    colors = variants.values_list('color', flat=True).distinct()

    total_stock = sum(variant.stock for variant in variants)
        
    related_products = Product.objects.filter(
        category = product.category,
        is_listed=True,
        is_deleted=False,
        is_available=True,
        is_blocked=False
    ).exclude(id=product.id)[:4]

    if not product.is_available or product.is_blocked:
        messages.error(request,'Product Unavailable')
        return redirect('product_unavailable')

    return render(request,'user_product_details.html',{
        'product': product,
        'related_products': related_products,
        'categories': categories,
        'variants': variants,
        'total_stock': total_stock,
        'sizes': sizes,
        'colors': colors,
        'coupons': coupons,
    })


@never_cache
@login_required
def add_to_wishlist(request,product_id):
    product = get_object_or_404(Product, id = product_id)

    wishlist_item = Wishlist.objects.filter(
        user = request.user,
        product = product
    ).first()

    if wishlist_item:
        wishlist_item.delete()
        messages.warning(request, f'{product.product_name} removed from wishlist 💔')
    else:
        Wishlist.objects.create(user=request.user,product=product)
        messages.success(request, f'{product.product_name} added to wishlist ❤️') 

    return redirect(request.META.get('HTTP_REFERER'))       

    

def product_unavailable(request):

    return render(request,'product_unavailable.html')
