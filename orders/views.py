from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
import string,random
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db import transaction
from cart.models import Cart
from .models import Order,OrderItem
from accounts.models import Address, Wallet, WalletTransaction
from category.models import Category
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO
from coupons.models import Coupon
from payments.models import Payment
import razorpay
from django.conf import settings
# Create your views here.

client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    )
)


def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

@login_required
def checkout(request):
    categories = Category.objects.filter(is_active=True)
    cart = get_object_or_404(Cart,user=request.user)

    cart_items = cart.items.all()

    if not cart_items.exists():
        messages.error(request,'Your cart is empty')
        return redirect('cart:view_cart')
    
    addresses = Address.objects.filter(user=request.user)

    subtotal = sum(item.subtotal() for item in cart_items)

    if subtotal >= 5000:
        shipping_charge = Decimal('0.00')
    else:
        shipping_charge = Decimal('40.00')     

    # Coupon details calculation
    coupon_code = request.session.get('coupon_code')
    coupon_discount = Decimal('0.00')
    coupon = None
    if coupon_code:
        try:
            from coupons.models import Coupon
            coupon = Coupon.objects.get(code=coupon_code)
            is_valid, msg = coupon.is_valid()
            if is_valid:
                can_use, msg_use = coupon.can_user_use(request.user)
                if can_use and subtotal >= coupon.min_purchase_amount:
                    coupon_discount, _ = coupon.calculate_discount(subtotal)
                else:
                    request.session.pop('coupon_code', None)
                    coupon = None
            else:
                request.session.pop('coupon_code', None)
                coupon = None
        except Coupon.DoesNotExist:
            request.session.pop('coupon_code', None)

    # Available coupons for this user
    from coupons.models import Coupon, CouponUsage
    from django.db.models import Exists, OuterRef
    today = __import__('django.utils.timezone', fromlist=['now']).now().date()
    all_active = Coupon.objects.filter(
        is_active=True, start_date__lte=today, end_date__gte=today
    ).annotate(
        user_has_used=Exists(CouponUsage.objects.filter(coupon=OuterRef('pk'), user=request.user))
    )
    available_coupons = []
    for c in all_active:
        if c.usage_limit and c.times_used >= c.usage_limit:
            continue
        if c.one_time_use and c.user_has_used:
            continue
        available_coupons.append(c)

    total = subtotal + shipping_charge - coupon_discount

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    context = {
        'categories': categories,
        'cart_items': cart_items,
        'addresses': addresses,
        'subtotal': subtotal,
        'shipping_charge': shipping_charge,
        'coupon': coupon,
        'coupon_discount': coupon_discount,
        'wallet': wallet,
        'total': total,
        'available_coupons': available_coupons,
    }

    return render(request, 'checkout.html', context)

