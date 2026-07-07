from django.shortcuts import render,redirect,get_object_or_404
from .models import Product,ProductImage,ProductVariant
from .forms import ProductForm, ProductVariantForm
from category.models import Category
from django.contrib.auth.decorators import login_required
import base64
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache
from django.contrib import messages
from adminpanel.decorators import admin_required

# Create your views here.


@never_cache
@admin_required
@login_required(login_url='admin_login')
def product_list(request):
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    products = Product.objects.filter(is_deleted=False).order_by('-id')

    if query:
        products = products.filter(product_name__icontains=query)     

    if category_id:         
         products = products.filter(category_id=category_id) 

    paginator = Paginator(products,5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)        

    return render(request, 'product_list.html', { 
          'products': page_obj,
          'page_obj':page_obj,
          'query': query
          })


@never_cache
@admin_required
@login_required(login_url='admin_login')
def add_product(request):

    form = ProductForm(request.POST or None, request.FILES or None)
    categories = Category.objects.all()

    
    files = request.FILES.getlist('gallery_images')
    cropped_gallery_images = request.POST.getlist('cropped_gallery_images')

    total_images = len(files) if files else len(cropped_gallery_images)

    if request.method == 'POST':
        cropped_image = request.POST.get('cropped_image')
        cropped_gallery_images = request.POST.getlist('cropped_gallery_images')

        if not cropped_image:
             messages.error(request,'Please crop the main image before submitting.')
        elif len(cropped_gallery_images) < 3:
             messages.error(request,'Please crop and upload atleast 3 gallery images.')
        elif len(cropped_gallery_images) > 5:
             messages.error(request,'Maximum 5 gallery images are allowed.')
        else:
             form = ProductForm(request.POST,request.FILES)    

                  
             if form.is_valid():
                   product = form.save(commit=False)
                   
                   
                    #save cropped main image                 
                   format,imgstr = cropped_image.split(';base64,')
                   ext = format.split('/')[-1]

                   product.image = ContentFile(
                        base64.b64decode(imgstr),
                        name='cropped.' + ext
                    )
                    #save product first
                   product.save()    
                   
                    #save gallery images              
                   for img in cropped_gallery_images:
                             format, imgstr = img.split(';base64,')
                             ext = format.split('/')[-1]

                             file = ContentFile(
                               base64.b64decode(imgstr),
                               name='gallery.' + ext
                            )

                             ProductImage.objects.create(product=product, image=file)                                     
            
                   messages.success(request,'Product Added Successfully!')
                   return redirect('products:add_variant',product.id)
             else:
                    messages.error(request,'Please correct the form Errors')                           
    
    return render(request,'add_product.html',{
        'form': form,
        'categories': categories  
          })


@never_cache
@admin_required
@login_required(login_url='admin_login')
def edit_product(request,id):
    product = get_object_or_404(Product,id=id)
    gallery_images = product.images.all()
    variants = product.variants.all()

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            updated_product = form.save(commit=False)

            updated_product.is_blocked = product.is_blocked
            updated_product.is_listed = product.is_listed
            updated_product.is_available = product.is_available
            updated_product.is_deleted = product.is_deleted

            updated_product.save()

            variant_ids = request.POST.getlist('variant_id')            

            for img in updated_product.images.all():

               new_image = request.FILES.get(
                     f'gallery_image_{img.id}'
                    )

               if new_image:
                    img.image = new_image
                    img.save()
            
            delete_ids = request.POST.getlist(
               'delete_gallery_images'  
            )

            if delete_ids:
                 ProductImage.objects.filter(
                      id__in=delete_ids,
                      product=updated_product
                 ).delete()

            new_images = request.FILES.getlist(
                 'new_gallery_images'
            )

            for image in new_images:
                 ProductImage.objects.create(
                      product=updated_product,
                      image=image
                 )                   

            messages.success(request, 'Product Edited Successfully.')   
            return redirect('products:product_list')
        else:
             messages.error(request,'Please correct the form Errors')
    else:
        form = ProductForm(instance=product)
    
    return render(request,'edit_product.html',{ 
        'form': form,
        'product': product,
        'variants': variants,
        'gallery_images': gallery_images,
        'categories': Category.objects.all()
          })

@never_cache
@admin_required
@login_required(login_url='admin_login')
def product_details(request,id):

    product = get_object_or_404(Product,id=id)
    variants = product.variants.all()

    sizes = variants.values_list('size', flat=True).distinct()
    colors = variants.values_list('color', flat=True).distinct()


    return render(request,'product_details.html', { 
         'product': product,
         'variants': variants,
         'colors': colors,
         'sizes': sizes,

         })

@never_cache
@admin_required
@login_required(login_url='admin_login') 
def add_variant(request,product_id):
     
     product = get_object_or_404(Product,id=product_id)

     if request.method=="POST":
          form = ProductVariantForm(
               request.POST,
               initial={'product': product})

          if form.is_valid():
               variant = form.save(commit=False)
               variant.product = product
               variant.save()
               return redirect('products:product_details', id=product_id)
          
     else:
          form = ProductVariantForm(initial={'product': product}) 

     return render(request,'add_variant.html',{
          'form': form,
          'product': product
     })


@never_cache
@admin_required
@login_required(login_url='admin_login')
def edit_variant(request, variant_id):
     
     variant = get_object_or_404(ProductVariant, id=variant_id)

     if request.method == "POST":
          form = ProductVariantForm(request.POST, instance=variant)

          if form.is_valid():
               form.save()
               return redirect('products:product_details', id=variant.product.id)
     else:
          form = ProductVariantForm(instance=variant)

     return render(request,'edit_variant.html',{
        'form': form,
        'variant': variant
     })          


@never_cache
@admin_required
@login_required(login_url='admin_login')
def delete_variant(request, variant_id):
     variant = get_object_or_404(ProductVariant,id=variant_id)
     product_id = variant.product.id

     variant.delete()
     messages.success(request, 'Variant Deleted Successfully.')
     return redirect('products:product_details',id=product_id)

@never_cache
@admin_required
@login_required(login_url='admin_login')
def toggle_listing(request,id):
     product = get_object_or_404(Product,id=id, is_deleted=False) 

     product.is_listed = not product.is_listed
     product.save()

     if product.is_listed:
          messages.success(request, 'Product listed successfully.')
     else:
          messages.success(request, 'Product unlisted successfully.')

     return redirect('products:product_list')              


@never_cache
@admin_required
@login_required(login_url='admin_login')
def delete_product(request,id):
     product = get_object_or_404(Product, id=id, is_deleted=False)
     product.is_deleted = True
     product.save()
     messages.success(request, 'Product moved to trash.')
     return redirect('products:product_list')






     






