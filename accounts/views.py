from django.shortcuts import render,redirect,get_object_or_404
import random
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate,get_user_model,login,logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from .models import CustomUser,Address,Wallet,WalletTransaction
from .forms import SignupForm, LoginForm,AddressForm
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from datetime import timedelta
from django.conf import settings
from products.models import Category
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError




User = get_user_model()

def signup(request):
    referral_code = request.GET.get('ref','')

    if request.method == "POST":

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password') 
        referral_code = request.POST.get('referral_code', '').strip().upper()

        # Empty field validation
        if not all([first_name,last_name,email,phone,password,confirm_password]):
            return signup_error(request,'Every Field Should be Fillied.')
        
        # First Name Validation
        if len(first_name) < 3 or len(first_name) > 15:
            messages.error(request, 'First name must be between 3 and 15 characters.')
            return redirect('signup')
        
        if not re.fullmatch(r'^[A-Za-z ]+$', first_name):
            messages.error(request, 'First name should contain only letters and space.')
            return redirect('signup')
        
        # Last Name Validation
        if len(last_name) < 3 or len(last_name) > 15:
            messages.error(request, 'Last name must be between 3 and 15 characters.')
            return redirect('signup')
        
        if not re.fullmatch(r'^[A-Za-z ]+$', last_name):
            messages.error(request, 'Last name should contain only letters and space.')
            return redirect('signup')

        # Email validation
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('signup')    

        if User.objects.filter(email=email).exists():
            return signup_error(request,'Email already registered.')
        
        # phone validation
        digits_only = re.sub(r'\D','', phone)

        if not digits_only.isdigit():
            messages.error(request, 'Phone number should contain digits only.')
            return redirect('signup')
        
        if len(digits_only) != 10:
            messages.error(request, 'Phone number must be exactly 10 digits.')
            return redirect('signup')

        sequential_patterns = ['1234567890','0123456789','9876543210','0987654321']  

        if digits_only in sequential_patterns:
            messages.error(request, 'Enter a valid phone number.')
            return redirect('signup')

        # check repeated digts like 11111111
        if len(set(digits_only)) == 1:
            messages.error(request, 'Enter a valid phone number.')
            return redirect('signup')
        
        # phone already exists
        if User.objects.filter(phone=digits_only).exists():
            messages.error(request, 'The phone number is already registered.')
            return redirect('signup')
        
        # password validation
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('signup')
        
        if not re.search(r'[a-z]', password):
            messages.error(request, 'Password must contain at least one lowercase letter.')
            return redirect('signup')
        if not re.search(r'[A-Z]', password):
            messages.error(request, 'Password must contain at least one uppercase letter.')
            return redirect('signup')
        if not re.search(r'[0-9]', password):   
            messages.error(request, 'Password must contain at least one number.')
            return redirect('signup')
        if not re.search(r'[@$%&*!?]', password):
            messages.error(request, 'Password must contain at least one special character.')
            return redirect('signup')
        
        # confirm password check
        if password != confirm_password:
            messages.error(request, 'Password does not match')
            return redirect('signup')

        otp = generate_otp()

        if not referral_code:
            referral_code = request.session.get('referral_code', '')

        request.session['signup_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': digits_only,
            'password': password,
            'referral_code': referral_code,
            'otp': otp,
            'otp_created_at': timezone.now().isoformat(),
        }

        request.session['otp'] = otp
        request.session['signup_email'] = email
        request.session['otp_purpose'] = 'signup'

        message = (
            f'Hello {first_name},\n\n'
            f'Your OTP for MyShoes account verification is: {otp}\n\n'
            f'This OTP will expire in 2 minutes.\n\n'
            f'If you did not request this, please ignore this email.\n\n'
            f'Thanks,\n MyShoes Team.'
        )

        send_mail(
            'MyShoes Account Verification OTP',
            message,
            'ishaque7jifri@gmail.com',
            [email],
            fail_silently=False,

        )
        print('otp1:',otp)
                
    
        return redirect('verify_otp')
    
    ref = request.GET.get('ref', '').strip()
    if ref:
        request.session['referral_code'] = ref
        
    return render(request,'signup.html',{'referral_code': referral_code,})

