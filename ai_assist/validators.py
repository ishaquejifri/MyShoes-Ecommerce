

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
    'max_budget',
    'features',
}

def validate_ai_response(data):

    if not isinstance(data, dict):
        raise ValueError('AI response must be a JSON object.')

    # Normalize keys returned by the model if it used max_price instead of max_budget
    if 'max_price' in data and 'max_budget' not in data:
        data['max_budget'] = data.pop('max_price')

    # Ensure all required keys exist (assigning None if missing)
    for field in REQUIRED_FIELDS:
        if field not in data:
            data[field] = None    

    # validate category
    category = data.get('category')
    if category is not None:
        category = str(category).lower()

        if category not in ALLOWED_CATEGORIES:
            data['category'] = None
        else:
            data['category'] = category
    
    # Validate Max Budget
    max_budget = data.get('max_budget')
    if max_budget is not None:
        try:
            max_budget = float(max_budget)
            if max_budget <= 0:
                data['max_budget'] = None
            else:
                data['max_budget'] = max_budget
        except (ValueError, TypeError):
            data['max_budget'] = None

    #validate features
    features = data.get('features')
    if not isinstance(features, list):
        data['features'] = []
    else:
        data['features'] = [str(f) for f in features if isinstance(f, (str,int,float))]     

    # validate size
    size = data.get('size')
    if size is not None:
        data['size'] = str(size).strip()

    return data   
        