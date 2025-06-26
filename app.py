from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash, get_flashed_messages
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Replace with a strong key in production

# 🔌 Database connection helper
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def home():
    error = None

    if request.method == 'POST':
        role = request.form['role']
        username = request.form.get('username')
        password = request.form['password']
        matric_no = request.form.get('matric_no')

        conn = get_db()
        cur = conn.cursor()

        if role == 'student':
            cur.execute("SELECT * FROM users WHERE username = ? AND role = 'student'", (matric_no,))
            user = cur.fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['level'] = user['level']  
                session['role'] = 'student'
                flash("You are logged in as Student.", "info")
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid student credentials."

        elif role == 'lecturer':
            cur.execute("SELECT * FROM users WHERE username = ? AND role = 'lecturer'", (username,))
            user = cur.fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = 'lecturer'
                flash("You are logged in as Lecturer.", "info")
                return redirect(url_for('lecturer_dashboard'))
            else:
                error = "Invalid lecturer credentials."

        elif role == 'admin':
            cur.execute("SELECT * FROM users WHERE username = ? AND role = 'admin'", (username,))
            user = cur.fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = 'admin'
                flash("You are logged in as Admin.", "info")
                return redirect(url_for('admin_dashboard'))
            else:
                error = "Invalid admin credentials."

    return render_template("home.html", error=error)


# 🟢 Register route (for students only)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        level = request.form['level']
        role = 'student'

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute('INSERT INTO users (username, email, password, level, role) VALUES (?, ?, ?, ?, ?)',
                        (username, email, password, level, role))
            conn.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            flash("User already exists.", "danger")
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        matric_no = request.form['matric_no']
        email = request.form['email']  # We can later improve this with email verification or OTP
       
        conn = get_db()
        cursor = conn.cursor()
        # Check if the user exists with the given matric number and email
        cursor.execute("SELECT * FROM users WHERE username = ? AND email= ? AND role = 'student'", (matric_no, email))
        user = cursor.fetchone()

        if user:
            # Redirect to reset confirmation page (or change password page)
            flash('Verified. You may now reset your password.', 'success')
            return redirect(url_for('change_password', matric_no=matric_no))
        else:
            flash('Invalid matric number or email.', 'danger')
    return render_template('reset_password.html')

# chnage_password route
@app.route('/change_password/<path:matric_no>', methods=['GET', 'POST'])
def change_password(matric_no):    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('change_password', matric_no=matric_no))

        # Update the user's password in the database
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password = ? WHERE username = ? AND role = 'student'", (new_password, matric_no))
        conn.commit()
        conn.close()

        flash('Password updated successfully. Please login.', 'success')
        return redirect(url_for('home'))
    return render_template('change_password.html', matric_no=matric_no)

# 🧭 Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    student_level = int(session['level'])  # Stored during login
    search_query = request.args.get('q', '').strip().lower()

    conn = get_db()
    cur = conn.cursor()

    # Get all courses for this level and below
    cur.execute("SELECT * FROM courses WHERE level <= ? ORDER BY level DESC", (student_level,))
    courses = cur.fetchall()

    # For each course, fetch materials
    all_courses = []
    for c in courses:
        cur.execute("SELECT * FROM materials WHERE course_id = ?", (c['id'],))
        materials = cur.fetchall()

        # Filter by search keyword
        if search_query:
            materials = [m for m in materials if search_query in m['title'].lower()]

        course_data = dict(c)
        course_data['materials'] = materials
        all_courses.append(course_data)

    conn.close()
    return render_template('dashboard.html', all_courses=all_courses)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    search_query = request.args.get('q', '').strip().lower()

    conn = get_db()
    cur = conn.cursor()

    # 🔹 Fetch all lecturers and all courses
    cur.execute("SELECT * FROM users WHERE role='lecturer'")
    all_lecturers = cur.fetchall()

    cur.execute("SELECT * FROM courses ORDER BY level")
    all_courses = cur.fetchall()

    # Check which lecturers have been assigned courses
    lecturers_with_assignment = []
    for lec in all_lecturers:
        cur.execute("SELECT 1 FROM lecturer_courses WHERE lecturer_id = ?", (lec['id'],))
        assigned = cur.fetchone() is not None
        lec_info = dict(lec)
        lec_info['id'] = int(lec['id'])  # 🔑 Ensure consistent type
        lec_info['assigned'] = assigned
        lecturers_with_assignment.append(lec_info)
    lecturers = lecturers_with_assignment

    # Fetch uploaded materials
    cur.execute("""
        SELECT m.id, m.title, m.filename, c.course_code, c.level, u.username AS uploader
        FROM materials m
        JOIN courses c ON m.course_id = c.id
        JOIN users u ON m.uploaded_by = u.id
        ORDER BY c.level, c.course_code
    """)
    all_materials = cur.fetchall()

    if search_query:
        all_materials = [m for m in all_materials if search_query in m['title'].lower()]

    # Fetch assigned courses
    cur.execute("""
        SELECT lc.id AS assignment_id, u.id AS lecturer_id, u.username AS lecturer, 
               c.course_code, c.course_title
        FROM lecturer_courses lc
        JOIN users u ON lc.lecturer_id = u.id
        JOIN courses c ON lc.course_id = c.id
    """)
    lecturer_course_rows = cur.fetchall()

    # Build mapping: lecturer_id → list of assigned courses
    lecturer_courses_map = {}
    for row in lecturer_course_rows:
        lec_id = row['lecturer_id']
        if lec_id not in lecturer_courses_map:
            lecturer_courses_map[lec_id] = []
        lecturer_courses_map[lec_id].append({
            'course_code': row['course_code'],
            'course_title': row['course_title'],
            'assignment_id': row['assignment_id']
        })

    # Find unassigned courses
    cur.execute("SELECT course_id FROM lecturer_courses")
    assigned_course_ids = [row['course_id'] for row in cur.fetchall()]
    unassigned_courses = [c for c in all_courses if c['id'] not in assigned_course_ids]

    # Get all courses again grouped with materials
    all_courses_with_materials = []
    for c in all_courses:
        cur.execute("SELECT * FROM materials WHERE course_id = ?", (c['id'],))
        materials = cur.fetchall()
        course_info = dict(c)
        course_info['materials'] = materials
        all_courses_with_materials.append(course_info)

    conn.close()
    return render_template(
        'admin_dashboard.html',
        lecturers=lecturers, courses=all_courses, all_materials=all_materials, lecturer_courses=lecturer_course_rows, all_courses=all_courses_with_materials, unassigned_courses=unassigned_courses, lecturer_courses_map=lecturer_courses_map
    )