def signup_error(request, message):
    messages.error(request, message)
    return render(request, 'signup.html')    

def generate_otp():
    return str(random.randint(100000, 999999))


@never_cache
def verify_otp(request):

    signup_data = request.session.get('signup_data')

    if request.method == 'POST':

        entered_otp = request.POST.get('otp')
      
        # SIGNUP OTP VERIFICATION
        
        if signup_data:

            created_at = signup_data.get('otp_created_at')

            if created_at:
                created_at = timezone.datetime.fromisoformat(created_at)

                if timezone.now() > created_at + timedelta(minutes=2):
                    messages.error(request, 'OTP has expired')
                    return redirect('signup')

            stored_otp = request.session.get('otp')
            print("Entered OTP:", entered_otp)
            print("Stored OTP:", stored_otp)
            
            if str(entered_otp) != str(stored_otp):
                messages.error(request, 'Invalid OTP')
                return redirect('verify_otp')

            referred_by_user = None
            ref_code = signup_data.get('referral_code')

            if ref_code:
                try:
                    referred_by_user = User.objects.get(referral_code=ref_code)
                except User.DoesNotExist:
                    pass

            user = User.objects.create_user(
                    username=signup_data['email'],
                    email=signup_data['email'],
                    first_name=signup_data['first_name'],
                    last_name=signup_data['last_name'],
                    password=signup_data['password'],
                    phone=signup_data['phone'],
                    referred_by=referred_by_user
                )

                # Payout referral bonuses
            if referred_by_user:
                    referrer_wallet, _ = Wallet.objects.get_or_create(user=referred_by_user)
                    referrer_wallet.deposit(
                        amount=Decimal('100.00'),
                        description=f"Referral reward for inviting {user.email}",
                        transaction_type='referral_reward'
                    )
                    referee_wallet, _ = Wallet.objects.get_or_create(user=user)
                    referee_wallet.deposit(
                        amount=Decimal('50.00'),
                        description=f"Sign up bonus using referral from {referred_by_user.email}",
                        transaction_type='referral_reward'
                    )

            request.session.pop('signup_data', None)
            request.session.pop('otp', None)
            request.session.pop('signup_email', None)
            request.session.pop('otp_purpose', None)
            request.session.pop('referral_code', None)

            messages.success(request, 'Account created successfully')
            return redirect('login')

            messages.error(request, 'Invalid OTP')
            return redirect('verify_otp')
        
        # PASSWORD RESET OTP
       
        reset_email = request.session.get('reset_email')
        reset_otp = request.session.get('reset_otp')

        if reset_email and reset_otp:

            created_at = request.session.get('reset_otp_created_at')

            if created_at:
                created_at = timezone.datetime.fromisoformat(created_at)

                if timezone.now() > created_at + timedelta(minutes=2):
                    messages.error(request, 'OTP has expired')
                    return redirect('forget_password')

            if str(entered_otp) == str(reset_otp):
                return redirect('new_password')

            messages.error(request, 'Invalid OTP')
            return redirect('verify_otp')

        messages.error(request, 'Session expired. Try again!')
        return redirect('login')
    
    # TIMER DATA FOR TEMPLATE
    
    expiry_time = None

    if signup_data:
        expiry_time = signup_data.get('otp_created_at')

    elif request.session.get('reset_otp_created_at'):
        expiry_time = request.session.get('reset_otp_created_at')

    return render(
        request,
        'email/verify_otp.html',
        {
            'otp_expiry': expiry_time
        }
    )

