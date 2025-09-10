from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from .auth import roles_required
from .models import db, Patient, Doctor, Appointment, MedicalRecord


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    patient_count = Patient.query.count()
    doctor_count = Doctor.query.count()
    appt_count = Appointment.query.count()
    recent_records = MedicalRecord.query.order_by(MedicalRecord.created_at.desc()).limit(5).all()
    return render_template(
        "dashboard.html",
        patient_count=patient_count,
        doctor_count=doctor_count,
        appt_count=appt_count,
        recent_records=recent_records,
    )


# Patients
@main_bp.route("/patients")
@login_required
def patients_list():
    q = request.args.get("q", "").strip()
    query = Patient.query
    if q:
        like = f"%{q}%"
        query = query.filter(Patient.name.like(like))
    patients = query.order_by(Patient.created_at.desc()).all()
    return render_template("patients/list.html", patients=patients, q=q)


@main_bp.route("/patients/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "nurse", "clerk")
def patients_new():
    if request.method == "POST":
        name = request.form.get("name").strip()
        gender = request.form.get("gender")
        dob = request.form.get("dob")
        contact = request.form.get("contact")
        address = request.form.get("address")
        dob_dt = datetime.strptime(dob, "%Y-%m-%d") if dob else None
        p = Patient(name=name, gender=gender, dob=dob_dt, contact=contact, address=address)
        db.session.add(p)
        db.session.commit()
        flash("患者已创建", "success")
        return redirect(url_for("main.patients_list"))
    return render_template("patients/form.html", patient=None)


@main_bp.route("/patients/<int:pid>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "nurse", "clerk")
def patients_edit(pid):
    patient = Patient.query.get_or_404(pid)
    if request.method == "POST":
        patient.name = request.form.get("name").strip()
        patient.gender = request.form.get("gender")
        dob = request.form.get("dob")
        patient.dob = datetime.strptime(dob, "%Y-%m-%d") if dob else None
        patient.contact = request.form.get("contact")
        patient.address = request.form.get("address")
        db.session.commit()
        flash("患者已更新", "success")
        return redirect(url_for("main.patients_list"))
    return render_template("patients/form.html", patient=patient)


@main_bp.route("/patients/<int:pid>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def patients_delete(pid):
    patient = Patient.query.get_or_404(pid)
    db.session.delete(patient)
    db.session.commit()
    flash("患者已删除", "info")
    return redirect(url_for("main.patients_list"))


@main_bp.route("/patients/<int:pid>")
@login_required
def patients_detail(pid):
    patient = Patient.query.get_or_404(pid)
    records = MedicalRecord.query.filter_by(patient_id=pid).order_by(MedicalRecord.created_at.desc()).all()
    return render_template("patients/detail.html", patient=patient, records=records)


# Medical Records
@main_bp.route("/patients/<int:pid>/records/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "doctor", "nurse")
def record_new(pid):
    patient = Patient.query.get_or_404(pid)
    doctors = Doctor.query.order_by(Doctor.name.asc()).all()
    if request.method == "POST":
        doctor_id = request.form.get("doctor_id") or None
        diagnosis = request.form.get("diagnosis")
        notes = request.form.get("notes")
        rec = MedicalRecord(patient_id=pid, doctor_id=doctor_id, diagnosis=diagnosis, notes=notes)
        db.session.add(rec)
        db.session.commit()
        flash("病例已添加", "success")
        return redirect(url_for("main.patients_detail", pid=pid))
    return render_template("records/form.html", patient=patient, doctors=doctors)


# Doctors
@main_bp.route("/doctors")
@login_required
def doctors_list():
    doctors = Doctor.query.order_by(Doctor.name.asc()).all()
    return render_template("doctors/list.html", doctors=doctors)


@main_bp.route("/doctors/new", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def doctors_new():
    if request.method == "POST":
        d = Doctor(
            name=request.form.get("name").strip(),
            department=request.form.get("department"),
            title=request.form.get("title"),
        )
        db.session.add(d)
        db.session.commit()
        flash("医生已创建", "success")
        return redirect(url_for("main.doctors_list"))
    return render_template("doctors/form.html", doctor=None)


@main_bp.route("/doctors/<int:did>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def doctors_edit(did):
    d = Doctor.query.get_or_404(did)
    if request.method == "POST":
        d.name = request.form.get("name").strip()
        d.department = request.form.get("department")
        d.title = request.form.get("title")
        db.session.commit()
        flash("医生已更新", "success")
        return redirect(url_for("main.doctors_list"))
    return render_template("doctors/form.html", doctor=d)


@main_bp.route("/doctors/<int:did>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def doctors_delete(did):
    d = Doctor.query.get_or_404(did)
    db.session.delete(d)
    db.session.commit()
    flash("医生已删除", "info")
    return redirect(url_for("main.doctors_list"))


# Appointments
@main_bp.route("/appointments")
@login_required
def appointments_list():
    appts = (
        Appointment.query.order_by(Appointment.scheduled_at.desc()).all()
    )
    return render_template("appointments/list.html", appts=appts)


@main_bp.route("/appointments/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "clerk")
def appointments_new():
    patients = Patient.query.order_by(Patient.name.asc()).all()
    doctors = Doctor.query.order_by(Doctor.name.asc()).all()
    if request.method == "POST":
        patient_id = int(request.form.get("patient_id"))
        doctor_id = int(request.form.get("doctor_id"))
        scheduled_at = datetime.strptime(request.form.get("scheduled_at"), "%Y-%m-%dT%H:%M")
        reason = request.form.get("reason")
        appt = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            scheduled_at=scheduled_at,
            reason=reason,
        )
        db.session.add(appt)
        db.session.commit()
        flash("预约已创建", "success")
        return redirect(url_for("main.appointments_list"))
    return render_template("appointments/form.html", patients=patients, doctors=doctors, appt=None)


@main_bp.route("/appointments/<int:aid>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "clerk")
def appointments_edit(aid):
    appt = Appointment.query.get_or_404(aid)
    patients = Patient.query.order_by(Patient.name.asc()).all()
    doctors = Doctor.query.order_by(Doctor.name.asc()).all()
    if request.method == "POST":
        appt.patient_id = int(request.form.get("patient_id"))
        appt.doctor_id = int(request.form.get("doctor_id"))
        appt.scheduled_at = datetime.strptime(request.form.get("scheduled_at"), "%Y-%m-%dT%H:%M")
        appt.status = request.form.get("status")
        appt.reason = request.form.get("reason")
        db.session.commit()
        flash("预约已更新", "success")
        return redirect(url_for("main.appointments_list"))
    return render_template("appointments/form.html", patients=patients, doctors=doctors, appt=appt)


@main_bp.route("/appointments/<int:aid>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def appointments_delete(aid):
    appt = Appointment.query.get_or_404(aid)
    db.session.delete(appt)
    db.session.commit()
    flash("预约已删除", "info")
    return redirect(url_for("main.appointments_list"))

