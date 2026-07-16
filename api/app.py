import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template_string, request, session, jsonify, redirect, url_for
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "super_secret_key_2024"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

os.makedirs('uploads', exist_ok=True)
os.makedirs('static', exist_ok=True)

# Database
users = {}

# Default Admin
users[1] = {
    "id": 1,
    "name": "Admin",
    "email": "admin@demo.com",
    "password": "admin123",
    "role": "admin",
    "user_type": "admin",
    "registration_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "last_login": "",
    "college": "",
    "domain": "",
    "experience_years": 0,
    "cgpa": 0,
    "resume_path": "",
    "meeting_scheduled": False,
    "meeting_start_time": None,
    "meeting_link": None,
    "meeting_live": False,
    "interview_complete": False,
    "final_score": 0,
    "passed": False,
    "company_message": ""
}

# Default User
users[2] = {
    "id": 2,
    "name": "Demo User",
    "email": "user@demo.com",
    "password": "123",
    "role": "user",
    "user_type": "student",
    "registration_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "last_login": "",
    "college": "ABC College",
    "domain": "Software Development",
    "experience_years": 0,
    "cgpa": 8.5,
    "resume_path": "",
    "meeting_scheduled": False,
    "meeting_start_time": None,
    "meeting_link": None,
    "meeting_live": False,
    "interview_complete": False,
    "final_score": 0,
    "passed": False,
    "company_message": ""
}

# LARA AI Tamil Questions
TAMIL_QUESTIONS = [
    {"tamil": "வணக்கம்! உங்களைப் பற்றி சொல்லுங்கள்?", "english": "Tell me about yourself", "time": 60},
    {"tamil": "உங்கள் கல்வி மற்றும் வேலை அனுபவம் பற்றி சொல்லுங்கள்?", "english": "Tell about your education and experience", "time": 60},
    {"tamil": "இந்த துறையில் நீங்கள் ஏன் வெற்றி பெற முடியும்?", "english": "Why will you succeed in this field?", "time": 60},
    {"tamil": "உங்கள் பலம் மற்றும் பலவீனங்கள் என்ன?", "english": "What are your strengths and weaknesses?", "time": 60},
    {"tamil": "எங்கள் நிறுவனத்தில் நீங்கள் என்ன மாற்றம் கொண்டு வர முடியும்?", "english": "What change can you bring to our company?", "time": 60}
]

