import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# USERS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL CHECK(role IN ('admin', 'lecturer', 'student')),
    level INTEGER CHECK(level IN (100, 200, 300, 400))
)
''')

# COURSES TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL UNIQUE,
    course_title TEXT NOT NULL,
    level INTEGER NOT NULL CHECK(level IN (100, 200, 300, 400))
)
''')

# BOOKS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    file_path TEXT NOT NULL,
    course_id INTEGER NOT NULL,
    uploaded_by INTEGER NOT NULL,
    FOREIGN KEY(course_id) REFERENCES courses(id),
    FOREIGN KEY(uploaded_by) REFERENCES users(id)
)
''')

# LECTURER_COURSES TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS lecturer_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecturer_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    FOREIGN KEY(lecturer_id) REFERENCES users(id),
    FOREIGN KEY(course_id) REFERENCES courses(id),
    UNIQUE(lecturer_id, course_id)
)
''')

# BORROW RECORDS (OPTIONAL)
c.execute('''
CREATE TABLE IF NOT EXISTS borrow_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    access_date TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES users(id),
    FOREIGN KEY(book_id) REFERENCES books(id)
)
''')
# MATERIALS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    course_id INTEGER,
    uploaded_by INTEGER,
    FOREIGN KEY(course_id) REFERENCES courses(id),
    FOREIGN KEY(uploaded_by) REFERENCES users(id)
);
''')

conn.commit()
conn.close()
print("Database setup complete.")
