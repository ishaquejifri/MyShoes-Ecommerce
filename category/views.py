from django.shortcuts import render,redirect,get_object_or_404
from .models import Category
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count,Q
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache

# Create your views here.
@never_cache
@login_required(login_url='admin_login')
def category_list(request):
    query = request.GET.get('q')

    
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_deleted=False))
    ).order_by('-id')

    if query:
        categories = categories.filter(name__icontains=query)

    paginator = Paginator(categories,5)  
    page_number = request.GET.get('page')  
    page_obj = paginator.get_page(page_number)    

    return render(request,'category_list.html',{  
        'page_obj': page_obj,
        'query': query   
    }) 

@never_cache
@login_required(login_url='admin_login')
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request,'Category is already exists')
            return redirect('add_category') 

        Category.objects.create(
            name = name,
            description = description,
            image = image
        ) 

        messages.success(request,'Category is successfully added')
        return redirect('category_list')  

    return render(request, 'add_category.html')

@never_cache
@login_required(login_url='admin_login')
def edit_category(request,id):
    category = get_object_or_404(Category, id=id)

    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')

        if request.FILES.get('image'):
            category.image = request.FILES.get('image')

        category.save()

        messages.success(request,'Category Updated Successfully')
        return redirect('category_list')
    
    return render(request,'edit_category.html',{
        'category': category
    })

@never_cache
@login_required(login_url='admin_login')
def toggle_category_status(request,id):
    category = Category.objects.get(id=id)
    category.is_active = not category.is_active
    category.save()

    return redirect('category_list')

@never_cache
@login_required(login_url='admin_login')
def delete_category(request,id):
    category = Category.objects.get(id=id)

    category.is_active = False
    category.save()

    messages.success(request,'Category is Disabled')
    return redirect('category_list')
