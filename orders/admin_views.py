from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render,redirect,get_object_or_404
from .models import Order,OrderItem,OrderStatusHistory
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from products.models import Product,ProductVariant
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from django.views.decorators.cache import never_cache
from adminpanel.decorators import admin_required
from django.db import transaction


@never_cache
@admin_required
@login_required(login_url='admin_login')
def admin_order_list(request):

    orders = Order.objects.all().order_by('-created_at')

    search = request.GET.get('search')

    if search:
        orders = orders.filter(
            Q(order_id__icontains=search) |
            Q(full_name__icontains=search) |
            Q(user__email__icontains=search)
        )

    status = request.GET.get('status') 

    if status:
        orders = orders.filter(status=status) 

    sort = request.GET.get('sort') 

    if sort == 'oldest':
        orders = orders.order_by('created_at')

    elif sort == 'latest':
        orders = orders.order_by('-created_at') 

    paginator = Paginator(orders, 10) 
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)


    context = {
        'orders': orders,
    }

    return render(request,'admin_orders.html', context)


@never_cache
@admin_required
@login_required(login_url='admin_login')
def admin_order_details(request, order_id):

    order = get_object_or_404(Order, order_id = order_id)
    order_items = OrderItem.objects.filter(order=order)
    timeline = order.history.order_by('timestamp')

    context = {
        'order': order,
        'order_items': order_items,
        'timeline': timeline,
        'status_choices': order.STATUS_CHOICES,
    }

    return render(request, 'admin_order_details.html', context)


@never_cache
@admin_required
@login_required(login_url='admin_login')
def admin_update_order_status(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')

        valid_status = [
            'pending',
            'confirmed',
            'processing',
            'shipped',
            'out_for_delivery',
            'delivered',
            'cancelled',
            'return_requested',
            'returned',
            'return_rejected',
        ]
 
        if new_status in valid_status and order.status.lower() != new_status.lower():
            with transaction.atomic():
                # If changing to returned or cancelled, restore stock for items not already cancelled or returned
                if new_status.lower() in ['cancelled', 'returned']:
                    for item in order.items.all():
                        if item.item_status.lower() not in ['cancelled', 'returned']:
                            variant = item.variant
                            variant.stock += item.quantity
                            variant.save()
                            item.item_status = new_status.lower()
                            item.save()

                order.status = new_status.lower()
                order.save()

                order.items.exclude(
                    item_status__in=['cancelled', 'returned', 'Cancelled', 'Returned']
                ).update(
                    item_status=new_status.lower()
                )

                OrderStatusHistory.objects.create(
                    order = order,
                    status = new_status
                )

                # Refund logic
                from accounts.models import Wallet, WalletTransaction
                wallet, _ = Wallet.objects.get_or_create(user=order.user)

                if new_status.lower() == 'cancelled':
                    # Only paid methods online and wallet get direct refund for cancellations
                    if order.payment_method in ['online', 'wallet']:
                        already_refunded = WalletTransaction.objects.filter(
                            wallet=wallet, order=order, transaction_type='refund', description__icontains="cancelled"
                        ).exists()
                        if not already_refunded:
                            wallet.deposit(
                                amount=order.total_amount,
                                description=f"Refund for cancelled Order #{order.order_id}",
                                transaction_type='refund',
                                order=order
                            )
                            messages.success(request, f"Refund of ₹{order.total_amount} credited to customer's wallet.")

                elif new_status.lower() == 'returned':
                    # All returns get wallet refunds upon admin confirmation
                    already_refunded = WalletTransaction.objects.filter(
                        wallet=wallet, order=order, transaction_type='refund', description__icontains="returned"
                    ).exists()
                    if not already_refunded:
                        wallet.deposit(
                            amount=order.total_amount,
                            description=f"Refund for returned Order #{order.order_id}",
                            transaction_type='refund',
                            order=order
                        )
                        messages.success(request, f"Refund of ₹{order.total_amount} credited to customer's wallet.")

            messages.success(request,'Order status updated successfully')
        else:
            messages.error(request, f'Invalid or unchanged status:{new_status}')    

    return redirect('admin_order_details', order_id=order.order_id)


@never_cache
@admin_required
@login_required(login_url='admin_login')
def inventory_management(request):

    variants = ProductVariant.objects.select_related('product').all().order_by('product__product_name')

    search = request.GET.get('search')

    if search:
        variants = variants.filter(
            Q(product__product_name__icontains=search) |
            Q(color__icontains=search) |
            Q(size__icontains=search)
        )

    stock_filter = request.GET.get('stock') 

    if stock_filter == 'in_stock':
        variants = variants.filter(stock__gt=0)

    elif stock_filter == 'out_stock':
        variants = variants.filter(stock=0)

    elif stock_filter == 'low_stock':
        variants = variants.filter(stock__lte=5,stock__gt=0)

    variants = variants.order_by('stock')

    paginator = Paginator(variants,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'variants': variants,
        'page_obj': page_obj,
    }   

    return render(request, 'inventory.html', context) 

@never_cache
@admin_required
@login_required(login_url='admin_login')
def update_stock(request, variant_id):

    variant = get_object_or_404(ProductVariant, id=variant_id)

    if request.method == 'POST':

        stock = request.POST.get('stock')

        variant.stock = stock
        variant.save()

        messages.success(request, 'Stock updated successfully')

        return redirect('inventory_management')

    context = {
        'variant': variant
    }

    return render(request, 'update_stock.html', context)    




