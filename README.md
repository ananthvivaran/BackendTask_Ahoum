# Backend Task – Events Platform (Ahoum)

A Django REST API backend for an events platform with JWT authentication, email OTP verification, role-based access control (RBAC), event management, and enrollments.


---

## 🚀 Features

### 🔐 Authentication & Authorization
- User signup with email OTP verification
- JWT-based login & refresh using SimpleJWT
- Block login for unverified users
- Role-Based Access Control:
  - Seeker – can search and enroll in events
  - Facilitator – can create and manage events

### 📅 Events
- Create, update, delete events (Facilitator only)
- List and view event details
- Search & filter events by:
  - location
  - language
  - date range
  - keyword (title/description)

### 🎟️ Enrollments
- Seekers can enroll in events
- Capacity check before enrollment
- Cancel enrollment
- View upcoming and past enrollments
- Prevent duplicate active enrollments

### 📊 Facilitator Dashboard
- List own events
- View total enrollments & available seats per event

### 🛡️ OTP Security
- OTP expiry (5 minutes)
- Max OTP attempts limit
- Email verification required before login

---

## 🏗️ Tech Stack

- Python 3
- Django
- Django REST Framework
- SimpleJWT
- SQLite (local dev)
- Git & GitHub

---

## 📁 Project Structure

events_backend/
│
├── backend/
├── events/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── urls.py
│   └── migrations/
│
├── manage.py
├── requirements.txt
└── README.md

---

## ⚙️ Setup Instructions

### 1️⃣ Clone repository
git clone https://github.com/ananthvivaran/BackendTask_Ahoum.git  
cd BackendTask_Ahoum

### 2️⃣ Create virtual environment
python -m venv venv  
venv\Scripts\activate   (Windows)

### 3️⃣ Install dependencies
pip install -r requirements.txt

### 4️⃣ Apply migrations
python manage.py makemigrations  
python manage.py migrate

### 5️⃣ Run server
python manage.py runserver

Server runs at:  
http://127.0.0.1:8000/

---

## 🔑 Environment Variables

Configure email in backend/settings.py:

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  
EMAIL_HOST = 'smtp.gmail.com'  
EMAIL_PORT = 587  
EMAIL_USE_TLS = True  
EMAIL_HOST_USER = 'your_email@gmail.com'  
EMAIL_HOST_PASSWORD = 'your_app_password'

(Use Gmail App Passwords)

---

## 🔁 Authentication Flow

1. Signup → /api/auth/signup/  
2. Receive OTP on email  
3. Verify OTP → /api/auth/verify/  
4. Login → /api/auth/login/ → get tokens  
5. Use header:  
Authorization: Bearer <access_token>

---

## 📌 API Endpoints

### Auth
- POST /api/auth/signup/
- POST /api/auth/verify/
- POST /api/auth/login/
- POST /api/auth/refresh/

### Events
- GET /api/events/
- GET /api/events/search/
- GET /api/events/<id>/
- POST /api/events/create/
- PUT /api/events/<id>/
- DELETE /api/events/<id>/delete/

### Enrollments (Seeker)
- POST /api/events/<id>/enroll/
- POST /api/events/<id>/cancel/
- GET /api/me/enrollments/upcoming/
- GET /api/me/enrollments/past/

### Facilitator
- GET /api/facilitator/my-events/

---

## 🧠 Design Decisions

- DRF + SimpleJWT for auth
- Email used as username
- OTP with expiry & attempts
- Unique constraint on active enrollments
- Indexed searchable fields

---

## 🗄️ Database

- SQLite for local development
- Compatible with PostgreSQL
- Indexed:
  - starts_at
  - language
  - location

---

## 🧪 API Testing

All APIs tested using Postman.

---

## 👤 Author

Ananth Vivaran  
GitHub: https://github.com/ananthvivaran

---

## ✅ Status

All major backend task requirements implemented:
- JWT Auth
- OTP verification
- RBAC
- Events CRUD
- Enrollments
- Search & filters
- Clean migrations
