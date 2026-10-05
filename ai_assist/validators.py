

ALLOWED_CATEGORIES = {
    'formal',
    'casual',
    'running',
    'boots',
}

REQUIRED_FIELDS = {
    'category',
    'purpose',
    'color',
    'size',
    'max_price',
    'features',
}

def validate_ai_response(data):

    if not isinstance(data, dict):
        raise ValueError('AI response must be a JSON object.')
    
    missing_fields = REQUIRED_FIELDS - data.keys()

    if missing_fields:
        raise ValueError(
            f'missing fields {', '.join(missing_fields)}'
        ) 

    category = data.get('category')

    if category is not None:
        category = category.lower()

        if category not in ALLOWED_CATEGORIES:
            raise ValueError('Invalid category.')
        data['category'] = category

    max_budget = data.get('max_budget')

    if max_budget is not None:
        if not isinstance(max_budget,(int,float)):
            raise ValueError('Invalid max_budget')
        if max_budget <= 0:
            raise ValueError('Budget must be geater than zero.')

    features = data.get('features')

    if not isinstance(features,list):
        raise ValueError('feature must be a list.') 

    for feature in features:
        if not isinstance(feature,str):
            raise ValueError('Each feature must be a string.')

    size = data.get('size')

    if size is not None:
        if not isinstance(size,str):
            raise ValueError('Size must be a string or null')
        data['size'] = size.strip()

    return data   
        