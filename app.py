from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3
import hashlib
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Database initialization with proper error handling
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
    
    # Users table
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
    
    # Candidates table
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
    
    # Insert default users
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, role, department, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('admin', admin_password, 'admin@recruitment.com', 'System Administrator', 'admin', 'IT', 1)
    )
    
    hr_password = hashlib.sha256('hr123'.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, role, department, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('hr_manager', hr_password, 'hr@recruitment.com', 'HR Manager', 'hr_manager', 'Human Resources', 1)
    )
    
    rec_password = hashlib.sha256('rec123'.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, role, department, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('recruiter1', rec_password, 'recruiter1@recruitment.com', 'Sarah Johnson', 'recruiter', 'Engineering', 1)
    )
    
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, role, department, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('recruiter2', rec_password, 'recruiter2@recruitment.com', 'Mike Peters', 'recruiter', 'Sales', 1)
    )
    
    int_password = hashlib.sha256('int123'.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, role, department, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('interviewer1', int_password, 'interviewer@recruitment.com', 'David Chen', 'interviewer', 'Engineering', 1)
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
    
    # Sample candidates
    sample_candidates = [
        ('John', 'Doe', 'john.doe@email.com', '555-0101', 'Experienced developer', 'Python, JavaScript, SQL', 5, 'Tech Corp', 'Senior Developer', 'active', 'linkedin', 3),
        ('Jane', 'Smith', 'jane.smith@email.com', '555-0102', 'Frontend expert', 'React, Vue, Angular', 3, 'Web Solutions', 'Frontend Lead', 'active', 'website', 3),
        ('Bob', 'Johnson', 'bob.johnson@email.com', '555-0103', 'Sales professional', 'Sales, CRM, Negotiation', 7, 'Sales Inc', 'Sales Director', 'active', 'referral', 4),
        ('Alice', 'Brown', 'alice.brown@email.com', '555-0104', 'HR specialist', 'Recruitment, HRIS, Employee Relations', 4, 'HR Solutions', 'HR Generalist', 'active', 'linkedin', 2),
        ('Charlie', 'Wilson', 'charlie.wilson@email.com', '555-0105', 'Design expert', 'Figma, Adobe XD, Sketch', 2, 'Design Studio', 'Junior Designer', 'active', 'portfolio', 3)
    ]
    
    for candidate in sample_candidates:
        cursor.execute('''
            INSERT INTO candidates (first_name, last_name, email, phone, resume, skills, experience, current_company, current_position, status, source, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', candidate)
    
    # After creating sample jobs and candidates, add SAMPLE APPLICATIONS
    cursor.execute("SELECT COUNT(*) FROM applications")
    if cursor.fetchone()[0] == 0:
        # Get job and candidate IDs
        cursor.execute("SELECT id FROM jobs LIMIT 5")
        job_ids = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT id FROM candidates LIMIT 5")
        candidate_ids = [row[0] for row in cursor.fetchall()]
        
        sample_applications = [
            (job_ids[0], candidate_ids[0], 'reviewed', 'Strong candidate', 4, 3),      # Sarah's job
            (job_ids[0], candidate_ids[1], 'interviewed', 'Good skills', 5, 3),       # Sarah's job
            (job_ids[1], candidate_ids[2], 'pending', 'Initial review', 3, 3),        # Sarah's job
            (job_ids[2], candidate_ids[3], 'reviewed', 'HR interview completed', 4, 2), # HR Manager's job
            (job_ids[3], candidate_ids[4], 'hired', 'Great sales experience', 5, 4),   # Mike's job
            (job_ids[3], candidate_ids[0], 'rejected', 'Not a fit', 2, 4),             # Mike's job
        ]
        
        for app in sample_applications:
            cursor.execute('''
                INSERT INTO applications (job_id, candidate_id, status, notes, rating, created_by, applied_date)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (app[0], app[1], app[2], app[3], app[4], app[5]))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

# Role-based decorators
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

# Log activity function
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

# Routes
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
        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user[0],)
        )
        conn.commit()
        
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['email'] = user[2]
        session['full_name'] = user[3]
        session['role'] = user[4]
        session['department'] = user[5]
        
        # Log activity
        log_activity(user[0], 'login', 'user', user[0], f"User logged in from {request.remote_addr}", request.remote_addr)
        
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
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn = sqlite3.connect('recruitment.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, email, full_name, role, department, created_by, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (username, hashed_password, email, full_name, role, department, session.get('user_id', 1), 1)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        if 'user_id' in session:
            log_activity(session['user_id'], 'create_user', 'user', user_id, f"Created user: {username} with role: {role}", request.remote_addr)
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({'success': False, 'error': 'Username or email already exists'}), 400

@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, full_name, role, department, is_active, last_login, created_at FROM users ORDER BY created_at DESC")
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
            'is_active': bool(user[6]),
            'last_login': user[7],
            'created_at': user[8]
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
        SET full_name=?, email=?, role=?, department=?, is_active=?
        WHERE id=?
    ''', (
        data.get('full_name', ''),
        data.get('email', ''),
        data.get('role', 'recruiter'),
        data.get('department', ''),
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
        'department': session.get('department', '')
    })

# Jobs endpoints with user filtering
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
    
    # Filter based on role
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

# Candidates endpoints with user filtering
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
        # Recruiters can only see candidates they created
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

# Applications endpoints
@app.route('/api/applications', methods=['GET'])
@login_required
def get_applications():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    role = session.get('role')
    user_id = session['user_id']
    
    if role == 'admin' or role == 'hr_manager':
        cursor.execute('''
            SELECT a.*, j.title as job_title, c.first_name, c.last_name, c.email,
                   u.full_name as reviewer_name, u2.full_name as creator_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN users u ON a.reviewed_by = u.id
            LEFT JOIN users u2 ON a.created_by = u2.id
            ORDER BY a.applied_date DESC
        ''')
    else:
        # Recruiters can only see applications for jobs they created or assigned
        cursor.execute('''
            SELECT a.*, j.title as job_title, c.first_name, c.last_name, c.email,
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
            'reviewer_name': app[15],
            'creator_name': app[16] if len(app) > 16 else ''
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
    
    cursor.execute('''
        UPDATE applications 
        SET status=?, notes=?, rating=?, reviewed_by=?, reviewed_date=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (
        data['status'],
        data.get('notes', ''),
        data.get('rating', None),
        session['user_id'],
        app_id
    ))
    
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], 'update_application', 'application', app_id, f"Updated application status to {data['status']}", request.remote_addr)
    
    return jsonify({'success': True})

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

# Interviews endpoints
@app.route('/api/interviews', methods=['GET'])
@login_required
def get_interviews():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    role = session.get('role')
    user_id = session['user_id']
    
    if role == 'admin' or role == 'hr_manager':
        cursor.execute('''
            SELECT i.*, a.job_id, a.candidate_id, j.title as job_title, c.first_name, c.last_name,
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
        # Interviewers can see interviews they are assigned to
        cursor.execute('''
            SELECT i.*, a.job_id, a.candidate_id, j.title as job_title, c.first_name, c.last_name,
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
        # Recruiters can see interviews for their jobs
        cursor.execute('''
            SELECT i.*, a.job_id, a.candidate_id, j.title as job_title, c.first_name, c.last_name,
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
            'interviewer_name': interview[14],
            'creator_name': interview[15] if len(interview) > 15 else ''
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
    conn.close()
    
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

# Dashboard stats endpoint
@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_stats():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    role = session.get('role')
    user_id = session['user_id']
    
    # Get statistics based on role
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
        
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM applications 
            GROUP BY status
        ''')
        application_status = cursor.fetchall()
        
        # Fixed recruiter performance query
        cursor.execute('''
            SELECT 
                u.id,
                u.full_name,
                u.username,
                COUNT(DISTINCT a.id) as application_count
            FROM users u
            LEFT JOIN jobs j ON (j.created_by = u.id OR j.assigned_to = u.id)
            LEFT JOIN applications a ON a.job_id = j.id
            WHERE u.role = 'recruiter'
            GROUP BY u.id
            ORDER BY application_count DESC
        ''')
        recruiter_performance = cursor.fetchall()
        
    elif role == 'recruiter':
        cursor.execute('''
            SELECT COUNT(*) FROM jobs 
            WHERE (created_by = ? OR assigned_to = ?) AND status = 'open'
        ''', (user_id, user_id))
        open_jobs = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM candidates WHERE created_by = ?
        ''', (user_id,))
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
    
    else:  # interviewer
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'open'")
        open_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM candidates")
        total_candidates = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM applications")
        total_applications = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM interviews 
            WHERE interviewer_id = ? AND status = 'scheduled'
        ''', (user_id,))
        scheduled_interviews = cursor.fetchone()[0]
        
        total_recruiters = 0
        
        cursor.execute('''
            SELECT i.status, COUNT(*) 
            FROM interviews i
            WHERE i.interviewer_id = ?
            GROUP BY i.status
        ''', (user_id,))
        application_status = cursor.fetchall()
        
        recruiter_performance = []
    
    conn.close()
    
    # Format the recruiter performance data properly
    perf_list = []
    for r in recruiter_performance:
        name = r[1] if r[1] else r[2]  # Use full_name if available, else username
        perf_list.append({
            'name': name,
            'count': r[3]  # application_count
        })
    
    return jsonify({
        'open_jobs': open_jobs,
        'total_candidates': total_candidates,
        'total_applications': total_applications,
        'scheduled_interviews': scheduled_interviews,
        'total_recruiters': total_recruiters,
        'application_status': [{'status': s[0] if s[0] else 'pending', 'count': s[1]} for s in application_status],
        'recruiter_performance': perf_list
    })

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

if __name__ == '__main__':
    # Delete existing database to start fresh with sample data
    if os.path.exists('recruitment.db'):
        os.remove('recruitment.db')
    
    init_db()
    print("\n" + "="*50)
    print("Recruitment Management System Started!")
    print("="*50)
    print("\nDefault User Credentials:")
    print("-" * 30)
    print("Admin:      admin / admin123")
    print("HR Manager: hr_manager / hr123")
    print("Recruiter 1: recruiter1 / rec123")
    print("Recruiter 2: recruiter2 / rec123")
    print("Interviewer: interviewer1 / int123")
    print("="*50)
    print("\nSample Data Added:")
    print("-" * 30)
    print("✓ 5 Jobs created")
    print("✓ 5 Candidates created") 
    print("✓ 6 Applications created (showing recruiter performance)")
    print("="*50)
    print("\nAccess the application at: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True)