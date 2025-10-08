import sqlite3
from datetime import datetime

def init_database():
    """Initialize the SQLite database and create the rsvp table."""
    conn = sqlite3.connect('rsvp_database.db')
    cursor = conn.cursor()
    
    # Create the rsvp table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rsvp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            email TEXT NOT NULL,
            dietary_option TEXT NOT NULL,
            event_date DATE NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()