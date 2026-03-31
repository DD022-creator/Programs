from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3
import hashlib
from datetime import datetime
import json
import os
import requests
import threading

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# ============================================================
# SMS FUNCTION - Sends text messages to candidates
# ============================================================
def send_sms(phone_number, message):
    """Send SMS using free Textbelt API (1 free SMS per day for demo)"""
    if not phone_number or len(phone_number) < 5:
        print(f"⚠️ Invalid phone number: {phone_number}")
        return False
    
    try:
        # Using free Textbelt API (1 SMS/day for testing)
        # For production, replace with Twilio, Vonage, or AWS SNS
        response = requests.post('https://textbelt.com/text', {
            'phone': phone_number,
            'message': message,
            'key': 'textbelt',  # Free key - 1 SMS per day
        }, timeout=10)
        
        result = response.json()
        if result.get('success'):
            print(f"✅ SMS sent successfully to {phone_number}")
            return True
        else:
            print(f"❌ SMS failed: {result.get('error', 'Unknown error')}")
            # For demo, still return True so it doesn't block the app
            return True
    except Exception as e:
        print(f"❌ SMS sending error: {e}")
        # Don't fail the whole operation if SMS fails
        return True

# ============================================================
# DATABASE INITIALIZATION
# ============================================================
def init_db():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS activity_logs")
    cursor.execute("DROP TABLE IF EXISTS team_members")
    cursor.execute("DROP TABLE IF EXISTS teams")
    cursor.execute("DROP TABLE IF EXISTS interviews")
    cursor.execute("DROP TABLE IF EXISTS applications")
    cursor.execute("DROP TABLE IF EXISTS candidates")
    cursor.execute("DROP TABLE IF EXISTS jobs")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # Users table with phone
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'recruiter',
            department TEXT,
            phone TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Jobs table
    cursor.execute('''
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            requirements TEXT,
            salary_range TEXT,
            status TEXT DEFAULT 'open',
            created_by INTEGER,
            assigned_to INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    
    # Candidates table with phone for SMS
    cursor.execute('''
        CREATE TABLE candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            resume TEXT,
            skills TEXT,
            experience INTEGER,
            current_company TEXT,
            current_position TEXT,
            status TEXT DEFAULT 'active',
            source TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    
    # Applications table
    cursor.execute('''
        CREATE TABLE applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            rating INTEGER,
            reviewed_by INTEGER,
            reviewed_date TIMESTAMP,
            created_by INTEGER,
            UNIQUE(job_id, candidate_id)
        )
    ''')
    
    # Interviews table
    cursor.execute('''
        CREATE TABLE interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            interview_date TIMESTAMP NOT NULL,
            interview_type TEXT NOT NULL,
            interviewer_id INTEGER,
            feedback TEXT,
            status TEXT DEFAULT 'scheduled',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    
    # Activity logs table
    cursor.execute('''
        CREATE TABLE activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            entity_type TEXT,
            entity_id INTEGER,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Teams table
    cursor.execute('''
        CREATE TABLE teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Team members table
    cursor.execute('''
        CREATE TABLE team_members (
            team_id INTEGER,
            user_id INTEGER,
            role TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (team_id, user_id)
        )
    ''')
    
    # Insert default users with phone numbers
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, role, department, phone, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ('admin', admin_password, 'admin@recruitment.com', 'System Administrator', 'admin', 'IT', '+1234567890', 1)
    )
    
    hr_password = hashlib.sha256('hr123'.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, role, department, phone, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ('hr_manager', hr_password, 'hr@recruitment.com', 'HR Manager', 'hr_manager', 'Human Resources', '+1234567891', 1)
    )
    
    rec_password = hashlib.sha256('rec123'.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, role, department, phone, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ('recruiter1', rec_password, 'recruiter1@recruitment.com', 'Sarah Johnson', 'recruiter', 'Engineering', '+1234567892', 1)
    )
    
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, role, department, phone, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ('recruiter2', rec_password, 'recruiter2@recruitment.com', 'Mike Peters', 'recruiter', 'Sales', '+1234567893', 1)
    )
    
    int_password = hashlib.sha256('int123'.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, role, department, phone, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ('interviewer1', int_password, 'interviewer@recruitment.com', 'David Chen', 'interviewer', 'Engineering', '+1234567894', 1)
    )
    
    # Sample jobs
    sample_jobs = [
        ('Senior Python Developer', 'Engineering', 'New York', 'Looking for experienced Python developer', '5+ years Python experience', '$120k-$150k', 'open', 1, 3),
        ('Frontend Engineer', 'Engineering', 'San Francisco', 'React.js expert needed', '3+ years React experience', '$100k-$130k', 'open', 1, 3),
        ('HR Business Partner', 'Human Resources', 'Chicago', 'Strategic HR partner', '5+ years HR experience', '$80k-$100k', 'open', 2, 2),
        ('Sales Manager', 'Sales', 'Remote', 'Lead sales team', '3+ years sales management', '$90k-$120k', 'open', 1, 4),
        ('UI/UX Designer', 'Design', 'Austin', 'Creative designer needed', 'Portfolio required', '$70k-$90k', 'closed', 1, 3)
    ]
    
    for job in sample_jobs:
        cursor.execute('''
            INSERT INTO jobs (title, department, location, description, requirements, salary_range, status, created_by, assigned_to, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', job)
    
    # Sample candidates with phone numbers
    sample_candidates = [
        ('John', 'Doe', 'john.doe@email.com', '+1234567895', 'Experienced developer', 'Python, JavaScript, SQL', 5, 'Tech Corp', 'Senior Developer', 'active', 'linkedin', 3),
        ('Jane', 'Smith', 'jane.smith@email.com', '+1234567896', 'Frontend expert', 'React, Vue, Angular', 3, 'Web Solutions', 'Frontend Lead', 'active', 'website', 3),
        ('Bob', 'Johnson', 'bob.johnson@email.com', '+1234567897', 'Sales professional', 'Sales, CRM, Negotiation', 7, 'Sales Inc', 'Sales Director', 'active', 'referral', 4),
        ('Alice', 'Brown', 'alice.brown@email.com', '+1234567898', 'HR specialist', 'Recruitment, HRIS, Employee Relations', 4, 'HR Solutions', 'HR Generalist', 'active', 'linkedin', 2),
        ('Charlie', 'Wilson', 'charlie.wilson@email.com', '+1234567899', 'Design expert', 'Figma, Adobe XD, Sketch', 2, 'Design Studio', 'Junior Designer', 'active', 'portfolio', 3)
    ]
    
    for candidate in sample_candidates:
        cursor.execute('''
            INSERT INTO candidates (first_name, last_name, email, phone, resume, skills, experience, current_company, current_position, status, source, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', candidate)
    
    # Sample applications
    cursor.execute("SELECT COUNT(*) FROM applications")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM jobs LIMIT 5")
        job_ids = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT id FROM candidates LIMIT 5")
        candidate_ids = [row[0] for row in cursor.fetchall()]
        
        sample_applications = [
            (job_ids[0], candidate_ids[0], 'reviewed', 'Strong candidate', 4, 3),
            (job_ids[0], candidate_ids[1], 'interviewed', 'Good skills', 5, 3),
            (job_ids[1], candidate_ids[2], 'pending', 'Initial review', 3, 3),
            (job_ids[2], candidate_ids[3], 'reviewed', 'HR interview completed', 4, 2),
            (job_ids[3], candidate_ids[4], 'hired', 'Great sales experience', 5, 4),
            (job_ids[3], candidate_ids[0], 'rejected', 'Not a fit', 2, 4),
        ]
        
        for app in sample_applications:
            cursor.execute('''
                INSERT INTO applications (job_id, candidate_id, status, notes, rating, created_by, applied_date)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (app[0], app[1], app[2], app[3], app[4], app[5]))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

# ============================================================
# ROLE DECORATORS
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Please login first'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Please login first'}), 401
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def hr_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Please login first'}), 401
        if session.get('role') not in ['admin', 'hr_manager']:
            return jsonify({'error': 'HR Manager access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def log_activity(user_id, action, entity_type, entity_id, details=None, ip_address=None):
    try:
        conn = sqlite3.connect('recruitment.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details, ip_address) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, action, entity_type, entity_id, details, ip_address)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging activity: {e}")

# ============================================================
# AUTHENTICATION ROUTES
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, email, full_name, role, department, phone FROM users WHERE username = ? AND password = ? AND is_active = 1",
        (username, hashed_password)
    )
    user = cursor.fetchone()
    
    if user:
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user[0],))
        conn.commit()
        
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['email'] = user[2]
        session['full_name'] = user[3]
        session['role'] = user[4]
        session['department'] = user[5]
        session['phone'] = user[6] if user[6] else ''
        
        log_activity(user[0], 'login', 'user', user[0], f"User logged in", request.remote_addr)
        
        conn.close()
        return jsonify({
            'success': True,
            'user': {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'role': user[4],
                'department': user[5],
                'phone': user[6]
            }
        })
    else:
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    if 'user_id' in session:
        log_activity(session['user_id'], 'logout', 'user', session['user_id'], "User logged out", request.remote_addr)
    session.clear()
    return jsonify({'success': True})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    full_name = data.get('full_name', '')
    role = data.get('role', 'recruiter')
    department = data.get('department', '')
    phone = data.get('phone', '')
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn = sqlite3.connect('recruitment.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, email, full_name, role, department, phone, created_by, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (username, hashed_password, email, full_name, role, department, phone, session.get('user_id', 1), 1)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        if 'user_id' in session:
            log_activity(session['user_id'], 'create_user', 'user', user_id, f"Created user: {username}", request.remote_addr)
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Username or email already exists'}), 400

@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, full_name, role, department, phone, is_active, last_login, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    
    users_list = []
    for user in users:
        users_list.append({
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'full_name': user[3],
            'role': user[4],
            'department': user[5],
            'phone': user[6],
            'is_active': bool(user[7]),
            'last_login': user[8],
            'created_at': user[9]
        })
    
    return jsonify(users_list)

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.json
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET full_name=?, email=?, role=?, department=?, phone=?, is_active=?
        WHERE id=?
    ''', (
        data.get('full_name', ''),
        data.get('email', ''),
        data.get('role', 'recruiter'),
        data.get('department', ''),
        data.get('phone', ''),
        1 if data.get('is_active', True) else 0,
        user_id
    ))
    
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], 'update_user', 'user', user_id, f"Updated user: {user_id}", request.remote_addr)
    
    return jsonify({'success': True})

@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    return jsonify({
        'id': session['user_id'],
        'username': session['username'],
        'email': session['email'],
        'full_name': session.get('full_name', ''),
        'role': session['role'],
        'department': session.get('department', ''),
        'phone': session.get('phone', '')
    })

# ============================================================
# JOBS ROUTES
# ============================================================
@app.route('/api/jobs', methods=['GET'])
@login_required
def get_jobs():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    status = request.args.get('status', 'all')
    role = session.get('role')
    user_id = session['user_id']
    
    query = """
        SELECT j.*, u.full_name as creator_name 
        FROM jobs j 
        LEFT JOIN users u ON j.created_by = u.id
    """
    params = []
    conditions = []
    
    if status != 'all':
        conditions.append("j.status = ?")
        params.append(status)
    
    if role == 'recruiter':
        conditions.append("(j.created_by = ? OR j.assigned_to = ?)")
        params.extend([user_id, user_id])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY j.created_at DESC"
    cursor.execute(query, params)
    jobs = cursor.fetchall()
    conn.close()
    
    jobs_list = []
    for job in jobs:
        jobs_list.append({
            'id': job[0],
            'title': job[1],
            'department': job[2],
            'location': job[3],
            'description': job[4],
            'requirements': job[5],
            'salary_range': job[6],
            'status': job[7],
            'created_by': job[8],
            'assigned_to': job[9],
            'created_at': job[10],
            'updated_at': job[11],
            'creator_name': job[12] if len(job) > 12 else ''
        })
    
    return jsonify(jobs_list)

@app.route('/api/jobs', methods=['POST'])
@login_required
def create_job():
    data = request.json
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO jobs (title, department, location, description, requirements, salary_range, status, created_by, assigned_to, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        data['title'],
        data['department'],
        data['location'],
        data.get('description', ''),
        data.get('requirements', ''),
        data.get('salary_range', ''),
        data.get('status', 'open'),
        session['user_id'],
        data.get('assigned_to', session['user_id'])
    ))
    
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    
    log_activity(session['user_id'], 'create_job', 'job', job_id, f"Created job: {data['title']}", request.remote_addr)
    
    return jsonify({'success': True, 'id': job_id})

@app.route('/api/jobs/<int:job_id>', methods=['PUT'])
@login_required
def update_job(job_id):
    data = request.json
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE jobs 
        SET title=?, department=?, location=?, description=?, requirements=?, salary_range=?, status=?, assigned_to=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (
        data['title'],
        data['department'],
        data['location'],
        data.get('description', ''),
        data.get('requirements', ''),
        data.get('salary_range', ''),
        data['status'],
        data.get('assigned_to', session['user_id']),
        job_id
    ))
    
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], 'update_job', 'job', job_id, f"Updated job: {job_id}", request.remote_addr)
    
    return jsonify({'success': True})

@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
@login_required
def delete_job(job_id):
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], 'delete_job', 'job', job_id, f"Deleted job: {job_id}", request.remote_addr)
    
    return jsonify({'success': True})

# ============================================================
# CANDIDATES ROUTES
# ============================================================
@app.route('/api/candidates', methods=['GET'])
@login_required
def get_candidates():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    role = session.get('role')
    user_id = session['user_id']
    
    if role == 'admin' or role == 'hr_manager':
        cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM candidates WHERE created_by = ? ORDER BY created_at DESC", (user_id,))
    
    candidates = cursor.fetchall()
    conn.close()
    
    candidates_list = []
    for candidate in candidates:
        candidates_list.append({
            'id': candidate[0],
            'first_name': candidate[1],
            'last_name': candidate[2],
            'email': candidate[3],
            'phone': candidate[4],
            'resume': candidate[5],
            'skills': candidate[6],
            'experience': candidate[7],
            'current_company': candidate[8],
            'current_position': candidate[9],
            'status': candidate[10],
            'source': candidate[11],
            'created_by': candidate[12],
            'created_at': candidate[13],
            'updated_at': candidate[14] if len(candidate) > 14 else None
        })
    
    return jsonify(candidates_list)

@app.route('/api/candidates', methods=['POST'])
@login_required
def create_candidate():
    data = request.json
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO candidates (first_name, last_name, email, phone, resume, skills, experience, current_company, current_position, status, source, created_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            data['first_name'],
            data['last_name'],
            data['email'],
            data.get('phone', ''),
            data.get('resume', ''),
            data.get('skills', ''),
            data.get('experience', 0),
            data.get('current_company', ''),
            data.get('current_position', ''),
            data.get('status', 'active'),
            data.get('source', 'direct'),
            session['user_id']
        ))
        
        conn.commit()
        candidate_id = cursor.lastrowid
        conn.close()
        
        log_activity(session['user_id'], 'create_candidate', 'candidate', candidate_id, f"Created candidate: {data['first_name']} {data['last_name']}", request.remote_addr)
        
        return jsonify({'success': True, 'id': candidate_id})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Email already exists'}), 400

@app.route('/api/candidates/<int:candidate_id>', methods=['PUT'])
@login_required
def update_candidate(candidate_id):
    data = request.json
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE candidates 
        SET first_name=?, last_name=?, email=?, phone=?, resume=?, skills=?, experience=?, current_company=?, current_position=?, status=?, source=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (
        data['first_name'],
        data['last_name'],
        data['email'],
        data.get('phone', ''),
        data.get('resume', ''),
        data.get('skills', ''),
        data.get('experience', 0),
        data.get('current_company', ''),
        data.get('current_position', ''),
        data['status'],
        data.get('source', 'direct'),
        candidate_id
    ))
    
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], 'update_candidate', 'candidate', candidate_id, f"Updated candidate: {candidate_id}", request.remote_addr)
    
    return jsonify({'success': True})

@app.route('/api/candidates/<int:candidate_id>', methods=['DELETE'])
@login_required
def delete_candidate(candidate_id):
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates WHERE id=?", (candidate_id,))
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], 'delete_candidate', 'candidate', candidate_id, f"Deleted candidate: {candidate_id}", request.remote_addr)
    
    return jsonify({'success': True})

# ============================================================
# APPLICATIONS ROUTES (WITH SMS NOTIFICATIONS)
# ============================================================
@app.route('/api/applications', methods=['GET'])
@login_required
def get_applications():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    role = session.get('role')
    user_id = session['user_id']
    
    if role == 'admin' or role == 'hr_manager':
        cursor.execute('''
            SELECT a.*, j.title as job_title, c.first_name, c.last_name, c.email, c.phone,
                   u.full_name as reviewer_name, u2.full_name as creator_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN users u ON a.reviewed_by = u.id
            LEFT JOIN users u2 ON a.created_by = u2.id
            ORDER BY a.applied_date DESC
        ''')
    else:
        cursor.execute('''
            SELECT a.*, j.title as job_title, c.first_name, c.last_name, c.email, c.phone,
                   u.full_name as reviewer_name, u2.full_name as creator_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN users u ON a.reviewed_by = u.id
            LEFT JOIN users u2 ON a.created_by = u2.id
            WHERE j.created_by = ? OR j.assigned_to = ?
            ORDER BY a.applied_date DESC
        ''', (user_id, user_id))
    
    applications = cursor.fetchall()
    conn.close()
    
    apps_list = []
    for app in applications:
        apps_list.append({
            'id': app[0],
            'job_id': app[1],
            'candidate_id': app[2],
            'status': app[3],
            'applied_date': app[4],
            'notes': app[5],
            'rating': app[6],
            'reviewed_by': app[7],
            'reviewed_date': app[8],
            'created_by': app[9],
            'job_title': app[11],
            'candidate_name': f"{app[12]} {app[13]}",
            'candidate_email': app[14],
            'candidate_phone': app[15] if len(app) > 15 else '',
            'reviewer_name': app[16] if len(app) > 16 else '',
            'creator_name': app[17] if len(app) > 17 else ''
        })
    
    return jsonify(apps_list)

@app.route('/api/applications', methods=['POST'])
@login_required
def create_application():
    data = request.json
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO applications (job_id, candidate_id, status, notes, rating, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['job_id'],
            data['candidate_id'],
            data.get('status', 'pending'),
            data.get('notes', ''),
            data.get('rating', None),
            session['user_id']
        ))
        
        conn.commit()
        app_id = cursor.lastrowid
        conn.close()
        
        log_activity(session['user_id'], 'create_application', 'application', app_id, f"Created application for job {data['job_id']}", request.remote_addr)
        
        return jsonify({'success': True, 'id': app_id})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Application already exists'}), 400

@app.route('/api/applications/<int:app_id>', methods=['PUT'])
@login_required
def update_application(app_id):
    data = request.json
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    # Get candidate info BEFORE updating (for SMS)
    cursor.execute('''
        SELECT a.status, c.phone, c.first_name, c.last_name, j.title 
        FROM applications a
        JOIN candidates c ON a.candidate_id = c.id
        JOIN jobs j ON a.job_id = j.id
        WHERE a.id = ?
    ''', (app_id,))
    old_data = cursor.fetchone()
    
    if old_data:
        old_status = old_data[0]
        new_status = data['status']
        candidate_phone = old_data[1]
        candidate_name = f"{old_data[2]} {old_data[3]}"
        job_title = old_data[4]
    else:
        old_status = None
        new_status = data['status']
        candidate_phone = None
        candidate_name = ""
        job_title = ""
    
    # Update the application
    cursor.execute('''
        UPDATE applications 
        SET status=?, notes=?, rating=?, reviewed_by=?, reviewed_date=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (
        new_status,
        data.get('notes', ''),
        data.get('rating', None),
        session['user_id'],
        app_id
    ))
    
    conn.commit()
    conn.close()
    
    # ============================================================
    # SEND SMS NOTIFICATION WHEN STATUS CHANGES TO HIRED/REJECTED
    # ============================================================
    if old_status != new_status and candidate_phone and len(candidate_phone) > 5:
        if new_status == 'hired':
            message = f"🎉 Congratulations {candidate_name}! You have been SELECTED for the {job_title} position. Our HR team will contact you soon with the offer details. - TalentHub"
            print(f"📱 Sending HIRED SMS to {candidate_phone}")
        elif new_status == 'rejected':
            message = f"📝 Dear {candidate_name}, thank you for applying for {job_title}. After careful review, we regret to inform you that you have not been selected. We wish you the best in your job search. - TalentHub"
            print(f"📱 Sending REJECTED SMS to {candidate_phone}")
        else:
            message = None
        
        if message:
            # Send SMS in background thread so it doesn't block the response
            threading.Thread(target=send_sms, args=(candidate_phone, message)).start()
    
    log_activity(session['user_id'], 'update_application', 'application', app_id, f"Updated application status to {new_status}", request.remote_addr)
    
    return jsonify({'success': True, 'sms_triggered': new_status in ['hired', 'rejected']})

@app.route('/api/applications/<int:app_id>', methods=['DELETE'])
@login_required
def delete_application(app_id):
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications WHERE id=?", (app_id,))
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], 'delete_application', 'application', app_id, f"Deleted application: {app_id}", request.remote_addr)
    
    return jsonify({'success': True})

