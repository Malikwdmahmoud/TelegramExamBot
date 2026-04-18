import sqlite3

DB_NAME = "exams.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year TEXT,
        department TEXT,
        subject TEXT,
        file_id TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_exam(year, department, subject, file_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO exams (year, department, subject, file_id)
    VALUES (?, ?, ?, ?)
    """, (year, department, subject, file_id))

    conn.commit()
    conn.close()

def get_exams(year, department):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    SELECT id, subject, file_id FROM exams
    WHERE year=? AND department=?
    """, (year, department))

    rows = cur.fetchall()
    conn.close()
    return rows
