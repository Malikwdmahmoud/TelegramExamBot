import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        id SERIAL PRIMARY KEY,
        year TEXT,
        department TEXT,
        subject TEXT,
        file_id TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


def insert_exam(year, department, subject, file_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO exams (year, department, subject, file_id)
    VALUES (%s, %s, %s, %s)
    """, (year, department, subject, file_id))

    conn.commit()
    cur.close()
    conn.close()


def get_exams(year, department):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT id, subject, file_id FROM exams
    WHERE year=%s AND department=%s
    """, (year, department))

    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows


def get_all_exams():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM exams")
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows


def delete_exam(exam_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM exams WHERE id=%s", (exam_id,))

    conn.commit()
    cur.close()
    conn.close()

def update_exam_subject(exam_id, new_subject):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE exams SET subject=%s WHERE id=%s",
        (new_subject, exam_id),
    )

    conn.commit()
    cur.close()
    conn.close()