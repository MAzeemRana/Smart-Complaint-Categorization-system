from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
import os
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from utils.email_utils import send_verification_email, send_reset_code_email
from complaint_classifier import ComplaintClassifier
import joblib
import random

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))

# ========== SIRF YAHI CHANGE KIA HAI ==========
# Database directory ensure karo
import os
os.makedirs('database', exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath("database/complaint_system.db")}'
# =============================================

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page'

# Initialize classifier (lazy loading)
classifier = None

def get_classifier():
    global classifier
    if classifier is None:
        try:
            classifier = ComplaintClassifier()
        except Exception:
            classifier = None
    return classifier

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    complaints = db.relationship('Complaint', backref='user', lazy=True)
    resolutions = db.relationship('ResolutionLog', backref='resolved_by_user', lazy=True)

class VerificationCode(db.Model):
    __tablename__ = 'verification_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

class Complaint(db.Model):
    __tablename__ = 'complaints'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    severity_score = db.Column(db.Float, default=0.0)
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(20), default='Pending')
    sentiment = db.Column(db.String(20))
    department = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    resolution_logs = db.relationship('ResolutionLog', backref='complaint', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    department = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ResolutionLog(db.Model):
    __tablename__ = 'resolution_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resolution_notes = db.Column(db.Text, nullable=False)
    resolution_time_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name')
        password = request.form.get('password')
        verification_code = request.form.get('verification_code')
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Invalid email format', 'error')
            return redirect(url_for('register'))
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        # Verify code
        code_record = VerificationCode.query.filter_by(
            email=email, 
            code=verification_code, 
            is_used=False
        ).first()

        if not code_record:
            flash('Invalid verification code. Please request a new one.', 'error')
            return redirect(url_for('register'))

        if code_record.expires_at < datetime.utcnow():
            flash('Verification code expired. Please request a new code.', 'error')
            return redirect(url_for('register'))
        
        # Create user
        from werkzeug.security import generate_password_hash
        user = User(
            email=email,
            name=name,
            password_hash=generate_password_hash(password),
            is_verified=True
        )
        
        code_record.is_used = True
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/send-verification', methods=['POST'])
def send_verification():
    data = request.get_json(silent=True)
    email = None
    if data and isinstance(data, dict):
        email = data.get('email')
    if not email:
        email = request.form.get('email')

    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400

    email = email.strip().lower()
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400

    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400

    # Check if email already registered
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    # Generate 6-digit code
    import random
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # Save to database
    verification = VerificationCode(
        email=email,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    
    db.session.add(verification)
    db.session.commit()
    
    # Send email
    success, info_message = send_verification_email(email, code)
    if success:
        return jsonify({'success': True, 'message': info_message or 'Verification code sent'})
    else:
        return jsonify({'success': False, 'message': info_message or 'Failed to send email'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            from werkzeug.security import check_password_hash
            if check_password_hash(user.password_hash, password):
                if user.is_verified:
                    login_user(user)
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Please verify your email first', 'error')
            else:
                flash('Invalid password', 'error')
        else:
            flash('Email not found', 'error')
    
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('forgot_password'))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('If the email is registered, a reset code has been sent', 'success')
            return redirect(url_for('reset_password'))

        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        verification = VerificationCode(
            email=email,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        db.session.add(verification)
        db.session.commit()

        success, info_message = send_reset_code_email(email, code)
        if success:
            flash('Reset code sent. Check your email and use it to reset your password.', 'success')
            return redirect(url_for('reset_password'))
        else:
            flash(info_message or 'Failed to send reset code. Try again later.', 'error')
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        code = request.form.get('code', '').strip()
        new_password = request.form.get('new_password')

        if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('reset_password'))

        if not code or len(code) != 6:
            flash('Please enter the 6-digit reset code', 'error')
            return redirect(url_for('reset_password'))

        if not new_password or len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('reset_password'))

        code_record = VerificationCode.query.filter_by(
            email=email,
            code=code,
            is_used=False
        ).first()

        if not code_record or code_record.expires_at < datetime.utcnow():
            flash('Invalid or expired reset code. Please try again.', 'error')
            return redirect(url_for('forgot_password'))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found for this email', 'error')
            return redirect(url_for('register'))

        user.password_hash = generate_password_hash(new_password)
        code_record.is_used = True
        db.session.commit()

        flash('Password reset successful! Please login with your new password.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    complaints_count = Complaint.query.filter_by(user_id=current_user.id).count()
    resolved_count = Complaint.query.filter_by(user_id=current_user.id, status='Resolved').count()
    pending_count = Complaint.query.filter_by(user_id=current_user.id, status='Pending').count()
    
    complaints_by_category = db.session.query(
        Complaint.category, db.func.count(Complaint.id)
    ).filter_by(user_id=current_user.id).group_by(Complaint.category).order_by(db.func.count(Complaint.id).desc()).all()
    complaints_by_category = [(row[0], row[1]) for row in complaints_by_category]
    top_category = complaints_by_category[0][0] if complaints_by_category else 'N/A'
    top_category_count = complaints_by_category[0][1] if complaints_by_category else 0

    complaints_by_priority = db.session.query(
        Complaint.priority, db.func.count(Complaint.id)
    ).filter_by(user_id=current_user.id).group_by(Complaint.priority).all()
    complaints_by_priority = [(row[0], row[1]) for row in complaints_by_priority]

    complaints_by_status = db.session.query(
        Complaint.status, db.func.count(Complaint.id)
    ).filter_by(user_id=current_user.id).group_by(Complaint.status).all()
    complaints_by_status = [(row[0], row[1]) for row in complaints_by_status]

    monthly_counts = (
        db.session.query(
            db.func.strftime('%Y-%m', Complaint.created_at),
            db.func.count(Complaint.id)
        )
        .filter_by(user_id=current_user.id)
        .group_by(db.func.strftime('%Y-%m', Complaint.created_at))
        .order_by(db.func.strftime('%Y-%m', Complaint.created_at))
        .all()
    )
    monthly_counts = [(row[0], row[1]) for row in monthly_counts]
    
    recent_complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         complaints_count=complaints_count,
                         resolved_count=resolved_count,
                         pending_count=pending_count,
                         top_category=top_category,
                         top_category_count=top_category_count,
                         complaints_by_category=complaints_by_category,
                         complaints_by_priority=complaints_by_priority,
                         complaints_by_status=complaints_by_status,
                         monthly_counts=monthly_counts,
                         recent_complaints=recent_complaints)

@app.route('/submit-complaint', methods=['GET', 'POST'])
@login_required
def submit_complaint():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority')  # Manual priority selection
        
        # Get classification
        classifier = get_classifier()
        if classifier:
            classification = classifier.classify_complaint(description)
        else:
            classification = {
                'category': 'Other',
                'severity_score': 0.5,
                'sentiment': 'neutral',
                'department': 'General Support'
            }
        
        # Create complaint with manual priority
        complaint = Complaint(
            user_id=current_user.id,
            title=title,
            description=description,
            category=classification['category'],
            severity_score=classification['severity_score'],
            priority=priority,  # Use manual priority
            sentiment=classification['sentiment'],
            department=classification['department']
        )
        
        db.session.add(complaint)
        db.session.commit()
        
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('my_complaints'))
    
    return render_template('submit_complaint.html')

@app.route('/my-complaints')
@login_required
def my_complaints():
    complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    return render_template('my_complaints.html', complaints=complaints)

@app.route('/complaint/<int:complaint_id>')
@login_required
def complaint_detail(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('complaint_detail.html', complaint=complaint)

@app.route('/delete-complaint/<int:complaint_id>', methods=['POST'])
@login_required
def delete_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    ResolutionLog.query.filter_by(complaint_id=complaint.id).delete()
    db.session.delete(complaint)
    db.session.commit()

    flash('Complaint deleted successfully.', 'success')
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('my_complaints'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    total_complaints = Complaint.query.count()
    pending_complaints = Complaint.query.filter_by(status='Pending').count()
    resolved_complaints = Complaint.query.filter_by(status='Resolved').count()
    
    complaints_by_category = db.session.query(
        Complaint.category, db.func.count(Complaint.id)
    ).group_by(Complaint.category).order_by(db.func.count(Complaint.id).desc()).all()
    complaints_by_category = [(row[0], row[1]) for row in complaints_by_category]
    top_category = complaints_by_category[0][0] if complaints_by_category else 'N/A'
    top_category_count = complaints_by_category[0][1] if complaints_by_category else 0

    complaints_by_priority = db.session.query(
        Complaint.priority, db.func.count(Complaint.id)
    ).group_by(Complaint.priority).all()
    complaints_by_priority = [(row[0], row[1]) for row in complaints_by_priority]

    complaints_by_status = db.session.query(
        Complaint.status, db.func.count(Complaint.id)
    ).group_by(Complaint.status).all()
    complaints_by_status = [(row[0], row[1]) for row in complaints_by_status]

    monthly_counts = (
        db.session.query(
            db.func.strftime('%Y-%m', Complaint.created_at),
            db.func.count(Complaint.id)
        )
        .group_by(db.func.strftime('%Y-%m', Complaint.created_at))
        .order_by(db.func.strftime('%Y-%m', Complaint.created_at))
        .all()
    )
    monthly_counts = [(row[0], row[1]) for row in monthly_counts]
    
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    
    return render_template('admin_dashboard.html',
                         total_complaints=total_complaints,
                         pending_complaints=pending_complaints,
                         resolved_complaints=resolved_complaints,
                         complaints_by_category=complaints_by_category,
                         top_category=top_category,
                         top_category_count=top_category_count,
                         complaints_by_priority=complaints_by_priority,
                         complaints_by_status=complaints_by_status,
                         monthly_counts=monthly_counts,
                         complaints=complaints)

@app.route('/admin-settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_password:
            flash('Current password is required.', 'error')
            return redirect(url_for('admin_settings'))

        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is not correct.', 'error')
            return redirect(url_for('admin_settings'))

        if new_email:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
                flash('Please enter a valid email address.', 'error')
                return redirect(url_for('admin_settings'))

            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('This email is already registered.', 'error')
                return redirect(url_for('admin_settings'))

            current_user.email = new_email

        if new_password:
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'error')
                return redirect(url_for('admin_settings'))
            if new_password != confirm_password:
                flash('New password and confirmation do not match.', 'error')
                return redirect(url_for('admin_settings'))
            current_user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash('Admin profile updated successfully.', 'success')
        return redirect(url_for('admin_settings'))

    return render_template('admin_settings.html')

@app.route('/update-complaint-status/<int:complaint_id>', methods=['POST'])
@login_required
def update_complaint_status(complaint_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    complaint = Complaint.query.get_or_404(complaint_id)
    status = request.json.get('status')
    resolution_notes = request.json.get('resolution_notes', '')
    
    previous_status = complaint.status
    if status == previous_status:
        return jsonify({'success': True, 'message': 'No change required'})

    complaint.status = status
    
    if status == 'Resolved' and previous_status != 'Resolved':
        resolution_time = (datetime.utcnow() - complaint.created_at).total_seconds() / 60
        
        resolution_log = ResolutionLog(
            complaint_id=complaint.id,
            resolved_by=current_user.id,
            resolution_notes=resolution_notes,
            resolution_time_minutes=int(resolution_time)
        )
        db.session.add(resolution_log)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Status updated'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default categories
        categories = [
            ('Billing Issue', 'Problems related to payments and billing', 'Finance'),
            ('Technical Problem', 'Technical issues with product/service', 'IT Support'),
            ('Service Delay', 'Delays in service delivery', 'Operations'),
            ('Quality Issue', 'Issues with product/service quality', 'Quality Assurance'),
            ('Customer Service', 'Issues with customer support', 'Customer Relations'),
            ('Other', 'Other types of complaints', 'General')
        ]
        
        for name, desc, dept in categories:
            if not Category.query.filter_by(name=name).first():
                category = Category(name=name, description=desc, department=dept)
                db.session.add(category)
        
        # Create admin user if not exists
        if not User.query.filter_by(email='admin@complaintsystem.com').first():
            from werkzeug.security import generate_password_hash
            admin = User(
                email='admin@complaintsystem.com',
                name='Admin',
                password_hash=generate_password_hash('admin123'),
                is_verified=True,
                is_admin=True
            )
            db.session.add(admin)
        
        db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
