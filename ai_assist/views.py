from django.shortcuts import render
from django.http import JsonResponse
from .services import analyze_shoe_request,find_matching_products
from django.views.decorators.http import require_http_methods
import json
from category.models import Category
import traceback
from openai import RateLimitError,AuthenticationError,APIConnectionError,APITimeoutError
# Create your views here.

def assist_page(request):
    categories = Category.objects.filter(is_active=True)
    return render(request, 'assist.html',{'categories': categories,})

@require_http_methods(['POST'])
def ai_search(request):

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
          {
              'success': False,
              'error': 'Invalid request'
          },
          status = 400  
        ) 

    message = body.get('message','').strip()

    if not message:
        return JsonResponse(
            {
                'success': False,
                'error': 'Please describe the shoes you are looking for.'
            },
            status = 400
        )

    if len(message) > 500:
        return JsonResponse(
            {
                'sucess': False,
                'error': 'Your request is too long.'
            },
            status = 400
        )

    try:
        requirements = analyze_shoe_request(message)
        products = find_matching_products(requirements)

        product_data = []

        for product in products:
            final_price = (product.get_discounted_price())

            product_data.append(
                {
                    'id': str(product.id),
                    'name': product.product_name,
                    'price': float(final_price),
                    'image': (
                        product.image.url if product.image else None
                    ),
                    'slug': product.slug,
                }
            )
        return JsonResponse(
            {
                'success': True,
                'requirements': requirements,
                'products': product_data,
            }
        )
    except RateLimitError as exc:

        print('OpenAI Quata error', exc)        

        return JsonResponse(
            {
                'success': False,
                'error': (
                    "The AI shopping assistant is "
                    "temporarily unavailable. "
                    "Please try again later."
                )
            },
            status = 503
        )

    except AuthenticationError as exc:

        print('OpenAI Authentication error', exc)

        return JsonResponse(
            {
                'success': False,
                'error':(
                    "The AI service configuration "
                "needs attention."
                )
            },
            status = 503
        )

    except (APITimeoutError,APIConnectionError) as exc:

        print('OpenAI Conncetion error', exc)

        return JsonResponse(
            {
                'success': False,
                'error':(
                    "The AI service could not be reached. "
                "Please try again."
                )
            },
            status = 503
        )

    except ValueError as exc:

        print('AI validation error', exc)

        return JsonResponse(
            {
                'success': False,
                'error': (
                     "We couldn't understand your request. "
                "Please try describing your shoe requirements "
                "more clearly."
                )
            },
            status = 500
        )

    except Exception as exc:

        print('Unexpected Ai error', exc)
        traceback.print_exc()

        return JsonResponse(
            {
                'success': False,
                'error': (
                     "Something went wrong. "
                "Please try again."
                )
            }, 
            status = 500
        )