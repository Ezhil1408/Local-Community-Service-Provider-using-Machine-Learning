import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'community_service.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add payment_mode column to bookings table
try:
    cursor.execute("ALTER TABLE bookings ADD COLUMN payment_mode TEXT DEFAULT 'Online'")
    print("Successfully added payment_mode column to bookings table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column payment_mode already exists")
    else:
        print(f"Error adding column: {e}")

# Commit changes and close connection
conn.commit()
conn.close()