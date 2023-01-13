from application import app
from flask import render_template, url_for, redirect, flash, get_flashed_messages
from application.form import UserDataForm
from application.models import ScheduledJobs
from application import db
import json

def _make_schedule():
    pass

@app.route('/')
def index():
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    lines = range(5, 10) # 5 - 9
    parking_lot = ScheduledJobs.query.filter(
        ScheduledJobs.status == 'Parking Lot'
        ).order_by(ScheduledJobs.product).all()
    active_jobs = ScheduledJobs.query.filter(ScheduledJobs.status in ['on Line {x}' for x in lines]).all()

    return render_template(
        'index.html', weekdays=weekdays,
        lines=lines, parking_lot=parking_lot
        )

@app.route('/view-all')
def view_work_orders():
    entries = ScheduledJobs.query.order_by(ScheduledJobs.date.desc()).all()
    return render_template('workorders.html', entries=entries)

@app.route('/add', methods=["POST", "GET"])
def add_work_order():
    form = UserDataForm()
    if form.validate_on_submit():
        entry = ScheduledJobs(
            product=form.product.data, status=form.status.data,
            lot_number=form.lot_number.data, lot_id=form.lot_id.data
            )
        db.session.add(entry)
        db.session.commit()
        flash(
            f'{form.product.data} {form.lot_id.data} (Lot #{form.lot_number.data}) '
            f'added successfully.', 'success'
            )
        return redirect(url_for('index'))
    return render_template('add.html', title='Add Work Order', form=form)

@app.route('/delete/<int:lot_number>')
def delete(lot_number):
    entry = ScheduledJobs.query.get_or_404(int(lot_number))
    db.session.delete(entry)
    db.session.commit()
    flash(f'Lot {lot_number} deleted.', 'danger')
    return redirect(url_for('view_work_orders'))

@app.route('/performance')
def performance():
    type_comparison = (
        db.session.query(
                db.func.sum(ScheduledJobs.lot_number),
                ScheduledJobs.product
            ).group_by(
                ScheduledJobs.product
                ).order_by(
                    ScheduledJobs.product
                    ).all()
        )

    product_comparison = (
        db.session.query(
                db.func.sum(ScheduledJobs.lot_number),
                ScheduledJobs.status
            ).group_by(
                ScheduledJobs.status
                ).order_by(
                    ScheduledJobs.status
                    ).all()
        )

    dates = (
        db.session.query(
                db.func.sum(ScheduledJobs.lot_number),
                ScheduledJobs.date
            ).group_by(
                ScheduledJobs.date
                ).order_by(
                    ScheduledJobs.date
                    ).all()
        )

    income_category = []
    for lot_numbers, _ in product_comparison:
        income_category.append(lot_numbers)

    income_expense = []
    for total_lot_number, _ in type_comparison:
        income_expense.append(total_lot_number)

    chart3_data = []
    dates_label = []
    for lot_number, date in dates:
        dates_label.append(date.strftime("%m-%d-%y"))
        chart3_data.append(lot_number)

    return render_template(
        'performance.html', 
        chart1_data=json.dumps(income_expense),
        income_category=json.dumps(income_category),
        chart3_data=json.dumps(chart3_data),
        dates_label =json.dumps(dates_label)
        )