import json
from datetime import datetime as dt
from datetime import timedelta
from math import ceil

from flask import flash, redirect, render_template, url_for
from werkzeug import Response

from application import app, db
from application.forms import (ConfirmDeleteForm, LoadWorkOrderForm,
                               NewWorkOrderForm, ProductDetailsForm)
from application.models import WorkOrders
from application.products import products
from application.schedule import CurrentSchedule, Schedule


@app.route('/')
def index() -> Response:
    return redirect(url_for('current_schedule'))


@app.route('/schedule')
def current_schedule() -> str:
    schedule = CurrentSchedule()
    schedule.refresh()

    return render_template(
        'schedule.html.jinja', title='Current Schedule',
        schedule=schedule
    )


@app.route('/schedule/<string:year_week>')
def view_schedule(year_week: str) -> str | Response:

    if year_week == dt.strftime(dt.now(), '%G-%V'):
        return redirect(url_for('current_schedule'))

    schedule = Schedule(year_week=year_week)
    schedule.refresh()
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


@app.route('/view-work-order/<int:lot_number>', methods=['GET', 'POST'])
def view_work_order(lot_number: int) -> str | Response:
    form = ConfirmDeleteForm()
    work_order = db.get_or_404(WorkOrders, lot_number)

    if form.validate_on_submit():
        return redirect(url_for('delete', lot_number=lot_number))

    return render_template(
        'view-work-order.html.jinja', title='Work Order Details',
        form=form, work_order=work_order
    )


@app.route('/add-work-order', methods=['GET', 'POST'])
def add_work_order() -> str | Response:

    form = NewWorkOrderForm()
    if form.validate_on_submit():
        product = str(form.product.data)
        lot_number = form.lot_number.data
        [product_name, short_name,
         item_number, standard_rate
         ] = products[product].values()

        strip_qty = form.strip_qty.data
        standard_time = ceil(strip_qty / standard_rate)

        work_order = WorkOrders(
            product=product,
            product_name=product_name,
            short_name=short_name,
            item_number=item_number,

            lot_id=form.lot_id.data,
            lot_number=lot_number,
            strip_lot_number=int(form.strip_lot_number.data),

            strip_qty=strip_qty,
            remaining_qty=strip_qty,
            standard_rate=standard_rate,
            standard_time=standard_time,
            remaining_time=standard_time,
            add_datetime=dt.now()
        )

        db.session.add(work_order)
        db.session.commit()

        flash(
            f'{short_name} {form.lot_id.data} '
            f'(Lot {lot_number}) added.',
            'success'
        )
        if product == 'other':
            return redirect(
                url_for('edit_work_order', lot_number=lot_number)
            )
        return redirect(url_for('current_schedule'))

    return render_template(
        'add-work-order.html.jinja', title='Add Work Order',
        form=form
    )


@app.route('/edit-work-order/<int:lot_number>', methods=['GET', 'POST'])
def edit_work_order(lot_number: int) -> str | Response:
    work_order = db.session.get(WorkOrders, lot_number)
    form = ProductDetailsForm(obj=work_order)

    if form.validate_on_submit():
        work_order.product_name = form.product_name.data
        work_order.short_name = form.short_name.data
        work_order.item_number = form.item_number.data
        work_order.standard_rate = form.standard_rate.data

        db.session.commit()

        return redirect(url_for('current_schedule'))

    return render_template('edit-work-order.html.jinja', form=form)


@app.route('/delete/<int:lot_number>')
def delete(lot_number: int) -> Response:
    work_order = db.session.get(WorkOrders, lot_number)
    db.session.delete(work_order)
    db.session.commit()
    flash(
        f'{work_order.short_name} {work_order.lot_id} '
        f'(Lot {lot_number}) deleted.', 'danger'
    )
    return redirect(url_for('current_schedule'))


@app.route('/load-work-order/<int:lot_number>', methods=['GET', 'POST'])
def load_work_order(lot_number: int) -> str | Response:
    work_order = db.session.get(WorkOrders, lot_number)
    form = LoadWorkOrderForm()
    
    if form.validate_on_submit():
        work_order.line = line = form.line.data
        # work_order.start_datetime = dt.combine(
        #     form.start_date.data, form.start_time.data
        # )
        # work_order.end_datetime = work_order.start_datetime + timedelta(
        #     hours=work_order.remaining_time
        # )
        if Schedule.on_line(line):
            work_order.status = 'Queued'
        else:
            work_order.status = 'Pouching'
            work_order.start_datetime = dt.now()

        work_order.log += f'Loaded to {work_order.line}: {dt.now()}\n'
        work_order.load_datetime = dt.now()
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
def unload_work_order(lot_number: int) -> Response:
    work_order = db.session.get(WorkOrders, lot_number)

    if work_order.status == 'Pouching' or work_order.status == 'Queued':
        flash(
            f'{work_order.short_name} {work_order.lot_id} '
            f'(Lot {lot_number}) unloaded from '
            f'Line {work_order.line}.',
            'warning'
        )
        work_order.status = 'Parking Lot'
        work_order.start_datetime = None
        work_order.end_datetime = None
        work_order.load_datetime = None

        work_order.log += f'Unloaded from {work_order.line}: {dt.now()}\n'
        work_order.line = None
        db.session.commit()

    return redirect(url_for('current_schedule'))


@app.route('/line-status/<int:line>')
def view_line_status(line: int) -> str:
    # pouching = WorkOrders.on_line(line=line)
    # scheduled = WorkOrders.scheduled_jobs
    return render_template('line-status.html.jinja', title=f'Line {line}',
                           line=line)


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
        dates_label=json.dumps(dates_label)
    )
