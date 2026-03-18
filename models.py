from database import db


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    roll_number = db.Column(db.String(50))
    semester = db.Column(db.Integer)

    applications = db.relationship("Application", backref="student", lazy=True)


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(200))
    password = db.Column(db.String(100))

    approved = db.Column(db.Boolean, default=False)

    drives = db.relationship("PlacementDrive", backref="company", lazy=True)


class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"))

    job_title = db.Column(db.String(200))
    description = db.Column(db.Text)
    eligibility = db.Column(db.String(200))
    deadline = db.Column(db.String(50))

    status = db.Column(db.String(50), default="Pending")

    applications = db.relationship("Application", backref="drive", lazy=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("student.id"))
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drive.id"))

    status = db.Column(db.String(50), default="Pending")

    resume = db.Column(db.String(200))


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200))
    action = db.Column(db.String(200))