from flask import Flask, render_template, request, redirect, session
import mysql.connector
import webbrowser
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_super_secret_key_here"

# ---------------- DB CONNECTION ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root"
)

cursor = db.cursor()

# CREATE DATABASE
cursor.execute("CREATE DATABASE IF NOT EXISTS healthcare_db")
cursor.execute("USE healthcare_db")


# ---------------- HELPER: CHECK COLUMN ----------------
def column_exists(table, column):
    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
    return cursor.fetchone() is not None


# ---------------- SETUP DATABASE ----------------
def setup_database():

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        password VARCHAR(255),
        role VARCHAR(50)
    )
    """)

    # 🔥 AUTO ADD PATIENT RECORD COLUMNS
    new_columns = {
        "age": "INT",
        "bp": "VARCHAR(20)",
        "diseases": "TEXT",
        "medicines": "TEXT"
    }

    for col, dtype in new_columns.items():
        if not column_exists("users", col):
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
            print(f"✅ Added column: {col}")

    # DOCTORS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        specialization VARCHAR(100)
    )
    """)

    # APPOINTMENTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        doctor_id INT,
        date DATE,
        status VARCHAR(50) DEFAULT 'Confirmed',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
    )
    """)

    # INSERT DEFAULT DOCTORS
    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO doctors (name, specialization) VALUES
        ('Dr. Ravi Kumar', 'Cardiologist'),
        ('Dr. Priya Sharma', 'Dermatologist'),
        ('Dr. Anil Reddy', 'Neurologist')
                    
        """)
    # 🔥 AUTO CREATE ADMIN USER
cursor.execute("SELECT * FROM users WHERE email='admin@gmail.com'")
if not cursor.fetchone():
    admin_pass = generate_password_hash("admin123")

    cursor.execute("""
    INSERT INTO users (name, email, password, role)
    VALUES (%s, %s, %s, %s)
    """, ("Admin", "admin@gmail.com", admin_pass, "admin"))

    print("✅ Admin created: admin@gmail.com / admin123")

    db.commit()


# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')


# ---------------- REGISTER ----------------
# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        age = request.form.get('age')
        bp = request.form.get('bp')
        diseases = request.form.get('diseases')
        medicines = request.form.get('medicines')

        hashed_password = generate_password_hash(password)

        # Check existing user
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return "Email already registered!"

        # 🔥 AUTO ADMIN LOGIC
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        admin_exists = cursor.fetchone()[0]

        role = "admin" if admin_exists == 0 else "user"

        cursor.execute("""
        INSERT INTO users (name, email, password, role, age, bp, diseases, medicines)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, email, hashed_password, role, age, bp, diseases, medicines))

        db.commit()
        return redirect('/login')

    return render_template('register.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['role'] = user[4]
            return redirect('/dashboard')

        return "Invalid credentials"

    return render_template('login.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('dashboard.html', name=session['user_name'])
    return redirect('/login')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- BOOK APPOINTMENT ----------------
@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        doctor_id = request.form['doctor']
        date = request.form['date']

        try:
            cursor.execute(
                "INSERT INTO appointments (user_id, doctor_id, date, status) VALUES (%s, %s, %s, %s)",
                (session['user_id'], doctor_id, date, "Confirmed")
            )
            db.commit()
            return redirect('/appointments')
        except Exception as e:
            return f"Error: {str(e)}"

    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()

    return render_template('book.html', doctors=doctors)


# ---------------- VIEW APPOINTMENTS ----------------
@app.route('/appointments')
def appointments():
    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute("""
        SELECT a.id, d.name, d.specialization, a.date, a.status
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.user_id = %s
        ORDER BY a.date DESC
    """, (session['user_id'],))

    data = cursor.fetchall()
    return render_template('appointments.html', appointments=data)


# ---------------- CANCEL APPOINTMENT ----------------
@app.route('/cancel/<int:id>', methods=['POST'])
def cancel(id):
    cursor.execute("UPDATE appointments SET status='Cancelled' WHERE id=%s", (id,))
    db.commit()
    return redirect('/appointments')


# ---------------- REPORTS ----------------
@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute("""
    SELECT name, age, bp, diseases, medicines
    FROM users WHERE id=%s
    """, (session['user_id'],))

    user = cursor.fetchone()
    return render_template('reports.html', user=user)


# ---------------- UPDATE REPORT ----------------
@app.route('/update_report', methods=['POST'])
def update_report():
    cursor.execute("""
    UPDATE users
    SET age=%s, bp=%s, diseases=%s, medicines=%s
    WHERE id=%s
    """, (
        request.form['age'],
        request.form['bp'],
        request.form['diseases'],
        request.form['medicines'],
        session['user_id']
    ))

    db.commit()
    return redirect('/reports')


# ---------------- DELETE ACCOUNT ----------------
@app.route('/delete_report', methods=['POST'])
def delete_report():
    cursor.execute("DELETE FROM users WHERE id=%s", (session['user_id'],))
    db.commit()
    session.clear()
    return redirect('/register')

# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin():
    if 'user_id' not in session or session['role'] != 'admin':
        return "Access Denied ❌"

    return render_template('admin.html')
# ---------------- ADMIN DOCTORS ----------------
@app.route('/admin/doctors', methods=['GET', 'POST'])
def admin_doctors():
    if session.get('role') != 'admin':
        return "Access Denied ❌"

    if request.method == 'POST':
        name = request.form['name']
        specialization = request.form['specialization']

        cursor.execute(
            "INSERT INTO doctors (name, specialization) VALUES (%s, %s)",
            (name, specialization)
        )
        db.commit()

    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()

    return render_template('admin_doctors.html', doctors=doctors)


# ---------------- DELETE DOCTOR ----------------
@app.route('/delete_doctor/<int:id>')
def delete_doctor(id):
    if session.get('role') != 'admin':
        return "Access Denied ❌"

    cursor.execute("DELETE FROM doctors WHERE id=%s", (id,))
    db.commit()

    return redirect('/admin/doctors')


# ---------------- ADMIN APPOINTMENTS ----------------
@app.route('/admin/appointments')
def admin_appointments():
    if session.get('role') != 'admin':
        return "Access Denied ❌"

    cursor.execute("""
        SELECT a.id, u.name, d.name, a.date, a.status
        FROM appointments a
        JOIN users u ON a.user_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
    """)

    data = cursor.fetchall()

    return render_template('admin_appointments.html', appointments=data)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    setup_database()
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True)