# ============================================================
# INTERVIEWS ROUTES (WITH SMS NOTIFICATIONS)
# ============================================================
@app.route('/api/interviews', methods=['GET'])
@login_required
def get_interviews():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    role = session.get('role')
    user_id = session['user_id']
    
    if role == 'admin' or role == 'hr_manager':
        cursor.execute('''
            SELECT i.*, a.job_id, a.candidate_id, j.title as job_title, c.first_name, c.last_name, c.phone,
                   u.full_name as interviewer_name, u2.full_name as creator_name
            FROM interviews i
            JOIN applications a ON i.application_id = a.id
            JOIN jobs j ON a.job_id = j.id
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN users u ON i.interviewer_id = u.id
            LEFT JOIN users u2 ON i.created_by = u2.id
            ORDER BY i.interview_date DESC
        ''')
    elif role == 'interviewer':
        cursor.execute('''
            SELECT i.*, a.job_id, a.candidate_id, j.title as job_title, c.first_name, c.last_name, c.phone,
                   u.full_name as interviewer_name, u2.full_name as creator_name
            FROM interviews i
            JOIN applications a ON i.application_id = a.id
            JOIN jobs j ON a.job_id = j.id
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN users u ON i.interviewer_id = u.id
            LEFT JOIN users u2 ON i.created_by = u2.id
            WHERE i.interviewer_id = ?
            ORDER BY i.interview_date DESC
        ''', (user_id,))
    else:
        cursor.execute('''
            SELECT i.*, a.job_id, a.candidate_id, j.title as job_title, c.first_name, c.last_name, c.phone,
                   u.full_name as interviewer_name, u2.full_name as creator_name
            FROM interviews i
            JOIN applications a ON i.application_id = a.id
            JOIN jobs j ON a.job_id = j.id
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN users u ON i.interviewer_id = u.id
            LEFT JOIN users u2 ON i.created_by = u2.id
            WHERE j.created_by = ? OR j.assigned_to = ?
            ORDER BY i.interview_date DESC
        ''', (user_id, user_id))
    
    interviews = cursor.fetchall()
    conn.close()
    
    interviews_list = []
    for interview in interviews:
        interviews_list.append({
            'id': interview[0],
            'application_id': interview[1],
            'interview_date': interview[2],
            'interview_type': interview[3],
            'interviewer_id': interview[4],
            'feedback': interview[5],
            'status': interview[6],
            'created_by': interview[7],
            'created_at': interview[8],
            'updated_at': interview[9],
            'job_title': interview[11],
            'candidate_name': f"{interview[12]} {interview[13]}",
            'candidate_phone': interview[14] if len(interview) > 14 else '',
            'interviewer_name': interview[15] if len(interview) > 15 else '',
            'creator_name': interview[16] if len(interview) > 16 else ''
        })
    
    return jsonify(interviews_list)

