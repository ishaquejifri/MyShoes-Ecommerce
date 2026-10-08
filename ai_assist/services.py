import json
from django.conf import settings
from openai import OpenAI
from .prompts import SYSTEM_PROMPT
from .validators import validate_ai_response
from products.models import Product
from google import genai
from google.genai import types
from google.genai.errors import ServerError,APIError

client = genai.Client(
     api_key=settings.GEMINI_API_KEY
)

FALLBACK_MODELS = [
    'gemini-3.8-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.1-flash-lite',
]


def analyze_shoe_request(user_message):
    response = None
    last_exception = None

    for model_name in FALLBACK_MODELS:
        try:
            response = client.models.generate_content(
            model=model_name,
            contents=user_message,
            config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type='application/json',
            )
            )
            break
        except (ServerError,APIError) as e:
            last_exception = e
            continue
    if not response:
        raise RuntimeError(f'All AI models are currently busy. error:{last_exception}')    

    raw_output = response.text.strip()

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError(
            'AI returned Invalid JSON format.'
        ) from exc


    return validate_ai_response(data) 

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

        product_ids = [p.id for p in filtered_products]
        products = Product.objects.filter(id__in=product_ids)
            
        
    color = requirements.get('color')

    if color:
        products = products.filter(
            variants__color__iexact=color,
            variants__is_active=True,
            variants__stock__gt=0
        ) 

    size = requirements.get('size')

    if size:
        products = products.filter(
            variants__size__iexact=size,
            variants__is_active=True,
            variants__stock__gt=0
        )       

    return products.distinct()[:5]   
