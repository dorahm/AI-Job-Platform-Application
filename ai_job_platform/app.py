from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import datetime
import uuid

# Set up template and static folders to point to project root
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

app = Flask(__name__, template_folder=os.path.join(PROJECT_DIR, 'templates'))
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
    skills = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    resumes = db.relationship('Resume', backref='user', lazy=True, cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='user', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('ChatMessage', backref='user', lazy=True, cascade='all, delete-orphan')

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_master = db.Column(db.Boolean, default=False)
    content_preview = db.Column(db.Text)
    quality_score = db.Column(db.Float, default=0.0)
    quality_feedback = db.Column(db.JSON, default=dict)

class JobPosting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    salary_min = db.Column(db.Float)
    salary_max = db.Column(db.Float)
    description = db.Column(db.Text)
    requirements = db.Column(db.JSON, default=list)
    skills = db.Column(db.JSON, default=list)
    employment_type = db.Column(db.String(50))  # Full-time, Part-time, Contract, Temporary
    industry = db.Column(db.String(100))
    posted_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete-orphan')

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posting.id'), nullable=False)
    applied_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(50), default='Applied')  # Applied, Interview, Rejected, Offer, Accepted
    notes = db.Column(db.Text)
    timeline = db.Column(db.JSON, default=list)
    resume_id = db.Column(db.Integer, db.ForeignKey('resume.id'))

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='user')  # user or assistant
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    topic = db.Column(db.String(50))  # resume, job, application, email, profile, etc.

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password or not name:
        return jsonify({'error': 'Missing fields'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        name=name
    )
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    session['user_id'] = user.id
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'location': user.location,
        'phone': user.phone,
        'summary': user.summary,
        'skills': user.skills or []
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'}), 200

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'location': user.location,
        'phone': user.phone,
        'summary': user.summary,
        'skills': user.skills or []
    }), 200

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    employment_type = request.args.get('employment_type', '')
    industry = request.args.get('industry', '')
    
    query = JobPosting.query
    
    if search:
        query = query.filter(db.or_(
            JobPosting.title.ilike(f'%{search}%'),
            JobPosting.company.ilike(f'%{search}%'),
            JobPosting.description.ilike(f'%{search}%')
        ))
    
    if location:
        query = query.filter(JobPosting.location.ilike(f'%{location}%'))
    
    if employment_type:
        query = query.filter_by(employment_type=employment_type)
    
    if industry:
        query = query.filter_by(industry=industry)
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    jobs = [{
        'id': job.id,
        'title': job.title,
        'company': job.company,
        'location': job.location,
        'salary_min': job.salary_min,
        'salary_max': job.salary_max,
        'description': job.description,
        'requirements': job.requirements or [],
        'skills': job.skills or [],
        'employment_type': job.employment_type,
        'industry': job.industry,
        'posted_date': job.posted_date.isoformat() if job.posted_date else None
    } for job in paginated.items]
    
    return jsonify({
        'jobs': jobs,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }), 200