@login_required
def place_order(request):
    if request.method != 'POST':
        return redirect('checkout')
    
    cart = get_object_or_404(Cart,user=request.user)
    cart_items = cart.items.all()

    if not cart_items.exists():
        messages.error(request,'Cart is empty')
        return redirect('cart:view_cart')
    
    address_id = request.POST.get('address_id')
    payment_method = request.POST.get('payment_method', 'cod')

    if not address_id:
        messages.error(request,'Please select an address')
        return redirect('checkout')
    
    address = get_object_or_404(Address,id=address_id, user=request.user)

    subtotal = sum(item.subtotal() for item in cart_items)
    shipping = Decimal('0.00') if subtotal >= 5000 else Decimal('40.00')
    
    # Coupon Discount logic
    coupon_code = request.session.get('coupon_code')
    coupon_discount = Decimal('0.00')
    coupon = None
    if coupon_code:
        try:
            from coupons.models import Coupon, CouponUsage
            coupon = Coupon.objects.get(code=coupon_code)
            is_valid, msg = coupon.is_valid()
            if is_valid:
                can_use, msg_use = coupon.can_user_use(request.user)
                if can_use and subtotal >= coupon.min_purchase_amount:
                    coupon_discount, _ = coupon.calculate_discount(subtotal)
        except Coupon.DoesNotExist:
            pass

    grand_total = subtotal + shipping - coupon_discount

    if payment_method == 'wallet':
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        if wallet.balance < grand_total:
            messages.error(request, 'Insufficient wallet balance.')
            return redirect('checkout')

    try:
        with transaction.atomic():
            order_id = generate_order_id()
            order = Order.objects.create(
                order_id = order_id,
                user = request.user,
                shipping_address = address,
                full_name = address.full_name,
                mobile = address.phone,
                street_address = address.address_line,
                city = address.city,
                state = address.state,
                postal_code = address.postal_code,
                payment_method = payment_method,
                status = 'confirmed' if payment_method == 'wallet' else 'pending',
                sub_total = subtotal,
                shipping_charge = shipping,
                coupon_discount = coupon_discount,
                total_amount = grand_total,
            )


            # ==========================
            # ONLINE PAYMENT
            # ==========================

            if payment_method == "online":

                razorpay_order = client.order.create({
                "amount": int(grand_total * 100),
                "currency": "INR",
                "receipt": order.order_id,
                "payment_capture": 1
                })

                Payment.objects.create(
                user=request.user,
                order=order,
                amount=grand_total,
                razorpay_order_id=razorpay_order["id"],
                status="Pending"
                )

                # Create Order Items
                for item in cart_items:

                    OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    product_name=item.product.product_name,
                    variant_size=item.variant.size,
                    variant_color=item.variant.color,
                    price=item.price,
                    original_price=item.product.base_price,
                    discount_amount=item.product.base_price-item.price,
                    quantity=item.quantity,
                    item_status="placed"
                )
                

                return render(
                    request,
                    "payment.html",
                    {   
                    "order": order,
                    "razorpay_key": settings.RAZORPAY_KEY_ID,
                    "razorpay_order_id": razorpay_order["id"],
                    "amount": int(grand_total * 100),
                }
            )


            # Deduct from Wallet if selected
            if payment_method == 'wallet':
                wallet, _ = Wallet.objects.get_or_create(user=request.user)
                wallet.withdraw(
                    grand_total,
                    f"Payment for Order #{order_id}",
                    transaction_type='payment',
                    order=order
                )
                order.payment_status = 'Paid'
                order.save()
                
                # Create Payment object for wallet
                Payment.objects.create(
                    user=request.user,
                    order=order,
                    amount=grand_total,
                    status='Success'
                )
            elif payment_method == 'cod':
                # Create Payment object for COD
                Payment.objects.create(
                    user=request.user,
                    order=order,
                    amount=grand_total,
                    status='Pending'
                )

            # Record Coupon Usage
            if coupon and coupon_discount > 0:
                CouponUsage.objects.create(
                    coupon=coupon,
                    user=request.user,
                    order=order,
                    discount_amount=coupon_discount,
                    cart_total_before_discount=subtotal
                )
                coupon.times_used += 1
                coupon.save(update_fields=['times_used'])

            for item in cart_items:
                variant = item.variant
                if variant.stock < item.quantity:
                    raise ValueError(f"Only {variant.stock} stock available for {item.product.product_name}")
                
                OrderItem.objects.create(
                    order = order,
                    product = item.product,
                    variant = variant,
                    product_name = item.product.product_name,
                    variant_size = variant.size,
                    variant_color = variant.color,
                    price = item.price,
                    original_price = item.product.base_price,
                    discount_amount = item.product.base_price - item.price,
                    quantity = item.quantity,
                    item_status = 'confirmed' if payment_method == 'wallet' else 'placed'
                )
                if payment_method != 'online':
                    variant.stock -= item.quantity
                    variant.save()
        
            cart_items.delete()
            request.session.pop('coupon_code', None)

    except Exception as e:
        messages.error(request, str(e))
        return redirect('checkout')

    messages.success(request,"Order Placed Successfully")
    return redirect('order_success', order_id = order.order_id)

@login_required
def order_success(request,order_id):
    order = get_object_or_404(Order, order_id = order_id, user= request.user)
    categories = Category.objects.filter(is_active=True)
    order_items = order.items.all()

    return render(request,'order_success.html',{
        'order': order,
        'order_items': order_items,
        'categories': categories,
        })

