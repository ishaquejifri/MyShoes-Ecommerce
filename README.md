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
- SQLite
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
myenv\Scripts\activate
```

5. Install dependencies:
```bash
pip install -r requirements.txt
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Start the server:
```bash
python manage.py runserver
```

## Author

Developed as part of an academic internship project.