@never_cache
def resend_otp(request):

    signup_data = request.session.get('signup_data')

    if not signup_data:
        return redirect('signup')
    
    otp = generate_otp()
    signup_data['otp'] = otp
    signup_data['otp_created_at'] = timezone.now().isoformat()
    request.session['signup_data'] = signup_data

    first_name = signup_data['first_name']

    message = (
        f'Hello {first_name},\n\n'
        f'Your new OTP for MyShoes account verification is: {otp}\n\n'
        f'This OTP will expire in 2 minutes.\n\n'
        'Thanks,\n MyShoes Team.'
    )
    

    send_mail(
        'Your New OTP',
        message,
        'ishaque7jifri@gmail.com',
        [signup_data['email']],
        fail_silently=False,        
    )
    print('otp2:',otp)
    messages.success(request, 'OTP Resent Successfully')

    return redirect('verify_otp')


@never_cache
def user_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request,username=email,password=password)

        if user is not None:
            if user.is_block:
                messages.error(request,'your account is blocked by admin')
                return redirect('login')
            login(request,user)
            messages.success(request,'Login successfully')

            request.session['just_logged_in'] = True
            # return redirect('home')
            return redirect('home')
        else:
            messages.error(request,'invalid email or password')  
       
    return render(request,'login.html')         

def logout_view(request):
    logout(request)
    messages.success(request,'Logged out successfully')
    return redirect('home')

def home(request):
    categories = Category.objects.filter(is_active=True)

    if request.session.pop('just_logged_in',False):
        messages.success(request,'You are logged in successfully')

    return render(request, "home.html",{
        'categories': categories,
    })     

        
    

def forget_password(request):

    if request.method == "POST":

        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)

            otp = generate_otp()

            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            request.session['otp_purpose'] = 'reset_password'
            request.session['reset_otp_created_at'] = timezone.now().isoformat()

            message = f"""
                    Hello,

                    We received a request to reset your MyShoes account password.

                    Your OTP is:

                    >>>>{otp}<<<<

                    This OTP will expire in 2 minutes.

                    If you did not request a password reset, please ignore this email.

                    Regards,
                    MyShoes Team
                    """     

            send_mail(
                "MyShoes Account Reset Password OTP",
                message,
                "ishaque7jifri@gmail.com",
                [email],
                fail_silently=False
            )

            print('forget.otp:',otp)
            return redirect("verify_otp")
        
        except User.DoesNotExist:
            messages.error(request,"Email not registered")

    return render(request,'password/forget_password.html')

def new_password(request):

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')

        if password != confirm:
            messages.error(request,'Passwords do not match')
            return redirect('new_password')
        
        email = request.session.get('reset_email')

        if not email:
            messages.error(request,'Session Expired')
            return redirect('login')
        
        try:
            user = User.objects.get(email = email)
            user.set_password(password)
            user.save()
        except User.DoesNotExist:
            messages.error(request,'User not found')
            return redirect('login')    

        request.session.pop('reset_email',None)
        request.session.pop('reset_otp',None)
        
        messages.success(request,'Password reset Successful')
        return redirect('login')
    
    return render(request,'password/new_password.html')


@never_cache
@login_required(login_url='login')
def profile(request):

    addresses = Address.objects.filter(user=request.user)
    categories = Category.objects.filter(is_active=True)  

    if request.method == 'POST':
        image = request.FILES.get('profile_image')

        if image:
            request.user.profile_image = image
            request.user.save()
            messages.success(request,'Profile image updated') 
        else:
            messages.error(request,'Please select an image')     

        return redirect('profile')
        
    return render(request,'accounts/profile.html',{
        'addresses': addresses,
        'categories': categories,
        })


