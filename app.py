import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecret'
app.config['UPLOAD_FOLDER'] = 'reports'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class Patient(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(10))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    contact = db.Column(db.String(15))
    address = db.Column(db.String(200))
    emergency_contact = db.Column(db.String(15), nullable=True)
    blood_group = db.Column(db.String(5))
    diagnosis = db.Column(db.String(100))
    admit_date = db.Column(db.String(20))
    discharge_date = db.Column(db.String(20))
    report_file = db.Column(db.String(100))

def generate_patient_id(name, dob):
    prefix = name.strip().upper()[:4].ljust(4, 'X')
    year = dob.split('-')[0]
    return f'{prefix}{year}'

@app.route('/')
def index():
    patients = Patient.query.all()
    return render_template('index.html', patients=patients)

@app.route('/add', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        pid = generate_patient_id(name, dob)

        if Patient.query.get(pid):
            flash("Patient with this ID already exists.", "danger")
            return redirect(url_for('add_patient'))

        if not (request.form['contact'].isdigit() and len(request.form['contact']) == 10):
            flash("Contact number must be 10 digits.", "danger")
            return redirect(url_for('add_patient'))

        emergency = request.form['emergency']
        if emergency and (not emergency.isdigit() or len(emergency) != 10):
            flash("Emergency contact must be 10 digits if provided.", "danger")
            return redirect(url_for('add_patient'))


        file = request.files['report']
        filename = None
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(f"{pid}_report.pdf")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        from datetime import datetime
        birth_year = int(dob.split("-")[0])
        age = datetime.now().year - birth_year

        patient = Patient(
            id=pid,
            name=name,
            dob=dob,
            age=age,
            gender=request.form['gender'],
            contact=request.form['contact'],
            address=request.form['address'],
            emergency_contact=request.form['emergency'],
            blood_group=request.form['blood'],
            diagnosis=request.form['diagnosis'],
            admit_date=request.form['admit'],
            discharge_date=request.form['discharge'],
            report_file=filename
        )
        db.session.add(patient)
        db.session.commit()
        flash("Patient added successfully!", "success")
        return redirect(url_for('index'))

    return render_template('add_patient.html', edit=False)

@app.route('/edit/<pid>', methods=['GET', 'POST'])
def edit_patient(pid):
    patient = Patient.query.get(pid)
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        patient.name = request.form['name']
        patient.dob = request.form['dob']
        patient.age = int(request.form['age'])
        patient.gender = request.form['gender']
        patient.contact = request.form['contact']
        patient.address = request.form['address']
        patient.emergency_contact = request.form['emergency']
        patient.blood_group = request.form['blood']
        patient.diagnosis = request.form['diagnosis']
        patient.admit_date = request.form['admit']
        patient.discharge_date = request.form['discharge']

        file = request.files['report']
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(f"{pid}_report.pdf")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            patient.report_file = filename

        db.session.commit()
        flash("Patient updated successfully.", "success")
        return redirect(url_for('index'))

    return render_template('add_patient.html', patient=patient, edit=True)

@app.route('/delete/<pid>', methods=['POST'])
def delete_patient(pid):
    patient = Patient.query.get(pid)
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for('index'))

    if patient.report_file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], patient.report_file)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(patient)
    db.session.commit()
    flash("Patient deleted successfully.", "info")
    return redirect(url_for('index'))

@app.route('/patient/<pid>')
def view_patient(pid):
    patient = Patient.query.get(pid)
    return render_template('view_patient.html', patient=patient)

@app.route('/report/<filename>')
def report(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    results = []

    if query:
        results = Patient.query.filter(
            (Patient.id.ilike(f'%{query}%')) |
            (Patient.contact.ilike(f'%{query}%'))
        ).all()

    return render_template('index.html', patients=results, search_query=query)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
