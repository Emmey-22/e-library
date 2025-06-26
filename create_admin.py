import sqlite3
from werkzeug.security import generate_password_hash

# Database path
db_path = 'database.db'

# Admin credentials
admin_username = 'MrAdmin'  
admin_password = 'admin123'  # Change this if you want
admin_email = 'admin@example.com'  # Optional
hashed_password = generate_password_hash(admin_password)

# Connect and insert
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if admin already exists
cursor.execute("SELECT * FROM users WHERE username = ? AND role = 'admin'", (admin_username,))
if cursor.fetchone():
    print(f"Admin user '{admin_username}' already exists.")
else:
    cursor.execute(
        "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'admin')",
        (admin_username, admin_email, hashed_password)
    )
    conn.commit()
    print(f"Admin user '{admin_username}' created successfully.")

conn.close()