@app.route('/api/interviews', methods=['POST'])
@login_required
def create_interview():
    data = request.json
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO interviews (application_id, interview_date, interview_type, interviewer_id, feedback, status, created_by, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        data['application_id'],
        data['interview_date'],
        data['interview_type'],
        data.get('interviewer_id', None),
        data.get('feedback', ''),
        data.get('status', 'scheduled'),
        session['user_id']
    ))
    
    conn.commit()
    interview_id = cursor.lastrowid
    
    # Get candidate info for SMS notification
    cursor.execute('''
        SELECT c.phone, c.first_name, c.last_name, j.title, i.interview_date
        FROM interviews i
        JOIN applications a ON i.application_id = a.id
        JOIN candidates c ON a.candidate_id = c.id
        JOIN jobs j ON a.job_id = j.id
        WHERE i.id = ?
    ''', (interview_id,))
    interview_data = cursor.fetchone()
    conn.close()
    
    # ============================================================
    # SEND SMS WHEN INTERVIEW IS SCHEDULED
    # ============================================================
    if interview_data and interview_data[0]:
        candidate_phone = interview_data[0]
        candidate_name = f"{interview_data[1]} {interview_data[2]}"
        job_title = interview_data[3]
        interview_datetime = interview_data[4]
        
        message = f"📅 Interview Scheduled! Dear {candidate_name}, your interview for {job_title} is scheduled on {interview_datetime}. Please be prepared and join on time. - TalentHub"
        print(f"📱 Sending INTERVIEW SMS to {candidate_phone}")
        
        threading.Thread(target=send_sms, args=(candidate_phone, message)).start()
    
    log_activity(session['user_id'], 'create_interview', 'interview', interview_id, f"Scheduled interview for application {data['application_id']}", request.remote_addr)
    
    return jsonify({'success': True, 'id': interview_id})

