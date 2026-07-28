from django.shortcuts import render,redirect,get_object_or_404
from django.conf import settings
import razorpay
import json
import time
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from urllib3 import request
from orders.models import Order,OrderItem
from cart.models import Cart,CartItem
from .models import Payment
from django.urls import reverse
from products.models import ProductVariant
from django.contrib import messages
from accounts.models import Wallet
from django.db import transaction


# Create your views here.

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID,
          settings.RAZORPAY_KEY_SECRET
          )
)

@require_POST
@login_required
def verify_payment(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'Failed', 'message': 'Invalid request method.'}, status=400)

    try:
        data = json.loads(request.body)

        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        db_order_id = data.get('order_id')

        order = get_object_or_404(Order, 
                                  id=db_order_id,  
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

        with transaction.atomic():
            order_items = OrderItem.objects.select_for_update().filter(order=order)
            
            out_of_stock_item = None
            for item in order_items:
                if item.variant.stock < item.quantity:
                    out_of_stock_item = item
                    break
            if out_of_stock_item:               
                    payment.status = 'Success'
                    payment.razorpay_payment_id=razorpay_payment_id
                    payment.razorpay_signature=razorpay_signature
                    payment.save()

                    order.payment_status = 'Paid'
                    order.status = 'pending'  # Hold for admin resolution
                    order.save()
                
                    return JsonResponse({
                    'status': 'error',
                    'message': f"Payment received, but {out_of_stock_item.product_name} is out of stock. Customer support will contact you.",
                    'redirect_url': reverse('payment_failed', kwargs={'order_id': order.id})
                }, status=400)
            
            for item in order_items:
                item.variant.stock -= item.quantity
                item.variant.save()
                item.item_status = 'confirmed'
                item.save()    

            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = 'Success'
            payment.save()

            order.payment_status = 'Paid'
            order.status = 'confirmed'
            order.save()        

            # clear user cart
            CartItem.objects.filter(
            cart__user=request.user
            ).delete()

        
        return JsonResponse({
            'status': 'success',
            'redirect_url': reverse('order_success', kwargs={'order_id': order.order_id})
        })   
            
    except razorpay.errors.SignatureVerificationError:
        
        if 'payment' in locals():
            payment.status = 'Failed'
            payment.save()

        if 'order' in locals():
            order.payment_status = 'Failed'
            order.status = 'Cancelled'
            order.save()
            redirect_target = reverse('payment_failed', kwargs={'order_id': order.id})
        else:
            redirect_target = reverse('checkout')

        return JsonResponse({
            'status': 'failed',
            'message': 'Signature verification failed',
            'redirect_url': redirect_target
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status = 500)


@login_required
def payment_failed(request, order_id):

    if hasattr(Order, 'uuid'):
        order = Order.objects.filter(uuid=order_id, user=request.user).first() or get_object_or_404(Order, id=order_id, user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    payment = Payment.objects.filter(order=order).last()

    return render(request, 'payment_failed.html', {
        'payment': payment,
        'order': order,
    })

@login_required
def retry_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    amount_in_paise = int(round(float(order.total_amount) * 100 ))
    unique_receipt = f'rec_{order.id}_{int(time.time())}'[:40]
    
    try:
        razorpay_order = client.order.create({
        'amount': amount_in_paise,
        'currency': 'INR',
        'receipt': unique_receipt,
        'payment_capture': 1,
    })
        
    except Exception as e:
        return redirect('payment_options', order.id) 

    payment, created = Payment.objects.get_or_create(
        order=order,
        defaults={
            'user': request.user,
            'amount': order.total_amount,
            'status': 'Pending',
            'razorpay_order_id': razorpay_order['id']
        }
    )

    if not created:
        payment.razorpay_order_id = razorpay_order['id']
        payment.status = 'Pending'
        payment.save()

    context = {
        'order': order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount': amount_in_paise,
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

            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'user': request.user,
                    'amount': order.total_amount,
                    'status': 'Pending'
                }
            )
            if not created:
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
    
    # Deduct from Wallet using withdraw method to log the transaction
    wallet.withdraw(
        order.total_amount,
        f"Payment for Order #{order.order_id}",
        transaction_type='payment',
        order=order
    )

    order.payment_method = 'wallet'
    order.payment_status = 'Paid'
    order.status = 'confirmed'
    order.save()

    payment, created = Payment.objects.get_or_create(
        order=order,
        defaults={
            'user': request.user,
            'amount': order.total_amount,
            'status': 'Success'
        }
    )
    if not created:
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

# RAZORPAY WEBHOOK HANDLER (NEW & REQUIRED)

@csrf_exempt    
def razorpay_webhook(request):
    '''
    Asynchoronous server to server handler for razorpay payment events
    '''
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
    request_body = request.body.decode('utf-8')
    received_signature = request.headers.get('X-Razorpay-Signature')

    if webhook_secret and received_signature:
        try:
            client.utility.verify_webhook_signature(
                request_body, received_signature, webhook_secret
            )
        except razorpay.errors.SignatureVerificationError:
            return HttpResponse(status=400)
    try:
        event_data = json.loads(request_body)
        event_type = event_data.get('event')

        if event_type =='payment.captured':
            payment_entity = event_data['payload']['payment']['entity']
            razorpay_order_id = payment_entity['order_id']
            razorpay_payment_id = payment_entity['id']  

            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                if payment != 'Success':
                    with transaction.atomic():
                        payment.status = 'Success'
                        payment.razorpay_payment_id= razorpay_payment_id
                        payment.save()

                        order = payment.order
                        order.payment_status = 'Paid'
                        order.status = 'confirmed'
                        order.save()

                        #deduct stock if not already deducted
                        for item in order.items.all():
                            if item.item_status != 'confirmed':
                                item.variant.stock = max(0, item.variant.stock - item.quantity)
                                item.variant.save()
                                item.item_status = 'confirmed'
                                item.save()

                        CartItem.objects.filter(cart__user=order.user).delete()
            except payment.DoesNotExist:
                pass 
        elif event_type == 'payment.failed':
            payment_entity = event_type['payload']['payment']['entity']
            razorpay_order_id = payment_entity['order_id']

            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                if payment.status == 'Pending':
                    payment.status = 'Failed'
                    payment.save()
                    order = payment.order
                    order.payment_status = 'Failed'
                    order.status = 'cancelled'
                    order.save()
            except Payment.DoesNotExist:
                pass
        
        return HttpResponse(status=200)
    except Exception:
        return HttpResponse(status=500)
                    




