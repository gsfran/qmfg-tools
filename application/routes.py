import datetime
import json
import sqlite3
from datetime import datetime as dt
from math import ceil

from flask import flash, redirect, render_template, url_for

from application import app, db
from application.forms import LoadWorkOrderForm, NewWorkOrderForm
from application.models import WorkOrders, WorkWeeks
from application.products import products
from application.schedule import CurrentSchedule, Schedule


@app.route('/')
def index() -> str:
    return current_schedule()

@app.route('/schedule')
def current_schedule() -> str:
    schedule = CurrentSchedule()
    print(schedule.work_orders)
    for work_order in schedule.work_orders:
        print(f'{work_order}')

    return render_template(
        'schedule.html.jinja', title='Current Schedule',
        schedule=schedule
        )

@app.route('/schedule/<string:year_week>')
def view_schedule(year_week: str) -> str:
    
    if year_week == dt.strftime(dt.now(), '%G-%V'):
        return redirect(url_for('current_schedule'))

    schedule = Schedule(year_week=year_week)
    return render_template(
        'schedule.html.jinja', title='View Schedule',
        schedule=schedule
    )

@app.route('/view-all-work-orders')
def view_all_work_orders() -> str:
    work_orders = (
        WorkOrders.query.order_by(WorkOrders.lot_number.desc()).all()
        )
    return render_template(
        'view-all-work-orders.html.jinja', title='All Work Orders',
        work_orders=work_orders
        )

@app.route('/view-work-order/<int:lot_number>')
def view_work_order(lot_number: int) -> str:
    work_order = WorkOrders.query.get_or_404(lot_number)
    return render_template(
        'view-work-order.html.jinja', title=f'Lot {lot_number}',
        work_order=work_order
        )

@app.route('/add-work-order', methods=['GET', 'POST'])
def add_work_order() -> str:
    form = NewWorkOrderForm()
    if form.validate_on_submit():
        product = form.product.data
        if product == 'other':
            product_name = form.other_name.data
            short_name = product.capitalize()
            item_number = form.other_item_num.data
            standard_rate = form.other_rate.data
        else:
            product_name = products[product].get('name')
            short_name = products[product].get('short_name')
            item_number = products[product].get('item_number')
            standard_rate = products[product].get('std_rate')

        strip_qty = int(form.strip_qty.data)
        standard_time = ceil(strip_qty / standard_rate)

        work_order = WorkOrders(
            product=product,
            product_name=product_name,
            short_name=short_name,
            item_number=item_number,

            lot_id=form.lot_id.data,
            lot_number=form.lot_number.data,
            strip_lot_number=int(form.strip_lot_number.data),

            strip_qty=strip_qty,
            remaining_qty=strip_qty,
            standard_rate=standard_rate,
            standard_time=standard_time,
            remaining_time=standard_time
            )

        db.session.add(work_order)
        db.session.commit()

        flash(
            f'{short_name} {form.lot_id.data} '
            f'(Lot {form.lot_number.data}) added.',
            'success'
            )
        return redirect(url_for('index'))

    return render_template(
        'add-work-order.html.jinja', title='Add Work Order',
        form=form
        )

@app.route('/delete/<int:lot_number>')
def delete(lot_number: int) -> app.response_class:
    work_order = WorkOrders.query.get_or_404(lot_number)
    db.session.delete(work_order)
    db.session.commit()
    flash(
        f'{work_order.short_name} {work_order.lot_id}'
        f'(Lot {lot_number}) deleted.', 'danger'
        )
    return redirect(url_for('current_schedule'))

@app.route('/load-work-order/<int:lot_number>', methods=['GET', 'POST'])
def load_work_order(lot_number: int) -> str:
    work_order = WorkOrders.query.get_or_404(lot_number)

    form = LoadWorkOrderForm()
    if form.validate_on_submit():
        work_order.line = form.line.data
        work_order.start_datetime = dt.combine(
            form.start_date.data, form.start_time.data
        )
        work_order.end_datetime = (
            work_order.start_datetime
            + datetime.timedelta(hours=work_order.remaining_time)
            )

        work_order.load_datetime = dt.now()
        work_order.status = 'Pouching'
        work_order.pouched_qty = 0
        work_order.log += f'Loaded to {work_order.line}: {dt.now()}\n'
        db.session.commit()

        flash(
            f'{work_order.short_name} {work_order.lot_id} '
            f'(Lot {lot_number}) loaded to '
            f'Line {work_order.line}.',
            'info'
            )

        return redirect(url_for('current_schedule'))

    return render_template(
        'load-work-order.html.jinja', title='Load Work Order',
        form=form, work_order=work_order
        )
    
@app.route('/unload-work-order/<int:lot_number>')
def unload_work_order(lot_number: int) -> str:
    work_order = WorkOrders.query.get_or_404(lot_number)
    
    if work_order.status == 'Pouching':
        flash(
            f'{work_order.short_name} {work_order.lot_id} '
            f'(Lot {lot_number}) unloaded from '
            f'Line {work_order.line}.',
            'warning'
            )
        work_order.status = 'Parking Lot'
        work_order.line = None
        work_order.end_datetime = None
        work_order.load_datetime = None
        work_order.log += f'Unoaded from {work_order.line}: {dt.now()}\n'
        
        db.session.commit()
    
    return redirect(url_for('current_schedule'))

@app.route('/performance')
def performance() -> str:
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
                WorkOrders.add_datetime
            ).group_by(
                WorkOrders.add_datetime
                ).order_by(
                    WorkOrders.add_datetime
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