from django.shortcuts import render,redirect,get_object_or_404
from django.conf import settings
import razorpay
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from urllib3 import request
from orders.models import Order,OrderItem
from cart.models import Cart,CartItem
from .models import Payment
from django.urls import reverse
from products.models import ProductVariant
from django.contrib import messages
from accounts.models import Wallet


# Create your views here.

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID,
          settings.RAZORPAY_KEY_SECRET
          )
)

@require_POST
@login_required
def verify_payment(request):

    payment = None
    order = None

    print("=" * 50)
    print("VERIFY PAYMENT CALLED")
    print(request.body)
    print("=" * 50)

    try:
        data = json.loads(request.body)

        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        order_id = data.get('order_id')

        order = get_object_or_404(Order, 
                                  id=order_id,  
                                  user=request.user)

        payment = get_object_or_404(Payment, order=order)

        if payment.razorpay_order_id != razorpay_order_id:
            return JsonResponse({
                "status": "failed",
                "message": "Invalid Razorpay Order."
                }, status=400)

        
        params = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        }

        client.utility.verify_payment_signature(params)

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'Success'
        payment.save()

        order.payment_status = 'Paid'
        order.status = 'confirmed'
        order.save()

        # Record Coupon Usage for Online Payments
        coupon_code = request.session.get('coupon_code')
        if coupon_code:
            try:
                from coupons.models import Coupon, CouponUsage
                coupon = Coupon.objects.get(code=coupon_code)
                if not CouponUsage.objects.filter(coupon=coupon, order=order).exists():
                    CouponUsage.objects.create(
                        coupon=coupon,
                        user=request.user,
                        order=order,
                        discount_amount=order.coupon_discount,
                        cart_total_before_discount=order.sub_total
                    )
                    coupon.times_used += 1
                    coupon.save(update_fields=['times_used'])
            except Exception as e:
                print("Error recording coupon usage for online order:", e)
            
            # Clear coupon from session
            request.session.pop('coupon_code', None)

        order_items = OrderItem.objects.filter(order=order)

        for item in order_items:
            variant = item.variant  

            if variant.stock < item.quantity:
                return JsonResponse({
                    'status': 'failed',
                     "message": f"{item.product_name} is out of stock."
                }, status=400)
            
            variant.stock -= item.quantity
            variant.save()

        CartItem.objects.filter(
            cart__user=request.user
        ).delete()

        return JsonResponse({
            'status': 'success',
            'redirect_url': reverse('order_success', kwargs={'order_id': order.order_id})

        })
    
    except razorpay.errors.SignatureVerificationError:
        
        if payment:
            payment.status = 'Failed'
            payment.save()

        if order:
            order.payment_status = 'Failed'
            order.save()

        return JsonResponse({
            'status': 'failed',
            'redirect_url': reverse('payment_failed', kwargs={'order_id': order_id})
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status = 500)

@login_required
def place_order(request):

    order = Order.objects.create(
        user=request.user,
        total_amount=grand_total,
        payment_method='online',
        status='Pending'  
    )

    
    payment_data = {
        'amount': int(grand_total * 100),
        'currency': 'INR',
        'payment_capture': 1
    }
    
    razorpay_order = client.order.create(
        data=payment_data
    )

    Payment.objects.create(
        user=request.user,
        order=order,
        amount=grand_total,
        razorpay_order_id=razorpay_order['id']
    )

    context = {
        'order': order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount': int(grand_total * 100) 
    }

    return render(request,'payment.html', context)



@login_required
def payment_failed(request, order_id):

    payment = get_object_or_404(Payment, order_id=order_id)

    return render(request, 'payment_failed.html', {
        'payment': payment,
        'order': payment.order,
    })

@login_required
def retry_payment(request, order_id):

    order = get_object_or_404(Order, id = order_id)

    payment = order.payment

    
    razorpay_order = client.order.create({
        'amount': int(order.total_amount * 100),
        'currency': 'INR',
        'receipt': str(order.order_id),
        'payment_capture': 1,
    })

    payment.razorpay_order_id = razorpay_order['id']
    payment.status = 'Pending'
    payment.save()

    context = {
        'order': order,
        'payment': payment,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount': int(order.total_amount * 100 ),
    }

    return render(request, 'retry_payment.html', context)

@login_required
def payment_options(request, order_id):

    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        order.payment_method = payment_method
        order.save()

        if payment_method == 'online':
            return redirect('retry_payment', order.id)
        
        elif payment_method == 'wallet':
            return redirect('wallet_retry_payment', order.id)

        elif payment_method == 'cod':

            if order.total_amount > 2000:
                messages.error(request,'Cash on Delivery is not available for orders above ₹2000.' )
                return redirect('payment_options', order.id)
            
            order.payment_method = 'cod'
            order.payment_status = 'Pending'
            order.status = 'confirmed'
            order.save()

            order_items = OrderItem.objects.filter(order=order)

            for item in order_items:
                variant = item.variant  

                if variant.stock < item.quantity:
                    messages.error(request, f"{item.product_name} is out of stock.")
                    return redirect('payment_options', order.id)
                
                variant.stock -= item.quantity
                variant.save()

            payment = order.payment
            payment.status = "Pending"
            payment.save()

            CartItem.objects.filter(
                cart__user=request.user
                ).delete()

            return redirect('order_details', order.order_id) 
        
    wallet = Wallet.objects.get(user=request.user)       
        
    return render(request, 'payment_options.html', {'order': order, "wallet": wallet})    

@login_required
def wallet_retry_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    wallet = Wallet.objects.get(user=request.user)

    if order.payment_status == "Paid":
        messages.info(request, "This order has already been paid.")
        return redirect("order_details", order.order_id)

    if wallet.balance < order.total_amount:
        messages.error(request, 'Insufficient wallet balance. ')
        return redirect('payment_options', order.id)
    
    wallet.balance -= order.total_amount
    wallet.save()

    order.payment_method = 'wallet'
    order.payment_status = 'Paid'
    order.status = 'confirmed'
    order.save()

    payment = order.payment
    payment.status = 'Success'
    payment.save()

    order_items = OrderItem.objects.filter(order=order)

    for item in order_items:
            variant = item.variant  

            if variant.stock < item.quantity:
                messages.error(request, f"{item.product_name} is out of stock.")
                return redirect('payment_options', order.id)
            
            variant.stock -= item.quantity
            variant.save()

    CartItem.objects.filter(
            cart__user=request.user
            ).delete()        


    return redirect('order_success', order.order_id)


#helper function to deduct stock for an order
def deduct_stock(order):
    order_items = OrderItem.objects.filter(order=order)

    for item in order_items:
        variant = item.variant

        if variant.stock < item.quantity:
            return False

        variant.stock -= item.quantity
        variant.save()

    CartItem.objects.filter(cart__user=order.user).delete()

    return True    