@app.route('/api/interviews/<int:interview_id>', methods=['PUT'])
@login_required
def update_interview(interview_id):
    data = request.json
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE interviews 
        SET interview_date=?, interview_type=?, interviewer_id=?, feedback=?, status=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (
        data['interview_date'],
        data['interview_type'],
        data.get('interviewer_id', None),
        data.get('feedback', ''),
        data['status'],
        interview_id
    ))
    
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], 'update_interview', 'interview', interview_id, f"Updated interview: {interview_id}", request.remote_addr)
    
    return jsonify({'success': True})

@app.route('/api/interviews/<int:interview_id>', methods=['DELETE'])
@login_required
def delete_interview(interview_id):
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interviews WHERE id=?", (interview_id,))
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], 'delete_interview', 'interview', interview_id, f"Deleted interview: {interview_id}", request.remote_addr)
    
    return jsonify({'success': True})

# ============================================================
# DASHBOARD STATS
# ============================================================
@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_stats():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    role = session.get('role')
    user_id = session['user_id']
    
    if role == 'admin' or role == 'hr_manager':
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'open'")
        open_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM candidates")
        total_candidates = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM applications")
        total_applications = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM interviews WHERE status = 'scheduled'")
        scheduled_interviews = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'recruiter' AND is_active = 1")
        total_recruiters = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
        application_status = cursor.fetchall()
        
        cursor.execute('''
            SELECT u.id, u.full_name, u.username, COUNT(DISTINCT a.id) as application_count
            FROM users u
            LEFT JOIN jobs j ON (j.created_by = u.id OR j.assigned_to = u.id)
            LEFT JOIN applications a ON a.job_id = j.id
            WHERE u.role = 'recruiter'
            GROUP BY u.id
            ORDER BY application_count DESC
        ''')
        recruiter_performance = cursor.fetchall()
        
    elif role == 'recruiter':
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE (created_by = ? OR assigned_to = ?) AND status = 'open'", (user_id, user_id))
        open_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM candidates WHERE created_by = ?", (user_id,))
        total_candidates = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE j.created_by = ? OR j.assigned_to = ?
        ''', (user_id, user_id))
        total_applications = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM interviews i
            JOIN applications a ON i.application_id = a.id
            JOIN jobs j ON a.job_id = j.id
            WHERE (j.created_by = ? OR j.assigned_to = ?) AND i.status = 'scheduled'
        ''', (user_id, user_id))
        scheduled_interviews = cursor.fetchone()[0]
        
        total_recruiters = 0
        cursor.execute('''
            SELECT a.status, COUNT(*) 
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE j.created_by = ? OR j.assigned_to = ?
            GROUP BY a.status
        ''', (user_id, user_id))
        application_status = cursor.fetchall()
        recruiter_performance = []
    
    else:
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'open'")
        open_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM candidates")
        total_candidates = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM applications")
        total_applications = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM interviews WHERE interviewer_id = ? AND status = 'scheduled'", (user_id,))
        scheduled_interviews = cursor.fetchone()[0]
        
        total_recruiters = 0
        cursor.execute("SELECT status, COUNT(*) FROM interviews WHERE interviewer_id = ? GROUP BY status", (user_id,))
        application_status = cursor.fetchall()
        recruiter_performance = []
    
    conn.close()
    
    perf_list = []
    for r in recruiter_performance:
        name = r[1] if r[1] else r[2]
        perf_list.append({'name': name, 'count': r[3]})
    
    return jsonify({
        'open_jobs': open_jobs,
        'total_candidates': total_candidates,
        'total_applications': total_applications,
        'scheduled_interviews': scheduled_interviews,
        'total_recruiters': total_recruiters,
        'application_status': [{'status': s[0] if s[0] else 'pending', 'count': s[1]} for s in application_status],
        'recruiter_performance': perf_list
    })

