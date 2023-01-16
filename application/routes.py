import datetime
import json


from datetime import datetime as dt
from flask import (flash, redirect, render_template, url_for)

from application import app, db
from application.form import NewWorkOrder
from application.models import WorkOrders
from application.schedule import Schedule, CurrentSchedule


@app.route('/')
def index():
    
    schedule = CurrentSchedule()
    lines = range(5, 10) # 5 - 9

    active_jobs = WorkOrders.query.filter(
        WorkOrders.status in ['on Line {x}' for x in lines]
        ).all()

    return render_template(
        'index.html', dates=schedule.dates, lines=lines,
        parking_lot=schedule.parking_lot(), current_hour=schedule.current_hour()
        )

@app.route('/view-all-work-orders')
def view_all_work_orders():
    work_orders = WorkOrders.query.order_by(
        WorkOrders.date.desc()
        ).all()
    return render_template('view-all-work-orders.html', work_orders=work_orders)

@app.route('/view-work-order/<int:lot_number>')
def view_work_order(lot_number):
    work_order = WorkOrders.query.get_or_404(int(lot_number))
    return render_template(
        'view-work-order.html', title=f'Lot {lot_number}',
        work_order=work_order
        )

@app.route('/add-work-order', methods=["POST", "GET"])
def add_work_order():
    form = NewWorkOrder()
    if form.validate_on_submit():
        entry = WorkOrders(
            product=form.product.data,
            lot_id=form.lot_id.data,
            lot_number=form.lot_number.data,
            strip_lot_number=form.strip_lot_number.data,
            quantity=form.quantity.data,
            status=form.status.data
            )
        db.session.add(entry)
        db.session.commit()
        flash(
            f'Lot #{form.lot_number.data} '
            f'({form.product.data} '
            f'{form.lot_id.data}) '
            f'added successfully.',
            'success'
            )

        return redirect(url_for('index'))

    return render_template(
        'add-work-order.html', title='Add Work Order',
        form=form
        )

@app.route('/delete/<int:lot_number>')
def delete(lot_number):
    entry = WorkOrders.query.get_or_404(int(lot_number))
    db.session.delete(entry)
    db.session.commit()
    flash(
        f'Lot #{lot_number} ({entry.product} '
        f'#{entry.lot_id}) deleted.', 'danger'
        )
    return redirect(url_for('view_all_work_orders'))

@app.route('/performance')
def performance():
    type_comparison = (
        db.session.query(
                db.func.sum(WorkOrders.lot_number),
                WorkOrders.product
            ).group_by(
                WorkOrders.product
                ).order_by(
                    WorkOrders.product
                    ).all()
        )

    product_comparison = (
        db.session.query(
                db.func.sum(WorkOrders.lot_number),
                WorkOrders.status
            ).group_by(
                WorkOrders.status
                ).order_by(
                    WorkOrders.status
                    ).all()
        )

    dates = (
        db.session.query(
                db.func.sum(WorkOrders.lot_number),
                WorkOrders.date
            ).group_by(
                WorkOrders.date
                ).order_by(
                    WorkOrders.date
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