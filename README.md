# MyShoes - E-commerce Web Application

MyShoes is an e-commerce web application developed using Django.  
It provides users with an online platform to browse products, manage accounts, and purchase footwear products.

## Features

### User Side
- User Registration and Login
- Email OTP Verification
- Password Reset
- Profile Management
- Browse Products
- Product Details Page
- Category-based Product Listing

### Admin Side
- Admin Login
- Dashboard
- Category Management
- Product Management
- Variant Management
- User Management

## Technologies Used

- Python
- Django
- PostgreSQL
- HTML
- CSS
- JavaScript
- Bootstrap / Tailwind CSS

## Project Structure

- `accounts/` - User authentication and profile management
- `adminpanel/` - Admin dashboard and user management
- `products/` - Product and category management
- `home/` - Homepage and user product display

## Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/ishaquejifri/MyShoes.git
```

2. Navigate to the project directory:
```bash
cd MyShoes
```

3. Create virtual environment:
```bash
python -m venv myenv
```

4. Activate virtual environment:
```bash
windows:
myenv\Scripts\activate

Mac/Linux:
source venv/bin/activate
```

5. Install dependencies:
```bash
pip install -r requirements.txt
```

6. Configure Database
```bash

Update PostgreSQL credentials in settings.py
DATABASES = { 'default': { 'ENGINE': 'django.db.backends.postgresql', 'NAME': 'myshoes_db', 'USER': 'postgres', 'PASSWORD': 'your_password', 'HOST': 'localhost', 'PORT': '5432', } }
```

7. Run migrations:
```bash
python manage.py migrate
```

8.Create Superuser (Admin Access) python manage.py createsuperuser

9. Start the server:
```bash
python manage.py runserver
```

10.Open in Browser http://127.0.0.1:8000/

Admin Panel:
http://127.0.0.1:8000/admin/


## Environment Variables

```.env
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=myshoes_db
DB_USER=postgres
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxx

🚀 Usage

Browse available shoes on the homepage

Click on products to view details

Manage products and users via /admin

Admin can add/edit/delete products

📁 Project Structure (Basic) Myshoes/ │── manage.py │── requirements.txt │── Myshoes/ │ ├── settings.py │ ├── urls.py │ ├── wsgi.py │── products/ │ ├── models.py │ ├── views.py │ ├── urls.py │── templates/ │── static/

## Author

Created by Syed Mohamed Ishaque jifri

📍 Project Status

Under Development – This is my first Django project

Planned Improvements:

Better UI design

Shopping cart functionality

Order & checkout system

Payment gateway integration