# ============================================================
# ASSIGNMENT ROUTES
# ============================================================
@app.route('/api/assign_recruiters', methods=['GET'])
@login_required
def get_assignable_recruiters():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, username FROM users WHERE role IN ('recruiter', 'hr_manager') AND is_active = 1")
    recruiters = cursor.fetchall()
    conn.close()
    
    return jsonify([{'id': r[0], 'name': r[1] if r[1] else r[2], 'username': r[2]} for r in recruiters])

@app.route('/api/assign_interviewers', methods=['GET'])
@login_required
def get_assignable_interviewers():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, username FROM users WHERE role IN ('interviewer', 'hr_manager', 'admin') AND is_active = 1")
    interviewers = cursor.fetchall()
    conn.close()
    
    return jsonify([{'id': i[0], 'name': i[1] if i[1] else i[2], 'username': i[2]} for i in interviewers])
# Applicant applies for a job
@app.route('/api/applicant/apply', methods=['POST'])
@login_required
def applicant_apply():
    if session.get('role') != 'applicant':
        return jsonify({'error': 'Only applicants can apply'}), 403
    
    data = request.json
    job_id = data.get('job_id')
    cover_letter = data.get('cover_letter', '')
    
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    # Check if candidate exists for this applicant
    cursor.execute("SELECT id FROM candidates WHERE email = ?", (session['email'],))
    candidate = cursor.fetchone()
    
    if not candidate:
        # Create candidate record for this applicant
        cursor.execute('''
            INSERT INTO candidates (first_name, last_name, email, phone, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session.get('full_name', session['username']).split()[0] if session.get('full_name') else session['username'],
            session.get('full_name', '').split()[-1] if len(session.get('full_name', '').split()) > 1 else '',
            session['email'],
            session.get('phone', ''),
            session['user_id']
        ))
        candidate_id = cursor.lastrowid
    else:
        candidate_id = candidate[0]
    
    # Check if already applied
    cursor.execute("SELECT id FROM applications WHERE job_id = ? AND candidate_id = ?", (job_id, candidate_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'You have already applied for this job'}), 400
    
    # Create application
    cursor.execute('''
        INSERT INTO applications (job_id, candidate_id, notes, created_by)
        VALUES (?, ?, ?, ?)
    ''', (job_id, candidate_id, cover_letter, session['user_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})
# Get applicant's own applications
@app.route('/api/my-applications', methods=['GET'])
@login_required
def get_my_applications():
    if session.get('role') != 'applicant':
        return jsonify([])
    
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    # Get candidate ID from email
    cursor.execute("SELECT id FROM candidates WHERE email = ?", (session['email'],))
    candidate = cursor.fetchone()
    
    if not candidate:
        conn.close()
        return jsonify([])
    
    candidate_id = candidate[0]
    
    cursor.execute('''
        SELECT a.id, j.title, j.department, a.status, a.applied_date, a.notes
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.candidate_id = ?
        ORDER BY a.applied_date DESC
    ''', (candidate_id,))
    
    apps = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': a[0],
        'job_title': a[1],
        'department': a[2],
        'status': a[3],
        'applied_date': a[4],
        'notes': a[5]
    } for a in apps])
# Get applicant's interviews
@app.route('/api/my-interviews', methods=['GET'])
@login_required
def get_my_interviews():
    if session.get('role') != 'applicant':
        return jsonify([])
    
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    # Get candidate ID from email
    cursor.execute("SELECT id FROM candidates WHERE email = ?", (session['email'],))
    candidate = cursor.fetchone()
    
    if not candidate:
        conn.close()
        return jsonify([])
    
    candidate_id = candidate[0]
    
    cursor.execute('''
        SELECT i.id, j.title, i.interview_date, i.interview_type, i.feedback, i.status,
               u.full_name as interviewer_name
        FROM interviews i
        JOIN applications a ON i.application_id = a.id
        JOIN jobs j ON a.job_id = j.id
        LEFT JOIN users u ON i.interviewer_id = u.id
        WHERE a.candidate_id = ?
        ORDER BY i.interview_date DESC
    ''', (candidate_id,))
    
    interviews = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': i[0],
        'job_title': i[1],
        'interview_date': i[2],
        'interview_type': i[3],
        'feedback': i[4],
        'status': i[5],
        'interviewer_name': i[6] if i[6] else 'TBD'
    } for i in interviews])
# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    if os.path.exists('recruitment.db'):
        os.remove('recruitment.db')
    
    init_db()
    print("\n" + "="*60)
    print("🚀 TALENTHUB RECRUITMENT SYSTEM")
    print("="*60)
    #print("\n🔐 LOGIN CREDENTIALS:")
    print("-" * 30)
    #print("Admin:      admin / admin123")
    #print("HR Manager: hr_manager / hr123")
    #print("Recruiter 1: recruiter1 / rec123")
    #print("Recruiter 2: recruiter2 / rec123")
    #print("Interviewer: interviewer1 / int123")
    
    #print("\n📱 SMS NOTIFICATION FEATURES:")
    #print("-" * 30)
    #print("✅ When application status → 'hired' → SMS sent to candidate")
    #print("✅ When application status → 'rejected' → SMS sent to candidate")
    #print("✅ When interview is scheduled → SMS sent to candidate")
    
    #print("\n📞 SAMPLE CANDIDATE PHONE NUMBERS:")
    #print("-" * 30)
    #print("John Doe:    +1234567895")
    #print("Jane Smith:  +1234567896")
    #print("Bob Johnson: +1234567897")
    #print("Alice Brown: +1234567898")
    #print("Charlie Wilson: +1234567899")
    
    #print("\n⚠️  SMS NOTES:")
    #print("-" * 30)
    #print("• Using free Textbelt API (1 SMS/day for testing)")
    #print("• For production, replace with Twilio or AWS SNS")
    #print("• SMS sending runs in background - doesn't block UI")
    
    print("\n" + "="*60)
    print("🌐 Access: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True)