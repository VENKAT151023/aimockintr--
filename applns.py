# ============================================================
# LARA AI - Mock Interview Platform
# Complete Flask Application - Vercel Ready
# Supports: http://localhost:5000 AND www.aimockintr.com
# VERSION: 3.1 - UPDATED (Lead stats removed, instant interview link,
#                          camera state fixed, retry button removed)
# ============================================================

from flask import Flask, render_template_string, request, session, jsonify, redirect, url_for, flash, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import json
import secrets
import threading
import time
import random
import re
import hashlib
import uuid
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import string
import base64
import hmac
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import requests
from collections import defaultdict
import statistics
import math
import itertools
from typing import Dict, List, Optional, Tuple, Any

# ============================================================
# LOGGING CONFIGURATION - FIXED FOR VERCEL (No FileHandler)
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'lara_ai_super_secret_key_2024_secure_7x9k2m')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Database configuration - PostgreSQL for Vercel, SQLite for local
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///lara_ai.db')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 280,
    'pool_size': 1,
    'max_overflow': 2,
}

# Upload configuration
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'svg'}
app.config['MAX_QUESTIONS'] = 10
app.config['INTERVIEW_DURATION'] = 60
app.config['PASS_SCORE'] = 60
app.config['OTP_EXPIRY_MINUTES'] = 10
app.config['MAX_LOGIN_ATTEMPTS'] = 5
app.config['LOCKOUT_TIME_MINUTES'] = 30
app.config['MAX_FILE_SIZE'] = 5 * 1024 * 1024

# Create necessary directories
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except (OSError, PermissionError):
    pass

try:
    os.makedirs('static', exist_ok=True)
except (OSError, PermissionError):
    pass

try:
    os.makedirs('static/css', exist_ok=True)
except (OSError, PermissionError):
    pass

try:
    os.makedirs('static/js', exist_ok=True)
except (OSError, PermissionError):
    pass

db = SQLAlchemy(app)

# ============================================================
# DATABASE MODELS
# ============================================================

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    user_type = db.Column(db.String(20), default='student')
    college = db.Column(db.String(200))
    domain = db.Column(db.String(100))
    experience_years = db.Column(db.Integer, default=0)
    cgpa = db.Column(db.Float, default=0.0)
    phone = db.Column(db.String(15))
    bio = db.Column(db.Text)
    skills = db.Column(db.Text)
    resume_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    profile_picture = db.Column(db.String(200))

    # Interview fields
    meeting_scheduled = db.Column(db.Boolean, default=False)
    meeting_start_time = db.Column(db.DateTime)
    meeting_link = db.Column(db.String(200))
    meeting_live = db.Column(db.Boolean, default=False)
    interview_complete = db.Column(db.Boolean, default=False)
    final_score = db.Column(db.Integer, default=0)
    passed = db.Column(db.Boolean, default=False)
    company_message = db.Column(db.Text)
    interview_date = db.Column(db.DateTime)
    interview_feedback = db.Column(db.Text)

    # Relationships
    notifications = db.relationship('Notification', backref='user', lazy=True)
    interview_answers = db.relationship('InterviewAnswer', backref='user', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)
    job_applications = db.relationship('JobApplication', backref='user', lazy=True)
    interview_sessions = db.relationship('InterviewSession', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'user_type': self.user_type,
            'college': self.college,
            'domain': self.domain,
            'experience_years': self.experience_years,
            'cgpa': self.cgpa,
            'phone': self.phone,
            'bio': self.bio,
            'skills': self.skills.split(',') if self.skills else [],
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None,
            'interview_complete': self.interview_complete,
            'final_score': self.final_score,
            'passed': self.passed,
            'company_message': self.company_message,
            'is_verified': self.is_verified
        }

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    priority = db.Column(db.String(20), default='normal')
    category = db.Column(db.String(30), default='system')
    icon = db.Column(db.String(50))
    expires_at = db.Column(db.DateTime)
    is_dismissible = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'link': self.link,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'priority': self.priority,
            'category': self.category,
            'icon': self.icon
        }

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100))
    action_type = db.Column(db.String(50))
    duration = db.Column(db.Integer, default=0)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    resource_id = db.Column(db.Integer)
    resource_type = db.Column(db.String(50))
    page_url = db.Column(db.String(200))
    http_method = db.Column(db.String(10))
    status_code = db.Column(db.Integer)

class InterviewAnswer(db.Model):
    __tablename__ = 'interview_answers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_index = db.Column(db.Integer)
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    score = db.Column(db.Integer, default=0)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    word_count = db.Column(db.Integer, default=0)
    sentiment_score = db.Column(db.Float, default=0.0)
    confidence_score = db.Column(db.Float, default=0.0)
    grammar_score = db.Column(db.Float, default=0.0)
    relevance_score = db.Column(db.Float, default=0.0)
    keywords_matched = db.Column(db.Text)
    answer_duration = db.Column(db.Integer, default=0)
    improvement_suggestions = db.Column(db.Text)
    category = db.Column(db.String(50))
    difficulty_level = db.Column(db.String(20), default='medium')

class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rating = db.Column(db.Integer, default=0)
    comment = db.Column(db.Text)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    interview_id = db.Column(db.Integer)
    experience_type = db.Column(db.String(30), default='interview')
    helpfulness_score = db.Column(db.Integer, default=0)
    ease_of_use = db.Column(db.Integer, default=0)
    satisfaction_score = db.Column(db.Integer, default=0)
    recommend_score = db.Column(db.Integer, default=0)
    improvement_areas = db.Column(db.Text)
    suggestions = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')
    admin_response = db.Column(db.Text)
    response_date = db.Column(db.DateTime)
    response_by = db.Column(db.Integer, db.ForeignKey('users.id'))

class OTP(db.Model):
    __tablename__ = 'otps'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(50), default='verification')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_used = db.Column(db.Boolean, default=False)
    attempt_count = db.Column(db.Integer, default=0)
    last_attempt = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))

class JobApplication(db.Model):
    __tablename__ = 'job_applications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    job_title = db.Column(db.String(100))
    company_name = db.Column(db.String(100))
    status = db.Column(db.String(20), default='applied')
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    interview_date = db.Column(db.DateTime)
    offer_status = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    job_description = db.Column(db.Text)
    application_letter = db.Column(db.Text)
    resume_version = db.Column(db.String(50))
    application_source = db.Column(db.String(50))
    rejection_reason = db.Column(db.Text)
    offer_details = db.Column(db.Text)
    salary_offered = db.Column(db.Float, default=0.0)
    joining_date = db.Column(db.DateTime)
    job_category = db.Column(db.String(50))
    job_type = db.Column(db.String(20), default='full-time')
    work_location = db.Column(db.String(100))
    skills_required = db.Column(db.Text)
    experience_required = db.Column(db.Integer, default=0)

class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    industry = db.Column(db.String(50))
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    logo_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    founded_year = db.Column(db.Integer)
    company_size = db.Column(db.String(20))
    revenue = db.Column(db.String(50))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    country = db.Column(db.String(50))
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    company_type = db.Column(db.String(50))
    specialties = db.Column(db.Text)
    hiring_status = db.Column(db.String(20), default='active')
    job_openings = db.Column(db.Integer, default=0)

class InterviewSession(db.Model):
    __tablename__ = 'interview_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    session_id = db.Column(db.String(100), unique=True)
    current_question = db.Column(db.Integer, default=0)
    answers = db.Column(db.Text)
    score = db.Column(db.Integer, default=0)
    camera_state = db.Column(db.Boolean, default=False)
    mic_state = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    question_set = db.Column(db.Text)
    current_category = db.Column(db.String(50))
    current_difficulty = db.Column(db.String(20), default='medium')
    time_spent = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=10)
    answered_count = db.Column(db.Integer, default=0)
    skipped_count = db.Column(db.Integer, default=0)
    average_response_time = db.Column(db.Float, default=0.0)
    performance_metrics = db.Column(db.Text)
    camera_enabled = db.Column(db.Boolean, default=False)
    microphone_enabled = db.Column(db.Boolean, default=False)
    feedback_generated = db.Column(db.Boolean, default=False)
    feedback_text = db.Column(db.Text)
    strengths = db.Column(db.Text)
    weaknesses = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    overall_rating = db.Column(db.Integer, default=0)
    category_scores = db.Column(db.Text)

# ============================================================
# TAMIL INTERVIEW QUESTIONS - EXACTLY 10 QUESTIONS
# ============================================================