@app.route('/admin/unassign_course/<int:assignment_id>', methods=['POST'])
def unassign_course(assignment_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM lecturer_courses WHERE id = ?", (assignment_id,))
    conn.commit()
    conn.close()

    flash("Course unassigned from lecturer.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_lecturer', methods=['POST'])
def add_lecturer():
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    username = request.form['username']
    email = request.form['email']
    password = generate_password_hash(request.form['password'])

    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'lecturer')",
                     (username, email, password))
        conn.commit()
        flash("Lecturer added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("Lecturer username already exists.", "danger")
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_course', methods=['POST'])
def add_course():
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    course_code = request.form['course_code']
    course_title = request.form['course_title']
    level = request.form['level']

    conn = get_db()
    try:
        conn.execute("INSERT INTO courses (course_code, course_title, level) VALUES (?, ?, ?)", (course_code, course_title, level))
        conn.commit()
        flash("Course added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("Course already exists.", "danger")
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/assign_course', methods=['POST'])
def assign_course():
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    lecturer_username = request.form['lecturer_username']
    course_code = request.form['course_code']

    conn = get_db()
    cur = conn.cursor()

    # Get lecturer ID
    cur.execute("SELECT id FROM users WHERE username = ? AND role = 'lecturer'", (lecturer_username,))
    lecturer = cur.fetchone()

    # Get course ID
    cur.execute("SELECT id FROM courses WHERE course_code = ?", (course_code,))
    course = cur.fetchone()

    if lecturer and course:
        # Check if already assigned
        cur.execute("SELECT * FROM lecturer_courses WHERE lecturer_id = ? AND course_id = ?", (lecturer['id'], course['id']))
        exists = cur.fetchone()
        if not exists:
            cur.execute("INSERT INTO lecturer_courses (lecturer_id, course_id) VALUES (?, ?)", (lecturer['id'], course['id']))
            conn.commit()
            flash("Course assigned successfully!", "success")
        else:
            flash("Course already assigned to this lecturer.", "warning")
    else:
        flash("Lecturer or course not found.", "danger")

    conn.close()
    return redirect(url_for('admin_dashboard', tab='assignCourse'))




@app.route('/admin/delete_lecturer/<int:lecturer_id>', methods=['POST'])
def delete_lecturer(lecturer_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    conn = get_db()
    cur = conn.cursor()

    # Remove from lecturer_courses first (if any)
    cur.execute("DELETE FROM lecturer_courses WHERE lecturer_id = ?", (lecturer_id,))
    cur.execute("DELETE FROM users WHERE id = ? AND role = 'lecturer'", (lecturer_id,))
    conn.commit()
    conn.close()

    flash("Lecturer deleted successfully.", "success")

    # Preserve current tab
    tab = request.args.get('tab', 'viewLecturers')
    return redirect(url_for('admin_dashboard') + f'#' + tab)


@app.route('/admin/edit_course/<int:course_id>', methods=['POST'])
def edit_course(course_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    course_code = request.form['course_code']
    course_title = request.form['course_title']
    level = request.form['level']

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE courses SET course_code = ?, course_title = ?, level = ? WHERE id = ?",
                (course_code, course_title, level, course_id))
    conn.commit()
    conn.close()

    flash("Course updated successfully.", "success")
    return redirect(url_for('admin_dashboard', tab='viewCourses'))

@app.route('/admin/edit_material/<int:material_id>', methods=['POST'])
def edit_material(material_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    title = request.form['title']

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE materials SET title = ? WHERE id = ?", (title, material_id))
    conn.commit()
    conn.close()

    flash("Material updated successfully.", "success")
    return redirect(url_for('admin_dashboard', tab='viewCourses'))

@app.route('/change_password', methods=['POST'])
def admin_change_password():
    if 'user_id' not in session:
        flash('Access denied. Please log in first.', 'danger')
        return redirect(url_for('home'))

    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cur.fetchone()

    if not check_password_hash(user['password'], current_password):
        flash("Current password is incorrect.", 'danger')
        return redirect(url_for('admin_dashboard') + '?tab=changePassword')

    if new_password != confirm_password:
        flash("New passwords do not match.", 'danger')
        return redirect(url_for('admin_dashboard') + '?tab=changePassword')

    hashed_password = generate_password_hash(new_password)
    cur.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, session['user_id']))
    conn.commit()
    flash("Password updated successfully!", 'success')
    return redirect(url_for('admin_dashboard') + '?tab=changePassword')

@app.route('/admin/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()

    flash("Course deleted successfully.", "success")
    return redirect(url_for('admin_dashboard', tab='viewCourses'))

@app.route('/admin/edit_lecturer/<int:lecturer_id>', methods=['POST'])
def edit_lecturer(lecturer_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    conn = get_db()
    cur = conn.cursor()

    if password.strip():
        hashed = generate_password_hash(password)
        cur.execute("UPDATE users SET username = ?, email = ?, password = ? WHERE id = ?", 
                    (username, email, hashed, lecturer_id))
    else:
        cur.execute("UPDATE users SET username = ?, email = ? WHERE id = ?", 
                    (username, email, lecturer_id))

    conn.commit()
    conn.close()
    flash("Lecturer details updated.", "success")
    return redirect(url_for('admin_dashboard', tab='viewLecturers'))



import os

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/lecturer/dashboard')
def lecturer_dashboard():
    if 'user_id' not in session or session['role'] != 'lecturer':
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    lecturer_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # Get assigned courses
    cur.execute("""
        SELECT c.id, c.course_code, c.course_title 
        FROM courses c
        JOIN lecturer_courses lc ON c.id = lc.course_id
        WHERE lc.lecturer_id = ?
    """, (lecturer_id,))
    courses = cur.fetchall()

    # Attach uploaded materials to each course
    assigned_courses = []
    for c in courses:
        cur.execute("SELECT * FROM materials WHERE course_id = ?", (c['id'],))
        materials = cur.fetchall()
        course_data = dict(c)
        course_data['materials'] = materials
        assigned_courses.append(course_data)

    conn.close()
    return render_template('lecturer_dashboard.html', assigned_courses=assigned_courses)

@app.route('/lecturer/upload', methods=['POST'])
def upload_material():
    if 'user_id' not in session or session['role'] != 'lecturer':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    title = request.form['title']
    course_id = request.form['course_id']
    file = request.files['file']

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        conn = get_db()
        conn.execute(
            "INSERT INTO materials (title, filename, course_id, uploaded_by) VALUES (?, ?, ?, ?)",
            (title, filename, course_id, session['user_id'])
        )
        conn.commit()
        conn.close()
        flash("Material uploaded.", "success")
    return redirect(url_for('lecturer_dashboard'))

@app.route('/admin/delete_material/<int:material_id>', methods=['POST'])
def delete_material(material_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()

    # Get filename before deleting
    cur.execute("SELECT filename FROM materials WHERE id = ?", (material_id,))
    row = cur.fetchone()
    if row:
        filename = row['filename']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete from database
        cur.execute("DELETE FROM materials WHERE id = ?", (material_id,))
        conn.commit()
        flash("Material deleted successfully.", "success")
    else:
        flash("Material not found.", "warning")

    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/lecturer/change_password', methods=['POST'])
def lecturer_change_password():
    if 'user_id' not in session:
        flash('Access denied. Please log in first.', 'danger')
        return redirect(url_for('home'))

    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    conn = get_db()
    cur = conn.cursor()

    # Fetch user from users table
    cur.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cur.fetchone()

    # Check if user is lecturer
    if not user or user['role'] != 'lecturer':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('home'))

    # Validate current password
    if not check_password_hash(user['password'], current_password):
        flash("Current password is incorrect.", 'danger')
        return redirect(url_for('lecturer_dashboard') + '?tab=changePassword')

    if new_password != confirm_password:
        flash("New passwords do not match.", 'danger')
        return redirect(url_for('lecturer_dashboard') + '?tab=changePassword')

    # Update password
    hashed_password = generate_password_hash(new_password)
    cur.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, session['user_id']))
    conn.commit()
    flash("Password updated successfully!", 'success')
    return redirect(url_for('lecturer_dashboard') + '?tab=changePassword')


# 🚪 Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.after_request
def add_cache_control(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
    app.run(debug=True)