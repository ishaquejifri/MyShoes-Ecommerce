from django.shortcuts import render,redirect,get_object_or_404
from .models import Banner
from .forms import BannerForm

# Create your views here.

def banner_list(request):
    banners = Banner.objects.all()
    return render(request, 'banner_list.html', {'banners': banners})


def add_banner(request):
    form = BannerForm()

    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('banner_list')
    return render(request, 'add_banner.html', {'form': form})
    
def edit_banner(request,id):
    banner = get_object_or_404(Banner, id=id)
    form = BannerForm(instance=banner)

    if request.method == 'POST':
        form = BannerForm(request.POSt, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            return redirect('banner_list')
    return render(request, 'edit_banner.html', {'form': form})

def delete_banner(request,id):
    banner = get_object_or_404(Banner, id=id)
    banner.delete()
    return redirect('banner_list')  

def toggle_banner(request,id):
    banner = get_object_or_404(Banner, id=id)
    banner.is_active = not banner.is_active
    banner.save()
    return redirect('banner_list')


      