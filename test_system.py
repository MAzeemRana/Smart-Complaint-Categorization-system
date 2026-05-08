#!/usr/bin/env python3
"""
Test script to verify Smart Complaint System registration and login.
Run: python test_system.py
"""

from app import app, db, User, VerificationCode
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
import random

def test_admin_login():
    """Test admin account login"""
    print("\n" + "="*60)
    print("TEST 1: Admin Login")
    print("="*60)
    
    with app.app_context():
        client = app.test_client()
        response = client.post('/login', data={
            'email': 'admin@complaintsystem.com',
            'password': 'admin123'
        }, follow_redirects=False)
        
        if response.status_code == 302 and response.headers.get('Location') == '/dashboard':
            print("✓ Admin login successful")
            print(f"  Status: {response.status_code}")
            print(f"  Redirects to: /dashboard")
            return True
        else:
            print("✗ Admin login failed")
            print(f"  Status: {response.status_code}")
            return False

def test_user_registration():
    """Test complete user registration flow"""
    print("\n" + "="*60)
    print("TEST 2: User Registration Flow")
    print("="*60)
    
    with app.app_context():
        db.create_all()
        
        # Clean up
        test_email = 'registration_test@example.com'
        User.query.filter_by(email=test_email).delete()
        VerificationCode.query.filter_by(email=test_email).delete()
        db.session.commit()
        
        # Create verification code
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        vc = VerificationCode(
            email=test_email,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        db.session.add(vc)
        db.session.commit()
        
        print(f"Step 1: Generated verification code: {code}")
        
        # Test registration
        client = app.test_client()
        response = client.post('/register', data={
            'email': test_email,
            'name': 'Test User',
            'password': 'testpass123',
            'verification_code': code
        }, follow_redirects=False)
        
        if response.status_code == 302:
            print(f"✓ Registration POST successful (Status: {response.status_code})")
        else:
            print(f"✗ Registration failed (Status: {response.status_code})")
            return False
        
        # Check user in database
        user = User.query.filter_by(email=test_email).first()
        if user:
            print(f"✓ User created in database")
            print(f"  Email: {user.email}")
            print(f"  Name: {user.name}")
            print(f"  Verified: {user.is_verified}")
            
            # Test login
            response = client.post('/login', data={
                'email': test_email,
                'password': 'testpass123'
            }, follow_redirects=False)
            
            if response.status_code == 302 and response.headers.get('Location') == '/dashboard':
                print(f"✓ Login successful with new account")
                print(f"  Redirects to: /dashboard")
                return True
            else:
                print(f"✗ Login failed")
                return False
        else:
            print("✗ User not found in database")
            return False

def test_password_reset():
    """Test password reset flow"""
    print("\n" + "="*60)
    print("TEST 3: Password Reset Flow")
    print("="*60)
    
    with app.app_context():
        db.create_all()
        
        test_email = 'reset_test@example.com'
        
        # Create user
        user = User(
            email=test_email,
            name='Reset Test User',
            password_hash='old_hash',
            is_verified=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Create reset code
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        vc = VerificationCode(
            email=test_email,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            is_used=False
        )
        db.session.add(vc)
        db.session.commit()
        
        print(f"Step 1: Generated reset code: {code}")
        
        client = app.test_client()
        response = client.post('/reset-password', data={
            'email': test_email,
            'code': code,
            'new_password': 'newpass123'
        }, follow_redirects=False)
        
        if response.status_code == 302 and response.headers.get('Location') == '/login':
            print(f"✓ Password reset successful (Status: {response.status_code})")
            print(f"  Redirects to: /login")
            
            # Verify password was updated
            user = User.query.filter_by(email=test_email).first()
            if user.password_hash != 'old_hash':
                print(f"✓ Password hash updated in database")
                return True
            else:
                print(f"✗ Password hash not updated")
                return False
        else:
            print(f"✗ Password reset failed (Status: {response.status_code})")
            return False

def test_database():
    """Test database connectivity"""
    print("\n" + "="*60)
    print("TEST 4: Database & Configuration")
    print("="*60)
    
    with app.app_context():
        try:
            db.create_all()
            
            # Count existing users
            user_count = User.query.count()
            print(f"✓ Database accessible")
            print(f"  Total users: {user_count}")
            
            # Check admin user
            admin = User.query.filter_by(email='admin@complaintsystem.com').first()
            if admin:
                print(f"✓ Admin user exists")
                print(f"  Email: {admin.email}")
                print(f"  Name: {admin.name}")
                print(f"  Is Admin: {admin.is_admin}")
                return True
            else:
                print(f"✗ Admin user not found")
                return False
        except Exception as e:
            print(f"✗ Database error: {e}")
            return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SMART COMPLAINT SYSTEM - TEST SUITE")
    print("="*60)
    
    results = {
        'Admin Login': test_admin_login(),
        'User Registration': test_user_registration(),
        'Password Reset': test_password_reset(),
        'Database': test_database()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED - System is ready for deployment!")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()