@never_cache
@login_required(login_url='login')
def edit_profile(request):
    categories = Category.objects.filter(is_active=True)

    user = request.user

    original_first_name = user.first_name
    original_last_name = user.last_name
    original_email = user.email
    original_phone = user.phone

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.phone = request.POST.get('phone', '').strip() 

        if not all([user.first_name, user.last_name, user.email, user.phone]):
            messages.error(request, 'All fields are required.')
            return redirect('edit_profile')

        if len(user.first_name) < 3 or len(user.first_name) > 15:
            messages.error(request, 'First name must be between 3 and 15 characters.')
            return redirect('edit_profile')
        
        if not re.fullmatch(r'^[A-Za-z ]+$', user.first_name):
            messages.error(request, 'First name should contain only letters and spaces.')
            return redirect('edit_profile')
        
        if len(user.last_name) < 3 or len(user.last_name) > 15:
            messages.error(request, 'Last name must be between 3 and 15 characters.')
            return redirect('edit_profile')
        
        if not re.fullmatch(r'^[A-Za-z ]+$', user.last_name):
            messages.error(request, 'Last name should contain only letters and spaces.')
            return redirect('edit_profile')
        
        try:
            validate_email(user.email)
        except ValidationError:
            messages.error(request, 'Enter a valid Email address')
            return redirect('edit_profile')

        if User.objects.exclude(id=user.id).filter(email=user.email).exists():
            messages.error(request, 'Email already existed')
            return redirect('edit_profile') 

        digits_only = re.sub(r'\D', '', user.phone)

        if len(digits_only) != 10:
            messages.error(request, 'Phone number must contain exactly 10 digits.')
            return redirect('edit_profile')

        if len(set(digits_only)) == 1:
            messages.error(request, 'Invalid phone number.')
            return redirect('edit_profile')

        if User.objects.exclude(id=user.id).filter(phone=digits_only).exists():
            messages.error(request, 'Phone number already registered.')
            return redirect('edit_profile')

        user.phone = digits_only

        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES.get('profile_image')

        if not request.FILES.get('profile_image') and (
            user.first_name == original_first_name and
            user.last_name == original_last_name and
            user.email == original_email and
            user.phone == original_phone
            ):
            messages.info(request, 'No changes detected.')
            return redirect('profile')    

        user.save()
        messages.success(request,'Profile Updated successfully') 
        return redirect('profile')   

    return render(request, 'accounts/edit_profile.html', {'user': user, 'categories': categories})   


@never_cache
@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_new_password')

        user = request.user

        if not user.check_password(current_password):
            messages.error(request,'Current password is incorrect')
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(request,'New passwords not matching')
            return redirect('change_password')

        if current_password == new_password:
            messages.error(request,'New password cannot be same as old password')
            return redirect('change_password')     
        
        user.set_password(new_password) 
        user.save()

        messages.success(request,'Password changed successfully, Please login again')
        return redirect('login')

    return render(request, 'accounts/change_password.html')   


@never_cache
@login_required(login_url='login')
def change_email(request):

    if request.method == 'POST':
        new_mail = request.POST.get('email')

        if not new_mail:
            messages.error(request,'Email is required')
            return redirect('change_email')
        
        otp = generate_otp()

        request.session['email_otp'] = otp
        request.session['new_email'] = new_mail
        request.session['email_otp_created_at'] = timezone.now().isoformat()

        message = f''' 

        Hello,

        Your new OTP for Email change is:

        >>>> {otp} <<<<

        This OTP will expire in 2 minutes.
        Thanks
        MyShoes

       '''

        try:
            send_mail(
                subject='Your OTP for Email Change',
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[new_mail],
                fail_silently=False,
            )
            print('email otp:',otp)

            messages.success(request,'OTP send to your new email')
            return redirect('email_change_otp')
        except Exception as e:
            messages.error(request,f'Error sending email: {e}')
            return redirect('change_email')

    return render(request, 'accounts/change_email.html') 



@never_cache
@login_required(login_url='login')
def email_change_otp(request):

    if request.method == "POST":

        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('email_otp') 
        new_email = request.session.get('new_email')

        print("Entered OTP:", entered_otp)
        print("Session OTP:", session_otp)

        if not entered_otp:
            messages.error(request,'Enter OTP')
            return redirect('email_change_otp')
        
        created_at = request.session.get('email_otp_created_at')

        if created_at:
            created_at = timezone.datetime.fromisoformat(created_at)

            if timezone.now() > created_at + timedelta(minutes=2):
                messages.error(request, 'OTP has Expired')
                return redirect('change_email')

        if str(entered_otp) == str(session_otp):
            user = request.user
            user.email = new_email
            user.save()

            request.session.pop('email_otp', None)
            request.session.pop('new_email', None)
            request.session.pop('email_otp_created_at', None)

            messages.success(request,'Email updated successfully')
            return redirect('profile')
        else:
            messages.error(request,'Invalid OTP')
    
    expiry_time = request.session.get('email_otp_created_at')        

    return render(request,'accounts/email_change_otp.html',{'otp_expiry': expiry_time})


