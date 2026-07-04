from django.shortcuts import render,redirect,get_object_or_404
from django.conf import settings
import razorpay
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from orders.models import Order,OrderItem
from cart.models import Cart,CartItem
from .models import Payment
from django.urls import reverse
from products.models import ProductVariant


# Create your views here.

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID,
          settings.RAZORPAY_KEY_SECRET
          )
)


def verify_payment(request):

    try:
        data = json.loads(request.body)

        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        order_id = data.get('order_id')

        order = get_object_or_404(Order, 
                                  id=order_id,
                                  user=request.user)
        
        payment = get_object_or_404(Payment,order=order)

        client = client

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
        order.status = 'Confirmed'
        order.save()

        order_items = OrderItem.objects.filter(order=order)

        for item in order_items:
            variant = item.variant
            variant.stock -= item.quantity
            variant.save()

        CartItem.objects.filter(
            cart__user=request.user
        ).delete()

        return JsonResponse({
            'status': 'success',
            'redirect_url': reverse('order_success', kwargs={'order_id': order_id})

        })
    
    except razorpay.errors.SignatureVerificationError:

        payment.status = 'Failed'
        payment.save()

        order.status = 'Failed'
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


def place_order(request):

    order = Order.objects.create(
        user=request.user,
        total_amount=grand_total,
        payment_method='Razorpay',
        status='Pending'  
    )

    client = client

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

def payment_success(request):

    payment_id = request.GET.get('payment_id')
    order_id = request.GET.get('order_id')
    signature = request.GET.get('signature')

    payment = Payment.objects.get(
        razorpay_order_id=order_id
    )

    client = client

    params = {
        'razorpay_order_id': order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature,
    }

    try:
        client.utility.verify_payment_signature(params)

        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.status = 'Success'
        payment.save()

        order = payment.order
        order.PAYMENT_STATUS = 'Paid'
        order.status = 'confirmed'
        order.save()
        return redirect('order_success')
    
    except:
        payment.status = 'Failed'
        payment.save()
        return redirect('payment_failed')

def payment_failed(request, order_id):

    payment = get_object_or_404(Payment, order_id=order_id)

    return render(request, 'payment_failed.html', {
        'payment': payment,
        'order': payment.order,
    })


def retry_payment(request, order_id):

    order = get_object_or_404(Order, id = order_id)

    payment = order.payment

    client = client

    razorpay_order = client.order.create({
        'amount': int(order.total_amount * 100),
        'currency': 'INR',
        'receipt': str(order.order_id),
        'payment_capture': 1,
    })

    payment.razorpay_order_id = razorpay_order['id'],
    payment.status = 'Pending',
    payment.save()

    context = {
        'order': order,
        'payment': payment,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount': int(order.total_amount * 100 ),
    }

    return render(request, 'retry_payment.html', context)