@login_required
def my_order(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    categories = Category.objects.filter(is_active=True)

    context = {
        'orders': orders,
        'categories': categories,
    }

    return render(request,'order_list.html', context)

@login_required
def cancel_order(request,order_id):
    categories = Category.objects.filter(is_active=True)
    order = get_object_or_404(Order, order_id=order_id,user=request.user)

    if order.status.lower() == 'delivered':
        messages.error(request,'Delivered orders cannot be cancelled' )
        return redirect('my_orders')

    if order.status.lower() == 'cancelled':
        messages.warning(request,'Order already cancelled')
        return redirect('my_orders')
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
       
        with transaction.atomic():
            #Restore stock
            for item in order.items.all():
                if item.item_status.lower() not in ['cancelled', 'returned']:
                    variant = item.variant
                    variant.stock += item.quantity
                    variant.save()

                    item.item_status = 'cancelled'
                    item.save()

            order.status = 'cancelled'
            order.cancellation_reason = reason
            
            old_total_amount = order.total_amount
            order.update_total()
            order.save()

            # Process refund directly if paid via online or wallet
            if order.payment_method in ['online', 'wallet']:
                wallet, _ = Wallet.objects.get_or_create(user=order.user)
                wallet.deposit(
                    amount=old_total_amount,
                    description=f"Refund for cancelled Order #{order.order_id}",
                    transaction_type='refund',
                    order=order
                )
                messages.success(request, f"Refund of ₹{old_total_amount} credited to your wallet.")

        messages.success(request, 'Order cancelled Successfully')
        return redirect('order_details', order_id=order.order_id)

    return render(request,'order_cancel.html', {
         'order': order,
        'categories': categories, }) 


@login_required
def cancel_order_item(request, item_id):
    order_item = get_object_or_404(
        OrderItem,
        id=item_id,
        order__user=request.user
    )

    if order_item.item_status.lower() in ['cancelled', 'returned', 'delivered']:
        messages.error(request, "This item cannot be cancelled.")
        return redirect(
            'order_details',
            order_id=order_item.order.order_id
        )

    with transaction.atomic():
        #cancel the item
        order_item.item_status = 'cancelled'
        order_item.save()

        # Restore stock
        variant = order_item.variant
        variant.stock += order_item.quantity
        variant.save()

        order = order_item.order
        remaining_items = order.items.exclude(
            item_status__in=['cancelled', 'returned']
        )

        if not remaining_items.exists():
            order.status = 'cancelled'
            order.save()

        # Update totals
        old_total_amount = order.total_amount
        order.update_total()
        order.refresh_from_db()

        # Refund item value to wallet if paid via online/wallet
        if order.payment_method in ['online', 'wallet']:
            refund_amount = old_total_amount - order.total_amount
            if refund_amount > 0:
                wallet, _ = Wallet.objects.get_or_create(user=order.user)
                wallet.deposit(
                    amount=refund_amount,
                    description=f"Refund for cancelled item {order_item.product_name} in Order #{order.order_id}",
                    transaction_type='refund',
                    order=order
                )
                messages.success(request, f"Refund of ₹{refund_amount} credited to your wallet.")

    messages.success(request, "Item cancelled successfully.")
    return redirect(
        'order_details',
        order_id=order.order_id
    )

@login_required
def order_details(request, order_id):
    print("URL order_id:", order_id)
    print("User:", request.user)
    order = get_object_or_404(Order, order_id = order_id, user = request.user)
    coupons = Coupon.objects.filter(is_active=True) 

    context = {
        'order': order,
        'coupons': coupons,
        'order_items': order.items.all(),
        'categories': Category.objects.filter(is_active=True),
    }

    return render(request, 'order_details.html', context)

@login_required
def return_order(request, order_id):
    order = get_object_or_404(Order, order_id = order_id, user = request.user) 

    if order.status.lower() != 'delivered':
        messages.error(request, 'Only Delivered Items can be returned')
        return redirect('order_details', order_id = order.order_id)  

    if request.method == 'POST':
        reason = request.POST.get('reason')
        
        # Mandatory reason
        if not reason:
            messages.error(request,'Return reason is required')
            return redirect('return_order', order_id = order.order_id) 
        
        # Mark status as return_requested instead of returned immediately
        order.status = 'return_requested'
        order.return_reason = reason
        order.save()

        # Mark non-cancelled items as return_requested
        order.items.exclude(item_status__in=['cancelled', 'returned']).update(item_status='return_requested')

        messages.success(request, 'Return request submitted successfully')
        return redirect('my_orders')

    return render(request, 'return_order_item.html', { 'order': order }) 



@login_required
def download_invoice(request, order_id):

    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    # Allow only delivered orders
    if order.status.lower() != "delivered":
        messages.error(request, "Invoice available only after delivery.")
        return redirect("order_details", order_id=order.order_id)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=28,
    )

    elements = []
    styles = getSampleStyleSheet()

    # TITLE
    title = Paragraph(
        f"<b>Invoice - Order #{order.order_id}</b>",
        styles['Title']
    )
    elements.append(title)
    elements.append(Spacer(1, 20))

    # CUSTOMER INFO (FIXED)
    customer_info = Paragraph(f"""
        <b>Customer Name:</b> {order.full_name}<br/>
        <b>Mobile:</b> {order.mobile}<br/>
        <b>Address:</b> {order.street_address}, {order.city}, {order.state}, {order.postal_code}<br/>
        <b>Payment Method:</b> {order.payment_method}<br/>
        <b>Order Status:</b> {order.status}<br/>
    """, styles['BodyText'])

    elements.append(customer_info)
    elements.append(Spacer(1, 20))

    # TABLE HEADER
    data = [
        ['Product', 'Variant', 'Qty', 'Price', 'Total']
    ]

    # ORDER ITEMS
    for item in order.items.all():

        price = item.product.offer_price   # FIXED
        total_price = item.quantity * price

        data.append([
            item.product_name,
            f"{item.variant_size} / {item.variant_color}",
            str(item.quantity),
            f"Rs {price}",
            f"Rs {total_price}",
        ])

    # GRAND TOTAL
    data.append([
        '',
        '',
        '',
        'Grand Total',
        f"Rs {order.total_amount}"
    ])

    table = Table(data, colWidths=[170, 120, 60, 80, 80])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 30))

    footer = Paragraph(
        "Thank you for shopping with Lotto Shoes!",
        styles['BodyText']
    )
    elements.append(footer)

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{order.order_id}.pdf"'

    response.write(pdf)
    return response