@app.route('/api/jobs/<int:job_id>/match', methods=['GET'])
def match_job(job_id):
    """Calculate match score between user and job"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    job = JobPosting.query.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # Calculate match score
    user_skills = set(s.lower() for s in (user.skills or []))
    job_skills = set(s.lower() for s in (job.skills or []))
    
    if job_skills:
        skill_match = len(user_skills & job_skills) / len(job_skills) * 40
    else:
        skill_match = 20
    
    # Location match (20%)
    location_match = 20 if user.location and user.location.lower() in job.location.lower() else 5
    
    # Employment type match (20%)
    employment_type_match = 20  # Simplified logic
    
    # Experience baseline (20%)
    experience_match = 20
    
    score = int(skill_match + location_match + employment_type_match + experience_match)
    score = min(100, max(20, score))  # Clamp between 20-100
    
    return jsonify({
        'job_id': job_id,
        'score': score,
        'skill_match': int(skill_match),
        'location_match': location_match,
        'employment_match': employment_type_match,
        'details': {
            'matched_skills': list(user_skills & job_skills),
            'missing_skills': list(job_skills - user_skills)
        }
    }), 200

@app.route('/api/applications', methods=['GET'])
def get_applications():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    applications = Application.query.filter_by(user_id=user_id).all()
    
    result = []
    for app in applications:
        job = app.job
        result.append({
            'id': app.id,
            'job_id': app.job_id,
            'job_title': job.title if job else '',
            'company': job.company if job else '',
            'status': app.status,
            'applied_date': app.applied_date.isoformat() if app.applied_date else None,
            'notes': app.notes,
            'timeline': app.timeline or []
        })
    
    return jsonify(result), 200

@app.route('/api/applications', methods=['POST'])
def create_application():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    job_id = data.get('job_id')
    
    if not job_id:
        return jsonify({'error': 'Job ID required'}), 400
    
    existing = Application.query.filter_by(user_id=user_id, job_id=job_id).first()
    if existing:
        return jsonify({'error': 'Already applied'}), 400
    
    app = Application(
        user_id=user_id,
        job_id=job_id,
        status='Applied'
    )
    db.session.add(app)
    db.session.commit()
    
    return jsonify({'id': app.id, 'status': 'Applied'}), 201

@app.route('/api/applications/<int:app_id>', methods=['PUT'])
def update_application(app_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    app = Application.query.get(app_id)
    if not app or app.user_id != user_id:
        return jsonify({'error': 'Not found'}), 404
    
    data = request.json
    if 'status' in data:
        app.status = data['status']
    if 'notes' in data:
        app.notes = data['notes']
    
    db.session.commit()
    return jsonify({'id': app.id, 'status': app.status}), 200

@app.route('/api/applications/<int:app_id>', methods=['DELETE'])
def delete_application(app_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    app = Application.query.get(app_id)
    if not app or app.user_id != user_id:
        return jsonify({'error': 'Not found'}), 404
    
    db.session.delete(app)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200

@app.route('/api/resumes', methods=['GET'])
def get_resumes():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    resumes = Resume.query.filter_by(user_id=user_id).all()
    result = [{
        'id': resume.id,
        'filename': resume.original_filename,
        'uploaded_at': resume.uploaded_at.isoformat() if resume.uploaded_at else None,
        'is_master': resume.is_master,
        'quality_score': resume.quality_score,
        'quality_feedback': resume.quality_feedback or {}
    } for resume in resumes]
    
    return jsonify(result), 200

@app.route('/api/resumes/upload', methods=['POST'])
def upload_resume():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    filename_with_id = f"{unique_id}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_with_id)
    
    file.save(filepath)
    
    resume = Resume(
        user_id=user_id,
        filename=filename_with_id,
        filepath=filepath,
        original_filename=filename,
        quality_score=85.0,
        quality_feedback={
            'strengths': ['Clear formatting', 'Good structure'],
            'improvements': ['Add more quantifiable achievements']
        }
    )
    db.session.add(resume)
    db.session.commit()
    
    return jsonify({
        'id': resume.id,
        'filename': resume.original_filename,
        'quality_score': resume.quality_score
    }), 201

@app.route('/api/resumes/<int:resume_id>/set-master', methods=['POST'])
def set_master_resume(resume_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    resume = Resume.query.get(resume_id)
    if not resume or resume.user_id != user_id:
        return jsonify({'error': 'Not found'}), 404
    
    # Unset other master resumes
    Resume.query.filter_by(user_id=user_id, is_master=True).update({'is_master': False})
    resume.is_master = True
    db.session.commit()
    
    return jsonify({'message': 'Master resume set'}), 200

@app.route('/api/resumes/<int:resume_id>', methods=['DELETE'])
def delete_resume(resume_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    resume = Resume.query.get(resume_id)
    if not resume or resume.user_id != user_id:
        return jsonify({'error': 'Not found'}), 404
    
    if os.path.exists(resume.filepath):
        os.remove(resume.filepath)
    
    db.session.delete(resume)
    db.session.commit()
    
    return jsonify({'message': 'Deleted'}), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    
    # Save user message
    user_msg = ChatMessage(
        user_id=user_id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()
    
    # Generate response based on intent
    response = generate_chat_response(user_message, user_id)
    
    # Save assistant response
    assistant_msg = ChatMessage(
        user_id=user_id,
        role='assistant',
        content=response
    )
    db.session.add(assistant_msg)
    db.session.commit()
    
    return jsonify({
        'user_message': user_message,
        'assistant_message': response
    }), 200

def generate_chat_response(message, user_id):
    """Generate context-aware chat responses based on user intent"""
    message_lower = message.lower()
    user = User.query.get(user_id)
    
    # Intent detection
    if any(word in message_lower for word in ['resume', 'upload', 'document', 'cv']):
        if not user.resumes:
            return "I notice you haven't uploaded a resume yet. You can upload one in the Resumes section to help us match you with better job opportunities."
        return f"You have {len(user.resumes)} resume(s) on file. Would you like to upload another one or set a master resume?"
    
    elif any(word in message_lower for word in ['job', 'position', 'role', 'work', 'find']):
        jobs_count = JobPosting.query.count()
        return f"We have {jobs_count} job opportunities available. Use filters like location or industry to find roles that match your profile. What kind of position are you looking for?"
    
    elif any(word in message_lower for word in ['skill', 'learn', 'improve', 'expert']):
        return "Building your skill profile helps us match you with more opportunities. Update your skills in the Profile section. What skills would you like to add?"
    
    elif any(word in message_lower for word in ['email', 'message', 'send', 'contact']):
        return "I can help you generate professional emails for job applications and follow-ups. Check the Email Tools section to create templates."
    
    elif any(word in message_lower for word in ['application', 'applied', 'status', 'interview', 'offer']):
        apps_count = Application.query.filter_by(user_id=user_id).count()
        return f"You have {apps_count} application(s) in progress. Track your applications to stay organized. Would you like to update the status of any applications?"
    
    elif any(word in message_lower for word in ['profile', 'name', 'location', 'phone', 'contact']):
        return f"Your current profile shows: {user.name} from {user.location or 'unknown location'}. You can update your profile anytime. Need help updating anything?"
    
    else:
        responses = [
            "I'm here to help with your job search! Ask me about finding jobs, uploading resumes, tracking applications, or generating professional emails.",
            "Sounds interesting! Would you like help with finding jobs, managing resumes, or tracking your applications?",
            "I can assist with various job search tasks. Try asking about jobs, resumes, applications, or professional emails."
        ]
        return responses[min(len(message) % 3, 2)]

@app.route('/api/email/generate', methods=['POST'])
def generate_email():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    email_type = data.get('type', 'application')
    job_title = data.get('job_title', 'Position')
    company = data.get('company', 'Company')
    
    templates = {
        'application': f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With my experience and skills, I am confident I can contribute significantly to your team.

Looking forward to discussing how I can add value to {company}.

Best regards""",
        
        'followup': f"""Dear Hiring Manager,

I hope this message finds you well. I wanted to follow up regarding my application for the {job_title} position at {company}. I remain very interested in this opportunity and would welcome any updates on the status.

Thank you for considering my application.

Best regards""",
        
        'thankyou': f"""Dear Hiring Manager,

Thank you for taking the time to meet with me for the {job_title} position at {company}. I enjoyed learning more about the role and your team.

I am excited about the opportunity to contribute to {company}.

Best regards"""
    }
    
    email_content = templates.get(email_type, templates['application'])
    
    return jsonify({
        'type': email_type,
        'subject': f"Application for {job_title} at {company}" if email_type == 'application' else f"Re: {job_title} Position at {company}",
        'body': email_content
    }), 200

