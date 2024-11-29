from sqlite3 import connect, Row
import time
import sqlite3

database = "student.db"

# Function to set WAL mode
def set_wal_mode():
    db = connect(database)
    db.execute('PRAGMA journal_mode=WAL;')
    db.close()

def retry_operation(func):
    def wrapper(*args, **kwargs):
        retries = 10  # Increase retries
        while retries > 0:
            try:
                return func(*args, **kwargs)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    time.sleep(2)  # Increase delay to 2 seconds
                    retries -= 1
                else:
                    raise
        raise sqlite3.OperationalError("Database is locked after multiple retries.")
    return wrapper

def getprocess(sql):
    set_wal_mode()  # Ensure WAL mode is set
    rows = []
    db = connect(database)
    db.row_factory = Row
    cursor = db.cursor()
    cursor.execute(sql)
    data = cursor.fetchall()
    rows = [dict(item) for item in data]
    cursor.close()
    db.close()
    return rows

def postprocess(sql):
    set_wal_mode()  # Ensure WAL mode is set
    db = connect(database)
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
    result = cursor.rowcount > 0
    cursor.close()
    db.close()
    return result

def getall_record(table):
    sql = f"SELECT * FROM `{table}`"
    return getprocess(sql)


def get_attendance(table):
    sql = f"""
    SELECT 
        a.idno, 
        s.lastname,
        s.firstname,
        s.course,
        s.level, 
        a.timelogged 
    FROM {table} a 
    JOIN students s 
    ON a.idno = s.idno;
    """
    return getprocess(sql)

def check_attendance_exists(table, idno):
    sql = f"SELECT 1 FROM {table} WHERE idno = ? AND DATE(timelogged) = DATE('now')"
    db = connect(database)
    cursor = db.cursor()
    cursor.execute(sql, (idno,))
    exists = cursor.fetchone() is not None
    cursor.close()
    db.close()
    return exists


@retry_operation
def savestudent(table, **kwargs):
    set_wal_mode()  # Ensure WAL mode is set
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    flds = "','".join(keys)
    data = "','".join(values)
    sql = f"INSERT INTO `{table}` ('{flds}') VALUES ('{data}')"
    db = connect(database)
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
    result = cursor.rowcount > 0
    cursor.close()
    db.close()
    return result

def student_exists(table, idno):
    sql = f"SELECT 1 FROM `{table}` WHERE idno = ?"
    db = connect(database)
    cursor = db.cursor()
    cursor.execute(sql, (idno,))
    exists = cursor.fetchone() is not None
    cursor.close()
    db.close()
    return exists

def get_student_by_id(idno):
    sql = "SELECT idno, lastname, firstname, course, level FROM students WHERE idno = ?"
    db = connect(database)
    db.row_factory = sqlite3.Row  # This is important to return rows as dictionaries
    cursor = db.cursor()
    cursor.execute(sql, (idno,))
    student = cursor.fetchone()
    cursor.close()
    db.close()
    if student:
        return {
            "idno": student["idno"],
            "lastname": student["lastname"],
            "firstname": student["firstname"],
            "course": student["course"],
            "level": student["level"]
        }
    return None

def edit_student_in_db(table, idno, **kwargs):
    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values()) + [idno]
    sql = f"UPDATE {table} SET {set_clause} WHERE idno = ?"
    db = connect(database)
    cursor = db.cursor()
    cursor.execute(sql, values)
    db.commit()
    success = cursor.rowcount > 0
    cursor.close()
    db.close()
    return success

def delete_student_from_db(table, idno):
    sql = f"DELETE FROM {table} WHERE idno = ?"
    db = connect(database)
    cursor = db.cursor()
    cursor.execute(sql, (idno,))
    db.commit()
    success = cursor.rowcount > 0
    cursor.close()
    db.close()
    return success

# Define get_all_students function
def get_all_students(table):
    sql = f"SELECT * FROM {table}"
    return getprocess(sql)

@retry_operation
def check_login(table, username, password):
    sql = f"SELECT * FROM {table} WHERE username = ? AND password = ?"
    db = connect(database)
    cursor = db.cursor()
    cursor.execute(sql, (username, password))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user is not None
