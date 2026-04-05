from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import datetime
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-job-platform-secret-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobplatform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# ─── Models ───────────────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    summary = db.Column(db.Text)
    skills = db.Column(db.Text, default='[]')
    job_preferences = db.Column(db.Text, default='{}')
    notification_settings = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    resumes = db.relationship('Resume', backref='user', lazy=True)
    applications = db.relationship('Application', backref='user', lazy=True)
    chat_history = db.relationship('ChatMessage', backref='user', lazy=True)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    original_name = db.Column(db.String(256), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_master = db.Column(db.Boolean, default=False)
    extracted_text = db.Column(db.Text)
    quality_score = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    version = db.Column(db.Integer, default=1)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    job_url = db.Column(db.String(500))
    status = db.Column(db.String(50), default='Applied')
    applied_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    compatibility_score = db.Column(db.Integer)
    notes = db.Column(db.Text)
    salary_range = db.Column(db.String(100))
    follow_up_date = db.Column(db.DateTime)
    email_log = db.Column(db.Text, default='[]')
    timeline = db.Column(db.Text, default='[]')

class JobPosting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    employment_type = db.Column(db.String(50))
    industry = db.Column(db.String(100))
    posted_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    url = db.Column(db.String(500))
    skills_required = db.Column(db.Text, default='[]')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# ─── Helpers ──────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
STATUS_COLORS = {
    'Applied': '#3B82F6',
    'Screening': '#8B5CF6',
    'Interview Scheduled': '#F59E0B',
    'Interviewed': '#06B6D4',
    'Offer Received': '#10B981',
    'Accepted': '#059669',
    'Rejected': '#EF4444',
    'Withdrawn': '#6B7280'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# ─── Auth Routes ──────────────────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        name=data['name'],
        phone=data.get('phone', ''),
        location=data.get('location', '')
    )
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({'success': True, 'user': {'id': user.id, 'name': user.name, 'email': user.email}})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    session['user_id'] = user.id
    return jsonify({'success': True, 'user': {'id': user.id, 'name': user.name, 'email': user.email}})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True})

@app.route('/api/auth/me')
def me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({
        'id': user.id, 'name': user.name, 'email': user.email,
        'phone': user.phone, 'location': user.location, 'summary': user.summary,
        'skills': json.loads(user.skills or '[]'),
        'job_preferences': json.loads(user.job_preferences or '{}')
    })

# ─── Profile Routes ───────────────────────────────────────────────────────────

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    user = get_current_user()
    data = request.get_json()
    user.name = data.get('name', user.name)
    user.phone = data.get('phone', user.phone)
    user.location = data.get('location', user.location)
    user.summary = data.get('summary', user.summary)
    if 'skills' in data:
        user.skills = json.dumps(data['skills'])
    if 'job_preferences' in data:
        user.job_preferences = json.dumps(data['job_preferences'])
    db.session.commit()
    return jsonify({'success': True})

# ─── Main Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
