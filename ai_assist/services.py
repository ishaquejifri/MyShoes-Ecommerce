import json
from django.conf import settings
from openai import OpenAI
from .prompts import SYSTEM_PROMPT
from .validators import validate_ai_response
from products.models import Product

client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)
            
def analyze_shoe_request(user_message):

    response = client.responses.create(
        model='gpt-5.4-mini',
        instructions=SYSTEM_PROMPT,
        input=user_message,
    )

    raw_output = response.output_text.strip()

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError(
            'AI returned Invalid JSON.'
        ) from exc


    return validate_ai_response 

def find_matching_products(requirements):

    products = Product.objects.filter(
            is_listed = True,
            is_deleted = False,
            is_available = True,
            is_blocked = False,
       ).select_related('category').prefetch_related('variants').distinct()

    category = requirements.get('category')

    if category:
        products = products.filter(
            category__name__iexact=category
        )

    max_budget = requirements.get('max_budget')

    if max_budget:
        filtered_products = []

        for product in products:
            final_price = product.get_discounted_price()

            if final_price <= max_budget:
                filtered_products.append(product)

        products = filtered_products
            
        
    color = requirements.get('color')

    if color:
        products = products.filter(
            variants__color__iexact=color,
            variants__is_active=True,
            variant__stock__gt=0
        ) 

    size = requirements.get('size')

    if size:
        products = products.filter(
            variants__size__iexact=size,
            variants__is_active=True,
            variants__stock__gt=0
        )       

    return products.distinct()[:5]   
