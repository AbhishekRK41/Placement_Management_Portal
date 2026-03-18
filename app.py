from flask import Flask, render_template, request, redirect, session, flash, send_from_directory
from config import Config
from database import db
from models import *
import os
import csv
from flask import Response

app = Flask(__name__)
app.config.from_object(Config)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- STUDENT REGISTER ----------------

@app.route("/register_student", methods=["GET","POST"])
def register_student():

    if request.method == "POST":

        existing = Student.query.filter_by(email=request.form["email"]).first()

        if existing:
            flash("Student already registered")
            return redirect("/register_student")

        student = Student(
            name=request.form["name"],
            email=request.form["email"],
            password=request.form["password"]
        )

        db.session.add(student)
        db.session.commit()

        flash("Registration successful")
        return redirect("/")

    return render_template("register_student.html")


# ---------------- COMPANY REGISTER ----------------

@app.route("/register_company", methods=["GET","POST"])
def register_company():

    if request.method == "POST":

        existing = Company.query.filter_by(email=request.form["email"]).first()

        if existing:
            flash("Company already exists")
            return redirect("/register_company")

        company = Company(
            name=request.form["name"],
            email=request.form["email"],
            hr_contact=request.form["hr"],
            website=request.form["website"],
            password=request.form["password"]
        )

        db.session.add(company)
        db.session.commit()

        flash("Company registered. Wait for admin approval.")
        return redirect("/")

    return render_template("register_company.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]
    role = request.form["role"]

    if role == "admin":

        if email == "admin" and password == "admin":

            session["role"] = "admin"

            return redirect("/admin_dashboard")


    if role == "student":

        student = Student.query.filter_by(email=email,password=password).first()

        if student:

            session["role"] = "student"
            session["student_id"] = student.id

            return redirect("/student_dashboard")


    if role == "company":

        company = Company.query.filter_by(email=email,password=password).first()

        if company and company.approved:

            session["role"] = "company"
            session["company_id"] = company.id

            return redirect("/company_dashboard")

    flash("Invalid Login")
    return redirect("/")


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin_dashboard")
def admin_dashboard():

    students = Student.query.count()
    companies = Company.query.count()
    drives = PlacementDrive.query.count()
    apps = Application.query.count()

    pending_companies = Company.query.filter_by(approved=False).all()
    pending_drives = PlacementDrive.query.filter_by(status="Pending").all()

    history = History.query.all()

    return render_template(
        "admin_dashboard.html",
        students=students,
        companies=companies,
        drives=drives,
        apps=apps,
        pending_companies=pending_companies,
        pending_drives=pending_drives,
        history=history
    )


# ---------------- APPROVE COMPANY ----------------

@app.route("/approve_company/<int:id>")
def approve_company(id):

    company = Company.query.get(id)
    company.approved = True

    history = History(
        name=company.name,
        action="Company Approved"
    )

    db.session.add(history)
    db.session.commit()

    flash("Company Approved")

    return redirect("/admin_dashboard")


# ---------------- APPROVE DRIVE ----------------

@app.route("/approve_drive/<int:id>")
def approve_drive(id):

    drive = PlacementDrive.query.get(id)
    drive.status = "Approved"

    history = History(
        name=f"{drive.company.name} - {drive.job_title}",
        action="Drive Approved"
    )

    db.session.add(history)
    db.session.commit()

    flash("Drive Approved")

    return redirect("/admin_dashboard")


# ---------------- STUDENT DASHBOARD ----------------

@app.route("/student_dashboard")
def student_dashboard():

    student_id = session.get("student_id")

    drives = PlacementDrive.query.filter_by(status="Approved").all()

    applications = Application.query.filter_by(student_id=student_id).all()

    # create dictionary: drive_id -> application
    app_map = {app.drive_id: app for app in applications}

    return render_template(
        "student_dashboard.html",
        drives=drives,
        app_map=app_map
    )


# ---------------- APPLY WITH RESUME ----------------

@app.route("/apply/<int:drive_id>", methods=["POST"])
def apply(drive_id):

    student_id = session.get("student_id")

    existing = Application.query.filter_by(
        student_id=student_id,
        drive_id=drive_id
    ).first()

    if existing:
        flash("Already applied")
        return redirect("/student_dashboard")

    file = request.files["resume"]

    filename = ""

    if file:
        filename = file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    application = Application(
        student_id=student_id,
        drive_id=drive_id,
        status="Pending",
        resume=filename
    )

    db.session.add(application)
    db.session.commit()

    flash("Application Submitted")

    return redirect("/student_dashboard")


# ---------------- COMPANY DASHBOARD ----------------

@app.route("/company_dashboard")
def company_dashboard():

    company_id = session.get("company_id")

    company = Company.query.get(company_id)

    drives = PlacementDrive.query.filter_by(company_id=company_id).all()

    return render_template(
        "company_dashboard.html",
        company=company,
        drives=drives
    )


# ---------------- VIEW APPLICATIONS ----------------

@app.route("/view_applications/<int:drive_id>")
def view_applications(drive_id):

    applications = Application.query.filter_by(drive_id=drive_id).all()

    return render_template(
        "view_applications.html",
        applications=applications
    )


# ---------------- UPDATE STATUS ----------------

@app.route("/update_status/<int:app_id>/<status>")
def update_status(app_id, status):

    application = Application.query.get(app_id)

    application.status = status

    db.session.commit()

    flash("Status Updated")

    return redirect(request.referrer)


# ---------------- DOWNLOAD RESUME ----------------

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


# ---------------- CREATE DRIVE ----------------

@app.route("/create_drive/<int:company_id>", methods=["GET","POST"])
def create_drive(company_id):

    if request.method == "POST":

        drive = PlacementDrive(
            company_id=company_id,
            job_title=request.form["title"],
            description=request.form["description"],
            eligibility=request.form["eligibility"],
            deadline=request.form["deadline"],
            status="Pending"
        )

        db.session.add(drive)
        db.session.commit()

        flash("Placement Drive Created")

        return redirect("/company_dashboard")

    return render_template("create_drive.html", company_id=company_id)

#----------------- History Search -------------------

@app.route("/search_history", methods=["POST"])
def search_history():

    keyword = request.form["keyword"]

    history = History.query.filter(History.name.contains(keyword)).all()

    students = Student.query.count()
    companies = Company.query.count()
    drives = PlacementDrive.query.count()
    apps = Application.query.count()

    pending_companies = Company.query.filter_by(approved=False).all()
    pending_drives = PlacementDrive.query.filter_by(status="Pending").all()

    return render_template(
        "admin_dashboard.html",
        students=students,
        companies=companies,
        drives=drives,
        apps=apps,
        pending_companies=pending_companies,
        pending_drives=pending_drives,
        history=history
    )

@app.route("/download_history")
def download_history():

    history = History.query.all()

    def generate():

        data = [["Name", "Action"]]

        for h in history:
            data.append([h.name, h.action])

        for row in data:
            yield ",".join(row) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=history.csv"}
    )

@app.route("/download_students")
def download_students():

    students = Student.query.all()

    def generate():

        data = [["Name", "Email", "Roll Number", "Semester"]]

        for s in students:
            data.append([
                s.name,
                s.email,
                s.roll_number,
                str(s.semester)
            ])

        for row in data:
            yield ",".join(row) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=students.csv"}
    )
    
if __name__ == "__main__":
    app.run(debug=True)