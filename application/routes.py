import datetime
import json

from datetime import datetime as dt
from flask import flash, redirect, render_template, url_for
from math import ceil

from application import app, db
from application.forms import NewWorkOrderForm, LoadWorkOrderForm
from application.models import WorkOrders
from application.schedule import CurrentSchedule, Schedule
from application.products import products


@app.route('/')
def index() -> str:
    lines = range(5, 10)
    schedule = CurrentSchedule(lines)
    
    return render_template(
        'index.html.jinja',
        schedule=schedule,
        lines=lines
        )

@app.route('/view-all-work-orders')
def view_all_work_orders() -> str:
    work_orders = (
        WorkOrders.query.order_by(WorkOrders.status.desc()).all()
        )
    return render_template(
        'view-all-work-orders.html.jinja', work_orders=work_orders
        )

@app.route('/view-work-order/<int:lot_number>')
def view_work_order(lot_number):
    work_order = WorkOrders.query.get_or_404(lot_number)
    return render_template(
        'view-work-order.html.jinja', title=f'Lot {lot_number}',
        work_order=work_order
        )

@app.route('/add-work-order', methods=["POST", "GET"])
def add_work_order() -> str:
    form = NewWorkOrderForm()
    if form.validate_on_submit():
        product = form.product.data
        
        product_name = products[product].get('name')
        item_number = products[product].get('item_number')
        standard_rate = products[product].get('std_rate')
        
        strip_qty=int(form.strip_qty.data)
        standard_time = ceil(strip_qty / standard_rate)

        work_order = WorkOrders(
            product=product,
            product_name=product_name,
            item_number = item_number,
            
            lot_id=form.lot_id.data,
            lot_number=int(form.lot_number.data),
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
            f'Lot #{form.lot_number.data} ({product_name} '
            f'{form.lot_id.data}) added successfully.',
            'info'
            )
        return redirect(url_for('index'))

    return render_template(
        'add-work-order.html.jinja', title='Add Work Order', form=form
        )

@app.route('/delete/<int:lot_number>')
def delete(lot_number: int) -> app.response_class:
    work_order = WorkOrders.query.get_or_404(lot_number)
    db.session.delete(work_order)
    db.session.commit()
    flash(
        f'Lot #{lot_number} ({work_order.product_name} '
        f'#{work_order.lot_id}) deleted.', 'danger'
        )
    return redirect(url_for('view_all_work_orders'))

@app.route('/load-work-order/<int:lot_number>', methods=["POST", "GET"])
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
        db.session.commit()

        flash(
            f'Lot #{work_order.lot_number} ({work_order.product_name} '
            f'{work_order.lot_id}) successfully loaded to '
            f'Line {work_order.line}.',
            'success'
            )

        return redirect(url_for('index'))

    return render_template(
        'load-work-order.html.jinja', title='Load Work Order', form=form,
        work_order=work_order
        )

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