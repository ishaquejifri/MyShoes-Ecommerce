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
from offers.utils import apply_offer_to_variant

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
    categories = Category.objects.all()

    if request.method == 'POST':

         form = ProductForm(request.POST, request.FILES)
         cropped_image = request.POST.get('cropped_image','').strip()
         cropped_gallery_images = request.POST.getlist('cropped_gallery_images')

         #validate image in backend
         has_image_error = False

         if not cropped_image:
              messages.error(request,'Main Image Error: Please crop the main image before submitting.')
              has_image_error = True
         if len(cropped_gallery_images) < 3:      
              messages.error(request,'Gallery Image Error: Please crop and upload atleast 3 gallery images.')
              has_image_error = True 
         elif len(cropped_gallery_images) > 5:
              messages.error(request,'Gallery Image Error: Maximum 5 gallery images are allowed.')
              has_image_error = True

         if form.is_valid() and not has_image_error:
              try:
                   product = form.save(commit=False)
                   #save main image
                   format,imgstr = cropped_image.split(';base64,')
                   ext = format.split('/')[-1]
                   product.image = ContentFile(
                        base64.b64decode(imgstr),name=f'main_{product.slug}.{ext}')
                   product.save()
                   #save gallery images
                   for idx,img in enumerate('cropped_gallery_images'):
                        format,imgstr = img.split(';base64,')
                        ext = format.split('/')[-1]
                        file = ContentFile(
                             base64.b64decode(imgstr),
                             name = f'gallery_{product.slug}_{idx+1}.{ext}')
                        ProductImage.objects.create(product=product,image=file)
                   messages.success(request,'Product Added Successfully!')

                   # Redirect using product.uuid or product.id based on URL pattern
                   redirect_id = getattr(product, 'uuid', product.id)
                   return redirect('products:add_variant', product_uuid=redirect_id) 
              except Exception as e:
                   messages.error(request, f'Error saving product: {str(e)}') 
         else:
              if not has_image_error and not form.is_valid():
                   messages.error(request,'Please correct the form Errors')
    else:
         form = ProductForm()        
                         
                                
    
    return render(request,'add_product.html',{
        'form': form,
        'categories': categories  
          })


@never_cache
@admin_required
@login_required(login_url='admin_login')
def edit_product(request,product_uuid):
    product = get_object_or_404(Product,uuid=product_uuid)
    gallery_images = product.images.all()
    variants = product.variants.all()

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)

        delete_ids = request.POST.getlist('delete_gallery_images')
        new_images = request.FILES.getlist('new_gallery_images')

        #calculate total gallery images after deletion and addition
        existing_count = gallery_images.count()
        delete_count = len(delete_ids)
        new_count = len(new_images)
        final_gallery_count = existing_count - delete_count + new_count

        gallery_error = None
        if final_gallery_count < 3:
             gallery_error = (f'Gallery must have atleast 3 images, you currently have {final_gallery_count}.')
        elif final_gallery_count > 5:
             gallery_error = (f'Gallery cannot exeed 5 images, you currently have {final_gallery_count}.')

        if form.is_valid() and not gallery_error:
             updated_product = form.save(commit=False)

             updated_product.is_blocked = product.is_blocked
             updated_product.is_listed = product.is_listed
             updated_product.is_available = product.is_available
             updated_product.is_deleted = product.is_deleted

             updated_product.save()

             if delete_ids:
                  ProductImage.objects.filter(id__in=delete_ids,product=updated_product).delete()

             for image in new_images:
                  ProductImage.objects.create(product=updated_product, image=image)

             messages.success(request, 'Product updated successfully.') 
             return redirect('products:product_list') 
        else:
         
         if gallery_error:
              messages.error(request, gallery_error)
         else:
              messages.error(request, 'Please correct the form errors below.')
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
def product_details(request,product_uuid):

    product = get_object_or_404(Product,uuid=product_uuid)
    variants = product.variants.all()

    general_images = [
         img.image.url for img in product.images.filter(variant__isnull=True) if img.image
    ]

    if not general_images and product.image:
         general_images = [product.image.url]

    pricing = {}
    variant_images = {}

    for variant in variants:
         pricing[variant.id] = apply_offer_to_variant(variant)

         v_imgs = [img.image.url for img in variant.images.all() if img.image]

         variant_images[str(variant.uuid)] = v_imgs if v_imgs else general_images  

    sizes = variants.values_list('size', flat=True).distinct()
    colors = variants.values_list('color', flat=True).distinct()


    return render(request,'product_details.html', { 
         'product': product,
         'variants': variants,
         'colors': colors,
         'sizes': sizes,
         'pricing': pricing,
         'general_images': general_images,
         'variant_images': variant_images,

         })

@never_cache
@admin_required
@login_required(login_url='admin_login') 
def add_variant(request, product_uuid):
     
     product = get_object_or_404(Product, uuid=product_uuid)

     if request.method=="POST":
          form = ProductVariantForm(
               request.POST,
               request.FILES)               

          if form.is_valid():
               variant = form.save(commit=False)
               variant.product = product
               variant.price = product.offer_price or product.base_price
               variant.save()

               images = request.FILES.getlist('images')
               for img in images:
                    ProductImage.objects.create(
                         product = product,
                         variant = variant,
                         image = img
                    )
               messages.success(request, 'Variant Added Successfully.')
               return redirect('products:product_details', product_uuid=product.uuid)          
          
     else:
          form = ProductVariantForm(initial={'product': product}) 

     return render(request,'add_variant.html',{
          'form': form,
          'product': product
     })


@never_cache
@admin_required
@login_required(login_url='admin_login')
def edit_variant(request, variant_uuid):

     variant = get_object_or_404(ProductVariant, uuid=variant_uuid)

     if request.method == "POST":
          form = ProductVariantForm(request.POST, request.FILES, instance=variant)

          if form.is_valid():
               form.save()

               images = request.FILES.getlist('images')
               for img in images:
                    ProductImage.objects.create(
                        variant=variant,
                        image=img

                    )
               messages.success(request, 'Variant Updated Successfully.')
               return redirect('products:product_details', product_uuid=variant.product.uuid)
          else:
               messages.error(request, 'This size and color combination is already exists for this product.')
     else:
          form = ProductVariantForm(instance=variant)

     return render(request,'edit_variant.html',{
        'form': form,
        'variant': variant
     })          


@never_cache
@admin_required
@login_required(login_url='admin_login')
def delete_variant(request, variant_uuid):
     variant = get_object_or_404(ProductVariant,uuid=variant_uuid)
     product_id = variant.product.id

     variant.delete()
     messages.success(request, 'Variant Deleted Successfully.')
     return redirect('products:product_details', product_uuid=variant.product.uuid)

@never_cache
@admin_required
@login_required(login_url='admin_login')
def toggle_listing(request,product_uuid):
     product = get_object_or_404(Product,uuid=product_uuid, is_deleted=False) 

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
def delete_product(request,product_uuid):
     product = get_object_or_404(Product, uuid=product_uuid, is_deleted=False)
     product.is_deleted = True
     product.save()
     messages.success(request, 'Product moved to trash.')
     return redirect('products:product_list')






     