TAMIL_INTERVIEW_QUESTIONS = [
    {
        "tamil": "உங்களைப் பற்றி சொல்லுங்கள். உங்கள் பின்னணி, கல்வி மற்றும் அனுபவம் பற்றி விளக்குங்கள்.",
        "english": "Tell me about yourself. Explain your background, education, and experience.",
        "time": 60,
        "category": "Introduction"
    },
    {
        "tamil": "உங்கள் பலம் மற்றும் பலவீனங்கள் என்ன? எப்படி அவற்றை மேம்படுத்துவீர்கள்?",
        "english": "What are your strengths and weaknesses? How do you improve them?",
        "time": 60,
        "category": "Self Assessment"
    },
    {
        "tamil": "ஏன் இந்த துறையில் வேலை செய்ய விரும்புகிறீர்கள்? உங்கள் ஆர்வம் என்ன?",
        "english": "Why do you want to work in this field? What is your passion?",
        "time": 60,
        "category": "Motivation"
    },
    {
        "tamil": "உங்கள் முக்கிய சாதனைகள் என்ன? உங்கள் மிகப் பெரிய வெற்றி எது?",
        "english": "What are your major achievements? What is your biggest success?",
        "time": 60,
        "category": "Achievements"
    },
    {
        "tamil": "குழுவில் எப்படி வேலை செய்வீர்கள்? மோதல் ஏற்பட்டால் எப்படி கையாள்வீர்கள்?",
        "english": "How do you work in a team? How do you handle conflicts?",
        "time": 60,
        "category": "Teamwork"
    },
    {
        "tamil": "மன அழுத்தத்தை எப்படி கையாள்வீர்கள்? கடினமான சூழ்நிலையில் எப்படி செயல்படுவீர்கள்?",
        "english": "How do you handle stress? How do you perform under pressure?",
        "time": 60,
        "category": "Stress Management"
    },
    {
        "tamil": "உங்கள் தொழில் இலக்குகள் என்ன? 5 ஆண்டுகளில் எங்கு இருக்க விரும்புகிறீர்கள்?",
        "english": "What are your career goals? Where do you see yourself in 5 years?",
        "time": 60,
        "category": "Goals"
    },
    {
        "tamil": "ஏன் எங்கள் நிறுவனத்தில் சேர விரும்புகிறீர்கள்? எங்களைப் பற்றி என்ன தெரியும்?",
        "english": "Why do you want to join our company? What do you know about us?",
        "time": 60,
        "category": "Company Fit"
    },
    {
        "tamil": "தொழில்நுட்ப துறையில் உங்கள் நிபுணத்துவம் என்ன? எந்த தொழில்நுட்பங்களில் தேர்ச்சி பெற்றுள்ளீர்கள்?",
        "english": "What is your expertise in the technical field? Which technologies are you proficient in?",
        "time": 60,
        "category": "Technical Skills"
    },
    {
        "tamil": "ஒரு கடினமான தொழில்நுட்ப பிரச்சனையை எப்படி தீர்த்தீர்கள்? உதாரணம் சொல்லுங்கள்.",
        "english": "How did you solve a difficult technical problem? Give an example.",
        "time": 60,
        "category": "Problem Solving"
    }
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_meeting_link(user_id):
    token = secrets.token_urlsafe(16)
    return f"/interview/{user_id}/{token}"

def calculate_interview_score(answers):
    score = 0
    feedback = []

    for idx, answer in enumerate(answers):
        text = answer.get('answer', '')
        length = len(text)
        question_score = 0

        if length > 150:
            question_score += 20
            feedback.append(f"Q{idx+1}: Excellent - Very detailed response")
        elif length > 100:
            question_score += 15
            feedback.append(f"Q{idx+1}: Good - Detailed response")
        elif length > 50:
            question_score += 10
            feedback.append(f"Q{idx+1}: Average - Moderate detail")
        elif length > 20:
            question_score += 5
            feedback.append(f"Q{idx+1}: Below Average - Needs more detail")
        else:
            feedback.append(f"Q{idx+1}: Poor - Response too short")

        keyword_groups = {
            'experience': ['experience', 'experienced', 'worked', 'work', 'job', 'career', 'professional'],
            'skill': ['skill', 'skills', 'learn', 'learning', 'knowledge', 'expertise', 'proficient'],
            'achieve': ['achieve', 'achieved', 'achievement', 'success', 'goal', 'accomplish', 'complete'],
            'team': ['team', 'collaborate', 'collaboration', 'group', 'together', 'colleague', 'partner'],
            'lead': ['lead', 'leader', 'leadership', 'managed', 'supervise', 'direct', 'guide'],
            'improve': ['improve', 'improvement', 'grow', 'growth', 'develop', 'development', 'enhance'],
            'problem': ['problem', 'solve', 'solution', 'challenge', 'tackle', 'resolve', 'fix'],
            'passion': ['passion', 'love', 'enjoy', 'interested', 'fascinated', 'excited', 'motivated'],
            'future': ['future', 'plan', 'goal', 'aim', 'target', 'vision', 'aspire']
        }

        for group, words in keyword_groups.items():
            if any(word in text.lower() for word in words):
                question_score += 2
                feedback.append(f"Q{idx+1}: Used '{group}' related vocabulary")

        score += min(question_score, 25)

    total_length = sum(len(a.get('answer', '')) for a in answers)
    if total_length > 800:
        score += 10
        feedback.append("Excellent overall response length")
    elif total_length > 400:
        score += 5
        feedback.append("Good overall response length")
    elif total_length > 200:
        score += 3
        feedback.append("Average overall response length")
    else:
        feedback.append("Overall response length needs improvement")

    return min(score, 100), feedback

def get_dashboard_stats(user_id):
    """Simplified stats - interview status only (lead/CRM stats removed)."""
    user = User.query.get(user_id)
    notifications = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    job_apps = JobApplication.query.filter_by(user_id=user_id).all()

    return {
        'unread_notifications': notifications,
        'interview_status': user.interview_complete if user else False,
        'interview_score': user.final_score if user else 0,
        'passed': user.passed if user else False,
        'total_jobs': len(job_apps)
    }

def create_notification(user_id, title, message, type='info', link=None):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        link=link
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def log_activity(user_id, action, details=None, ip=None, user_agent=None):
    log = ActivityLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip,
        user_agent=user_agent
    )
    db.session.add(log)
    db.session.commit()
    return log

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_user_by_id(user_id):
    try:
        return User.query.get(user_id)
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None

def get_current_user():
    if 'user_id' in session:
        return get_user_by_id(session['user_id'])
    return None

def is_authenticated():
    return 'user_id' in session

def is_admin():
    user = get_current_user()
    return user and user.role == 'admin'

def sanitize_input(text):
    if text:
        return text.strip()
    return ''

def generate_resume_filename(original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    return f"{uuid.uuid4().hex}_{datetime.utcnow().strftime('%Y%m%d')}.{ext}"

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def get_avg_score(users):
    scores = [u.final_score for u in users if u.interview_complete]
    return round(sum(scores) / len(scores), 1) if scores else 0

def get_pass_rate(users):
    total = len([u for u in users if u.interview_complete])
    passed = len([u for u in users if u.passed])
    return round(passed / total * 100, 1) if total > 0 else 0

def format_datetime(dt):
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return None

def is_account_locked(user):
    if user.locked_until and user.locked_until > datetime.utcnow():
        return True
    return False

def reset_login_attempts(user):
    user.login_attempts = 0
    user.locked_until = None
    db.session.commit()

def increment_login_attempts(user):
    user.login_attempts += 1
    if user.login_attempts >= app.config['MAX_LOGIN_ATTEMPTS']:
        user.locked_until = datetime.utcnow() + timedelta(minutes=app.config['LOCKOUT_TIME_MINUTES'])
    db.session.commit()
    return user.login_attempts

def generate_verification_token():
    return secrets.token_urlsafe(32)

def create_otp(email, purpose='verification'):
    otp_code = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=app.config['OTP_EXPIRY_MINUTES'])
    OTP.query.filter_by(email=email, purpose=purpose, is_used=False).delete()
    new_otp = OTP(
        email=email,
        otp=otp_code,
        purpose=purpose,
        expires_at=expiry
    )
    db.session.add(new_otp)
    db.session.commit()
    return otp_code

def verify_otp(email, otp_code, purpose='verification'):
    otp_record = OTP.query.filter_by(
        email=email,
        otp=otp_code,
        purpose=purpose,
        is_used=False
    ).first()
    if not otp_record:
        return False, "Invalid OTP"
    if otp_record.expires_at < datetime.utcnow():
        return False, "OTP expired"
    otp_record.is_used = True
    db.session.commit()
    return True, "OTP verified"

# ============================================================
# DECORATORS
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Please login to access this page.', 'warning')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Please login to access this page.', 'warning')
            return redirect('/login')
        if not is_admin():
            flash('Admin access required.', 'danger')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# ============================================================
# HTML TEMPLATES
# ============================================================

