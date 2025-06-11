# HUST SHOP - Ecommerce Platform

![Django](https://img.shields.io/badge/Django-3.2-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)

## 📦 Cài đặt dự án

### 1. Clone repository
```bash
git clone https://github.com/mingquanjp/HUSTSHOP.git
cd HUSTSHOP
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
```
#### Windows:
.\venv\Scripts\activate
#### Mac/Linux:
source venv/bin/activate

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
Lưu ý: Nếu gặp lỗi, chạy pip install --upgrade pip để cập nhật pip.
### 4. Environment Configuration
Create and setting .env file with your secret information
```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DB_NAME=hustshop_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 5. Database Setup AND Create SuperUser
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run the Server
```bash
python manage.py runserver
```



