# Registration & Login Guide - Smart Complaint System

## Quick Start

### Run the Application
```bash
cd /home/ishaq-raza-khosa/Desktop/KHizen
source venv/bin/activate
python app.py
```

Open browser: `http://localhost:5000`

---

## Login (Easiest Way to Test)

**Admin Account (Pre-created):**
- Email: `admin@complaintsystem.com`
- Password: `admin123`

This account has admin privileges to:
- View all complaints
- Update complaint statuses
- See analytics dashboard

---

## User Registration Flow

### Step 1: Register New User

Go to: `http://localhost:5000/register`

Fill in the form:
- **Full Name**: Enter your name
- **Email Address**: Enter valid email
- **Verification Code**: (leave empty for now)
- **Password**: Enter password (min 6 chars)
- **Confirm Password**: Must match password

### Step 2: Get Verification Code

1. Click blue **"Send Code"** button next to email field
2. You will see alert: ✓ "Verification code sent!"
3. Check your email inbox for a code
4. If using Gmail, the code is in the automated email

### Step 3: Complete Registration

1. Copy the 6-digit code from email
2. Paste it in **"Verification Code"** field
3. Click **"Register"** button
4. You will see: "Registration successful! Please login."
5. Login with your credentials

---

## Forgot Password

If you forget your password:

1. Go to: `http://localhost:5000/login`
2. Click **"Forgot Password?"** link
3. Enter your registered email
4. Click **"Send Reset Code"**
5. Check your email for reset code
6. Go to `/reset-password`
7. Enter email, reset code, and new password
8. Click **"Reset Password"**
9. Login with new password

---

## Features Included

✅ User Registration with Email Verification  
✅ User Login with Email & Password  
✅ Password Reset/Recovery  
✅ Dashboard with Complaint Statistics  
✅ Submit Complaints with AI Classification  
✅ View My Complaints  
✅ Admin Dashboard  
✅ Update Complaint Status (Admin)  
✅ Resolution Logs (Admin)  

---

## Database

SQLite database is auto-created at:
`/home/ishaq-raza-khosa/Desktop/KHizen/database/complaint_system.db`

Default admin user:
- Email: `admin@complaintsystem.com`
- Password: `admin123`

---

## Testing Registration Programmatically

```python
from app import app, db, User, VerificationCode
from datetime import datetime, timedelta
import random

with app.app_context():
    # Create verification code
    code = '123456'
    vc = VerificationCode(
        email='user@example.com',
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db.session.add(vc)
    db.session.commit()
    
    # Test registration
    client = app.test_client()
    response = client.post('/register', data={
        'email': 'user@example.com',
        'name': 'Test User',
        'password': 'password123',
        'verification_code': code
    })
    
    print(f"Registration Status: {response.status_code}")
    user = User.query.filter_by(email='user@example.com').first()
    print(f"User Created: {user is not None}")
```

---

## Email Configuration

Email is configured in `.env` file:
```
EMAIL_USER=irkhosa101@gmail.com
EMAIL_PASSWORD=uabgvxrlblmwhixr
```

Using Gmail App Password (recommended for Gmail accounts).

---

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login user
- `GET /logout` - Logout user
- `POST /send-verification` - Send verification code
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password

### User Routes
- `GET /dashboard` - User dashboard
- `POST /submit-complaint` - Submit new complaint
- `GET /my-complaints` - View user's complaints
- `GET /complaint/<id>` - View complaint details

### Admin Routes
- `GET /admin` - Admin dashboard
- `POST /update-complaint-status/<id>` - Update complaint status

---

## Common Issues & Solutions

### "Invalid verification code" Error
- Make sure you copied the code correctly from email
- Codes expire after 30 minutes
- Click "Send Code" again to get a new code

### "Email already registered" Error
- Try logging in with existing credentials
- Use "Forgot Password" if you don't remember the password

### Email not receiving codes
- Check spam/junk folder
- Verify email address is correct
- Check `.env` file for email credentials

### "Email credentials not configured"
- Ensure `.env` file exists with:
  - `EMAIL_USER=your_email@gmail.com`
  - `EMAIL_PASSWORD=your_app_password`

---

## Project Structure

```
KHizen/
├── app.py                    # Main Flask application
├── complaint_classifier.py   # AI classifier for complaints
├── requirements.txt          # Python dependencies
├── .env                      # Email & config credentials
├── database/
│   └── complaint_system.db   # SQLite database
├── utils/
│   └── email_utils.py        # Email sending functions
├── static/
│   ├── css/style.css         # Styling
│   └── js/main.js            # Frontend logic
├── templates/
│   ├── base.html             # Base template
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── dashboard.html        # User dashboard
│   ├── admin_dashboard.html  # Admin dashboard
│   └── ...                   # Other templates
```

---

## Ready for Submission

The system includes:
1. ✅ Complete user registration with email verification
2. ✅ Login authentication
3. ✅ Password reset functionality
4. ✅ Complaint submission with AI classification
5. ✅ Admin dashboard with analytics
6. ✅ Database persistence
7. ✅ Error handling and validation
8. ✅ Responsive UI with Bootstrap

---

**Test Account:**
- Email: `admin@complaintsystem.com`
- Password: `admin123`

**Created:** April 2026  
**Version:** 1.0
