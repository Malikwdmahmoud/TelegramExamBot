import sqlite3

DB_NAME = "exams.db"


# إنشاء قاعدة البيانات
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


# إدخال امتحان جديد
def insert_exam(year, department, subject, file_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO exams (year, department, subject, file_id)
    VALUES (?, ?, ?, ?)
    """, (year, department, subject, file_id))

    conn.commit()
    conn.close()


# جلب السنوات
def get_years():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT year FROM exams")
    data = [row[0] for row in cur.fetchall()]

    conn.close()
    return data


# جلب الأقسام
def get_departments(year):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT department FROM exams WHERE year=?", (year,))
    data = [row[0] for row in cur.fetchall()]

    conn.close()
    return data


# جلب المواد
def get_subjects(year, department):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT subject FROM exams 
        WHERE year=? AND department=?
    """, (year, department))

    data = [row[0] for row in cur.fetchall()]

    conn.close()
    return data


# جلب الامتحانات
def get_exams(year, department, subject):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT file_id FROM exams
        WHERE year=? AND department=? AND subject=?
    """, (year, department, subject))

    data = [row[0] for row in cur.fetchall()]

    conn.close()
    return data
