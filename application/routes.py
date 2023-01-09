from application import app
from flask import render_template, url_for, redirect, flash, get_flashed_messages
from application.form import UserDataForm
from application.models import ScheduledJobs
from application import db
import json


@app.route('/')
def index():
    entries = ScheduledJobs.query.order_by(ScheduledJobs.date.desc()).all()
    return render_template('index.html', entries=entries)

@app.route('/add', methods=["POST", "GET"])
def add_work_order():
    form = UserDataForm()
    if form.validate_on_submit():
        entry = ScheduledJobs(
            product=form.product.data, category=form.category.data,
            lot_number=form.lot_number.data
            )
        db.session.add(entry)
        db.session.commit()
        flash(
            f'{form.product.data}: Lot #{form.lot_number.data} '
            f'has been added.', 'success'
            )
        return redirect(url_for('index'))
    return render_template('add.html', title='Add Work Order', form=form)

@app.route('/delete-post/<int:entry_id>')
def delete(entry_id):
    entry = ScheduledJobs.query.get_or_404(int(entry_id))
    db.session.delete(entry)
    db.session.commit()
    flash(f'Entry deleted.', 'danger')
    return redirect(url_for("index"))

@app.route('/dashboard')
def dashboard():
    type_comparison = db.session.query(db.func.sum(ScheduledJobs.lot_number), ScheduledJobs.product).group_by(ScheduledJobs.product).order_by(ScheduledJobs.product).all()

    product_comparison = db.session.query(db.func.sum(ScheduledJobs.lot_number), ScheduledJobs.category).group_by(ScheduledJobs.category).order_by(ScheduledJobs.category).all()

    dates = db.session.query(db.func.sum(ScheduledJobs.lot_number), ScheduledJobs.date).group_by(ScheduledJobs.date).order_by(ScheduledJobs.date).all()

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

    return render_template('dashboard.html',
                            chart1_data=json.dumps(income_expense),
                            income_category=json.dumps(income_category),
                            chart3_data=json.dumps(chart3_data),
                            dates_label =json.dumps(dates_label)
                        )