@app.route('/api/cv/compose', methods=['POST'])
def compose_cv():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    
    cv_content = {
        'name': user.name,
        'contact': {
            'email': user.email,
            'phone': user.phone or 'Not provided',
            'location': user.location or 'Not provided'
        },
        'summary': user.summary or 'Professional seeking new opportunities',
        'skills': user.skills or [],
        'experience': [{
            'title': 'Professional',
            'description': 'Seeking new role'
        }],
        'education': [{
            'institution': 'Your Institution',
            'degree': 'Your Degree'
        }]
    }
    
    return jsonify(cv_content), 200

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.json
    if 'name' in data:
        user.name = data['name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'location' in data:
        user.location = data['location']
    if 'summary' in data:
        user.summary = data['summary']
    if 'skills' in data:
        user.skills = data['skills']
    
    db.session.commit()
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
        'location': user.location,
        'summary': user.summary,
        'skills': user.skills or []
    }), 200

# ─── Seed Database ────────────────────────────────────────────────────────────

def seed_jobs():
    """Seed database with 25 diverse job postings"""
    if JobPosting.query.first():
        return  # Database already seeded
    
    jobs_data = [
        # Technology
        {'title': 'Senior Python Developer', 'company': 'TechCorp', 'location': 'San Francisco, CA', 'salary_min': 120000, 'salary_max': 160000, 'employment_type': 'Full-time', 'industry': 'Technology', 'skills': ['Python', 'Django', 'PostgreSQL'], 'requirements': ['5+ years experience', 'BS in CS or related']},
        {'title': 'React Frontend Engineer', 'company': 'WebSolutions', 'location': 'New York, NY', 'salary_min': 100000, 'salary_max': 140000, 'employment_type': 'Full-time', 'industry': 'Technology', 'skills': ['React', 'JavaScript', 'CSS'], 'requirements': ['3+ years with React', 'Strong CSS skills']},
        {'title': 'DevOps Engineer', 'company': 'CloudTech', 'location': 'Austin, TX', 'salary_min': 110000, 'salary_max': 150000, 'employment_type': 'Full-time', 'industry': 'Technology', 'skills': ['Docker', 'Kubernetes', 'AWS'], 'requirements': ['3+ years DevOps', 'Docker expertise']},
        {'title': 'Java Backend Developer', 'company': 'FinTech Solutions', 'location': 'Boston, MA', 'salary_min': 115000, 'salary_max': 155000, 'employment_type': 'Full-time', 'industry': 'Technology', 'skills': ['Java', 'Spring Boot', 'Microservices'], 'requirements': ['4+ years Java', 'Microservices knowledge']},
        {'title': 'Full Stack Developer', 'company': 'StartupXYZ', 'location': 'Remote', 'salary_min': 95000, 'salary_max': 130000, 'employment_type': 'Full-time', 'industry': 'Technology', 'skills': ['React', 'Node.js', 'MongoDB'], 'requirements': ['3+ years full stack', 'Startup experience preferred']},
        
        # Data Science
        {'title': 'Data Scientist', 'company': 'DataInsight', 'location': 'Seattle, WA', 'salary_min': 130000, 'salary_max': 170000, 'employment_type': 'Full-time', 'industry': 'Data Science', 'skills': ['Python', 'Machine Learning', 'SQL'], 'requirements': ['3+ years data science', 'ML expertise']},
        {'title': 'ML Engineer', 'company': 'AI Labs', 'location': 'Mountain View, CA', 'salary_min': 140000, 'salary_max': 180000, 'employment_type': 'Full-time', 'industry': 'Data Science', 'skills': ['TensorFlow', 'Python', 'Deep Learning'], 'requirements': ['4+ years ML', 'Deep learning knowledge']},
        {'title': 'Analytics Engineer', 'company': 'DataCorp', 'location': 'Chicago, IL', 'salary_min': 110000, 'salary_max': 145000, 'employment_type': 'Full-time', 'industry': 'Data Science', 'skills': ['SQL', 'Python', 'Tableau'], 'requirements': ['3+ years analytics', 'Dashboard skills']},
        
        # Finance
        {'title': 'Financial Analyst', 'company': 'Goldman Finance', 'location': 'New York, NY', 'salary_min': 125000, 'salary_max': 165000, 'employment_type': 'Full-time', 'industry': 'Finance', 'skills': ['Excel', 'Financial Modeling', 'SQL'], 'requirements': ['3+ years finance', 'Excel expert']},
        {'title': 'Risk Manager', 'company': 'Risk Solutions', 'location': 'London, UK', 'salary_min': 135000, 'salary_max': 170000, 'employment_type': 'Full-time', 'industry': 'Finance', 'skills': ['Risk Analysis', 'Python', 'VBA'], 'requirements': ['5+ years risk', 'Regulatory knowledge']},
        
        # Healthcare
        {'title': 'Healthcare Data Analyst', 'company': 'MedTech', 'location': 'San Diego, CA', 'salary_min': 85000, 'salary_max': 120000, 'employment_type': 'Full-time', 'industry': 'Healthcare', 'skills': ['SQL', 'Python', 'HIPAA'], 'requirements': ['2+ years healthcare IT', 'HIPAA compliance knowledge']},
        {'title': 'Biomedical Engineer', 'company': 'BioSystems', 'location': 'Boston, MA', 'salary_min': 95000, 'salary_max': 135000, 'employment_type': 'Full-time', 'industry': 'Healthcare', 'skills': ['CAD', 'MATLAB', 'Biomedical Engineering'], 'requirements': ['3+ years biomedical', 'CAD proficiency']},
        
        # Design
        {'title': 'UX Designer', 'company': 'Design Studio', 'location': 'Los Angeles, CA', 'salary_min': 80000, 'salary_max': 115000, 'employment_type': 'Full-time', 'industry': 'Design', 'skills': ['Figma', 'User Research', 'Prototyping'], 'requirements': ['3+ years UX', 'Figma expertise']},
        {'title': 'UI/UX Designer', 'company': 'Creative Labs', 'location': 'Remote', 'salary_min': 75000, 'salary_max': 110000, 'employment_type': 'Full-time', 'industry': 'Design', 'skills': ['Figma', 'Adobe XD', 'CSS'], 'requirements': ['2+ years UI/UX', 'Design portfolio']},
        
        # Artificial Intelligence
        {'title': 'NLP Engineer', 'company': 'AI Research', 'location': 'Los Angeles, CA', 'salary_min': 145000, 'salary_max': 185000, 'employment_type': 'Full-time', 'industry': 'AI', 'skills': ['NLP', 'Transformers', 'PyTorch'], 'requirements': ['4+ years NLP', 'Transformer models']},
        {'title': 'Computer Vision Engineer', 'company': 'Vision Tech', 'location': 'Portland, OR', 'salary_min': 140000, 'salary_max': 180000, 'employment_type': 'Full-time', 'industry': 'AI', 'skills': ['Computer Vision', 'OpenCV', 'Deep Learning'], 'requirements': ['4+ years CV', 'Deep learning expertise']},
        
        # Product Management
        {'title': 'Product Manager', 'company': 'Tech Innovations', 'location': 'San Francisco, CA', 'salary_min': 135000, 'salary_max': 175000, 'employment_type': 'Full-time', 'industry': 'Product', 'skills': ['Product Strategy', 'Data Analysis', 'Agile'], 'requirements': ['4+ years product', 'B2B/B2C experience']},
        {'title': 'Senior Product Manager', 'company': 'Market Leaders', 'location': 'New York, NY', 'salary_min': 160000, 'salary_max': 210000, 'employment_type': 'Full-time', 'industry': 'Product', 'skills': ['Product Leadership', 'Analytics', 'Strategy'], 'requirements': ['6+ years product', 'Leadership experience']},
        
        # Cybersecurity
        {'title': 'Security Engineer', 'company': 'SecureNet', 'location': 'Arlington, VA', 'salary_min': 130000, 'salary_max': 170000, 'employment_type': 'Full-time', 'industry': 'Security', 'skills': ['Cybersecurity', 'Network Security', 'Python'], 'requirements': ['4+ years security', 'Security certifications']},
        {'title': 'Penetration Tester', 'company': 'CyberDefense', 'location': 'Austin, TX', 'salary_min': 125000, 'salary_max': 160000, 'employment_type': 'Full-time', 'industry': 'Security', 'skills': ['Penetration Testing', 'Security Tools', 'Networking'], 'requirements': ['3+ years pen testing', 'CEH certified']},
        
        # Mobile
        {'title': 'iOS Developer', 'company': 'MobileFirst', 'location': 'San Francisco, CA', 'salary_min': 120000, 'salary_max': 160000, 'employment_type': 'Full-time', 'industry': 'Mobile', 'skills': ['Swift', 'iOS', 'Objective-C'], 'requirements': ['3+ years iOS', 'App Store experience']},
        {'title': 'Android Developer', 'company': 'AppWorks', 'location': 'Mountain View, CA', 'salary_min': 115000, 'salary_max': 155000, 'employment_type': 'Full-time', 'industry': 'Mobile', 'skills': ['Kotlin', 'Android', 'Java'], 'requirements': ['3+ years Android', 'Play Store knowledge']},
        {'title': 'Flutter Developer', 'company': 'CrossPlatform', 'location': 'Remote', 'salary_min': 105000, 'salary_max': 145000, 'employment_type': 'Full-time', 'industry': 'Mobile', 'skills': ['Flutter', 'Dart', 'Firebase'], 'requirements': ['2+ years Flutter', 'Cross-platform experience']},
    ]
    
    for job_data in jobs_data:
        job = JobPosting(
            title=job_data['title'],
            company=job_data['company'],
            location=job_data['location'],
            salary_min=job_data['salary_min'],
            salary_max=job_data['salary_max'],
            employment_type=job_data['employment_type'],
            industry=job_data['industry'],
            skills=job_data['skills'],
            requirements=job_data['requirements'],
            description=f"Exciting opportunity for a {job_data['title']} at {job_data['company']} in {job_data['location']}"
        )
        db.session.add(job)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_jobs()
    app.run(debug=True)