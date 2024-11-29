from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dbhelper import savestudent, get_all_students, student_exists, check_login, get_student_by_id, edit_student_in_db, delete_student_from_db, get_attendance, check_attendance_exists
from sqlite3 import connect
import base64
import os
import qrcode

database = "student.db"  # Define your database name

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = 'your_secret_key'  # Needed for flashing messages

@app.route("/")
def first():
    students = get_all_students("students")
    return render_template("login.html", students=students)

@app.route("/index")
def index():
    students = get_all_students("students")
    return render_template("index.html", students=students, pagetitle="STUDENT")

@app.route("/list")
def list_students():
    students = get_all_students("students")
    return render_template("list.html", students=students, pagetitle="STUDENTLIST")

@app.route("/attendance")
def list_attendance():
    attendances = get_attendance("attendance")
    return render_template("attendance.html", attendances=attendances, pagetitle="ATTENDANCE CHECKER")

@app.route("/get_student", methods=["GET"])
def get_student():
    idno = request.args.get("idno")
    student = get_student_by_id(idno)
    if student:
        return jsonify(student)
    else:
        return jsonify({"error": "Student not found"}), 404

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if check_login("users", username, password):
        return redirect(url_for("list_students"))
    else:
        flash("Invalid Account, please try again", "error")
        return redirect(url_for("login"))

@app.route("/edit_student", methods=["POST"])
def edit_student():
    idno = request.form["idno"]
    lastname = request.form["lastname"]
    firstname = request.form["firstname"]
    course = request.form["course"]
    level = request.form["level"]
    success = edit_student_in_db("students", idno, lastname=lastname, firstname=firstname, course=course, level=level)
    if success:
        return redirect(url_for("list_students"))
    else:
        return "Error updating student."

@app.route("/delete_student", methods=["POST"])
def delete_student():
    idno = request.form["idno"]
    success = delete_student_from_db("students", idno)
    if success:
        return redirect(url_for("list_students"))
    else:
        return "Error deleting student."

@app.route("/generate_qr_code", methods=["GET"])
def generate_qr_code():
    idno = request.args.get("idno")
    qr_code_path = os.path.join('static/qrcodes', f"{idno}_qrcode.png")
    qr = qrcode.make(idno)
    qr.save(qr_code_path)
    return jsonify({"qr_code_url": url_for('static', filename=f"qrcodes/{idno}_qrcode.png")})

@app.route("/record_attendance", methods=["POST"])
def record_attendance():
    data = request.json
    idno = data.get("idno")

    # Check if the idno is already recorded today
    exists = check_attendance_exists("attendance", idno)
    if exists:
        return jsonify({"success": False, "message": "Attendance already recorded."})

    # Record attendance
    sql = "INSERT INTO attendance (idno) VALUES (?)"
    db = connect(database)
    cursor = db.cursor()
    cursor.execute(sql, (idno,))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"success": True})

@app.route("/add_student", methods=["POST"])
def add_student():
    idno = request.form["idno"]
    lastname = request.form["lastname"]
    firstname = request.form["firstname"]
    course = request.form["course"]
    level = request.form["level"]
    image_data = request.form["imageData"]

    # Validate that IDNo and Level are numeric
    if not idno.isdigit() or not level.isdigit():
        flash("IDNo and Level must be numeric. Cannot add student.", "error")
        return redirect(url_for("index"))

    # Check if the IDNo already exists
    if student_exists("students", idno):
        flash("IDNo already exists. Cannot add student.", "error")
        return redirect(url_for("index"))

    # Generate automatic image file path
    image_file_name = f"{idno}.png"
    image_file_path = os.path.join('static/profiles', image_file_name)

    # Decode image data and save to file
    image_data = image_data.split(",")[1]  # Remove the "data:image/png;base64," part
    with open(image_file_path, "wb") as fh:
        fh.write(base64.b64decode(image_data))

    # Generate QR code
    qr_code_path = os.path.join('static/qrcodes', f"{idno}_qrcode.png")
    qr = qrcode.make(idno)
    qr.save(qr_code_path)

    # Save to database
    success = savestudent(
        table="students",
        idno=idno,
        lastname=lastname,
        firstname=firstname,
        course=course,
        level=level,
        images=image_file_path  # Save the file path to the database
    )
    if success:
        return redirect(url_for("index"))
    else:
        return "Error adding student."

if __name__ == "__main__":
    app.run(debug=True)
