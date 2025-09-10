from flask import Flask, render_template, request, redirect, url_for, flash, g, abort
import os
from datetime import datetime

from db import get_db, close_db, init_db, ensure_initialized, query_one, query_all


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Ensure DB is ready and connections close properly
    app.teardown_appcontext(close_db)

    # Flask 3.x 移除了 before_first_request，这里在应用创建时初始化
    ensure_initialized()

    @app.route('/')
    def index():
        return redirect(url_for('patients'))

    # ------------------------- Patients -------------------------
    @app.route('/patients')
    def patients():
        q = request.args.get('q', '').strip()
        db = get_db()
        if q:
            rows = query_all(
                db,
                """
                SELECT * FROM patients
                WHERE name LIKE ? OR phone LIKE ? OR id_number LIKE ?
                ORDER BY created_at DESC
                """,
                (f'%{q}%', f'%{q}%', f'%{q}%'),
            )
        else:
            rows = query_all(db, "SELECT * FROM patients ORDER BY created_at DESC")
        return render_template('patients/index.html', patients=rows, q=q)

    @app.route('/patients/new', methods=['GET', 'POST'])
    def patient_new():
        if request.method == 'POST':
            form = request.form
            name = form.get('name', '').strip()
            if not name:
                flash('姓名为必填项', 'error')
                return render_template('patients/new_edit.html', form=form, mode='new')
            dob = form.get('date_of_birth') or ''
            # simple normalize date
            if dob:
                try:
                    dob = datetime.strptime(dob, '%Y-%m-%d').date().isoformat()
                except ValueError:
                    flash('出生日期格式应为 YYYY-MM-DD', 'error')
                    return render_template('patients/new_edit.html', form=form, mode='new')
            db = get_db()
            db.execute(
                """
                INSERT INTO patients (name, gender, date_of_birth, phone, address, id_number, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    (form.get('gender') or '').strip(),
                    dob,
                    (form.get('phone') or '').strip(),
                    (form.get('address') or '').strip(),
                    (form.get('id_number') or '').strip(),
                    datetime.utcnow().isoformat(timespec='seconds'),
                ),
            )
            db.commit()
            flash('患者创建成功', 'success')
            return redirect(url_for('patients'))
        return render_template('patients/new_edit.html', form={}, mode='new')

    def _get_patient_or_404(pid):
        db = get_db()
        row = query_one(db, 'SELECT * FROM patients WHERE id = ?', (pid,))
        if not row:
            abort(404)
        return row

    @app.route('/patients/<int:pid>')
    def patient_detail(pid):
        patient = _get_patient_or_404(pid)
        db = get_db()
        visits = query_all(
            db,
            'SELECT * FROM visits WHERE patient_id = ? ORDER BY visit_date DESC, id DESC',
            (pid,),
        )
        return render_template('patients/detail.html', patient=patient, visits=visits)

    @app.route('/patients/<int:pid>/edit', methods=['GET', 'POST'])
    def patient_edit(pid):
        patient = _get_patient_or_404(pid)
        if request.method == 'POST':
            form = request.form
            name = form.get('name', '').strip()
            if not name:
                flash('姓名为必填项', 'error')
                return render_template('patients/new_edit.html', form=form, mode='edit', patient=patient)
            dob = form.get('date_of_birth') or ''
            if dob:
                try:
                    dob = datetime.strptime(dob, '%Y-%m-%d').date().isoformat()
                except ValueError:
                    flash('出生日期格式应为 YYYY-MM-DD', 'error')
                    return render_template('patients/new_edit.html', form=form, mode='edit', patient=patient)
            db = get_db()
            db.execute(
                """
                UPDATE patients SET name=?, gender=?, date_of_birth=?, phone=?, address=?, id_number=?
                WHERE id=?
                """,
                (
                    name,
                    (form.get('gender') or '').strip(),
                    dob,
                    (form.get('phone') or '').strip(),
                    (form.get('address') or '').strip(),
                    (form.get('id_number') or '').strip(),
                    pid,
                ),
            )
            db.commit()
            flash('患者信息已更新', 'success')
            return redirect(url_for('patient_detail', pid=pid))
        form = dict(patient)
        return render_template('patients/new_edit.html', form=form, mode='edit', patient=patient)

    @app.route('/patients/<int:pid>/delete', methods=['POST'])
    def patient_delete(pid):
        _ = _get_patient_or_404(pid)
        db = get_db()
        db.execute('DELETE FROM patients WHERE id=?', (pid,))
        db.commit()
        flash('患者及其相关就诊记录已删除', 'success')
        return redirect(url_for('patients'))

    # ------------------------- Visits -------------------------
    def _get_visit_or_404(vid):
        db = get_db()
        row = query_one(db, 'SELECT * FROM visits WHERE id = ?', (vid,))
        if not row:
            abort(404)
        return row

    @app.route('/patients/<int:pid>/visits/new', methods=['GET', 'POST'])
    def visit_new(pid):
        patient = _get_patient_or_404(pid)
        if request.method == 'POST':
            form = request.form
            visit_date = form.get('visit_date') or ''
            if visit_date:
                try:
                    visit_date = datetime.strptime(visit_date, '%Y-%m-%d').date().isoformat()
                except ValueError:
                    flash('就诊日期格式应为 YYYY-MM-DD', 'error')
                    return render_template('visits/new_edit.html', form=form, mode='new', patient=patient)
            db = get_db()
            db.execute(
                """
                INSERT INTO visits (patient_id, visit_date, symptoms, diagnosis, treatment, doctor, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid,
                    visit_date,
                    (form.get('symptoms') or '').strip(),
                    (form.get('diagnosis') or '').strip(),
                    (form.get('treatment') or '').strip(),
                    (form.get('doctor') or '').strip(),
                    (form.get('notes') or '').strip(),
                ),
            )
            db.commit()
            flash('就诊记录已添加', 'success')
            return redirect(url_for('patient_detail', pid=pid))
        return render_template('visits/new_edit.html', form={}, mode='new', patient=patient)

    @app.route('/visits/<int:vid>/edit', methods=['GET', 'POST'])
    def visit_edit(vid):
        visit = _get_visit_or_404(vid)
        patient = _get_patient_or_404(visit['patient_id'])
        if request.method == 'POST':
            form = request.form
            visit_date = form.get('visit_date') or ''
            if visit_date:
                try:
                    visit_date = datetime.strptime(visit_date, '%Y-%m-%d').date().isoformat()
                except ValueError:
                    flash('就诊日期格式应为 YYYY-MM-DD', 'error')
                    return render_template('visits/new_edit.html', form=form, mode='edit', patient=patient, visit=visit)
            db = get_db()
            db.execute(
                """
                UPDATE visits SET visit_date=?, symptoms=?, diagnosis=?, treatment=?, doctor=?, notes=?
                WHERE id=?
                """,
                (
                    visit_date,
                    (form.get('symptoms') or '').strip(),
                    (form.get('diagnosis') or '').strip(),
                    (form.get('treatment') or '').strip(),
                    (form.get('doctor') or '').strip(),
                    (form.get('notes') or '').strip(),
                    vid,
                ),
            )
            db.commit()
            flash('就诊记录已更新', 'success')
            return redirect(url_for('patient_detail', pid=patient['id']))
        form = dict(visit)
        return render_template('visits/new_edit.html', form=form, mode='edit', patient=patient, visit=visit)

    @app.route('/visits/<int:vid>/delete', methods=['POST'])
    def visit_delete(vid):
        visit = _get_visit_or_404(vid)
        db = get_db()
        db.execute('DELETE FROM visits WHERE id=?', (vid,))
        db.commit()
        flash('就诊记录已删除', 'success')
        return redirect(url_for('patient_detail', pid=visit['patient_id']))

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