# ========================================================
# LANDING PAGE WITH FEATURE MODALS
# ========================================================
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
        .hero-logo{font-size:72px;font-weight:900;font-family:'Orbitron',monospace;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb,#48bb78);-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:gradient 6s ease infinite;background-size:300% 300%;}
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
        .feature-card{background:rgba(255,255,255,0.03);border-radius:24px;padding:30px;border:1px solid rgba(255,255,255,0.06);transition:0.5s;cursor:pointer;text-align:center;}
        .feature-card:hover{transform:translateY(-10px);border-color:#667eea;box-shadow:0 20px 60px rgba(102,126,234,0.05);}
        .feature-card .icon{font-size:48px;margin-bottom:15px;transition:0.3s;}
        .feature-card:hover .icon{transform:scale(1.1);}
        .feature-card h3{font-size:18px;font-family:'Orbitron',monospace;letter-spacing:1px;margin-bottom:10px;color:#fff;}
        .feature-card p{font-size:14px;color:rgba(255,255,255,0.4);line-height:1.6;}
        .feature-card .click-hint{font-size:10px;color:rgba(255,255,255,0.15);margin-top:12px;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .footer{position:relative;z-index:1;text-align:center;padding:40px 20px;border-top:1px solid rgba(255,255,255,0.04);}
        .footer p{font-size:12px;color:rgba(255,255,255,0.15);font-family:'Orbitron',monospace;letter-spacing:2px;}
        @media(max-width:768px){.hero-logo{font-size:36px;}.hero-sub{font-size:14px;}.features h2{font-size:24px;}}

        /* ===== MODAL STYLES ===== */
        .modal-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);backdrop-filter:blur(20px);z-index:9999;display:none;align-items:center;justify-content:center;padding:20px;animation:fadeIn 0.3s ease;}
        .modal-overlay.active{display:flex;}
        .modal-box{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:28px;max-width:750px;width:100%;max-height:90vh;overflow-y:auto;padding:45px;position:relative;animation:slideUp 0.4s ease;}
        .modal-box::-webkit-scrollbar{width:4px;}
        .modal-box::-webkit-scrollbar-track{background:transparent;}
        .modal-box::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.1);border-radius:10px;}
        .modal-close{position:sticky;top:0;float:right;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.04);color:#fff;width:44px;height:44px;border-radius:50%;font-size:20px;cursor:pointer;transition:0.3s;display:flex;align-items:center;justify-content:center;z-index:10;}
        .modal-close:hover{background:#ff6b6b;border-color:#ff6b6b;transform:rotate(90deg);}
        .modal-icon{font-size:64px;text-align:center;margin:10px 0 20px 0;}
        .modal-title{font-size:28px;font-weight:700;font-family:'Orbitron',monospace;letter-spacing:1px;text-align:center;background:linear-gradient(135deg,#fff,#888);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:20px;}
        .modal-section{margin:20px 0;padding:18px 20px;background:rgba(255,255,255,0.02);border-radius:16px;border-left:3px solid #667eea;}
        .modal-section h4{font-size:14px;font-weight:600;color:#667eea;font-family:'Orbitron',monospace;letter-spacing:0.5px;margin-bottom:8px;}
        .modal-section p{font-size:14px;color:rgba(255,255,255,0.7);line-height:1.8;}
        .modal-section ul{list-style:none;padding:0;margin:5px 0;}
        .modal-section ul li{padding:6px 0 6px 24px;position:relative;font-size:13px;color:rgba(255,255,255,0.6);line-height:1.6;}
        .modal-section ul li::before{content:"▸";position:absolute;left:0;color:#667eea;font-weight:bold;}
        .modal-tags{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0;}
        .modal-tag{background:rgba(255,255,255,0.03);padding:4px 14px;border-radius:30px;font-size:10px;color:rgba(255,255,255,0.4);border:1px solid rgba(255,255,255,0.03);font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .modal-tag.green{color:#48bb78;border-color:rgba(72,187,120,0.06);background:rgba(72,187,120,0.03);}
        .modal-tag.blue{color:#667eea;border-color:rgba(102,126,234,0.06);background:rgba(102,126,234,0.03);}
        .modal-tag.purple{color:#764ba2;border-color:rgba(118,75,162,0.06);background:rgba(118,75,162,0.03);}
        @keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
        @keyframes slideUp{from{opacity:0;transform:translateY(30px);}to{opacity:1;transform:translateY(0);}}
        @media(max-width:600px){.modal-box{padding:25px;}.modal-title{font-size:22px;}.modal-section{padding:14px 16px;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="bg-orb"></div><div class="bg-orb"></div><div class="bg-orb"></div><div class="bg-orb"></div>

<!-- ===== HERO SECTION ===== -->
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

<!-- ===== FEATURES SECTION ===== -->
<div class="features">
    <h2>Why LARA AI?</h2>
    <div class="features-grid">
        <!-- Feature 1: AI-Powered Interviews -->
        <div class="feature-card" onclick="openModal('ai')">
            <div class="icon">🤖</div>
            <h3>AI-Powered Interviews</h3>
            <p>Experience realistic interviews with LARA AI that adapts to your responses in real-time.</p>
            <div class="click-hint"><i class="fas fa-hand-pointer"></i> Click to learn more</div>
        </div>

        <!-- Feature 2: Tamil Interview Mode -->
        <div class="feature-card" onclick="openModal('tamil')">
            <div class="icon">🎙️</div>
            <h3>Tamil Interview Mode</h3>
            <p>Practice in your native language. LARA AI conducts interviews in Tamil for better understanding.</p>
            <div class="click-hint"><i class="fas fa-hand-pointer"></i> Click to learn more</div>
        </div>

        <!-- Feature 3: Instant Scoring -->
        <div class="feature-card" onclick="openModal('scoring')">
            <div class="icon">📊</div>
            <h3>Instant Scoring</h3>
            <p>Get immediate feedback with detailed scoring on technical skills, communication, and confidence.</p>
            <div class="click-hint"><i class="fas fa-hand-pointer"></i> Click to learn more</div>
        </div>

        <!-- Feature 4: Camera & Mic Support -->
        <div class="feature-card" onclick="openModal('camera')">
            <div class="icon">🎥</div>
            <h3>Camera & Mic Support</h3>
            <p>Real interview simulation with camera and microphone integration for a complete experience.</p>
            <div class="click-hint"><i class="fas fa-hand-pointer"></i> Click to learn more</div>
        </div>

        <!-- Feature 5: Performance Analytics -->
        <div class="feature-card" onclick="openModal('analytics')">
            <div class="icon">📈</div>
            <h3>Performance Analytics</h3>
            <p>Track your progress with detailed analytics and identify areas for improvement.</p>
            <div class="click-hint"><i class="fas fa-hand-pointer"></i> Click to learn more</div>
        </div>

        <!-- Feature 6: Enterprise Ready -->
        <div class="feature-card" onclick="openModal('enterprise')">
            <div class="icon">🏢</div>
            <h3>Enterprise Ready</h3>
            <p>Built for colleges, placement cells, and recruitment agencies with admin dashboard.</p>
            <div class="click-hint"><i class="fas fa-hand-pointer"></i> Click to learn more</div>
        </div>
    </div>
</div>

<div class="footer"><p>© 2026 LARA AI Mock Interview Platform • Powered by Artificial Intelligence</p></div>

<!-- ===== MODAL OVERLAY ===== -->
<div class="modal-overlay" id="featureModal" onclick="closeModalOutside(event)">
    <div class="modal-box" id="modalContent">
        <button class="modal-close" onclick="closeModal()"><i class="fas fa-times"></i></button>
        <div id="modalBody"></div>
    </div>
</div>

<script>
    // ===== FEATURE DATA =====
    const featureData = {
        'ai': {
            icon: '🤖',
            title: 'AI-Powered Interviews',
            description: 'LARA AI uses advanced artificial intelligence to conduct realistic interview simulations. The AI adapts to your responses in real-time, asking follow-up questions and evaluating your answers just like a human interviewer would.',
            howItWorks: [
                'AI analyzes your response content and quality',
                'Follow-up questions generated based on your answers',
                'Real-time evaluation of your communication skills',
                'Adaptive difficulty based on your performance'
            ],
            forCandidates: 'Practice in a stress-free environment. Get comfortable with AI interviews that feel real. Receive instant feedback and improve your skills before the actual interview.',
            forRecruiters: 'Screen candidates efficiently. AI-powered interviews can be conducted at scale. Get standardized evaluations across all candidates.',
            keyFeatures: ['Real-time adaptation', 'Natural language processing', 'Behavioral analysis', 'Voice tone detection'],
            tags: ['🧠 AI Powered', '⚡ Real-time', '🎯 Adaptive']
        },
        'tamil': {
            icon: '🎙️',
            title: 'Tamil Interview Mode',
            description: 'LARA AI is the first platform to offer full Tamil language interview practice. Conduct your entire interview in Tamil, the language you are most comfortable with.',
            howItWorks: [
                'AI understands Tamil speech and text',
                'Questions are asked in Tamil',
                'Your answers are evaluated in Tamil context',
                'Tamil cultural nuances are considered'
            ],
            forCandidates: 'Build confidence by practicing in your mother tongue. Express yourself freely without language barriers. Perfect for Tamil-speaking professionals.',
            forRecruiters: 'Assess candidates in their native language. Get more authentic responses and better evaluate communication skills.',
            keyFeatures: ['Tamil speech recognition', 'Tamil language processing', 'Cultural sensitivity', 'Regional language support'],
            tags: ['🎯 Tamil', '🌏 Regional', '🗣️ Native Language']
        },
        'scoring': {
            icon: '📊',
            title: 'Instant Scoring System',
            description: 'Get immediate, detailed feedback on your interview performance. LARA AI scores you on multiple parameters and provides actionable insights.',
            howItWorks: [
                'AI evaluates your answers in real-time',
                'Multiple scoring parameters analyzed',
                'Detailed breakdown of your strengths',
                'Areas for improvement highlighted'
            ],
            forCandidates: 'Know exactly where you stand. Understand your strengths and weaknesses. Get actionable feedback to improve your interview skills.',
            forRecruiters: 'Objective scoring eliminates bias. Standardized evaluation across all candidates. Quick identification of top performers.',
            keyFeatures: ['Multi-parameter scoring', 'Real-time feedback', 'Detailed analytics', 'Progress tracking'],
            tags: ['📈 Scoring', '⚡ Instant', '📊 Analytics']
        },
        'camera': {
            icon: '🎥',
            title: 'Camera & Mic Support',
            description: 'Experience a complete interview simulation with full camera and microphone integration. Practice your body language, confidence, and verbal communication.',
            howItWorks: [
                'Video recording of your interview',
                'Audio analysis of your voice',
                'Body language tracking',
                'Confidence level assessment'
            ],
            forCandidates: 'Practice your non-verbal communication. Get comfortable on camera. Improve your confidence and presentation skills.',
            forRecruiters: 'Assess candidates holistically. Evaluate both verbal and non-verbal communication. Record interviews for team review.',
            keyFeatures: ['Video recording', 'Audio analysis', 'Body language tracking', 'Confidence scoring'],
            tags: ['🎥 Video', '🎤 Audio', '📹 Recording']
        },
        'analytics': {
            icon: '📈',
            title: 'Performance Analytics',
            description: 'Track your progress over time with detailed performance analytics. Identify patterns, track improvements, and focus on areas that need attention.',
            howItWorks: [
                'Track performance across multiple interviews',
                'Identify improvement areas',
                'Compare scores over time',
                'Get personalized recommendations'
            ],
            forCandidates: 'Monitor your progress and growth. See which areas you have improved. Focus on your weak points with targeted practice.',
            forRecruiters: 'Track candidate progress over time. Identify consistent performers. Make data-driven decisions.',
            keyFeatures: ['Progress tracking', 'Performance trends', 'Personalized insights', 'Goal setting'],
            tags: ['📈 Analytics', '📊 Trends', '🎯 Goals']
        },
        'enterprise': {
            icon: '🏢',
            title: 'Enterprise Ready',
            description: 'LARA AI is built for organizations of all sizes. From colleges to recruitment agencies, our platform scales to meet your needs with comprehensive admin controls.',
            howItWorks: [
                'Admin dashboard for management',
                'Bulk candidate scheduling',
                'Custom interview templates',
                'Organization-wide analytics'
            ],
            forCandidates: 'Get access to professional interview practice. Prepare for actual job interviews with enterprise-grade tools.',
            forRecruiters: 'Streamline your hiring process. Conduct interviews at scale. Get standardized evaluations across all candidates.',
            keyFeatures: ['Admin dashboard', 'Bulk scheduling', 'Custom templates', 'Organization analytics'],
            tags: ['🏢 Enterprise', '👔 Professional', '📋 Admin']
        }
    };

    // ===== MODAL FUNCTIONS =====
    function openModal(featureKey) {
        const data = featureData[featureKey];
        if (!data) return;

        const modal = document.getElementById('featureModal');
        const body = document.getElementById('modalBody');

        body.innerHTML = `
            <div class="modal-icon">${data.icon}</div>
            <h2 class="modal-title">${data.title}</h2>
            
            <div class="modal-tags">
                ${data.tags.map(tag => `<span class="modal-tag">${tag}</span>`).join('')}
            </div>

            <div class="modal-section">
                <h4><i class="fas fa-info-circle"></i> Overview</h4>
                <p>${data.description}</p>
            </div>

            <div class="modal-section">
                <h4><i class="fas fa-cogs"></i> How It Works</h4>
                <ul>
                    ${data.howItWorks.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                <div class="modal-section" style="border-left-color:#48bb78;">
                    <h4 style="color:#48bb78;"><i class="fas fa-user-graduate"></i> For Candidates</h4>
                    <p>${data.forCandidates}</p>
                </div>
                <div class="modal-section" style="border-left-color:#ff6b6b;">
                    <h4 style="color:#ff6b6b;"><i class="fas fa-building"></i> For Recruiters</h4>
                    <p>${data.forRecruiters}</p>
                </div>
            </div>

            <div class="modal-section" style="border-left-color:#fdcb6e;">
                <h4 style="color:#fdcb6e;"><i class="fas fa-star"></i> Key Features</h4>
                <ul>
                    ${data.keyFeatures.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>

            <div style="text-align:center;margin-top:20px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.03);">
                <span style="font-size:11px;color:rgba(255,255,255,0.2);font-family:'Orbitron',monospace;letter-spacing:1px;">
                    <i class="fas fa-robot"></i> LARA AI • Click outside to close
                </span>
            </div>
        `;

        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        document.getElementById('featureModal').classList.remove('active');
        document.body.style.overflow = '';
    }

    function closeModalOutside(event) {
        if (event.target === document.getElementById('featureModal')) {
            closeModal();
        }
    }

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeModal();
    });
</script>
</body>
</html>
'''

# ========================================================
# USER LOGIN PAGE
# ========================================================
USER_LOGIN_HTML = '''
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
        .logo i{font-size:30px;}
        .sub{text-align:center;color:#48bb78;margin:10px 0 30px 0;font-size:13px;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .sub i{color:#48bb78;}
        input{width:100%;padding:14px;margin:10px 0;border:1px solid rgba(255,255,255,0.04);border-radius:14px;font-size:14px;transition:0.3s;background:rgba(255,255,255,0.02);color:#fff;font-family:'Inter',sans-serif;}
        input:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.04);}
        input::placeholder{color:rgba(255,255,255,0.3);}
        button{width:100%;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;padding:14px;border-radius:14px;font-size:15px;cursor:pointer;transition:0.5s;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;}
        button:hover{transform:translateY(-3px);box-shadow:0 10px 40px rgba(102,126,234,0.08);}
        .links{text-align:center;margin-top:18px;color:#ffffff;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .links a{color:#667eea;text-decoration:none;font-weight:500;}
        .links a:hover{color:#764ba2;}
        .demo{background:rgba(255,255,255,0.01);padding:15px;border-radius:14px;margin-top:20px;border:1px solid rgba(255,255,255,0.02);font-size:11px;color:#ffffff;text-align:center;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .demo strong{color:#48bb78;}
        .back-btn{display:inline-block;margin-top:15px;color:#ffffff;text-decoration:none;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .back-btn i{color:#667eea;}
        .back-btn:hover{color:#667eea;}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="container">
    <div class="card">
        <div class="logo"><i class="fas fa-user"></i> User Login</div>
        <div class="sub"><i class="fas fa-user-check"></i> Candidate / Student Access</div>
        <form method="POST" action="/user-login">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit"><i class="fas fa-sign-in-alt"></i> Login</button>
        </form>
        <div class="links"><a href="/register"><i class="fas fa-user-plus"></i> New User? Register</a></div>
        <div class="demo"><strong>Demo User:</strong> user@demo.com / 123</div>
        <div style="text-align:center;"><a href="/" class="back-btn"><i class="fas fa-arrow-left"></i> Back to Home</a></div>
    </div>
</div>
</body>
</html>
'''

# ========================================================
# ADMIN LOGIN PAGE
# ========================================================
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
        .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 40%,rgba(255,107,107,0.05),transparent 50%),radial-gradient(ellipse at 70% 60%,rgba(118,75,162,0.04),transparent 50%);pointer-events:none;}
        .container{position:relative;z-index:1;max-width:420px;width:100%;}
        .card{background:rgba(255,255,255,0.02);backdrop-filter:blur(40px);border-radius:24px;padding:40px;border:1px solid rgba(255,255,255,0.04);border-top:3px solid #ff6b6b;}
        .logo{text-align:center;font-size:26px;font-weight:900;background:linear-gradient(135deg,#ff6b6b,#ee5a24);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Orbitron',monospace;letter-spacing:2px;}
        .logo i{font-size:30px;}
        .sub{text-align:center;color:#ff6b6b;margin:10px 0 30px 0;font-size:13px;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .sub i{color:#ff6b6b;}
        input{width:100%;padding:14px;margin:10px 0;border:1px solid rgba(255,255,255,0.04);border-radius:14px;font-size:14px;transition:0.3s;background:rgba(255,255,255,0.02);color:#fff;font-family:'Inter',sans-serif;}
        input:focus{outline:none;border-color:#ff6b6b;box-shadow:0 0 0 3px rgba(255,107,107,0.04);}
        input::placeholder{color:rgba(255,255,255,0.3);}
        button{width:100%;background:linear-gradient(135deg,#ff6b6b,#ee5a24);color:#fff;border:none;padding:14px;border-radius:14px;font-size:15px;cursor:pointer;transition:0.5s;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;}
        button:hover{transform:translateY(-3px);box-shadow:0 10px 40px rgba(255,107,107,0.08);}
        .demo{background:rgba(255,255,255,0.01);padding:15px;border-radius:14px;margin-top:20px;border:1px solid rgba(255,255,255,0.02);font-size:11px;color:#ffffff;text-align:center;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .demo strong{color:#ff6b6b;}
        .back-btn{display:inline-block;margin-top:15px;color:#ffffff;text-decoration:none;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .back-btn i{color:#ff6b6b;}
        .back-btn:hover{color:#ff6b6b;}
        .admin-badge{display:inline-block;background:rgba(255,107,107,0.06);padding:4px 14px;border-radius:30px;font-size:9px;color:#ff6b6b;border:1px solid rgba(255,107,107,0.06);font-family:'Orbitron',monospace;letter-spacing:1px;margin-top:5px;}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="container">
    <div class="card">
        <div class="logo"><i class="fas fa-shield-alt"></i> Admin Login</div>
        <div class="sub"><i class="fas fa-lock"></i> Administrator Access</div>
        <div style="text-align:center;"><span class="admin-badge"><i class="fas fa-crown"></i> ADMIN PANEL</span></div>
        <form method="POST" action="/admin-login">
            <input type="email" name="email" placeholder="Admin Email" required>
            <input type="password" name="password" placeholder="Admin Password" required>
            <button type="submit"><i class="fas fa-sign-in-alt"></i> Admin Login</button>
        </form>
        <div class="demo"><strong>Admin Demo:</strong> admin@demo.com / admin123</div>
        <div style="text-align:center;"><a href="/" class="back-btn"><i class="fas fa-arrow-left"></i> Back to Home</a></div>
    </div>
</div>
</body>
</html>
'''

# ========================================================
# ADMIN PANEL HTML
# ========================================================
ADMIN_HTML = '''
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LARA AI - Admin</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;color:#fff;overflow-x:hidden;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.02) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 20%,rgba(255,107,107,0.06),transparent 60%),radial-gradient(ellipse at 70% 80%,rgba(118,75,162,0.04),transparent 60%);pointer-events:none;}
        .bg-orb{position:fixed;border-radius:50%;filter:blur(120px);animation:floatOrb 30s infinite ease-in-out;pointer-events:none;}
        .bg-orb:nth-child(1){width:600px;height:600px;background:#ff6b6b;top:-200px;right:-100px;opacity:0.06;animation-delay:0s;}
        .bg-orb:nth-child(2){width:500px;height:500px;background:#764ba2;bottom:-150px;left:-100px;opacity:0.05;animation-delay:12s;}
        .bg-orb:nth-child(3){width:400px;height:400px;background:#f093fb;top:40%;left:40%;opacity:0.04;animation-delay:24s;}
        @keyframes floatOrb{0%,100%{transform:translate(0,0) scale(1);}33%{transform:translate(80px,-60px) scale(1.2);}66%{transform:translate(-60px,40px) scale(0.8);}}
        .admin-container{position:relative;z-index:1;max-width:1400px;margin:0 auto;padding:20px;}
        .admin-header{background:rgba(255,255,255,0.03);backdrop-filter:blur(40px);border-radius:20px;padding:20px 30px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center;border:1px solid rgba(255,255,255,0.04);}
        .admin-logo{font-size:24px;font-weight:900;font-family:'Orbitron',monospace;background:linear-gradient(135deg,#ff6b6b,#ee5a24);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:2px;}
        .admin-logo span{background:linear-gradient(135deg,#48bb78,#38a169);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
        .admin-nav{display:flex;gap:8px;flex-wrap:wrap;}
        .admin-nav a{color:#ffffff;text-decoration:none;padding:10px 20px;border-radius:12px;transition:0.4s;font-weight:500;font-size:12px;border:1px solid rgba(255,255,255,0.06);display:flex;align-items:center;gap:8px;font-family:'Orbitron',monospace;letter-spacing:0.5px;background:rgba(255,255,255,0.02);}
        .admin-nav a:hover{background:rgba(255,255,255,0.06);color:#fff;border-color:rgba(255,255,255,0.1);}
        .admin-nav a.active{background:linear-gradient(135deg,#ff6b6b,#ee5a24);color:#fff;border-color:transparent;box-shadow:0 8px 40px rgba(255,107,107,0.15);}
        .admin-nav .logout-btn{background:rgba(255,0,0,0.06);color:#ff6b6b;border:1px solid rgba(255,0,0,0.06);}
        .admin-nav .logout-btn:hover{background:#ff6b6b;color:#fff;border-color:#ff6b6b;box-shadow:0 8px 40px rgba(255,107,107,0.15);}
        .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:20px;margin-bottom:30px;}
        .stat-card{background:rgba(255,255,255,0.02);backdrop-filter:blur(20px);border-radius:16px;padding:22px;border:1px solid rgba(255,255,255,0.04);transition:0.4s;position:relative;overflow:hidden;}
        .stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#ff6b6b,#ee5a24);opacity:0;transition:0.4s;}
        .stat-card:hover::before{opacity:1;}
        .stat-card:hover{transform:translateY(-6px);border-color:rgba(255,107,107,0.1);box-shadow:0 20px 60px rgba(0,0,0,0.2);}
        .stat-label{font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#ffffff;font-weight:600;font-family:'Orbitron',monospace;}
        .stat-number{font-size:36px;font-weight:900;margin:5px 0;color:#ffffff;font-family:'Orbitron',monospace;text-shadow:0 0 30px rgba(255,255,255,0.05);}
        .stat-icon{font-size:18px;opacity:0.08;position:absolute;right:20px;top:20px;}
        .table-card{background:rgba(255,255,255,0.02);backdrop-filter:blur(20px);border-radius:16px;padding:25px;border:1px solid rgba(255,255,255,0.04);overflow-x:auto;}
        .table-title{font-size:14px;font-weight:600;margin-bottom:20px;color:#ffffff;display:flex;align-items:center;gap:10px;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .table-title i{color:#ff6b6b;}
        .table-title .count{font-size:11px;font-weight:400;color:#ffffff;}
        table{width:100%;border-collapse:collapse;}
        th{color:#ffffff;padding:14px;text-align:left;border-bottom:2px solid rgba(255,255,255,0.03);font-weight:600;font-size:9px;text-transform:uppercase;letter-spacing:1.5px;font-family:'Orbitron',monospace;}
        td{color:#ffffff;padding:14px;border-bottom:1px solid rgba(255,255,255,0.02);font-size:12px;}
        tr:hover{background:rgba(255,255,255,0.02);}
        .badge{padding:4px 14px;border-radius:30px;font-size:9px;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .badge-success{background:rgba(72,187,120,0.08);color:#48bb78;border:1px solid rgba(72,187,120,0.06);}
        .badge-danger{background:rgba(255,107,107,0.08);color:#ff6b6b;border:1px solid rgba(255,107,107,0.06);}
        .badge-warning{background:rgba(253,203,110,0.08);color:#fdcb6e;border:1px solid rgba(253,203,110,0.06);}
        .badge-info{background:rgba(99,179,237,0.08);color:#63b3ed;border:1px solid rgba(99,179,237,0.06);}
        .badge-gray{background:rgba(255,255,255,0.04);color:#ffffff;border:1px solid rgba(255,255,255,0.03);}
        .btn-sm{background:linear-gradient(135deg,#ff6b6b,#ee5a24);color:#fff;border:none;padding:5px 14px;border-radius:8px;cursor:pointer;font-weight:600;font-size:10px;transition:0.3s;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .btn-sm:hover{transform:scale(1.05);box-shadow:0 8px 30px rgba(255,107,107,0.1);}
        .btn-sm.green{background:linear-gradient(135deg,#48bb78,#38a169);}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
        @media(max-width:768px){.admin-header{flex-direction:column;gap:15px;}.admin-nav{justify-content:center;}.stats-grid{grid-template-columns:1fr 1fr;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="bg-orb"></div><div class="bg-orb"></div><div class="bg-orb"></div>
<div class="admin-container">
    <div class="admin-header">
        <div class="admin-logo">🎯 LARA <span>Admin</span></div>
        <div class="admin-nav">
            <a href="/admin" class="active"><i class="fas fa-chart-pie"></i> Dashboard</a>
            <a href="/admin/users"><i class="fas fa-users"></i> Users</a>
            <a href="/admin/schedule"><i class="fas fa-calendar-plus"></i> Schedule</a>
            <a href="/logout" class="logout-btn"><i class="fas fa-sign-out-alt"></i> Logout</a>
        </div>
    </div>
    <div class="stats-grid">
        <div class="stat-card"><i class="fas fa-users stat-icon"></i><div class="stat-label">Total Users</div><div class="stat-number">{{ users|length }}</div></div>
        <div class="stat-card"><i class="fas fa-check-circle stat-icon"></i><div class="stat-label">✅ Passed</div><div class="stat-number">{{ passed_count }}</div></div>
        <div class="stat-card"><i class="fas fa-times-circle stat-icon"></i><div class="stat-label">❌ Failed</div><div class="stat-number">{{ failed_count }}</div></div>
        <div class="stat-card"><i class="fas fa-chart-line stat-icon"></i><div class="stat-label">📈 Avg Score</div><div class="stat-number">{{ avg_score }}%</div></div>
    </div>
    <div class="table-card">
        <div class="table-title"><i class="fas fa-list"></i> All Users <span class="count">({{ users|length }} users)</span></div>
        <table>
            <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Type</th><th>Domain</th><th>Exp</th><th>Status</th><th>Score</th><th>Action</th></tr></thead>
            <tbody>
                {% for u in users.values() %}
                <tr>
                    <td>{{ u.id }}</td><td>{{ u.name }}</td><td>{{ u.email }}</td>
                    <td>{% if u.user_type == 'student' %}🎓{% elif u.user_type == 'admin' %}👑{% else %}💼{% endif %}</td>
                    <td>{{ u.domain or '-' }}</td><td>{{ u.experience_years or 0 }}y</td>
                    <td>
                        {% if u.interview_complete %}
                            {% if u.passed %}<span class="badge badge-success">✅ Passed</span>
                            {% else %}<span class="badge badge-danger">❌ Failed</span>{% endif %}
                        {% elif u.meeting_live %}<span class="badge badge-warning">🔴 Live</span>
                        {% elif u.meeting_scheduled %}<span class="badge badge-info">⏳ Scheduled</span>
                        {% else %}<span class="badge badge-gray">Pending</span>{% endif %}
                    </td>
                    <td>{% if u.final_score %}{{ u.final_score }}%{% else %}-{% endif %}</td>
                    <td>
                        {% if not u.interview_complete and u.id != 1 %}
                            <a href="/admin/schedule/{{ u.id }}"><button class="btn-sm green">Schedule</button></a>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>
'''

# ========================================================
# USER DASHBOARD HTML
# ========================================================
USER_HTML = '''
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
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;color:#fff;overflow-x:hidden;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:60px 60px;pointer-events:none;}
        .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 20% 30%,rgba(102,126,234,0.05),transparent 50%),radial-gradient(ellipse at 80% 70%,rgba(118,75,162,0.04),transparent 50%);pointer-events:none;}
        .bg-orb{position:fixed;border-radius:50%;filter:blur(150px);animation:floatOrb 35s infinite ease-in-out;pointer-events:none;}
        .bg-orb:nth-child(1){width:700px;height:700px;background:#667eea;top:-250px;right:-150px;opacity:0.05;animation-delay:0s;}
        .bg-orb:nth-child(2){width:600px;height:600px;background:#764ba2;bottom:-200px;left:-150px;opacity:0.04;animation-delay:14s;}
        .bg-orb:nth-child(3){width:500px;height:500px;background:#f093fb;top:40%;left:40%;opacity:0.03;animation-delay:28s;}
        .bg-orb:nth-child(4){width:400px;height:400px;background:#48bb78;top:10%;right:20%;opacity:0.03;animation-delay:42s;}
        @keyframes floatOrb{0%,100%{transform:translate(0,0) scale(1);}25%{transform:translate(120px,-80px) scale(1.3);}50%{transform:translate(-80px,60px) scale(0.7);}75%{transform:translate(100px,120px) scale(1.2);}}
        .user-container{position:relative;z-index:1;max-width:1300px;margin:0 auto;padding:20px;}
        .user-header{background:rgba(255,255,255,0.02);backdrop-filter:blur(40px);border-radius:20px;padding:18px 30px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center;border:1px solid rgba(255,255,255,0.04);}
        .user-logo{font-size:22px;font-weight:900;font-family:'Orbitron',monospace;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;display:flex;align-items:center;gap:10px;letter-spacing:2px;}
        .user-logo i{font-size:24px;background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
        .user-nav{display:flex;gap:8px;flex-wrap:wrap;}
        .user-nav a{color:#ffffff;text-decoration:none;padding:8px 18px;border-radius:10px;transition:0.4s;font-weight:500;font-size:12px;border:1px solid rgba(255,255,255,0.06);display:flex;align-items:center;gap:8px;font-family:'Orbitron',monospace;letter-spacing:0.5px;background:rgba(255,255,255,0.02);}
        .user-nav a:hover{background:rgba(255,255,255,0.05);color:#fff;border-color:rgba(255,255,255,0.1);}
        .user-nav .logout-btn{background:rgba(255,0,0,0.05);color:#ff6b6b;border:1px solid rgba(255,0,0,0.05);}
        .user-nav .logout-btn:hover{background:#ff6b6b;color:#fff;border-color:#ff6b6b;box-shadow:0 8px 40px rgba(255,107,107,0.1);}
        .sidebar-container{display:flex;gap:25px;}
        .main-content{flex:3;}
        .sidebar{flex:1;}
        .welcome-card{background:rgba(255,255,255,0.02);backdrop-filter:blur(20px);border-radius:20px;padding:30px;margin-bottom:25px;border:1px solid rgba(255,255,255,0.04);border-left:3px solid #667eea;}
        .welcome-card h1{font-size:24px;font-weight:700;color:#ffffff;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .welcome-card .sub{color:#ffffff;margin-top:5px;font-size:13px;font-weight:300;letter-spacing:1px;}
        .profile-tags{display:flex;gap:10px;flex-wrap:wrap;margin-top:15px;}
        .tag{background:rgba(255,255,255,0.03);padding:5px 16px;border-radius:30px;font-size:11px;color:#ffffff;border:1px solid rgba(255,255,255,0.03);display:flex;align-items:center;gap:6px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .tag.primary{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;box-shadow:0 8px 30px rgba(102,126,234,0.08);}
        .meeting-portal{background:rgba(255,255,255,0.02);backdrop-filter:blur(20px);border-radius:20px;padding:40px;margin-bottom:25px;border:1px solid rgba(255,255,255,0.04);text-align:center;}
        .meeting-portal .status-badge{display:inline-block;padding:6px 24px;border-radius:30px;font-size:10px;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;color:#ffffff;}
        .status-scheduled{background:rgba(253,203,110,0.08);color:#fdcb6e;border:1px solid rgba(253,203,110,0.06);}
        .status-live{background:rgba(255,107,107,0.08);color:#ff6b6b;border:1px solid rgba(255,107,107,0.06);animation:pulse 1.5s infinite;}
        .status-complete{background:rgba(72,187,120,0.08);color:#48bb78;border:1px solid rgba(72,187,120,0.06);}
        .join-interview-btn{background:linear-gradient(135deg,#48bb78,#38a169);color:#fff;padding:18px 50px;font-size:17px;font-weight:700;border-radius:60px;border:none;cursor:pointer;transition:0.5s;text-decoration:none;display:inline-block;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .join-interview-btn:hover{transform:scale(1.05);box-shadow:0 20px 60px rgba(72,187,120,0.08);}
        .join-interview-btn.ready{animation:pulse-glow 2s infinite;}
        @keyframes pulse-glow{0%,100%{box-shadow:0 0 30px rgba(72,187,120,0.03);}50%{box-shadow:0 0 80px rgba(72,187,120,0.08);}}
        .actions-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px;margin-top:20px;}
        .action-card{background:rgba(255,255,255,0.02);backdrop-filter:blur(10px);border-radius:16px;padding:20px;text-align:center;cursor:pointer;transition:0.4s;border:1px solid rgba(255,255,255,0.03);}
        .action-card:hover{transform:translateY(-6px);border-color:rgba(102,126,234,0.08);background:rgba(255,255,255,0.04);}
        .action-card .icon{font-size:30px;margin-bottom:8px;}
        .action-card .label{color:#ffffff;font-weight:500;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .sidebar-card{background:rgba(255,255,255,0.02);backdrop-filter:blur(20px);border-radius:20px;padding:25px;position:sticky;top:20px;border:1px solid rgba(255,255,255,0.04);}
        .sidebar-card h3{color:#ffffff;text-align:center;margin-bottom:15px;border-bottom:1px solid rgba(255,255,255,0.03);padding-bottom:12px;font-weight:600;font-size:13px;display:flex;align-items:center;justify-content:center;gap:10px;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .sidebar-card h3 i{color:#667eea;}
        .result-box{padding:20px;border-radius:16px;text-align:center;margin-top:10px;}
        .result-pass{background:rgba(72,187,120,0.04);border:1px solid rgba(72,187,120,0.04);}
        .result-fail{background:rgba(255,107,107,0.04);border:1px solid rgba(255,107,107,0.04);}
        .result-pending{background:rgba(253,203,110,0.04);border:1px solid rgba(253,203,110,0.04);}
        .result-score{font-size:44px;font-weight:900;margin:10px 0;font-family:'Orbitron',monospace;color:#ffffff;}
        .result-pass .result-score{color:#48bb78;}
        .result-fail .result-score{color:#ff6b6b;}
        .company-msg{font-size:12px;margin:10px 0;line-height:1.6;color:#ffffff;}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
        @media(max-width:768px){.user-header{flex-direction:column;gap:15px;}.sidebar-container{flex-direction:column;}.join-interview-btn{font-size:14px;padding:14px 30px;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="bg-orb"></div><div class="bg-orb"></div><div class="bg-orb"></div><div class="bg-orb"></div>
<div class="user-container">
    <div class="user-header">
        <div class="user-logo"><i class="fas fa-robot"></i> LARA AI</div>
        <div class="user-nav">
            <a href="/"><i class="fas fa-home"></i> Home</a>
            <a href="/profile"><i class="fas fa-user"></i> Profile</a>
            <a href="/logout" class="logout-btn"><i class="fas fa-sign-out-alt"></i> Logout</a>
        </div>
    </div>
    <div class="sidebar-container">
        <div class="main-content">
            <div class="welcome-card">
                <h1>👋 Welcome, {{ session.user_name }}!</h1>
                <div class="sub">🤖 LARA AI Tamil Interview Platform</div>
                <div class="profile-tags">
                    <span class="tag primary">{% if session.user_type == 'student' %}<i class="fas fa-graduation-cap"></i> Student{% else %}<i class="fas fa-briefcase"></i> Professional{% endif %}</span>
                    <span class="tag"><i class="fas fa-university"></i> {{ session.college or 'Not specified' }}</span>
                    <span class="tag"><i class="fas fa-code"></i> {{ session.domain or 'Not specified' }}</span>
                    <span class="tag"><i class="fas fa-star"></i> {% if session.experience_years == 0 %}Fresher{% else %}{{ session.experience_years }} years{% endif %}</span>
                </div>
            </div>
            <div class="meeting-portal">
                <h2><i class="fas fa-video"></i> Interview Portal</h2>
                
                {% if session.interview_complete %}
                    <div class="status-badge status-complete"><i class="fas fa-check-circle"></i> COMPLETED</div>
                    <div style="font-size:48px;font-weight:900;margin:15px 0;background:linear-gradient(135deg,#48bb78,#38a169);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Orbitron',monospace;">{{ session.final_score }}%</div>
                    <p style="font-size:14px;color:#ffffff;">{{ session.company_message }}</p>
                    <a href="/result"><button class="join-interview-btn" style="background:linear-gradient(135deg,#667eea,#764ba2);"><i class="fas fa-chart-bar"></i> View Result</button></a>
                    
                {% elif session.meeting_scheduled %}
                    <div class="status-badge status-scheduled"><i class="fas fa-clock"></i> SCHEDULED</div>
                    <div style="font-size:20px;color:#fdcb6e;margin:10px 0;font-family:'Orbitron',monospace;letter-spacing:1px;">✅ Your interview has been scheduled!</div>
                    <div class="join-btn-container" style="margin-top:20px;">
                        <a href="{{ session.meeting_link }}" target="_blank" class="join-interview-btn ready" id="joinBtn">
                            <i class="fas fa-video"></i> Join Interview Now <span class="arrow">→</span>
                        </a>
                    </div>
                    <div style="margin-top:15px;font-size:12px;color:#ffffff;font-family:'Orbitron',monospace;letter-spacing:0.5px;">
                        <i class="fas fa-link"></i> Meeting Link: {{ session.meeting_link }}
                    </div>
                    
                {% elif session.meeting_live %}
                    <div class="status-badge status-live"><i class="fas fa-circle"></i> LIVE - JOIN NOW!</div>
                    <div class="timer" id="interviewTimer">05:00</div>
                    <p style="color:#ffffff;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:1px;">Interview ends in 5 minutes</p>
                    <a href="{{ session.meeting_link }}" target="_blank" class="join-interview-btn ready" id="joinBtn"><i class="fas fa-video"></i> Join Interview <span class="arrow">→</span></a>
                    
                {% else %}
                    <div class="status-badge" style="background:rgba(255,255,255,0.02);color:#ffffff;border:1px solid rgba(255,255,255,0.02);"><i class="fas fa-hourglass"></i> WAITING</div>
                    <p style="margin-top:20px;color:#ffffff;">Admin will schedule your interview.</p>
                {% endif %}
            </div>
            <div class="actions-grid">
                <div class="action-card" onclick="window.location.href='/profile'"><div class="icon">👤</div><div class="label">Profile</div></div>
                <div class="action-card" onclick="window.location.href='/resume'"><div class="icon">📄</div><div class="label">Resume</div></div>
                <div class="action-card" onclick="window.location.href='/result'"><div class="icon">📊</div><div class="label">Results</div></div>
            </div>
        </div>
        <div class="sidebar">
            <div class="sidebar-card">
                <h3><i class="fas fa-chart-simple"></i> Result Status</h3>
                {% if session.interview_complete %}
                    {% if session.passed %}
                        <div class="result-box result-pass">
                            <div style="font-size:44px;">🎉</div>
                            <div class="result-score">{{ session.final_score }}%</div>
                            <div style="font-weight:700;color:#48bb78;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:1px;"><i class="fas fa-check-circle"></i> PASSED</div>
                            <div class="company-msg">{{ session.company_message }}</div>
                        </div>
                    {% else %}
                        <div class="result-box result-fail">
                            <div style="font-size:44px;">😔</div>
                            <div class="result-score">{{ session.final_score }}%</div>
                            <div style="font-weight:700;color:#ff6b6b;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:1px;"><i class="fas fa-times-circle"></i> FAILED</div>
                            <div class="company-msg">{{ session.company_message }}</div>
                        </div>
                    {% endif %}
                {% elif session.meeting_live %}
                    <div class="result-box result-pending">
                        <div style="font-size:44px;">⏳</div>
                        <div style="font-weight:700;margin:10px 0;color:#fdcb6e;font-family:'Orbitron',monospace;letter-spacing:1px;font-size:12px;"><i class="fas fa-spinner fa-spin"></i> IN PROGRESS</div>
                        <p style="color:#ffffff;font-size:12px;">LARA AI is interviewing</p>
                    </div>
                {% elif session.meeting_scheduled %}
                    <div class="result-box result-pending">
                        <div style="font-size:44px;">📅</div>
                        <div style="font-weight:700;margin:10px 0;color:#fdcb6e;font-family:'Orbitron',monospace;letter-spacing:1px;font-size:12px;">SCHEDULED</div>
                        <p style="color:#ffffff;font-size:12px;">Your interview is ready! Click Join Now.</p>
                    </div>
                {% else %}
                    <div class="result-box result-pending">
                        <div style="font-size:44px;">📋</div>
                        <div style="font-weight:700;margin:10px 0;color:#ffffff;font-family:'Orbitron',monospace;letter-spacing:1px;font-size:12px;">NOT SCHEDULED</div>
                        <p style="color:#ffffff;font-size:12px;">Admin will schedule</p>
                    </div>
                {% endif %}
                <div style="margin-top:15px;padding-top:15px;border-top:1px solid rgba(255,255,255,0.02);text-align:center;">
                    <div style="font-size:8px;color:#ffffff;letter-spacing:2px;text-transform:uppercase;font-family:'Orbitron',monospace;">LARA AI • Mock Interview</div>
                </div>
            </div>
        </div>
    </div>
</div>
<script>
    {% if session.meeting_live %}
    let timeLeft = 300;
    function updateInterviewTimer() {
        const el = document.getElementById('interviewTimer');
        if(!el) return;
        const m = Math.floor(timeLeft/60);
        const s = timeLeft%60;
        el.innerHTML = m.toString().padStart(2,'0') + ':' + s.toString().padStart(2,'0');
        if(timeLeft <= 0) {
            el.innerHTML = "00:00";
            window.location.href = '/force-complete';
        } else {
            timeLeft--;
            setTimeout(updateInterviewTimer, 1000);
        }
    }
    updateInterviewTimer();
    {% endif %}
</script>
</body>
</html>
'''

# ========================================================
# INTERVIEW PAGE
# ========================================================
INTERVIEW_PAGE = '''
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
        body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;padding:20px;color:#fff;}
        .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
        .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 40%,rgba(102,126,234,0.04),transparent 50%),radial-gradient(ellipse at 70% 60%,rgba(118,75,162,0.03),transparent 50%);pointer-events:none;}
        .container{position:relative;z-index:1;max-width:1000px;margin:0 auto;}
        .card{background:rgba(255,255,255,0.02);backdrop-filter:blur(40px);border-radius:24px;padding:40px;border:1px solid rgba(255,255,255,0.04);}
        .ai-header{display:flex;align-items:center;gap:18px;margin-bottom:25px;padding-bottom:20px;border-bottom:1px solid rgba(255,255,255,0.03);}
        .ai-avatar{width:80px;height:80px;border-radius:50%;overflow:hidden;border:2px solid #667eea;flex-shrink:0;box-shadow:0 0 40px rgba(102,126,234,0.05);}
        .ai-avatar img{width:100%;height:100%;object-fit:cover;}
        .ai-name{font-size:20px;font-weight:700;color:#ffffff;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .ai-status{font-size:11px;color:#48bb78;display:flex;align-items:center;gap:8px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .ai-status .dot{width:8px;height:8px;background:#48bb78;border-radius:50%;animation:pulse 1s infinite;}
        .ai-qcount{text-align:right;}
        .ai-qcount .num{font-size:18px;font-weight:700;color:#667eea;font-family:'Orbitron',monospace;}
        .ai-qcount .label{font-size:9px;color:#ffffff;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .chat-container{background:rgba(255,255,255,0.02);border-radius:16px;padding:20px;margin:20px 0;max-height:350px;overflow-y:auto;border:1px solid rgba(255,255,255,0.03);}
        .chat-message{display:flex;margin-bottom:15px;align-items:flex-start;gap:12px;}
        .chat-message.ai{flex-direction:row;}
        .chat-message.user{flex-direction:row-reverse;}
        .chat-bubble{padding:12px 18px;border-radius:18px;max-width:80%;word-wrap:break-word;font-size:13px;line-height:1.6;color:#ffffff;}
        .chat-message.ai .chat-bubble{background:rgba(255,255,255,0.04);color:#fff;border-bottom-left-radius:4px;}
        .chat-message.user .chat-bubble{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border-bottom-right-radius:4px;}
        .chat-avatar{width:35px;height:35px;border-radius:50%;overflow:hidden;flex-shrink:0;}
        .chat-avatar img{width:100%;height:100%;object-fit:cover;}
        .question-box{background:rgba(255,255,255,0.02);padding:25px;border-radius:16px;margin:20px 0;border-left:3px solid #667eea;}
        .tamil-question{font-size:22px;font-weight:600;color:#ffffff;line-height:1.6;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .english-hint{font-size:12px;color:#ffffff;margin-top:10px;font-style:italic;font-family:'Inter',sans-serif;}
        .timer-bar{height:3px;background:rgba(255,255,255,0.03);border-radius:3px;margin:20px 0;overflow:hidden;}
        .timer-fill{height:100%;background:linear-gradient(90deg,#48bb78,#38a169);border-radius:3px;transition:width 0.1s linear;}
        .time-left{text-align:right;font-size:12px;color:#ffffff;margin-top:5px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        textarea{width:100%;padding:15px;border:1px solid rgba(255,255,255,0.04);border-radius:14px;font-size:15px;margin:15px 0;resize:vertical;transition:0.3s;background:rgba(255,255,255,0.02);color:#fff;font-family:'Inter',sans-serif;}
        textarea:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.04);}
        textarea::placeholder{color:rgba(255,255,255,0.3);}
        button{background:linear-gradient(135deg,#48bb78,#38a169);color:#fff;border:none;padding:15px 30px;border-radius:60px;cursor:pointer;font-size:15px;width:100%;transition:0.5s;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;}
        button:hover{transform:scale(1.02);box-shadow:0 10px 40px rgba(72,187,120,0.05);}
        .progress{display:flex;justify-content:space-between;margin:15px 0;color:#ffffff;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .media-controls{display:flex;gap:12px;justify-content:center;margin:15px 0;flex-wrap:wrap;}
        .media-btn{background:rgba(255,255,255,0.02);color:#fff;border:1px solid rgba(255,255,255,0.04);padding:10px 20px;border-radius:12px;cursor:pointer;font-size:12px;transition:0.3s;font-weight:500;display:flex;align-items:center;gap:8px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .media-btn:hover{transform:scale(1.05);background:rgba(255,255,255,0.04);}
        .media-btn.active{background:linear-gradient(135deg,#48bb78,#38a169);border-color:#48bb78;}
        .media-btn.red{background:rgba(255,107,107,0.06);border-color:rgba(255,107,107,0.04);color:#ff6b6b;}
        .media-btn.red:hover{background:#ff6b6b;color:#fff;}
        #videoContainer{text-align:center;margin:15px 0;}
        #localVideo{width:100%;max-width:400px;border-radius:16px;background:#0a0a0f;border:1px solid rgba(255,255,255,0.03);}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
        @media(max-width:768px){.card{padding:20px;}.ai-header{flex-wrap:wrap;}.tamil-question{font-size:18px;}}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="container">
    <div class="card">
        <div class="ai-header">
            <div class="ai-avatar">
                <img src="{{ url_for('static', filename='lara_avatar.jpg') }}" alt="LARA AI" onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22 viewBox=%220 0 100 100%22%3E%3Crect width=%22100%22 height=%22100%22 fill=%22%23667eea%22/%3E%3Ctext x=%2250%22 y=%2255%22 font-size=%2230%22 text-anchor=%22middle%22 fill=%22white%22 font-family=%22Arial%22%3E🤖%3C/text%3E%3C/svg%3E';">
            </div>
            <div>
                <div class="ai-name"><i class="fas fa-robot" style="color:#667eea;"></i> LARA AI</div>
                <div class="ai-status"><span class="dot"></span> Active - Tamil Mode</div>
            </div>
            <div class="ai-qcount">
                <div class="num">{{ q_index }}/{{ total_q }}</div>
                <div class="label">Questions</div>
            </div>
        </div>
        <div class="chat-container" id="chatContainer">
            <div class="chat-message ai">
                <div class="chat-avatar">
                    <img src="{{ url_for('static', filename='lara_avatar.jpg') }}" alt="LARA" onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2235%22 height=%2235%22 viewBox=%220 0 35 35%22%3E%3Crect width=%2235%22 height=%2235%22 fill=%22%23667eea%22/%3E%3Ctext x=%2217.5%22 y=%2222%22 font-size=%2216%22 text-anchor=%22middle%22 fill=%22white%22 font-family=%22Arial%22%3E🤖%3C/text%3E%3C/svg%3E';">
                </div>
                <div class="chat-bubble"><strong>LARA AI:</strong> வணக்கம்! {{ session.user_name }}!<br><i class="fas fa-robot"></i> நான் LARA AI.</div>
            </div>
            <div class="chat-message ai">
                <div class="chat-avatar">
                    <img src="{{ url_for('static', filename='lara_avatar.jpg') }}" alt="LARA" onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2235%22 height=%2235%22 viewBox=%220 0 35 35%22%3E%3Crect width=%2235%22 height=%2235%22 fill=%22%23667eea%22/%3E%3Ctext x=%2217.5%22 y=%2222%22 font-size=%2216%22 text-anchor=%22middle%22 fill=%22white%22 font-family=%22Arial%22%3E🤖%3C/text%3E%3C/svg%3E';">
                </div>
                <div class="chat-bubble"><strong>LARA AI:</strong> கேள்விக்கு பதில் சொல்லுங்கள்.</div>
            </div>
        </div>
        <div class="media-controls">
            <button class="media-btn active" onclick="toggleCamera()" id="cameraBtn"><i class="fas fa-video"></i> Camera</button>
            <button class="media-btn active" onclick="toggleMic()" id="micBtn"><i class="fas fa-microphone"></i> Mic</button>
            <button class="media-btn red" onclick="startRecording()"><i class="fas fa-circle"></i> Record</button>
        </div>
        <div id="videoContainer">
            <video id="localVideo" autoplay muted playsinline style="width:100%;max-width:400px;border-radius:16px;background:#0a0a0f;border:1px solid rgba(255,255,255,0.03);"></video>
        </div>
        <div class="question-box">
            <div class="tamil-question">❓ {{ current_q['tamil'] }}</div>
            <div class="english-hint">💡 {{ current_q['english'] }}</div>
        </div>
        <div class="timer-bar"><div class="timer-fill" id="timerFill" style="width:100%"></div></div>
        <div class="time-left" id="timeLeft">1:00 remaining</div>
        <form method="POST" action="/submit-interview-answer" id="answerForm">
            <textarea name="answer" rows="4" placeholder="தமிழில் பதில் சொல்லுங்கள்..." required></textarea>
            <button type="submit"><i class="fas fa-paper-plane"></i> Submit</button>
        </form>
        <div class="progress"><span><i class="fas fa-chart-simple"></i> Progress</span><span>{{ q_index }}/{{ total_q }}</span></div>
    </div>
</div>
<script>
    let videoStream = null;
    let isCameraOn = false;
    let isMicOn = true;
    let isRecording = false;
    let mediaRecorder = null;
    let recordedChunks = [];
    const video = document.getElementById('localVideo');
    const cameraBtn = document.getElementById('cameraBtn');
    const micBtn = document.getElementById('micBtn');
    let cameraOffState = sessionStorage.getItem('lara_camera_off') === 'true';
    let micOffState = sessionStorage.getItem('lara_mic_off') === 'true';
    async function toggleCamera() {
        try {
            if (videoStream && isCameraOn) {
                videoStream.getTracks().forEach(track => track.stop());
                videoStream = null;
                video.srcObject = null;
                isCameraOn = false;
                cameraBtn.innerHTML = '<i class="fas fa-video-slash"></i> Camera';
                cameraBtn.classList.remove('active');
                cameraBtn.style.background = 'rgba(255,255,255,0.02)';
                sessionStorage.setItem('lara_camera_off', 'true');
                return;
            }
            videoStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            video.srcObject = videoStream;
            isCameraOn = true;
            cameraBtn.innerHTML = '<i class="fas fa-video"></i> Camera';
            cameraBtn.classList.add('active');
            cameraBtn.style.background = '';
            sessionStorage.removeItem('lara_camera_off');
            if (videoStream) {
                videoStream.getAudioTracks().forEach(track => {
                    track.enabled = !micOffState;
                });
                isMicOn = !micOffState;
                micBtn.innerHTML = isMicOn ? '<i class="fas fa-microphone"></i> Mic' : '<i class="fas fa-microphone-slash"></i> Mic';
                micBtn.classList.toggle('active', isMicOn);
            }
        } catch(e) {
            alert('❌ Camera/Mic access denied!');
        }
    }
    function toggleMic() {
        if (!videoStream || !isCameraOn) {
            alert('Turn on camera first!');
            return;
        }
        videoStream.getAudioTracks().forEach(track => {
            track.enabled = !track.enabled;
        });
        isMicOn = videoStream.getAudioTracks()[0]?.enabled;
        micBtn.innerHTML = isMicOn ? '<i class="fas fa-microphone"></i> Mic' : '<i class="fas fa-microphone-slash"></i> Mic';
        micBtn.classList.toggle('active', isMicOn);
        sessionStorage.setItem('lara_mic_off', isMicOn ? 'false' : 'true');
    }
    function startRecording() {
        if (!videoStream || !isCameraOn) {
            alert('Turn on camera first!');
            return;
        }
        if (isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            const btn = event.target;
            btn.innerHTML = '<i class="fas fa-circle"></i> Record';
            btn.classList.remove('active');
            btn.style.background = '';
            return;
        }
        recordedChunks = [];
        mediaRecorder = new MediaRecorder(videoStream);
        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) recordedChunks.push(e.data);
        };
        mediaRecorder.onstop = function() {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'lara_interview_recording.webm';
            a.click();
            alert('✅ Recording saved!');
        };
        mediaRecorder.start();
        isRecording = true;
        const btn = event.target;
        btn.innerHTML = '<i class="fas fa-stop"></i> Stop';
        btn.classList.add('active');
        btn.style.background = '#e53e3e';
    }
    window.onload = function() {
        if (!sessionStorage.getItem('lara_camera_off')) {
            setTimeout(toggleCamera, 1000);
        } else {
            cameraBtn.innerHTML = '<i class="fas fa-video-slash"></i> Camera';
            cameraBtn.classList.remove('active');
            cameraBtn.style.background = 'rgba(255,255,255,0.02)';
        }
        if (sessionStorage.getItem('lara_mic_off') === 'true') {
            micBtn.innerHTML = '<i class="fas fa-microphone-slash"></i> Mic';
            micBtn.classList.remove('active');
        }
    };
    let timeLeft = {{ current_q['time'] }};
    const timerFill = document.getElementById('timerFill');
    const timeLeftSpan = document.getElementById('timeLeft');
    const form = document.getElementById('answerForm');
    function updateTimer() {
        if(timeLeft <= 0) {
            timeLeftSpan.innerHTML = "⏰ Time's up!";
            timerFill.style.background = "#f56565";
            form.submit();
        } else {
            const seconds = timeLeft % 60;
            const percent = (timeLeft / {{ current_q['time'] }} * 100);
            timerFill.style.width = percent + '%';
            if(percent < 20) timerFill.style.background = "#f56565";
            timeLeftSpan.innerHTML = Math.floor(timeLeft/60) + ':' + seconds.toString().padStart(2,'0') + ' remaining';
            timeLeft--;
            setTimeout(updateTimer, 1000);
        }
    }
    updateTimer();
</script>
</body>
</html>
'''

# ========================================================
# RESULT PAGE
# ========================================================
RESULT_PAGE = '''
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
        .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 40%,rgba(102,126,234,0.04),transparent 50%),radial-gradient(ellipse at 70% 60%,rgba(118,75,162,0.03),transparent 50%);pointer-events:none;}
        .container{position:relative;z-index:1;max-width:550px;width:100%;}
        .card{background:rgba(255,255,255,0.02);backdrop-filter:blur(40px);border-radius:24px;padding:40px;text-align:center;border:1px solid rgba(255,255,255,0.04);}
        .icon{font-size:64px;margin:10px 0;}
        .card h1{font-size:26px;font-weight:700;margin-bottom:5px;font-family:'Orbitron',monospace;letter-spacing:1px;color:#ffffff;}
        .lara-score{background:rgba(255,255,255,0.02);border-radius:16px;padding:25px;margin:20px 0;border:1px solid rgba(255,255,255,0.03);}
        .lara-score h3{font-size:13px;font-weight:500;color:#ffffff;font-family:'Orbitron',monospace;letter-spacing:1px;}
        .score{font-size:60px;font-weight:900;margin:10px 0;font-family:'Orbitron',monospace;color:#ffffff;}
        .pass .score{color:#48bb78;}
        .fail .score{color:#ff6b6b;}
        .company-msg{font-size:14px;margin:15px 0;line-height:1.7;color:#ffffff;}
        .details{background:rgba(255,255,255,0.01);border-radius:14px;padding:20px;margin:20px 0;border:1px solid rgba(255,255,255,0.02);text-align:left;}
        .details p{padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.02);color:#ffffff;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .details p:last-child{border-bottom:none;}
        .details span{color:#ffffff;font-weight:500;}
        .btn-group{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:10px;}
        .btn{background:rgba(255,255,255,0.02);color:#fff;border:1px solid rgba(255,255,255,0.04);padding:12px 30px;border-radius:60px;cursor:pointer;font-size:12px;transition:0.4s;text-decoration:none;display:inline-block;font-weight:500;display:flex;align-items:center;gap:8px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
        .btn:hover{transform:scale(1.05);background:rgba(255,255,255,0.04);}
        .btn.green{background:linear-gradient(135deg,#48bb78,#38a169);border:none;}
        .btn.green:hover{box-shadow:0 10px 40px rgba(72,187,120,0.05);}
        .btn.gray{background:rgba(113,128,150,0.04);border-color:rgba(113,128,150,0.03);}
        .btn.gray:hover{background:rgba(113,128,150,0.08);}
    </style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="container">
    <div class="card {% if passed %}pass{% else %}fail{% endif %}">
        <div class="icon">{% if passed %}🎉{% else %}😔{% endif %}</div>
        <h1>{% if passed %}Congratulations!{% else %}We're Sorry{% endif %}</h1>
        <div class="lara-score">
            <h3><i class="fas fa-robot"></i> LARA AI Score</h3>
            <div class="score">{{ score }}%</div>
        </div>
        <div class="company-msg">{{ message }}</div>
        <div class="details">
            <p>📅 <strong>Date:</strong> <span>{{ date }}</span></p>
            <p>📊 <strong>Score:</strong> <span>{{ score }}%</span></p>
            <p>📝 <strong>Status:</strong> <span>{% if passed %}✅ Passed{% else %}❌ Failed{% endif %}</span></p>
        </div>
        <div class="btn-group">
            <a href="/"><button class="btn"><i class="fas fa-home"></i> Home</button></a>
            <a href="/profile"><button class="btn green"><i class="fas fa-user"></i> Profile</button></a>
            <a href="/"><button class="btn gray"><i class="fas fa-redo"></i> Retry</button></a>
        </div>
    </div>
</div>
</body>
</html>
'''

# ========================================================
# ROUTES
# ========================================================

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template_string(LANDING_HTML)
    if session.get('role') == 'admin':
        return redirect('/admin')
    uid = session.get('user_id')
    if uid in users:
        u = users[uid]
        session['user_name'] = u['name']
        session['user_type'] = u.get('user_type', '')
        session['college'] = u.get('college', '')
        session['domain'] = u.get('domain', '')
        session['experience_years'] = u.get('experience_years', 0)
        session['cgpa'] = u.get('cgpa', '')
        session['meeting_scheduled'] = u.get('meeting_scheduled', False)
        session['meeting_start_time'] = u.get('meeting_start_time', '')
        session['meeting_link'] = u.get('meeting_link', '')
        session['meeting_live'] = u.get('meeting_live', False)
        session['interview_complete'] = u.get('interview_complete', False)
        session['final_score'] = u.get('final_score', 0)
        session['passed'] = u.get('passed', False)
        session['company_message'] = u.get('company_message', '')
    return render_template_string(USER_HTML, session=session)

@app.route('/login')
def user_login_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template_string(USER_LOGIN_HTML)

@app.route('/admin-login')
def admin_login_page():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect('/admin')
        return redirect('/')
    return render_template_string(ADMIN_LOGIN_HTML)

@app.route('/user-login', methods=['POST'])
def user_login():
    email = request.form['email']
    password = request.form['password']
    for uid, u in users.items():
        if u['email'] == email and u['password'] == password and u['role'] == 'user':
            session['user_id'] = uid
            session['user_name'] = u['name']
            session['role'] = u['role']
            session['user_type'] = u.get('user_type', '')
            session['college'] = u.get('college', '')
            session['domain'] = u.get('domain', '')
            session['experience_years'] = u.get('experience_years', 0)
            session['cgpa'] = u.get('cgpa', '')
            session['meeting_scheduled'] = u.get('meeting_scheduled', False)
            session['meeting_start_time'] = u.get('meeting_start_time', '')
            session['meeting_link'] = u.get('meeting_link', '')
            session['meeting_live'] = u.get('meeting_live', False)
            session['interview_complete'] = u.get('interview_complete', False)
            session['final_score'] = u.get('final_score', 0)
            session['passed'] = u.get('passed', False)
            session['company_message'] = u.get('company_message', '')
            users[uid]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return '<script>alert("✅ Welcome back, ' + u['name'] + '!");window.location.href="/"</script>'
    return '<script>alert("❌ Invalid user credentials!");window.location.href="/login"</script>'

@app.route('/admin-login', methods=['POST'])
def admin_login():
    email = request.form['email']
    password = request.form['password']
    for uid, u in users.items():
        if u['email'] == email and u['password'] == password and u['role'] == 'admin':
            session['user_id'] = uid
            session['user_name'] = u['name']
            session['role'] = u['role']
            users[uid]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return '<script>alert("✅ Welcome Admin!");window.location.href="/admin"</script>'
    return '<script>alert("❌ Invalid admin credentials!");window.location.href="/admin-login"</script>'

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template_string('''
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
            .container{position:relative;z-index:1;max-width:520px;width:100%;}
            .card{background:rgba(255,255,255,0.02);backdrop-filter:blur(40px);border-radius:24px;padding:40px;border:1px solid rgba(255,255,255,0.04);}
            .logo{text-align:center;font-size:26px;font-weight:900;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-family:'Orbitron',monospace;letter-spacing:2px;}
            .logo i{font-size:30px;}
            .sub{text-align:center;color:#ffffff;margin:10px 0 25px 0;font-size:13px;font-family:'Orbitron',monospace;letter-spacing:1px;}
            input,select{width:100%;padding:12px;margin:8px 0;border:1px solid rgba(255,255,255,0.04);border-radius:14px;font-size:13px;transition:0.3s;background:rgba(255,255,255,0.02);color:#fff;font-family:'Inter',sans-serif;}
            input:focus,select:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.04);}
            input::placeholder,select option{color:rgba(255,255,255,0.3);}
            select option{background:#0a0a0f;color:#fff;}
            button{width:100%;background:linear-gradient(135deg,#48bb78,#38a169);color:#fff;border:none;padding:14px;border-radius:14px;font-size:15px;cursor:pointer;transition:0.5s;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:1px;}
            button:hover{transform:translateY(-3px);box-shadow:0 10px 40px rgba(72,187,120,0.05);}
            .links{text-align:center;margin-top:18px;color:#ffffff;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
            .links a{color:#667eea;text-decoration:none;font-weight:500;}
            .links a:hover{color:#764ba2;}
            .row{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
            .file-input{width:100%;padding:12px;margin:8px 0;border:1px solid rgba(255,255,255,0.04);border-radius:14px;background:rgba(255,255,255,0.02);color:rgba(255,255,255,0.3);font-size:12px;font-family:'Inter',sans-serif;}
            .file-input::-webkit-file-upload-button{background:rgba(255,255,255,0.02);color:#fff;border:none;padding:8px 16px;border-radius:8px;cursor:pointer;font-weight:500;}
            .back-btn{display:inline-block;margin-top:15px;color:#ffffff;text-decoration:none;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
            .back-btn i{color:#667eea;}
            .back-btn:hover{color:#667eea;}
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
            <form method="POST" action="/register" enctype="multipart/form-data">
                <input type="text" name="name" placeholder="Full Name" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <select name="user_type" required>
                    <option value="">Select User Type</option>
                    <option value="student">🎓 Student</option>
                    <option value="professional">💼 Professional</option>
                </select>
                <div class="row">
                    <input type="text" name="college" placeholder="College / Company">
                    <select name="passed_out_year">
                        <option value="">Passed Year</option>
                        {% for y in range(2015,2027) %}<option>{{ y }}</option>{% endfor %}
                    </select>
                </div>
                <div class="row">
                    <input type="text" name="domain" placeholder="Enter Your Domain" required>
                    <select name="experience_years">
                        <option value="0">0 - Fresher</option>
                        {% for y in range(1,11) %}<option value="{{ y }}">{{ y }} years</option>{% endfor %}
                        <option value="11">10+ years</option>
                    </select>
                </div>
                <input type="number" name="cgpa" step="0.01" placeholder="CGPA (0-10)">
                <input type="file" name="resume" accept=".pdf,.doc,.docx" class="file-input">
                <button type="submit"><i class="fas fa-check"></i> Register</button>
            </form>
            <div class="links"><a href="/login"><i class="fas fa-lock"></i> Login</a></div>
            <div style="text-align:center;"><a href="/" class="back-btn"><i class="fas fa-arrow-left"></i> Back to Home</a></div>
        </div>
    </div>
    </body>
    </html>
    ''')

@app.route('/register', methods=['POST'])
def register():
    new_id = len(users) + 1
    reg_time = datetime.now()
    # ========== ONLY THIS LINE CHANGED ==========
    meeting_link = f"https://ai-mock-interview-five-beta.vercel.app/start-interview/{new_id}"
    # =============================================
    
    resume_path = ''
    if request.files.get('resume') and request.files['resume'].filename:
        file = request.files['resume']
        resume_path = f"uploads/{new_id}_{file.filename}"
        file.save(resume_path)
    
    users[new_id] = {
        'id': new_id,
        'name': request.form['name'],
        'email': request.form['email'],
        'password': request.form['password'],
        'role': 'user',
        'user_type': request.form['user_type'],
        'college': request.form.get('college', ''),
        'domain': request.form.get('domain', ''),
        'experience_years': int(request.form.get('experience_years', 0)),
        'cgpa': request.form.get('cgpa', ''),
        'resume_path': resume_path,
        'registration_time': reg_time.strftime("%Y-%m-%d %H:%M:%S"),
        'last_login': '',
        'meeting_scheduled': True,
        'meeting_start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'meeting_link': meeting_link,
        'meeting_live': True,
        'interview_complete': False,
        'final_score': 0,
        'passed': False,
        'company_message': ''
    }
    
    return '<script>alert("✅ Registration successful! Your interview is scheduled!");window.location.href="/"</script>'

@app.route('/logout')
def logout():
    session.clear()
    return '<script>window.location.href="/"</script>'

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return '<script>alert("⚠️ Please login as Admin!");window.location.href="/admin-login"</script>'
    if session.get('role') != 'admin':
        return '<script>alert("⚠️ Admin access only!");window.location.href="/"</script>'
    
    users_list = list(users.values())
    passed_count = sum(1 for u in users_list if u.get('passed'))
    failed_count = sum(1 for u in users_list if u.get('interview_complete') and not u.get('passed'))
    scores = [u.get('final_score', 0) for u in users_list if u.get('interview_complete')]
    avg_score = sum(scores) // len(scores) if scores else 0
    return render_template_string(ADMIN_HTML, users=users, passed_count=passed_count, failed_count=failed_count, avg_score=avg_score)

@app.route('/admin/users')
def admin_users():
    if session.get('role') != 'admin':
        return redirect('/')
    return admin()

@app.route('/admin/schedule')
def admin_schedule():
    if session.get('role') != 'admin':
        return redirect('/')
    return admin()

@app.route('/admin/schedule/<int:user_id>')
def admin_schedule_user(user_id):
    if session.get('role') != 'admin':
        return '<script>alert("Admin only!");window.location.href="/"</script>'
    if user_id in users and user_id != 1:
        meeting_link = f"https://ai-mock-interview-five-beta.vercel.app/start-interview/{user_id}"
        users[user_id]['meeting_scheduled'] = True
        users[user_id]['meeting_start_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users[user_id]['meeting_link'] = meeting_link
        users[user_id]['meeting_live'] = True
        return '<script>alert("✅ Interview scheduled! Click Join Now to start!");window.location.href="/admin"</script>'
    return '<script>alert("User not found!");window.location.href="/admin"</script>'

@app.route('/start-interview/<int:user_id>')
def start_interview(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect('/')
    session['tamil_q_list'] = TAMIL_QUESTIONS
    session['tamil_q_index'] = 0
    session['tamil_answers'] = []
    return redirect('/interview-session')

@app.route('/interview-session')
def interview_session():
    if 'tamil_q_index' not in session:
        return redirect('/')
    q_index = session['tamil_q_index']
    all_q = session.get('tamil_q_list', [])
    if q_index >= len(all_q):
        total_score = 0
        for ans in session.get('tamil_answers', []):
            score = min(len(ans.get('answer', '')) / 30 * 100, 100)
            total_score += score
        final_score = total_score // len(session['tamil_answers']) if session['tamil_answers'] else 70
        passed = final_score >= 60
        if passed:
            company_message = "🎉 Congratulations! LARA AI has evaluated your answers. You have impressed us with your skills. Welcome to the team! 🎊"
        else:
            company_message = "😊 Thank you for your time. LARA AI has analyzed your answers. Unfortunately we're not moving forward with you. Better luck next time! 💪 Keep practicing."
        session['final_score'] = final_score
        session['passed'] = passed
        session['company_message'] = company_message
        session['interview_complete'] = True
        if session.get('user_id') in users:
            users[session['user_id']]['interview_complete'] = True
            users[session['user_id']]['final_score'] = final_score
            users[session['user_id']]['passed'] = passed
            users[session['user_id']]['company_message'] = company_message
            users[session['user_id']]['meeting_live'] = False
        session.pop('tamil_q_index', None)
        session.pop('tamil_q_list', None)
        session.pop('tamil_answers', None)
        return '<script>alert("🎉 LARA AI Interview Complete! Your score: ' + str(final_score) + '%");window.location.href="/result"</script>'
    current_q = all_q[q_index]
    return render_template_string(INTERVIEW_PAGE, current_q=current_q, q_index=q_index+1, total_q=len(all_q))

@app.route('/submit-interview-answer', methods=['POST'])
def submit_interview_answer():
    if 'tamil_q_index' not in session:
        return redirect('/')
    answer = request.form['answer']
    q_index = session['tamil_q_index']
    all_q = session.get('tamil_q_list', [])
    current_q = all_q[q_index] if q_index < len(all_q) else {}
    answers = session.get('tamil_answers', [])
    answers.append({'question': current_q.get('tamil', ''), 'answer': answer})
    session['tamil_answers'] = answers
    session['tamil_q_index'] = q_index + 1
    return redirect('/interview-session')

@app.route('/force-complete')
def force_complete():
    if 'tamil_q_index' in session:
        session['tamil_q_index'] = len(session.get('tamil_q_list', []))
    return redirect('/interview-session')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template_string('''
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
            body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;color:#fff;}
            .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
            .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 40%,rgba(102,126,234,0.05),transparent 50%),radial-gradient(ellipse at 70% 60%,rgba(118,75,162,0.04),transparent 50%);pointer-events:none;}
            .container{position:relative;z-index:1;max-width:550px;width:100%;}
            .card{background:rgba(255,255,255,0.02);backdrop-filter:blur(40px);border-radius:24px;padding:40px;border:1px solid rgba(255,255,255,0.04);}
            h1{text-align:center;font-size:24px;font-weight:700;color:#ffffff;margin-bottom:20px;font-family:'Orbitron',monospace;letter-spacing:1px;}
            .info-row{display:flex;padding:12px;border-bottom:1px solid rgba(255,255,255,0.02);}
            .info-label{width:140px;font-weight:600;color:#ffffff;font-size:12px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
            .info-value{flex:1;color:#ffffff;font-size:13px;}
            .btn-group{text-align:center;margin-top:25px;}
            .btn{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;padding:12px 30px;border-radius:60px;cursor:pointer;font-size:13px;transition:0.4s;text-decoration:none;display:inline-block;font-weight:600;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
            .btn:hover{transform:scale(1.05);box-shadow:0 10px 40px rgba(102,126,234,0.06);}
            @media(max-width:500px){.info-row{flex-direction:column;}.info-label{margin-bottom:5px;}}
        </style>
    </head>
    <body>
    <div class="bg-grid"></div>
    <div class="bg-glow"></div>
    <div class="container">
        <div class="card">
            <h1><i class="fas fa-user-circle" style="color:#667eea;"></i> Profile</h1>
            <div class="info-row"><div class="info-label">Name:</div><div class="info-value">{{ session.user_name }}</div></div>
            <div class="info-row"><div class="info-label">Type:</div><div class="info-value">{% if session.user_type == 'student' %}🎓 Student{% elif session.user_type == 'admin' %}👑 Admin{% else %}💼 Professional{% endif %}</div></div>
            <div class="info-row"><div class="info-label">College/Company:</div><div class="info-value">{{ session.college or 'Not specified' }}</div></div>
            <div class="info-row"><div class="info-label">Domain:</div><div class="info-value">{{ session.domain or 'Not specified' }}</div></div>
            <div class="info-row"><div class="info-label">Experience:</div><div class="info-value">{% if session.experience_years == 0 %}Fresher{% else %}{{ session.experience_years }} years{% endif %}</div></div>
            <div class="info-row"><div class="info-label">CGPA:</div><div class="info-value">{{ session.cgpa or 'Not specified' }}</div></div>
            <div class="btn-group"><a href="/"><button class="btn"><i class="fas fa-home"></i> Home</button></a></div>
        </div>
    </div>
    </body>
    </html>
    ''')

@app.route('/result')
def result():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template_string(RESULT_PAGE, score=session.get('final_score', 0),
                                 passed=session.get('passed', False),
                                 message=session.get('company_message', ''),
                                 date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/resume')
def resume():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ta">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LARA AI - Resume</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            *{margin:0;padding:0;box-sizing:border-box;}
            body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;color:#fff;}
            .bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:50px 50px;pointer-events:none;}
            .bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;z-index:0;background:radial-gradient(ellipse at 30% 40%,rgba(102,126,234,0.05),transparent 50%),radial-gradient(ellipse at 70% 60%,rgba(118,75,162,0.04),transparent 50%);pointer-events:none;}
            .container{position:relative;z-index:1;max-width:480px;width:100%;}
            .card{background:rgba(255,255,255,0.02);backdrop-filter:blur(40px);border-radius:24px;padding:40px;border:1px solid rgba(255,255,255,0.04);text-align:center;}
            h1{font-size:24px;font-weight:700;color:#ffffff;margin-bottom:10px;font-family:'Orbitron',monospace;letter-spacing:1px;}
            p{color:#ffffff;margin-bottom:20px;font-size:13px;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
            .file-input{width:100%;padding:12px;border:1px solid rgba(255,255,255,0.04);border-radius:14px;background:rgba(255,255,255,0.02);color:#ffffff;font-size:12px;font-family:'Inter',sans-serif;margin-bottom:15px;}
            .file-input::-webkit-file-upload-button{background:rgba(255,255,255,0.02);color:#fff;border:none;padding:8px 16px;border-radius:8px;cursor:pointer;font-weight:500;}
            .btn{background:linear-gradient(135deg,#48bb78,#38a169);color:#fff;border:none;padding:12px 30px;border-radius:60px;cursor:pointer;font-size:13px;transition:0.4s;font-weight:600;width:100%;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
            .btn:hover{transform:scale(1.02);box-shadow:0 10px 40px rgba(72,187,120,0.05);}
            .btn-group{margin-top:15px;}
            .btn-back{background:rgba(255,255,255,0.02);color:#fff;border:1px solid rgba(255,255,255,0.04);padding:12px 30px;border-radius:60px;cursor:pointer;font-size:13px;transition:0.4s;text-decoration:none;display:inline-block;font-weight:500;width:100%;font-family:'Orbitron',monospace;letter-spacing:0.5px;}
            .btn-back:hover{background:rgba(255,255,255,0.04);}
        </style>
    </head>
    <body>
    <div class="bg-grid"></div>
    <div class="bg-glow"></div>
    <div class="container">
        <div class="card">
            <h1><i class="fas fa-file-pdf" style="color:#667eea;"></i> Resume</h1>
            <p>Upload your resume for interview preparation</p>
            <form method="POST" action="/upload-resume" enctype="multipart/form-data">
                <input type="file" name="resume" accept=".pdf,.doc,.docx" class="file-input" required>
                <button type="submit" class="btn"><i class="fas fa-upload"></i> Upload</button>
            </form>
            <div class="btn-group"><a href="/"><button class="btn-back"><i class="fas fa-home"></i> Home</button></a></div>
        </div>
    </div>
    </body>
    </html>
    ''')

@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    file = request.files.get('resume')
    if file and file.filename:
        filename = f"{session['user_id']}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        if session['user_id'] in users:
            users[session['user_id']]['resume_path'] = filepath
        session['resume_uploaded'] = True
    return '<script>alert("✅ Resume uploaded successfully!");window.location.href="/profile"</script>'

# ========================================================
# RUN THE APP
# ========================================================
if __name__ == '__main__':
    print("="*60)
    print("🤖 LARA AI Mock Interview Platform")
    print("📍 Open: http://localhost:5000")
    print("📝 Demo Credentials:")
    print("   User Login:   user@demo.com / 123")
    print("   Admin Login:  admin@demo.com / admin123")
    print("="*60)
    app.run(debug=True, port=5000)