import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('recruitment.db')
cursor = conn.cursor()

# Get all recruiters
cursor.execute("SELECT id, full_name FROM users WHERE role = 'recruiter'")
recruiters = cursor.fetchall()

if not recruiters:
    print("No recruiters found!")
    exit()

print(f"Found {len(recruiters)} recruiters")

# Get all jobs and candidates
cursor.execute("SELECT id, title, created_by FROM jobs")
jobs = cursor.fetchall()

cursor.execute("SELECT id, first_name, last_name FROM candidates")
candidates = cursor.fetchall()

# Add 5 applications for each recruiter
statuses = ['pending', 'reviewed', 'interviewed', 'hired']
added = 0

for recruiter_id, recruiter_name in recruiters:
    recruiter_jobs = [j for j in jobs if j[2] == recruiter_id]
    
    if not recruiter_jobs:
        print(f"⚠️  {recruiter_name} has no jobs. Creating a sample job...")
        cursor.execute('''
            INSERT INTO jobs (title, department, location, description, requirements, status, created_by, assigned_to)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (f'Position for {recruiter_name}', 'General', 'Remote', 'Sample job', 'Experience required', 'open', recruiter_id, recruiter_id))
        job_id = cursor.lastrowid
        recruiter_jobs = [(job_id, f'Position for {recruiter_name}', recruiter_id)]
    
    for i in range(5):
        job = random.choice(recruiter_jobs)
        candidate = random.choice(candidates)
        status = random.choice(statuses)
        
        try:
            cursor.execute('''
                INSERT INTO applications (job_id, candidate_id, status, notes, rating, created_by, applied_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                job[0],
                candidate[0],
                status,
                f'Application for {job[1]}',
                random.randint(1, 5) if status != 'pending' else None,
                recruiter_id,
                datetime.now() - timedelta(days=random.randint(1, 30))
            ))
            added += 1
        except:
            pass

conn.commit()

print(f"\n✅ Added {added} applications!")

# Show results
cursor.execute('''
    SELECT u.full_name, COUNT(a.id) 
    FROM users u
    LEFT JOIN jobs j ON j.created_by = u.id
    LEFT JOIN applications a ON a.job_id = j.id
    WHERE u.role = 'recruiter'
    GROUP BY u.id
''')
results = cursor.fetchall()
print("\n📊 Updated Performance:")
for name, count in results:
    print(f"  {name}: {count} applications")

conn.close()
print("\n✨ Done! Refresh your dashboard.")