LANDING_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Mock Interview Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;color:#fff;overflow-x:hidden;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.02) 1px,transparent 1px);background-size:60px 60px;pointer-events:none;}
        .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 20%,rgba(102,126,234,0.06),transparent 50%),radial-gradient(ellipse at 70% 80%,rgba(118,75,162,0.04),transparent 50%);pointer-events:none;}
        .bg-orb{position:fixed;border-radius:50%;filter:blur(150px);animation:floatOrb 30s infinite ease-in-out;pointer-events:none;}
        .bg-orb:nth-child(1){width:700px;height:700px;background:#667eea;top:-300px;right:-200px;opacity:0.05;animation-delay:0s;}
        .bg-orb:nth-child(2){width:600px;height:600px;background:#764ba2;bottom:-250px;left:-150px;opacity:0.04;animation-delay:12s;}
        .bg-orb:nth-child(3){width:500px;height:500px;background:#f093fb;top:40%;left:40%;opacity:0.03;animation-delay:24s;}
        .bg-orb:nth-child(4){width:400px;height:400px;background:#48bb78;top:10%;right:20%;opacity:0.03;animation-delay:36s;}
        @keyframes floatOrb{0%,100%{transform:translate(0,0) scale(1);}25%{transform:translate(120px,-80px) scale(1.3);}50%{transform:translate(-80px,60px) scale(0.7);}75%{transform:translate(100px,120px) scale(1.2);}}
        .hero{position:relative;z-index:1;min-height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:20px;}
        .hero-logo{font-size:72px;font-weight:900;font-family:'Orbitron',monospace;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb,#48bb78);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-size:300% 300%;animation:gradient 6s ease infinite;}
        @keyframes gradient{0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}
        .hero-sub{font-size:20px;color:rgba(255,255,255,0.6);margin-top:20px;font-family:'Orbitron',monospace;letter-spacing:4px;}
        .hero-desc{font-size:18px;color:rgba(255,255,255,0.4);max-width:700px;margin-top:15px;line-height:1.8;}
        .hero-buttons{margin-top:40px;display:flex;gap:20px;flex-wrap:wrap;justify-content:center;}
        .btn-hero{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:16px 40px;border-radius:60px;font-size:16px;font-weight:600;text-decoration:none;transition:0.5s;border:none;cursor:pointer;font-family:'Orbitron',monospace;letter-spacing:1px;display:inline-flex;align-items:center;gap:10px;}
        .btn-hero:hover{transform:scale(1.05);box-shadow:0 20px 60px rgba(102,126,234,0.3);}
        .btn-hero.outline{background:transparent;border:2px solid rgba(255,255,255,0.2);}
        .btn-hero.outline:hover{background:rgba(255,255,255,0.05);border-color:#667eea;}
        .btn-hero.admin-btn{border-color:rgba(255,107,107,0.3);color:#ff6b6b;}
        .btn-hero.admin-btn:hover{border-color:#ff6b6b;background:rgba(255,107,107,0.05);}
        .features{position:relative;z-index:1;padding:80px 20px;max-width:1200px;margin:0 auto;}
        .features h2{font-size:36px;font-weight:700;text-align:center;font-family:'Orbitron',monospace;letter-spacing:2px;margin-bottom:50px;background:linear-gradient(135deg,#fff,#888);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
        .features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:30px;}
        .feature-card{background:rgba(255,255,255,0.03);border-radius:24px;padding:30px;border:1px solid rgba(255,255,255,0.06);transition:0.5s;text-align:center;}
        .feature-card:hover{transform:translateY(-10px);border-color:#667eea;box-shadow:0 20px 60px rgba(102,126,234,0.05);}
        .feature-card .icon{font-size:48px;margin-bottom:15px;}
        .feature-card h3{font-size:18px;font-family:'Orbitron',monospace;letter-spacing:1px;margin-bottom:10px;color:#fff;}
        .feature-card p{font-size:14px;color:rgba(255,255,255,0.4);line-height:1.6;}
        .footer{position:relative;z-index:1;text-align:center;padding:40px 20px;border-top:1px solid rgba(255,255,255,0.04);}
        .footer p{font-size:12px;color:rgba(255,255,255,0.15);font-family:'Orbitron',monospace;letter-spacing:2px;}
        .footer .domain{color:#667eea;font-weight:bold;}
        .footer .social{margin-top:15px;display:flex;gap:15px;justify-content:center;}
        .footer .social a{color:rgba(255,255,255,0.2);font-size:20px;transition:0.3s;}
        .footer .social a:hover{color:#667eea;}
        @media(max-width:768px){.hero-logo{font-size:36px;}.hero-sub{font-size:14px;}.features h2{font-size:24px;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="bg-orb"></div><div class="bg-orb"></div><div class="bg-orb"></div><div class="bg-orb"></div>
<div class="hero">
    <div class="hero-logo">LARA AI</div>
    <div class="hero-sub">Mock Interview Platform</div>
    <div class="hero-desc">Next-generation AI-powered interview preparation platform. Practice with LARA AI in Tamil, get instant feedback, and ace your interviews.</div>
    <div class="hero-buttons">
        <a href="/login" class="btn-hero"><i class="fas fa-sign-in-alt"></i> User Login</a>
        <a href="/register" class="btn-hero outline"><i class="fas fa-user-plus"></i> Register</a>
        <a href="/admin-login" class="btn-hero admin-btn"><i class="fas fa-shield-alt"></i> Admin Login</a>
    </div>
</div>
<div class="features">
    <h2>Why LARA AI?</h2>
    <div class="features-grid">
        <div class="feature-card"><div class="icon">🤖</div><h3>AI-Powered Interviews</h3><p>Experience realistic interviews with LARA AI that adapts to your responses in real-time.</p></div>
        <div class="feature-card"><div class="icon">🎙️</div><h3>Tamil Interview Mode</h3><p>Practice in your native language. LARA AI conducts interviews in Tamil for better understanding.</p></div>
        <div class="feature-card"><div class="icon">📊</div><h3>Instant Scoring</h3><p>Get immediate feedback with detailed scoring on technical skills, communication, and confidence.</p></div>
        <div class="feature-card"><div class="icon">🎥</div><h3>Camera & Mic Support</h3><p>Real interview simulation with camera and microphone integration for a complete experience.</p></div>
        <div class="feature-card"><div class="icon">📈</div><h3>Performance Analytics</h3><p>Track your progress with detailed analytics and identify areas for improvement.</p></div>
        <div class="feature-card"><div class="icon">🏢</div><h3>Enterprise Ready</h3><p>Built for colleges, placement cells, and recruitment agencies with admin dashboard.</p></div>
    </div>
</div>
<div class="footer">
    <p>© 2026 LARA AI • <span class="domain">www.aimockintr.com</span> • Powered by Artificial Intelligence</p>
    <div class="social">
        <a href="#"><i class="fab fa-linkedin"></i></a>
        <a href="#"><i class="fab fa-twitter"></i></a>
        <a href="#"><i class="fab fa-github"></i></a>
        <a href="#"><i class="fab fa-youtube"></i></a>
    </div>
</div>
</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - User Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 40%,rgba(102,126,234,0.05),transparent 50%),radial-gradient(ellipse at 70% 60%,rgba(118,75,162,0.04),transparent 50%);pointer-events:none;}
        .container{position:relative;z-index:1;max-width:420px;width:100%;}
        .card{background:rgba(255,255,255,0.02);backdrop-filter:blur(40px);border-radius:24px;padding:40px;border:1px solid rgba(255,255,255,0.04);}
        .logo{text-align:center;font-size:26px;font-weight:900;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Orbitron',monospace;letter-spacing:2px;}
        .sub{text-align:center;color:#48bb78;margin:10px 0 30px 0;font-size:13px;font-family:'Orbitron',monospace;letter-spacing:1px;}
        input{width:100%;padding:14px;margin:10px 0;border:1px solid rgba(255,255,255,0.04);border-radius:14px;font-size:14px;transition:0.3s;background:rgba(255,255,255,0.02);color:#fff;font-family:'Inter',sans-serif;}
        input:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.04);}
        input::placeholder{color:rgba(255,255,255,0.3);}
        button{width:100%;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;padding:14px;border-radius:14px;font-size:15px;cursor:pointer;transition:0.5s;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;}
        button:hover{transform:translateY(-3px);box-shadow:0 10px 40px rgba(102,126,234,0.08);}
        .links{text-align:center;margin-top:18px;color:#ffffff;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .links a{color:#667eea;text-decoration:none;font-weight:500;}
        .demo{background:rgba(255,255,255,0.01);padding:15px;border-radius:14px;margin-top:20px;border:1px solid rgba(255,255,255,0.02);font-size:11px;color:#ffffff;text-align:center;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .demo strong{color:#48bb78;}
        .back-btn{display:inline-block;margin-top:15px;color:#ffffff;text-decoration:none;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .back-btn i{color:#667eea;}
        .back-btn:hover{color:#667eea;}
        .domain-tag{text-align:center;font-size:10px;color:rgba(255,255,255,0.15);margin-top:15px;font-family:'Orbitron',monospace;letter-spacing:1px;}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="container">
    <div class="card">
        <div class="logo"><i class="fas fa-user"></i> User Login</div>
        <div class="sub"><i class="fas fa-user-check"></i> Candidate / Student Access</div>
        <form id="loginForm">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit"><i class="fas fa-sign-in-alt"></i> Login</button>
        </form>
        <div class="links"><a href="/register"><i class="fas fa-user-plus"></i> New User? Register</a></div>
        <div class="demo"><strong>Demo User:</strong> user@demo.com / 123</div>
        <div style="text-align:center;"><a href="/" class="back-btn"><i class="fas fa-arrow-left"></i> Back to Home</a></div>
        <div class="domain-tag"><a href="https://www.aimockintr.com">www.aimockintr.com</a></div>
    </div>
</div>
<script>
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    try {
        const response = await fetch('/login', {method: 'POST', body: formData});
        const data = await response.json();
        if(data.success) {
            window.location.href = data.redirect;
        } else {
            alert(data.message || 'Login failed. Please try again.');
        }
    } catch(err) {
        alert('Network error. Please check your connection.');
        console.error(err);
    }
});
</script>
</body>
</html>
'''

REGISTER_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Register</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 40%,rgba(102,126,234,0.05),transparent 50%),radial-gradient(ellipse at 70% 60%,rgba(118,75,162,0.04),transparent 50%);pointer-events:none;}
        .container{position:relative;z-index:1;max-width:580px;width:100%;}
        .card{background:rgba(255,255,255,0.02);backdrop-filter:blur(40px);border-radius:24px;padding:40px;border:1px solid rgba(255,255,255,0.04);}
        .logo{text-align:center;font-size:26px;font-weight:900;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Orbitron',monospace;letter-spacing:2px;}
        .sub{text-align:center;color:#ffffff;margin:10px 0 25px 0;font-size:13px;font-family:'Orbitron',monospace;letter-spacing:1px;}
        input,select,textarea{width:100%;padding:12px;margin:8px 0;border:1px solid rgba(255,255,255,0.04);border-radius:14px;font-size:13px;transition:0.3s;background:rgba(255,255,255,0.02);color:#fff;font-family:'Inter',sans-serif;}
        input:focus,select:focus,textarea:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.04);}
        input::placeholder,select option,textarea::placeholder{color:rgba(255,255,255,0.3);}
        select option{background:#0a0a0f;color:#fff;}
        textarea{min-height:60px;resize:vertical;}
        button{width:100%;background:linear-gradient(135deg,#48bb78,#38a169);color:#fff;border:none;padding:14px;border-radius:14px;font-size:15px;cursor:pointer;transition:0.5s;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;}
        button:hover{transform:translateY(-3px);box-shadow:0 10px 40px rgba(72,187,120,0.05);}
        .links{text-align:center;margin-top:18px;color:#ffffff;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .links a{color:#667eea;text-decoration:none;font-weight:500;}
        .back-btn{display:inline-block;margin-top:15px;color:#ffffff;text-decoration:none;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .back-btn i{color:#667eea;}
        .back-btn:hover{color:#667eea;}
        .row{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
        .file-input{width:100%;padding:12px;margin:8px 0;border:1px solid rgba(255,255,255,0.04);border-radius:14px;background:rgba(255,255,255,0.02);color:rgba(255,255,255,0.3);font-size:12px;font-family:'Inter',sans-serif;}
        .file-input::-webkit-file-upload-button{background:rgba(255,255,255,0.02);color:#fff;border:none;padding:8px 16px;border-radius:8px;cursor:pointer;font-weight:500;}
        .domain-tag{text-align:center;font-size:10px;color:rgba(255,255,255,0.15);margin-top:15px;font-family:'Orbitron',monospace;letter-spacing:1px;}
        @media(max-width:500px){.row{grid-template-columns:1fr;}.card{padding:25px;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="container">
    <div class="card">
        <div class="logo"><i class="fas fa-user-plus"></i> Create Account</div>
        <div class="sub">Join LARA AI Platform</div>
        <form id="registerForm" enctype="multipart/form-data">
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="password" name="confirm_password" placeholder="Confirm Password" required>
            <select name="user_type" required>
                <option value="">Select User Type</option>
                <option value="student">🎓 Student</option>
                <option value="professional">💼 Professional</option>
                <option value="entrepreneur">🚀 Entrepreneur</option>
                <option value="other">Other</option>
            </select>
            <div class="row">
                <input type="text" name="college" placeholder="College / Company">
                <input type="text" name="domain" placeholder="Enter Your Domain" required>
            </div>
            <div class="row">
                <select name="experience_years">
                    <option value="0">0 - Fresher</option>
                    <option value="1">1 year</option>
                    <option value="2">2 years</option>
                    <option value="3">3 years</option>
                    <option value="4">4 years</option>
                    <option value="5">5+ years</option>
                </select>
                <input type="number" name="cgpa" step="0.01" placeholder="CGPA (0-10)">
            </div>
            <input type="tel" name="phone" placeholder="Phone Number">
            <textarea name="bio" placeholder="Short Bio (Optional)"></textarea>
            <input type="text" name="skills" placeholder="Skills (comma separated)">
            <input type="file" name="resume" accept=".pdf,.doc,.docx" class="file-input">
            <button type="submit" id="registerBtn"><i class="fas fa-check"></i> Register</button>
        </form>
        <div class="links"><a href="/login"><i class="fas fa-lock"></i> Already have account? Login</a></div>
        <div style="text-align:center;"><a href="/" class="back-btn"><i class="fas fa-arrow-left"></i> Back to Home</a></div>
        <div class="domain-tag"><a href="https://www.aimockintr.com">www.aimockintr.com</a></div>
    </div>
</div>
<script>
document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const btn = document.getElementById('registerBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = 'Please wait...';
    const formData = new FormData(this);
    try {
        const response = await fetch('/register', {method: 'POST', body: formData});
        const data = await response.json();
        if(data.success) {
            alert(data.message);
            window.location.href = '/login';
        } else {
            alert(data.message || 'Registration failed. Please check your details.');
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    } catch(err) {
        alert('Network error. Please check your connection.');
        console.error(err);
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
});
</script>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 40%,rgba(102,126,234,0.05),transparent 50%),radial-gradient(ellipse at 70% 60%,rgba(118,75,162,0.04),transparent 50%);pointer-events:none;}
        .container{position:relative;z-index:1;max-width:1200px;margin:0 auto;padding:20px;}
        .header{background:rgba(255,255,255,0.05);backdrop-filter:blur(20px);border-radius:20px;padding:18px 30px;display:flex;justify-content:space-between;align-items:center;border:1px solid rgba(255,255,255,0.08);margin-bottom:30px;}
        .logo{font-size:26px;font-weight:900;font-family:'Orbitron',monospace;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
        .logo .domain{font-size:10px;color:rgba(255,255,255,0.2);display:block;}
        .nav a{color:rgba(255,255,255,0.7);text-decoration:none;padding:8px 16px;border-radius:10px;font-weight:500;font-size:14px;transition:0.3s;}
        .nav a:hover{background:rgba(255,255,255,0.08);color:#fff;}
        .nav .logout{background:rgba(245,101,101,0.15);color:#f56565;}
        .nav .logout:hover{background:#f56565;color:#fff;}
        .welcome{font-size:28px;font-weight:700;margin-bottom:20px;background:linear-gradient(135deg,#fff,#a0aec0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .interview-cta{background:linear-gradient(135deg,rgba(72,187,120,0.15),rgba(56,161,105,0.08));border:1px solid rgba(72,187,120,0.3);border-radius:20px;padding:26px 30px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:15px;}
        .interview-cta .txt h3{font-family:'Orbitron',monospace;font-size:16px;letter-spacing:1px;color:#48bb78;}
        .interview-cta .txt p{font-size:13px;color:rgba(255,255,255,0.6);margin-top:6px;}
        .interview-cta a.join-btn{background:linear-gradient(135deg,#48bb78,#38a169);color:#fff;padding:14px 30px;border-radius:50px;text-decoration:none;font-weight:700;font-family:'Orbitron',monospace;letter-spacing:1px;font-size:13px;box-shadow:0 10px 30px rgba(72,187,120,0.25);}
        .actions{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px;}
        .action-btn{background:rgba(255,255,255,0.05);backdrop-filter:blur(10px);border-radius:16px;padding:20px;text-align:center;cursor:pointer;transition:0.3s;border:1px solid rgba(255,255,255,0.05);text-decoration:none;color:#fff;}
        .action-btn:hover{transform:translateY(-5px);border-color:#667eea;background:rgba(255,255,255,0.08);}
        .action-btn .icon{font-size:32px;}
        .action-btn .label{font-size:13px;margin-top:8px;color:rgba(255,255,255,0.8);font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .footer-text{text-align:center;margin-top:30px;font-size:10px;color:rgba(255,255,255,0.1);font-family:'Orbitron',monospace;letter-spacing:1px;}
        @media(max-width:768px){.header{flex-direction:column;gap:15px;}.nav{display:flex;flex-wrap:wrap;justify-content:center;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="container">
    <div class="header">
        <div class="logo">🎯 LARA AI <span class="domain">www.aimockintr.com</span></div>
        <div class="nav">
            <a href="/dashboard">🏠 Home</a>
            <a href="/profile">👤 Profile</a>
            <a href="/interview">🎙️ Interview</a>
            <a href="/notifications">🔔 {% if stats.unread_notifications > 0 %}<span style="background:#f56565;color:#fff;border-radius:50%;padding:2px 6px;font-size:10px;">{{ stats.unread_notifications }}</span>{% endif %}</a>
            <a href="/logout" class="logout">🚪 Logout</a>
        </div>
    </div>
    <div class="welcome">👋 Vanakkam, {{ user.name }}!</div>

    {% if not user.interview_complete and user.meeting_live and user.meeting_link %}
    <div class="interview-cta">
        <div class="txt">
            <h3>🤖 LARA AI Interview Ready!</h3>
            <p>Your mock interview is ready to start right now.</p>
        </div>
        <a href="{{ user.meeting_link }}" class="join-btn">🎙️ Join LARA AI Interview</a>
    </div>
    {% endif %}

    <div class="actions">
        <a href="/profile" class="action-btn"><div class="icon">👤</div><div class="label">Profile</div></a>
        <a href="/interview" class="action-btn"><div class="icon">🎙️</div><div class="label">Start Interview</div></a>
        <a href="/admin" class="action-btn" style="border-color:rgba(102,126,234,0.3);"><div class="icon">⚙️</div><div class="label">Admin Panel</div></a>
    </div>
    <div class="footer-text">www.aimockintr.com • LARA AI Mock Interview Platform</div>
</div>
</body>
</html>
'''

ADMIN_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Admin Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;color:#fff;overflow-x:hidden;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.02) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .admin-container{position:relative;z-index:1;max-width:1400px;margin:0 auto;padding:20px;}
        .admin-header{background:rgba(255,255,255,0.03);backdrop-filter:blur(40px);border-radius:20px;padding:20px 30px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center;border:1px solid rgba(255,255,255,0.04);}
        .admin-logo{font-size:24px;font-weight:900;font-family:'Orbitron',monospace;background:linear-gradient(135deg,#ff6b6b,#ee5a24);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:2px;}
        .admin-logo span{background:linear-gradient(135deg,#48bb78,#38a169);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
        .admin-logo .domain{font-size:10px;color:rgba(255,255,255,0.2);display:block;}
        .admin-nav{display:flex;gap:8px;flex-wrap:wrap;}
        .admin-nav a{color:#ffffff;text-decoration:none;padding:10px 20px;border-radius:12px;transition:0.4s;font-weight:500;font-size:12px;border:1px solid rgba(255,255,255,0.06);display:flex;align-items:center;gap:8px;font-family:'Orbitron',monospace;letter-spacing:0.5px;background:rgba(255,255,255,0.02);}
        .admin-nav a:hover{background:rgba(255,255,255,0.06);color:#fff;border-color:rgba(255,255,255,0.1);}
        .admin-nav a.active{background:linear-gradient(135deg,#ff6b6b,#ee5a24);color:#fff;border-color:transparent;box-shadow:0 8px 40px rgba(255,107,107,0.15);}
        .admin-nav .logout-btn{background:rgba(255,0,0,0.06);color:#ff6b6b;border:1px solid rgba(255,0,0,0.06);}
        .admin-nav .logout-btn:hover{background:#ff6b6b;color:#fff;border-color:#ff6b6b;}
        .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:20px;margin-bottom:30px;}
        .stat-card{background:rgba(255,255,255,0.02);backdrop-filter:blur(20px);border-radius:16px;padding:22px;border:1px solid rgba(255,255,255,0.04);}
        .stat-card .num{font-size:30px;font-weight:900;font-family:'Orbitron',monospace;color:#667eea;}
        .stat-card .label{font-size:11px;color:rgba(255,255,255,0.4);margin-top:5px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .table-card{background:rgba(255,255,255,0.02);backdrop-filter:blur(20px);border-radius:16px;padding:25px;border:1px solid rgba(255,255,255,0.04);overflow-x:auto;margin-bottom:20px;}
        .table-title{font-size:14px;font-weight:600;margin-bottom:20px;color:#ffffff;display:flex;align-items:center;gap:10px;font-family:'Orbitron',monospace;letter-spacing:1px;}
        table{width:100%;border-collapse:collapse;}
        th{color:rgba(255,255,255,0.5);padding:12px;text-align:left;border-bottom:2px solid rgba(255,255,255,0.03);font-weight:600;font-size:9px;text-transform:uppercase;letter-spacing:1.5px;font-family:'Orbitron',monospace;}
        td{color:rgba(255,255,255,0.8);padding:12px;border-bottom:1px solid rgba(255,255,255,0.02);font-size:12px;}
        tr:hover{background:rgba(255,255,255,0.02);}
        .badge{padding:3px 10px;border-radius:30px;font-size:8px;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .badge-success{background:rgba(72,187,120,0.08);color:#48bb78;border:1px solid rgba(72,187,120,0.06);}
        .badge-warning{background:rgba(253,203,110,0.08);color:#fdcb6e;border:1px solid rgba(253,203,110,0.06);}
        .btn-sm{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;padding:5px 12px;border-radius:8px;cursor:pointer;font-weight:600;font-size:9px;transition:0.3s;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .btn-sm:hover{transform:scale(1.05);}
        .btn-sm.green{background:linear-gradient(135deg,#48bb78,#38a169);}
        .footer-text{text-align:center;margin-top:30px;font-size:10px;color:rgba(255,255,255,0.08);font-family:'Orbitron',monospace;letter-spacing:1px;}
        @media(max-width:768px){.admin-header{flex-direction:column;gap:15px;}.admin-nav{justify-content:center;}.stats-grid{grid-template-columns:1fr 1fr;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="admin-container">
    <div class="admin-header">
        <div class="admin-logo">🎯 LARA <span>Admin</span> <span class="domain">www.aimockintr.com</span></div>
        <div class="admin-nav">
            <a href="/admin" class="active"><i class="fas fa-chart-pie"></i> Dashboard</a>
            <a href="/admin/users"><i class="fas fa-users"></i> Users</a>
            <a href="/admin/schedule"><i class="fas fa-calendar-plus"></i> Schedule</a>
            <a href="/logout" class="logout-btn"><i class="fas fa-sign-out-alt"></i> Logout</a>
        </div>
    </div>
    <div class="stats-grid">
        <div class="stat-card"><div class="num">{{ stats.total_users }}</div><div class="label">Total Users</div></div>
        <div class="stat-card"><div class="num" style="color:#48bb78;">{{ stats.completed_interviews }}</div><div class="label">✅ Interviews Completed</div></div>
        <div class="stat-card"><div class="num" style="color:#ed8936;">{{ stats.pending_interviews }}</div><div class="label">⏳ Pending</div></div>
        <div class="stat-card"><div class="num" style="color:#63b3ed;">{{ stats.avg_score }}%</div><div class="label">📊 Avg Score</div></div>
        <div class="stat-card"><div class="num" style="color:#48bb78;">{{ stats.pass_rate }}%</div><div class="label">📈 Pass Rate</div></div>
    </div>
    <div class="table-card">
        <div class="table-title"><i class="fas fa-users"></i> All Users</div>
        <table>
            <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Type</th><th>Domain</th><th>Status</th><th>Score</th><th>Action</th></tr></thead>
            <tbody>
                {% for u in users %}
                <tr>
                    <td>{{ u.id }}</td><td>{{ u.name }}</td><td>{{ u.email }}</td>
                    <td>{% if u.user_type == 'student' %}🎓{% elif u.role == 'admin' %}👑{% else %}💼{% endif %}</td>
                    <td>{{ u.domain or '-' }}</td>
                    <td>{% if u.interview_complete %}<span class="badge badge-success">✅ Done{% else %}<span class="badge badge-warning">⏳ Pending{% endif %}</span></td>
                    <td>{{ u.final_score or '-' }}</td>
                    <td>{% if not u.interview_complete and u.role != 'admin' %}<a href="/admin/schedule/{{ u.id }}"><button class="btn-sm green">Schedule</button></a>{% endif %}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <div class="footer-text">www.aimockintr.com • LARA AI Admin Panel</div>
</div>
</body>
</html>
'''

PROFILE_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Profile</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .container{position:relative;z-index:1;max-width:800px;margin:0 auto;padding:20px;}
        .card{background:rgba(255,255,255,0.05);backdrop-filter:blur(20px);border-radius:20px;padding:30px;border:1px solid rgba(255,255,255,0.08);}
        .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:10px;}
        .header h2{font-size:24px;font-family:'Orbitron',monospace;}
        .info-row{display:flex;padding:12px;border-bottom:1px solid rgba(255,255,255,0.02);}
        .info-label{width:140px;font-weight:600;color:rgba(255,255,255,0.5);font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .info-value{flex:1;color:#ffffff;font-size:13px;}
        .btn{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;padding:12px 30px;border-radius:60px;cursor:pointer;font-size:13px;transition:0.4s;text-decoration:none;display:inline-block;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .btn:hover{transform:scale(1.05);box-shadow:0 10px 40px rgba(102,126,234,0.06);}
        .btn-group{display:flex;gap:15px;margin-top:20px;flex-wrap:wrap;}
        .footer-text{text-align:center;margin-top:30px;font-size:10px;color:rgba(255,255,255,0.08);font-family:'Orbitron',monospace;letter-spacing:1px;}
        @media(max-width:500px){.info-row{flex-direction:column;}.info-label{margin-bottom:5px;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="container">
    <div class="card">
        <div class="header">
            <h2><i class="fas fa-user-circle" style="color:#667eea;"></i> My Profile</h2>
            <a href="/dashboard" class="btn" style="padding:8px 20px;font-size:12px;">🏠 Dashboard</a>
        </div>
        <div class="info-row"><div class="info-label">Name:</div><div class="info-value">{{ user.name }}</div></div>
        <div class="info-row"><div class="info-label">Email:</div><div class="info-value">{{ user.email }}</div></div>
        <div class="info-row"><div class="info-label">Type:</div><div class="info-value">{% if user.user_type == 'student' %}🎓 Student{% elif user.role == 'admin' %}👑 Admin{% else %}💼 Professional{% endif %}</div></div>
        <div class="info-row"><div class="info-label">College/Company:</div><div class="info-value">{{ user.college or 'Not specified' }}</div></div>
        <div class="info-row"><div class="info-label">Domain:</div><div class="info-value">{{ user.domain or 'Not specified' }}</div></div>
        <div class="info-row"><div class="info-label">Experience:</div><div class="info-value">{% if user.experience_years == 0 %}Fresher{% else %}{{ user.experience_years }} years{% endif %}</div></div>
        <div class="info-row"><div class="info-label">CGPA:</div><div class="info-value">{{ user.cgpa or 'Not specified' }}</div></div>
        <div class="info-row"><div class="info-label">Phone:</div><div class="info-value">{{ user.phone or 'Not specified' }}</div></div>
        <div class="info-row"><div class="info-label">Bio:</div><div class="info-value">{{ user.bio or 'Not specified' }}</div></div>
        <div class="info-row"><div class="info-label">Skills:</div><div class="info-value">{{ user.skills or 'Not specified' }}</div></div>
        <div class="info-row"><div class="info-label">Interview Status:</div><div class="info-value">{% if user.interview_complete %}✅ Completed (Score: {{ user.final_score }}%){% elif user.meeting_live %}🔴 Live{% elif user.meeting_scheduled %}⏳ Scheduled{% else %}📅 Not Scheduled{% endif %}</div></div>
        <div class="btn-group">
            <a href="/dashboard"><button class="btn">🏠 Home</button></a>
            <a href="/edit-profile"><button class="btn" style="background:linear-gradient(135deg,#48bb78,#38a169);">✏️ Edit Profile</button></a>
        </div>
        <div class="footer-text">www.aimockintr.com</div>
    </div>
</div>
</body>
</html>
'''

INTERVIEW_HOME_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Interview</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .container{position:relative;z-index:1;max-width:900px;margin:0 auto;padding:20px;}
        .card{background:rgba(255,255,255,0.05);backdrop-filter:blur(20px);border-radius:20px;padding:30px;border:1px solid rgba(255,255,255,0.08);}
        h2{font-size:24px;font-family:'Orbitron',monospace;margin-bottom:20px;}
        .status-box{padding:20px;border-radius:16px;text-align:center;margin:20px 0;border:1px solid rgba(255,255,255,0.04);}
        .status-box .icon{font-size:64px;margin:10px 0;}
        .btn{background:linear-gradient(135deg,#48bb78,#38a169);color:#fff;border:none;padding:14px 40px;border-radius:60px;font-size:16px;cursor:pointer;transition:0.5s;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;text-decoration:none;display:inline-block;}
        .btn:hover{transform:scale(1.05);box-shadow:0 10px 40px rgba(72,187,120,0.3);}
        .btn.secondary{background:linear-gradient(135deg,#667eea,#764ba2);}
        .btn-group{display:flex;gap:15px;justify-content:center;flex-wrap:wrap;margin-top:20px;}
        .footer-text{text-align:center;margin-top:30px;font-size:10px;color:rgba(255,255,255,0.08);font-family:'Orbitron',monospace;letter-spacing:1px;}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="container">
    <div class="card">
        <h2><i class="fas fa-video" style="color:#667eea;"></i> AI Interview Portal</h2>
        <div class="status-box">
            {% if user.interview_complete %}
                <div class="icon">🎉</div>
                <h3>Interview Completed!</h3>
                <p style="font-size:18px;font-weight:700;color:#48bb78;font-family:'Orbitron',monospace;">Your Score: {{ user.final_score }}%</p>
                <p>{{ user.company_message }}</p>
                <div class="btn-group">
                    <a href="/dashboard"><button class="btn">🏠 Dashboard</button></a>
                </div>
            {% elif user.meeting_live %}
                <div class="icon">🔴</div>
                <h3 style="color:#ff6b6b;">Interview is Live!</h3>
                <p>Your interview with LARA AI is ready. Click below to join.</p>
                <div class="btn-group">
                    <a href="{{ user.meeting_link }}"><button class="btn">🎙️ Join LARA AI Interview</button></a>
                </div>
            {% elif user.meeting_scheduled %}
                <div class="icon">⏳</div>
                <h3 style="color:#fdcb6e;">Interview Scheduled</h3>
                <p>Your interview has been scheduled. You will be notified when it's live.</p>
                <div class="btn-group">
                    <a href="/dashboard"><button class="btn secondary">🏠 Dashboard</button></a>
                </div>
            {% else %}
                <div class="icon">📅</div>
                <h3>No Interview Scheduled</h3>
                <p>Admin will schedule your interview. Please check back later.</p>
                <div class="btn-group">
                    <a href="/dashboard"><button class="btn secondary">🏠 Dashboard</button></a>
                </div>
            {% endif %}
        </div>
        <div class="footer-text">www.aimockintr.com</div>
    </div>
</div>
</body>
</html>
'''

INTERVIEW_SESSION_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Interview Session</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 40%,rgba(102,126,234,0.05),transparent 50%),radial-gradient(ellipse at 70% 60%,rgba(118,75,162,0.04),transparent 50%);pointer-events:none;}
        .container{position:relative;z-index:1;max-width:900px;width:100%;}
        .card{background:rgba(255,255,255,0.05);backdrop-filter:blur(20px);border-radius:24px;padding:40px;border:1px solid rgba(255,255,255,0.08);}
        .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:25px;padding-bottom:20px;border-bottom:1px solid rgba(255,255,255,0.08);}
        .header .title{font-size:22px;font-weight:700;font-family:'Orbitron',monospace;background:linear-gradient(135deg,#fff,#a0aec0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
        .header .progress{font-size:14px;color:rgba(255,255,255,0.5);font-family:'Orbitron',monospace;}
        .question-box{background:rgba(255,255,255,0.05);padding:30px;border-radius:16px;margin:20px 0;border-left:4px solid #667eea;}
        .question-tamil{font-size:28px;font-weight:600;line-height:1.6;}
        .question-english{font-size:16px;color:rgba(255,255,255,0.4);margin-top:10px;font-style:italic;}
        .timer-bar{height:6px;background:rgba(255,255,255,0.08);border-radius:4px;margin:20px 0;overflow:hidden;}
        .timer-fill{height:100%;background:linear-gradient(90deg,#48bb78,#38a169);border-radius:4px;transition:width 0.1s linear;}
        .time-left{text-align:right;font-size:14px;color:rgba(255,255,255,0.5);margin-top:5px;font-family:'Orbitron',monospace;}
        .camera-controls{display:flex;gap:15px;justify-content:center;margin:15px 0;flex-wrap:wrap;}
        .cam-btn{background:rgba(255,255,255,0.08);color:#fff;border:1px solid rgba(255,255,255,0.1);padding:10px 20px;border-radius:30px;cursor:pointer;font-family:'Orbitron',monospace;font-size:12px;transition:0.3s;}
        .cam-btn:hover{background:rgba(255,255,255,0.15);}
        .cam-btn.active{background:#48bb78;border-color:#48bb78;}
        .cam-btn.inactive{background:#f56565;border-color:#f56565;}
        .video-container{background:#1a1a2e;border-radius:16px;overflow:hidden;margin:15px 0;position:relative;aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;}
        .video-container video{width:100%;height:100%;object-fit:cover;background:#1a1a2e;}
        .video-placeholder{color:rgba(255,255,255,0.3);font-size:18px;font-family:'Orbitron',monospace;}
        .voice-indicator{display:flex;align-items:center;gap:10px;justify-content:center;margin:10px 0;}
        .voice-dot{width:12px;height:12px;border-radius:50%;background:#48bb78;animation:pulse 1.5s ease-in-out infinite;}
        .voice-dot.inactive{background:#f56565;animation:none;}
        @keyframes pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.5;transform:scale(0.8);}}
        textarea{width:100%;padding:16px;border:1px solid rgba(255,255,255,0.1);border-radius:14px;font-size:16px;margin:15px 0;resize:vertical;background:rgba(255,255,255,0.05);color:#fff;font-family:'Inter',sans-serif;min-height:120px;}
        textarea:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.15);}
        .btn-submit{width:100%;background:linear-gradient(135deg,#48bb78,#38a169);color:#fff;border:none;padding:16px;border-radius:14px;font-size:18px;cursor:pointer;transition:0.3s;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .btn-submit:hover{transform:scale(1.02);box-shadow:0 10px 40px rgba(72,187,120,0.3);}
        .mic-btn{background:rgba(255,255,255,0.08);color:#fff;border:1px solid rgba(255,255,255,0.1);padding:10px 20px;border-radius:30px;cursor:pointer;font-family:'Orbitron',monospace;font-size:12px;transition:0.3s;}
        .mic-btn:hover{background:rgba(255,255,255,0.15);}
        .mic-btn.recording{background:#f56565;border-color:#f56565;animation:blink 0.8s ease-in-out infinite;}
        @keyframes blink{0%,100%{opacity:1;}50%{opacity:0.5;}}
        .footer-text{text-align:center;margin-top:20px;font-size:9px;color:rgba(255,255,255,0.08);font-family:'Orbitron',monospace;letter-spacing:1px;}
        @media(max-width:768px){.card{padding:20px;}.question-tamil{font-size:22px;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="container">
    <div class="card">
        <div class="header">
            <div class="title">🤖 LARA AI Interview</div>
            <div class="progress">Question {{ index }}/{{ total }}</div>
        </div>
        <div class="question-box">
            <div class="question-tamil">❓ {{ question.tamil }}</div>
            <div class="question-english">💡 {{ question.english }}</div>
        </div>
        <div class="video-container">
            <video id="videoElement" autoplay playsinline></video>
            <div class="video-placeholder" id="videoPlaceholder">🎥 Camera Off</div>
        </div>
        <div class="camera-controls">
            <button class="cam-btn {% if camera_state %}active{% else %}inactive{% endif %}" id="camToggle" onclick="toggleCamera()">
                {% if camera_state %}📷 Camera ON{% else %}📷 Camera OFF{% endif %}
            </button>
            <button class="mic-btn" id="micToggle" onclick="toggleMic()">🎤 Voice OFF</button>
        </div>
        <div class="voice-indicator">
            <span>🎙️ Voice Recognition</span>
            <div class="voice-dot" id="voiceDot"></div>
        </div>
        <div class="timer-bar"><div class="timer-fill" id="timerFill" style="width:100%"></div></div>
        <div class="time-left" id="timeLeft">1:00 remaining</div>
        <form id="answerForm">
            <textarea name="answer" id="answerInput" placeholder="தமிழில் உங்கள் பதில் சொல்லுங்கள்... LARA AI காத்திருக்கிறது..." required></textarea>
            <input type="hidden" name="camera_state" id="cameraStateInput" value="{{ 'true' if camera_state else 'false' }}">
            <button type="submit" class="btn-submit">➡️ Submit Answer</button>
        </form>
        <div class="footer-text">www.aimockintr.com</div>
    </div>
</div>
<script>
/*
   CAMERA STATE LOGIC (FIXED):
   - cameraOn ALWAYS starts from the exact state saved from the previous
     question (server-rendered camera_state). It is never force-enabled.
   - The camera only turns on when the user explicitly clicks the button.
   - Once toggled off/on by the user, that exact state carries forward
     to every following question until the user changes it again.
*/
let stream = null;
let cameraOn = {{ 'true' if camera_state else 'false' }};
let micOn = false;
let recognition = null;
const cameraStateInput = document.getElementById('cameraStateInput');

async function toggleCamera() {
    const btn = document.getElementById('camToggle');
    const video = document.getElementById('videoElement');
    const placeholder = document.getElementById('videoPlaceholder');
    if (cameraOn) {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        video.style.display = 'none';
        placeholder.style.display = 'block';
        btn.textContent = '📷 Camera OFF';
        btn.className = 'cam-btn inactive';
        cameraOn = false;
        cameraStateInput.value = 'false';
        saveCameraState(false);
    } else {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            video.srcObject = stream;
            video.style.display = 'block';
            placeholder.style.display = 'none';
            btn.textContent = '📷 Camera ON';
            btn.className = 'cam-btn active';
            cameraOn = true;
            cameraStateInput.value = 'true';
            saveCameraState(true);
        } catch(err) {
            alert('Camera access denied. Please allow camera permissions.');
            console.error(err);
        }
    }
}

function saveCameraState(state) {
    fetch('/api/camera-state', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({camera_state: state})
    }).catch(err => console.error('Error saving camera state:', err));
}

function toggleMic() {
    const btn = document.getElementById('micToggle');
    const dot = document.getElementById('voiceDot');
    if (micOn) {
        if (recognition) {
            recognition.stop();
            recognition = null;
        }
        btn.textContent = '🎤 Voice OFF';
        btn.className = 'mic-btn';
        dot.className = 'voice-dot inactive';
        micOn = false;
    } else {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            alert('Voice recognition not supported in this browser. Please use Chrome.');
            return;
        }
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'ta-IN';
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.onresult = function(event) {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            document.getElementById('answerInput').value = transcript;
        };
        recognition.onerror = function(event) {
            console.error('Speech error:', event.error);
        };
        recognition.start();
        btn.textContent = '🎤 Voice ON';
        btn.className = 'mic-btn recording';
        dot.className = 'voice-dot';
        micOn = true;
    }
}

// On page load: ONLY show the camera if cameraOn is exactly true
// (i.e. the state that was carried over from the previous question).
// If false (default, or user turned it off previously), never
// auto-request camera permission or auto-enable it.
window.onload = function() {
    const video = document.getElementById('videoElement');
    const placeholder = document.getElementById('videoPlaceholder');
    const btn = document.getElementById('camToggle');
    if (cameraOn === true) {
        navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then(function(mediaStream) {
                stream = mediaStream;
                video.srcObject = stream;
                video.style.display = 'block';
                placeholder.style.display = 'none';
                btn.textContent = '📷 Camera ON';
                btn.className = 'cam-btn active';
                cameraOn = true;
                cameraStateInput.value = 'true';
            })
            .catch(function(err) {
                console.log('Camera not available:', err);
                cameraOn = false;
                cameraStateInput.value = 'false';
                video.style.display = 'none';
                placeholder.style.display = 'block';
                btn.textContent = '📷 Camera OFF';
                btn.className = 'cam-btn inactive';
            });
    } else {
        video.style.display = 'none';
        placeholder.style.display = 'block';
        btn.textContent = '📷 Camera OFF';
        btn.className = 'cam-btn inactive';
        cameraOn = false;
        cameraStateInput.value = 'false';
    }
};

let timeLeft = 60;
const timerFill = document.getElementById('timerFill');
const timeLeftSpan = document.getElementById('timeLeft');
const form = document.getElementById('answerForm');

function updateTimer() {
    if(timeLeft <= 0) {
        timeLeftSpan.innerHTML = "⏰ Time's up! Auto-submitting...";
        timerFill.style.background = "#f56565";
        form.dispatchEvent(new Event('submit', {cancelable: true}));
    } else {
        const seconds = timeLeft % 60;
        const percent = (timeLeft / 60 * 100);
        timerFill.style.width = percent + '%';
        if(percent < 20) timerFill.style.background = "#f56565";
        timeLeftSpan.innerHTML = Math.floor(timeLeft/60) + ':' + seconds.toString().padStart(2,'0') + ' remaining';
        timeLeft--;
        setTimeout(updateTimer, 1000);
    }
}
updateTimer();

document.getElementById('answerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    if (recognition) {
        recognition.stop();
    }
    // Always send the CURRENT, real cameraOn state - this is what
    // guarantees the next question keeps exactly this same state.
    cameraStateInput.value = cameraOn ? 'true' : 'false';
    const formData = new FormData(this);
    const response = await fetch('/submit-answer', {method: 'POST', body: formData});
    const data = await response.json();
    if(data.success) {
        window.location.href = data.redirect;
    }
});
</script>
</body>
</html>
'''

RESULT_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Result</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .container{position:relative;z-index:1;max-width:550px;width:100%;}
        .card{background:rgba(255,255,255,0.05);backdrop-filter:blur(20px);border-radius:24px;padding:40px;text-align:center;border:1px solid rgba(255,255,255,0.08);}
        .icon{font-size:72px;margin:10px 0;}
        .card h1{font-size:28px;font-weight:700;margin-bottom:5px;font-family:'Orbitron',monospace;}
        .score-box{background:rgba(255,255,255,0.05);border-radius:16px;padding:25px;margin:20px 0;border:1px solid rgba(255,255,255,0.05);}
        .score-box h3{font-size:16px;font-weight:500;color:rgba(255,255,255,0.5);font-family:'Orbitron',monospace;letter-spacing:1px;}
        .score{font-size:64px;font-weight:900;margin:10px 0;font-family:'Orbitron',monospace;}
        .pass .score{color:#48bb78;}
        .fail .score{color:#f56565;}
        .msg{font-size:16px;margin:15px 0;line-height:1.7;color:rgba(255,255,255,0.7);}
        .btn-group{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:20px;}
        .btn{background:rgba(255,255,255,0.08);color:#fff;border:1px solid rgba(255,255,255,0.1);padding:12px 30px;border-radius:50px;cursor:pointer;font-size:14px;transition:0.3s;text-decoration:none;font-weight:500;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .btn:hover{transform:scale(1.05);background:rgba(255,255,255,0.15);}
        .btn.green{background:linear-gradient(135deg,#48bb78,#38a169);border:none;}
        .btn.green:hover{box-shadow:0 10px 40px rgba(72,187,120,0.3);}
        .footer-text{text-align:center;margin-top:30px;font-size:9px;color:rgba(255,255,255,0.08);font-family:'Orbitron',monospace;letter-spacing:1px;}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="container">
    <div class="card {% if user.passed %}pass{% else %}fail{% endif %}">
        <div class="icon">{% if user.passed %}🎉{% else %}😔{% endif %}</div>
        <h1>{% if user.passed %}Congratulations! 🎊{% else %}We're Sorry 😔{% endif %}</h1>
        <div class="score-box">
            <h3>🤖 LARA AI Score</h3>
            <div class="score">{{ user.final_score }}%</div>
        </div>
        <div class="msg">{{ user.company_message }}</div>
        <div class="btn-group">
            <a href="/dashboard"><button class="btn green">🏠 Back to Dashboard</button></a>
        </div>
        <div class="footer-text">www.aimockintr.com</div>
    </div>
</div>
</body>
</html>
'''

ADMIN_LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Admin Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .container{position:relative;z-index:1;max-width:420px;width:100%;}
        .card{background:rgba(255,255,255,0.02);backdrop-filter:blur(40px);border-radius:24px;padding:40px;border:1px solid rgba(255,255,255,0.04);border-top:3px solid #ff6b6b;}
        .logo{text-align:center;font-size:26px;font-weight:900;background:linear-gradient(135deg,#ff6b6b,#ee5a24);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Orbitron',monospace;letter-spacing:2px;}
        .sub{text-align:center;color:#ff6b6b;margin:10px 0 30px 0;font-size:13px;font-family:'Orbitron',monospace;letter-spacing:1px;}
        input{width:100%;padding:14px;margin:10px 0;border:1px solid rgba(255,255,255,0.04);border-radius:14px;font-size:14px;background:rgba(255,255,255,0.02);color:#fff;font-family:'Inter',sans-serif;}
        input:focus{outline:none;border-color:#ff6b6b;box-shadow:0 0 0 3px rgba(255,107,107,0.04);}
        button{width:100%;background:linear-gradient(135deg,#ff6b6b,#ee5a24);color:#fff;border:none;padding:14px;border-radius:14px;font-size:15px;cursor:pointer;transition:0.5s;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;}
        button:hover{transform:translateY(-3px);box-shadow:0 10px 40px rgba(255,107,107,0.08);}
        .demo{background:rgba(255,255,255,0.01);padding:15px;border-radius:14px;margin-top:20px;border:1px solid rgba(255,255,255,0.02);font-size:11px;color:#ffffff;text-align:center;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .demo strong{color:#ff6b6b;}
        .back-btn{display:inline-block;margin-top:15px;color:#ffffff;text-decoration:none;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .back-btn i{color:#ff6b6b;}
        .back-btn:hover{color:#ff6b6b;}
        .admin-badge{display:inline-block;background:rgba(255,107,107,0.06);padding:4px 14px;border-radius:30px;font-size:9px;color:#ff6b6b;border:1px solid rgba(255,107,107,0.06);font-family:'Orbitron',monospace;letter-spacing:1px;margin-top:5px;}
        .domain-tag{text-align:center;font-size:10px;color:rgba(255,255,255,0.15);margin-top:15px;font-family:'Orbitron',monospace;letter-spacing:1px;}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="container">
    <div class="card">
        <div class="logo"><i class="fas fa-shield-alt"></i> Admin Login</div>
        <div class="sub"><i class="fas fa-lock"></i> Administrator Access</div>
        <div style="text-align:center;"><span class="admin-badge"><i class="fas fa-crown"></i> ADMIN PANEL</span></div>
        <form id="adminLoginForm">
            <input type="email" name="email" placeholder="Admin Email" required>
            <input type="password" name="password" placeholder="Admin Password" required>
            <button type="submit"><i class="fas fa-sign-in-alt"></i> Admin Login</button>
        </form>
        <div class="demo"><strong>Admin Demo:</strong> admin@demo.com / admin123</div>
        <div style="text-align:center;"><a href="/" class="back-btn"><i class="fas fa-arrow-left"></i> Back to Home</a></div>
        <div class="domain-tag">www.aimockintr.com</div>
    </div>
</div>
<script>
document.getElementById('adminLoginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    try {
        const response = await fetch('/admin-login', {method: 'POST', body: formData});
        const data = await response.json();
        if(data.success) {
            window.location.href = data.redirect;
        } else {
            alert(data.message || 'Invalid admin credentials');
        }
    } catch(err) {
        alert('Network error. Please check your connection.');
        console.error(err);
    }
});
</script>
</body>
</html>
'''

NOTIFICATIONS_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Notifications</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .container{position:relative;z-index:1;max-width:800px;margin:0 auto;padding:20px;}
        .card{background:rgba(255,255,255,0.05);backdrop-filter:blur(20px);border-radius:20px;padding:30px;border:1px solid rgba(255,255,255,0.08);}
        h2{font-size:24px;font-family:'Orbitron',monospace;margin-bottom:20px;}
        .notification-item{padding:15px;border-bottom:1px solid rgba(255,255,255,0.04);}
        .notification-item:last-child{border-bottom:none;}
        .notification-title{font-weight:600;color:#fff;}
        .notification-message{color:rgba(255,255,255,0.5);font-size:13px;margin-top:5px;}
        .notification-time{font-size:10px;color:rgba(255,255,255,0.2);margin-top:5px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .btn{background:rgba(255,255,255,0.08);color:#fff;border:1px solid rgba(255,255,255,0.1);padding:10px 25px;border-radius:50px;cursor:pointer;font-size:13px;transition:0.3s;text-decoration:none;font-weight:500;font-family:'Orbitron',monospace;letter-spacing:0.5px;display:inline-block;}
        .btn:hover{transform:scale(1.05);background:rgba(255,255,255,0.15);}
        .empty-state{text-align:center;padding:40px 20px;}
        .empty-state .icon{font-size:48px;color:rgba(255,255,255,0.05);}
        .empty-state h3{color:rgba(255,255,255,0.2);margin-top:10px;font-family:'Orbitron',monospace;}
        .btn-group{margin-top:20px;}
        .footer-text{text-align:center;margin-top:30px;font-size:9px;color:rgba(255,255,255,0.08);font-family:'Orbitron',monospace;letter-spacing:1px;}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="container">
    <div class="card">
        <h2><i class="fas fa-bell" style="color:#667eea;"></i> Notifications</h2>
        {% if notifications %}
            {% for n in notifications %}
            <div class="notification-item">
                <div class="notification-title">{{ n.title }}</div>
                <div class="notification-message">{{ n.message }}</div>
                <div class="notification-time">{{ n.created_at.strftime('%Y-%m-%d %H:%M') }}</div>
            </div>
            {% endfor %}
        {% else %}
            <div class="empty-state">
                <div class="icon">🔔</div>
                <h3>No notifications</h3>
                <p style="color:rgba(255,255,255,0.1);">You're all caught up!</p>
            </div>
        {% endif %}
        <div class="btn-group">
            <a href="/dashboard"><button class="btn">🏠 Dashboard</button></a>
        </div>
        <div class="footer-text">www.aimockintr.com</div>
    </div>
</div>
</body>
</html>
'''

EDIT_PROFILE_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edit Profile - LARA AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .container{position:relative;z-index:1;max-width:600px;margin:0 auto;padding:20px;}
        .card{background:rgba(255,255,255,0.05);backdrop-filter:blur(20px);border-radius:20px;padding:30px;border:1px solid rgba(255,255,255,0.08);}
        h2{font-size:24px;font-family:'Orbitron',monospace;margin-bottom:20px;}
        input,select,textarea{width:100%;padding:12px;margin:8px 0;border:1px solid rgba(255,255,255,0.04);border-radius:14px;font-size:13px;background:rgba(255,255,255,0.02);color:#fff;font-family:'Inter',sans-serif;}
        input:focus,select:focus,textarea:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.04);}
        textarea{min-height:80px;resize:vertical;}
        button{width:100%;background:linear-gradient(135deg,#48bb78,#38a169);color:#fff;border:none;padding:14px;border-radius:14px;font-size:15px;cursor:pointer;transition:0.5s;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;}
        button:hover{transform:translateY(-3px);box-shadow:0 10px 40px rgba(72,187,120,0.05);}
        .btn-back{background:rgba(255,255,255,0.02);color:#fff;border:1px solid rgba(255,255,255,0.04);padding:12px 30px;border-radius:60px;cursor:pointer;font-size:13px;transition:0.4s;text-decoration:none;display:inline-block;font-weight:500;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .btn-back:hover{background:rgba(255,255,255,0.04);}
        .footer-text{text-align:center;margin-top:30px;font-size:9px;color:rgba(255,255,255,0.08);font-family:'Orbitron',monospace;letter-spacing:1px;}
        @media(max-width:500px){.row{grid-template-columns:1fr;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="container">
    <div class="card">
        <h2><i class="fas fa-edit" style="color:#667eea;"></i> Edit Profile</h2>
        <form id="editProfileForm">
            <input type="text" name="name" value="{{ user.name }}" required>
            <input type="text" name="college" value="{{ user.college or '' }}" placeholder="College / Company">
            <input type="text" name="domain" value="{{ user.domain or '' }}" placeholder="Domain" required>
            <select name="experience_years">
                <option value="0" {% if user.experience_years == 0 %}selected{% endif %}>0 - Fresher</option>
                <option value="1" {% if user.experience_years == 1 %}selected{% endif %}>1 year</option>
                <option value="2" {% if user.experience_years == 2 %}selected{% endif %}>2 years</option>
                <option value="3" {% if user.experience_years == 3 %}selected{% endif %}>3 years</option>
                <option value="4" {% if user.experience_years == 4 %}selected{% endif %}>4 years</option>
                <option value="5" {% if user.experience_years >= 5 %}selected{% endif %}>5+ years</option>
            </select>
            <input type="number" name="cgpa" step="0.01" value="{{ user.cgpa or '' }}" placeholder="CGPA (0-10)">
            <input type="tel" name="phone" value="{{ user.phone or '' }}" placeholder="Phone Number">
            <textarea name="bio" placeholder="Short Bio">{{ user.bio or '' }}</textarea>
            <input type="text" name="skills" value="{{ user.skills or '' }}" placeholder="Skills (comma separated)">
            <button type="submit">✔ Update Profile</button>
        </form>
        <div style="text-align:center;margin-top:15px;"><a href="/profile" class="btn-back"><i class="fas fa-arrow-left"></i> Back to Profile</a></div>
        <div class="footer-text">www.aimockintr.com</div>
    </div>
</div>
<script>
document.getElementById('editProfileForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const response = await fetch('/edit-profile', {method: 'POST', body: formData});
    const data = await response.json();
    if(data.success) {
        alert(data.message);
        window.location.href = '/profile';
    } else {
        alert(data.message || 'Update failed. Please try again.');
    }
});
</script>
</body>
</html>
'''

# ============================================================
# ROUTES - COMPLETE APPLICATION
# ============================================================

@app.route('/')
def index():
    if 'user_id' in session:
        user = get_current_user()
        if user and user.role == 'admin':
            return redirect('/admin')
        return redirect('/dashboard')
    return render_template_string(LANDING_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_authenticated():
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({'success': False, 'message': 'Invalid email or password'})

        if not user.is_active:
            return jsonify({'success': False, 'message': 'Account is deactivated'})

        if is_account_locked(user):
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            return jsonify({'success': False, 'message': f'Account locked. Try again in {remaining} minutes'})

        if user.check_password(password):
            reset_login_attempts(user)
            session.permanent = True
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_activity(user.id, 'login', 'User logged in')
            return jsonify({'success': True, 'redirect': '/admin' if user.role == 'admin' else '/dashboard'})
        else:
            attempts = increment_login_attempts(user)
            remaining = app.config['MAX_LOGIN_ATTEMPTS'] - attempts
            return jsonify({'success': False, 'message': f'Invalid password. {remaining} attempts remaining'})

    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_authenticated():
        return redirect('/')
    if request.method == 'POST':
        try:
            name = sanitize_input(request.form.get('name'))
            email = sanitize_input(request.form.get('email'))
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            user_type = request.form.get('user_type', 'student')
            college = sanitize_input(request.form.get('college', ''))
            domain = sanitize_input(request.form.get('domain', ''))
            experience_years = int(request.form.get('experience_years', 0) or 0)
            cgpa = float(request.form.get('cgpa', 0) or 0)
            phone = sanitize_input(request.form.get('phone', ''))
            bio = sanitize_input(request.form.get('bio', ''))
            skills = sanitize_input(request.form.get('skills', ''))

            if not name or len(name) < 2:
                return jsonify({'success': False, 'message': 'Name must be at least 2 characters'})
            if not validate_email(email):
                return jsonify({'success': False, 'message': 'Please enter a valid email address'})
            if not password or len(password) < 3:
                return jsonify({'success': False, 'message': 'Password must be at least 3 characters'})
            if password != confirm_password:
                return jsonify({'success': False, 'message': 'Passwords do not match'})
            if User.query.filter_by(email=email).first():
                return jsonify({'success': False, 'message': 'Email already registered'})

            user = User(
                name=name,
                email=email,
                user_type=user_type,
                college=college,
                domain=domain,
                experience_years=experience_years,
                cgpa=cgpa,
                phone=phone,
                bio=bio,
                skills=skills,
                is_active=True,
                is_verified=False
            )
            user.set_password(password)

            # INSTANT INTERVIEW LINK: no waiting thread anymore.
            # As soon as the account is created, the interview is
            # scheduled AND live immediately, so the "Join LARA AI
            # Interview" button shows up on the dashboard right away.
            db.session.add(user)
            db.session.commit()

            user.meeting_scheduled = True
            user.meeting_start_time = datetime.utcnow()
            user.meeting_link = generate_meeting_link(user.id)
            user.meeting_live = True
            db.session.commit()

            create_notification(
                user.id,
                'Welcome to LARA AI!',
                'Your interview is ready right now. Click "Join LARA AI Interview" on your dashboard to begin.',
                'success',
                user.meeting_link
            )

            log_activity(user.id, 'register', 'New user registered')
            return jsonify({'success': True, 'message': 'Registration successful! Please login - your interview will be ready immediately.'})
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    return render_template_string(REGISTER_HTML)

@app.route('/logout')
def logout():
    if is_authenticated():
        log_activity(session['user_id'], 'logout', 'User logged out')
    session.clear()
    return '<script>window.location.href="/"</script>'

@app.route('/dashboard')
def dashboard():
    if not is_authenticated():
        return redirect('/login')
    user = get_current_user()
    if not user:
        return redirect('/login')
    stats = get_dashboard_stats(user.id)
    return render_template_string(DASHBOARD_HTML, user=user, stats=stats)

@app.route('/profile')
def profile():
    if not is_authenticated():
        return redirect('/login')
    user = get_current_user()
    if not user:
        return redirect('/login')
    return render_template_string(PROFILE_HTML, user=user)

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if not is_authenticated():
        return redirect('/login')
    user = get_current_user()
    if not user:
        return redirect('/login')
    if request.method == 'POST':
        user.name = sanitize_input(request.form.get('name'))
        user.college = sanitize_input(request.form.get('college'))
        user.domain = sanitize_input(request.form.get('domain'))
        user.experience_years = int(request.form.get('experience_years', 0) or 0)
        user.cgpa = float(request.form.get('cgpa', 0) or 0)
        user.phone = sanitize_input(request.form.get('phone'))
        user.bio = sanitize_input(request.form.get('bio'))
        user.skills = sanitize_input(request.form.get('skills'))
        db.session.commit()
        log_activity(user.id, 'edit_profile', 'Profile updated')
        return jsonify({'success': True, 'message': 'Profile updated successfully!'})
    return render_template_string(EDIT_PROFILE_HTML, user=user)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login_page():
    if is_authenticated():
        if is_admin():
            return redirect('/admin')
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, role='admin').first()
        if user and user.check_password(password):
            session.permanent = True
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_activity(user.id, 'admin_login', 'Admin logged in')
            return jsonify({'success': True, 'redirect': '/admin'})
        return jsonify({'success': False, 'message': 'Invalid admin credentials'})
    return render_template_string(ADMIN_LOGIN_HTML)

@app.route('/admin')
def admin():
    if not is_authenticated() or not is_admin():
        return redirect('/')
    users = User.query.order_by(User.created_at.desc()).all()
    non_admin_users = [u for u in users if u.role != 'admin']
    completed = [u for u in non_admin_users if u.interview_complete]
    stats = {
        'total_users': len(users),
        'completed_interviews': len(completed),
        'pending_interviews': len(non_admin_users) - len(completed),
        'avg_score': get_avg_score(non_admin_users),
        'pass_rate': get_pass_rate(non_admin_users),
    }
    return render_template_string(ADMIN_HTML, users=users, stats=stats)

@app.route('/admin/users')
def admin_users():
    if not is_authenticated() or not is_admin():
        return redirect('/')
    return admin()

@app.route('/admin/schedule')
def admin_schedule():
    if not is_authenticated() or not is_admin():
        return redirect('/')
    return admin()

@app.route('/admin/schedule/<int:user_id>')
def admin_schedule_user(user_id):
    if not is_authenticated() or not is_admin():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    user = User.query.get(user_id)
    if not user or user.role == 'admin':
        return jsonify({'success': False, 'message': 'User not found'})
    # Instant scheduling - no delay, interview is live immediately.
    user.meeting_scheduled = True
    user.meeting_start_time = datetime.utcnow()
    user.meeting_link = generate_meeting_link(user.id)
    user.meeting_live = True
    user.interview_complete = False
    user.final_score = 0
    user.passed = False
    db.session.commit()
    create_notification(user.id, 'Interview Live!', 'Your interview is now live. Click the link to join.', 'success', user.meeting_link)
    log_activity(session['user_id'], 'schedule_interview', f'Scheduled interview for user {user_id}')
    return jsonify({'success': True, 'message': 'Interview scheduled successfully!'})

@app.route('/interview')
def interview_home():
    if not is_authenticated():
        return redirect('/login')
    user = get_current_user()
    if not user:
        return redirect('/login')
    if user.meeting_live and user.meeting_link:
        return redirect(user.meeting_link)
    return render_template_string(INTERVIEW_HOME_HTML, user=user)

@app.route('/interview/<int:user_id>/<token>')
def interview_session(user_id, token):
    if not is_authenticated() or session['user_id'] != user_id:
        return redirect('/login')
    user = get_user_by_id(user_id)
    if not user or user.meeting_link != f"/interview/{user_id}/{token}":
        return redirect('/')
    if not user.meeting_live:
        return redirect('/interview')

    existing_session = InterviewSession.query.filter_by(
        user_id=user_id,
        is_active=True
    ).first()

    if existing_session:
        session['interview_questions'] = TAMIL_INTERVIEW_QUESTIONS
        session['interview_index'] = existing_session.current_question
        session['interview_answers'] = json.loads(existing_session.answers) if existing_session.answers else []
        session['camera_state'] = existing_session.camera_state
        session['interview_session_id'] = existing_session.session_id
    else:
        session_id = secrets.token_urlsafe(16)
        # Camera defaults OFF - user must explicitly turn it on.
        new_session = InterviewSession(
            user_id=user_id,
            session_id=session_id,
            current_question=0,
            answers=json.dumps([]),
            camera_state=False,
            mic_state=False,
            is_active=True
        )
        db.session.add(new_session)
        db.session.commit()

        session['interview_questions'] = TAMIL_INTERVIEW_QUESTIONS
        session['interview_index'] = 0
        session['interview_answers'] = []
        session['camera_state'] = False
        session['interview_session_id'] = session_id

    return redirect('/interview-session')

@app.route('/interview-session')
def interview_session_page():
    if not is_authenticated():
        return redirect('/login')
    if 'interview_index' not in session:
        return redirect('/interview')
    questions = session.get('interview_questions', [])
    index = session.get('interview_index', 0)
    if index >= len(questions):
        # All questions answered - score immediately and go straight
        # to the result screen (no extra waiting screen in between).
        answers = session.get('interview_answers', [])
        score, feedback = calculate_interview_score(answers)
        user = get_current_user()
        user.interview_complete = True
        user.final_score = score
        user.passed = score >= app.config['PASS_SCORE']
        user.meeting_live = False
        user.interview_date = datetime.utcnow()
        user.interview_feedback = '\n'.join(feedback)
        if user.passed:
            user.company_message = "🎉 Congratulations! You have passed the LARA AI interview! Welcome to the team!"
        else:
            user.company_message = "😔 Thank you for attending. Your score was below the passing mark this time - keep practicing and you'll do better!"
        if 'interview_session_id' in session:
            existing_session = InterviewSession.query.filter_by(
                session_id=session['interview_session_id']
            ).first()
            if existing_session:
                existing_session.is_active = False
                existing_session.completed_at = datetime.utcnow()
                db.session.commit()
        db.session.commit()
        for idx, ans in enumerate(answers):
            interview_ans = InterviewAnswer(
                user_id=user.id,
                question_index=idx,
                question=ans.get('question', ''),
                answer=ans.get('answer', ''),
                score=score // len(answers) if answers else 0
            )
            db.session.add(interview_ans)
        db.session.commit()
        create_notification(user.id, 'Interview Completed', f'Your interview is complete. Score: {score}%', 'success' if user.passed else 'info')
        log_activity(user.id, 'interview_complete', f'Interview completed with score {score}')
        session.pop('interview_questions', None)
        session.pop('interview_index', None)
        session.pop('interview_answers', None)
        session.pop('camera_state', None)
        session.pop('interview_session_id', None)
        return redirect('/result')
    camera_state = session.get('camera_state', False)
    current_q = questions[index]
    return render_template_string(INTERVIEW_SESSION_HTML,
                                 question=current_q,
                                 index=index + 1,
                                 total=len(questions),
                                 camera_state=camera_state)

@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    if not is_authenticated():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    answer = request.form.get('answer', '')
    camera_state = request.form.get('camera_state', 'false') == 'true'
    session['camera_state'] = camera_state
    if 'interview_session_id' in session:
        existing_session = InterviewSession.query.filter_by(
            session_id=session['interview_session_id']
        ).first()
        if existing_session:
            existing_session.camera_state = camera_state
            db.session.commit()
    if 'interview_answers' not in session:
        session['interview_answers'] = []
    questions = session.get('interview_questions', [])
    index = session.get('interview_index', 0)
    if index < len(questions):
        answers_list = session['interview_answers']
        answers_list.append({
            'question': questions[index]['tamil'],
            'answer': answer
        })
        session['interview_answers'] = answers_list
        session['interview_index'] = index + 1
        if 'interview_session_id' in session:
            existing_session = InterviewSession.query.filter_by(
                session_id=session['interview_session_id']
            ).first()
            if existing_session:
                existing_session.current_question = session['interview_index']
                existing_session.answers = json.dumps(session['interview_answers'])
                db.session.commit()
    return jsonify({'success': True, 'redirect': '/interview-session'})

@app.route('/result')
def interview_result():
    if not is_authenticated():
        return redirect('/login')
    user = get_current_user()
    if not user:
        return redirect('/login')
    return render_template_string(RESULT_HTML, user=user)

@app.route('/notifications')
def notifications():
    if not is_authenticated():
        return redirect('/login')
    notifications_list = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).all()
    for n in notifications_list:
        if not n.is_read:
            n.is_read = True
            n.read_at = datetime.utcnow()
    db.session.commit()
    return render_template_string(NOTIFICATIONS_HTML, notifications=notifications_list)

@app.route('/api/user')
def api_user():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    user = get_current_user()
    return jsonify(user.to_dict() if user else {})

@app.route('/api/stats')
def api_stats():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    stats = get_dashboard_stats(session['user_id'])
    return jsonify(stats)

@app.route('/api/camera-state', methods=['POST'])
def api_camera_state():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    camera_state = data.get('camera_state', False)
    session['camera_state'] = camera_state
    if 'interview_session_id' in session:
        existing_session = InterviewSession.query.filter_by(
            session_id=session['interview_session_id']
        ).first()
        if existing_session:
            existing_session.camera_state = camera_state
            db.session.commit()
    return jsonify({'success': True, 'camera_state': camera_state})

@app.route('/api/camera-state', methods=['GET'])
def api_get_camera_state():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    camera_state = session.get('camera_state', False)
    return jsonify({'camera_state': camera_state})

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email'))
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'Email not found'})
        token = generate_verification_token()
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password reset link sent to your email'})
    return render_template_string('''
    <!DOCTYPE html>
    <html><head><title>Forgot Password</title></head>
    <body><h2>Forgot Password</h2>
    <form id="forgotForm"><input type="email" name="email" placeholder="Email" required>
    <button type="submit">Send Reset Link</button></form>
    <script>
    document.getElementById('forgotForm').addEventListener('submit', async function(e){
        e.preventDefault();
        const formData=new FormData(this);
        const response=await fetch('/forgot-password',{method:'POST',body:formData});
        const data=await response.json();
        alert(data.message);
    });
    </script></body></html>
    ''')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expiry < datetime.utcnow():
        return 'Invalid or expired token'
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if password != confirm:
            return jsonify({'success': False, 'message': 'Passwords do not match'})
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password reset successfully'})
    return '''
    <!DOCTYPE html>
    <html><head><title>Reset Password</title></head>
    <body><h2>Reset Password</h2>
    <form method="POST"><input type="password" name="password" placeholder="New Password" required>
    <input type="password" name="confirm_password" placeholder="Confirm Password" required>
    <button type="submit">Reset Password</button></form></body></html>
    '''

@app.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        return 'Invalid verification token'
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    return 'Email verified successfully! You can now login.'

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(e):
    return '''
    <html><body style="background:#0a0a0f;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;text-align:center;">
    <div><h1 style="font-size:80px;font-family:monospace;">404</h1><p>Page not found</p>
    <a href="/" style="color:#667eea;text-decoration:none;font-family:monospace;">← Go Home</a></div>
    </body></html>
    ''', 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return '''
    <html><body style="background:#0a0a0f;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;text-align:center;">
    <div><h1 style="font-size:80px;font-family:monospace;">500</h1><p>Something went wrong</p>
    <a href="/" style="color:#667eea;text-decoration:none;font-family:monospace;">← Go Home</a></div>
    </body></html>
    ''', 500

# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@demo.com').first():
            admin_user = User(
                name='Admin',
                email='admin@demo.com',
                user_type='professional',
                domain='Administration',
                role='admin',
                bio='System Administrator',
                skills='Python, Flask, SQL, Leadership',
                is_verified=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            logger.info("Admin user created: admin@demo.com / admin123")
        if not User.query.filter_by(email='user@demo.com').first():
            demo_user = User(
                name='Demo User',
                email='user@demo.com',
                user_type='student',
                domain='Technology',
                college='ABC University',
                bio='Passionate learner with interest in AI and technology',
                skills='Python, Flask, SQL, JavaScript',
                phone='+91 9876543210',
                is_verified=True
            )
            demo_user.set_password('123')
            db.session.add(demo_user)
            logger.info("Demo user created: user@demo.com / 123")
        db.session.commit()

try:
    init_db()
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == '__main__':
    print("="*70)
    print("🎯 LARA AI - Mock Interview Platform")
    print("📍 Local URL: http://localhost:5000")
    print("🌐 Official Domain: www.aimockintr.com")
    print("📝 Demo Credentials:")
    print("   👤 User:  user@demo.com / 123")
    print("   👑 Admin: admin@demo.com / admin123")
    print("📋 Total Questions: 10")
    print("="*70)
    print("🚀 Starting server on http://localhost:5000")
    print("="*70)
    app.run(debug=True, host='0.0.0.0', port=5000)