@never_cache
@login_required
def resend_email_otp(request):

    new_email = request.session.get('new_email')

    if not new_email:
        messages.error(request, 'Email session expired.')
        return redirect('change_email')
    
    otp = generate_otp()

    request.session['email_otp'] = otp
    request.session['email_otp_created_at'] = timezone.now().isoformat()

    message = f''' 

        Hello,

        Your Email change new resend OTP is:

        >>>> {otp} <<<<

        This OTP will expire in 2 minutes.
        Thanks
        MyShoes

       '''
    
    send_mail(
        subject='Your OTP for Email Change',
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[new_email],
        fail_silently=False,
    )

    messages.success(request, 'New OTP sent Successfully.')
    return redirect('email_change_otp')


@never_cache
@login_required(login_url='login')
def my_address(request):

    addresses = Address.objects.filter(user=request.user).order_by('-id')
    categories = Category.objects.filter(is_active=True)

    return render(request,'accounts/my_address.html',{'addresses': addresses, 'categories': categories})    


@never_cache
@login_required(login_url='login')
def add_address(request):

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user

            if address.is_default:
                Address.objects.filter(user=request.user).update(is_default=False)

            if not Address.objects.filter(user=request.user).exists():
                address.is_default=True    

            address.save()
            messages.success(request,'Address added successfully')

            if next_url == 'checkout':
                return redirect('checkout')

            return redirect('my_address')
    else:
        form = AddressForm()
        

    return render(request,'accounts/add_address.html',{'form': form, 'next': next_url})

@never_cache
@login_required(login_url='login')
def edit_address(request,id):

    next_url = request.GET.get('next') or request.POST.get('next')
    address = get_object_or_404(Address,id=id,user=request.user)

    if request.method == "POST":
        form = AddressForm(request.POST,instance=address)
        if form.is_valid():

            if not form.has_changed():
                messages.info(request, 'No changes detected')
                return redirect('my_address')
            
            updated_address = form.save(commit=False)

            if updated_address.is_default:
                Address.objects.filter(user = request.user).exclude(id=address.id).update(is_default = False)

            updated_address.save()

            messages.success(request,'Address updated successfully')
            if next_url == 'checkout':
                return redirect('checkout')
            return redirect('my_address')

        else:
            messages.error(request, 'Failed to update the address. Please check the form.')    
    else:
        form = AddressForm(instance=address)


    return render(request,'accounts/edit_address.html',{
        'form': form,
        'address':address,
        'next': next_url    
        })  


@never_cache
@login_required(login_url='login')
def delete_address(request, id):

    if request.method != "POST":
        return redirect('my_address')

    next_url = request.POST.get('next')

    address = get_object_or_404(
        Address,
        id=id,
        user=request.user
    )

    # Prevent deleting default address (optional)
    if address.is_default:
        messages.error(request, 'Default address cannot be deleted')
        return redirect('my_address')

    address.delete()

    messages.success(request, 'Address Deleted Successfully')

    if next_url == 'checkout':
        return redirect('checkout')

    return redirect('my_address')


@never_cache
@login_required(login_url='login')
def user_wallet(request):
    categories = Category.objects.filter(is_active=True)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all().order_by('-timestamp')

    if request.method == 'POST':
        amount = request.POST.get('amount', '').strip()
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError
            wallet.deposit(amount, "Funds deposited to wallet", transaction_type='deposit')
            messages.success(request, f"₹{amount} deposited successfully to your wallet!")
            return redirect('user_wallet')
        except (ValueError, InvalidOperation):
            messages.error(request, "Please enter a valid deposit amount.")
            return redirect('user_wallet')

    return render(request, 'accounts/wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
        'categories': categories,
    })