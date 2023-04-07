import json
from datetime import datetime as dt
from math import ceil

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from is_safe_url import is_safe_url
from werkzeug import Response
from werkzeug.urls import url_parse

from application import app, db
from application.forms import (ConfirmDeleteForm, LoadWorkOrderForm, LoginForm,
                               NewWorkOrderForm, ProductDetailsForm,
                               RegistrationForm)
from application.models import User, WorkOrder
from application.products import products
from application.schedules import CurrentPouchingSchedule, PouchingSchedule


@app.route('/')
@app.route('/index')
def index() -> Response:
    return redirect(url_for('current_schedule'))


@app.route('/user-login', methods=['GET', 'POST'])
def login() -> str | Response:

    if current_user.is_authenticated:  # type: ignore[call-arg]
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():

        user = db.session.execute(
            db.select(User).where(
                User.username == form.username.data
            )
        ).scalar_one_or_none()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        flash('Logged in successfully.', 'success')

        next_page = request.args.get('next')

        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        if not is_safe_url(next_page, None):
            return abort(400)

        return redirect(next_page)

    return render_template(
        'user-login.html.jinja', title='User Login',
        form=form
    )


@app.route('/logout')
@login_required
def logout() -> Response:
    logout_user()
    return redirect(url_for('index'))


@app.route('/register-user', methods=['GET', 'POST'])
def register() -> str | Response:

    if current_user.is_authenticated:  # type: ignore[call-arg]
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful.', 'success')
        return redirect(url_for('index'))

    return render_template(
        'register-user.html.jinja', title='Register New User',
        form=form
    )


@app.route('/schedule')
def current_schedule() -> str:
    schedule = CurrentPouchingSchedule()
    schedule.refresh()

    return render_template(
        'schedule.html.jinja', title='Current Schedule',
        schedule=schedule
    )


@app.route('/schedule/<string:year_week>')
def view_schedule(year_week: str) -> str | Response:

    if year_week == dt.strftime(dt.now(), '%G-%V'):
        return redirect(url_for('current_schedule'))

    schedule = PouchingSchedule(year_week=year_week)
    schedule.refresh()
    return render_template(
        'schedule.html.jinja', title='View Schedule',
        schedule=schedule
    )


@app.route('/view-all-work-orders')
def view_all_work_orders() -> str:
    work_orders = (
        WorkOrder.query.order_by(WorkOrder.pouch_lot_num.desc()).all()
    )
    return render_template(
        'view-all-work-orders.html.jinja', title='All Work Orders',
        work_orders=work_orders
    )


@app.route('/view-work-order/<int:lot_number>', methods=['GET', 'POST'])
def view_work_order(lot_number: int) -> str | Response:

    form = ConfirmDeleteForm()
    work_order = db.session.execute(
        db.select(WorkOrder).where(
            WorkOrder.pouch_lot_num == lot_number
        )
    ).scalar_one_or_none()

    if work_order is None:
        flash(f'Work Order #{lot_number} Not Found', 'warning')
        return redirect(url_for('index'))

    if form.validate_on_submit():
        return redirect(url_for('delete', lot_number=lot_number))

    return render_template(
        'view-work-order.html.jinja', title='Work Order Details',
        form=form, work_order=work_order
    )


@app.route('/add-work-order', methods=['GET', 'POST'])
@login_required
def add_work_order() -> str | Response:

    form = NewWorkOrderForm()
    if form.validate_on_submit():
        product = str(form.product.data)
        lot_number = form.lot_number.data
        [product_name, short_name,
         item_number, standard_rate
         ] = products[product].values()

        strip_qty = form.strip_qty.data
        if strip_qty is not None and standard_rate is not None:
            standard_time = ceil(
                int(strip_qty) / int(standard_rate)
            )
        else:
            raise Exception('Error calculating lot standard time.')

        work_order = WorkOrder(
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
@login_required
def edit_work_order(lot_number: int) -> str | Response:
    work_order = db.session.execute(
        db.select(WorkOrder).where(
            WorkOrder.pouch_lot_num == lot_number
        )
    ).scalar_one_or_none()

    if work_order is None:
        flash(f'Work Order #{lot_number} Not Found', 'warning')
        return redirect(url_for('index'))

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
@login_required
def delete(lot_number: int) -> Response:
    work_order = db.session.execute(
        db.select(WorkOrder).where(
            WorkOrder.pouch_lot_num == lot_number
        )
    ).scalar_one_or_none()

    if work_order is None:
        flash(f'Work Order #{lot_number} Not Found', 'warning')
        return redirect(url_for('index'))

    db.session.delete(work_order)
    db.session.commit()
    flash(
        f'{work_order.short_name} {work_order.lot_id} '
        f'(Lot {lot_number}) deleted.', 'danger'
    )
    return redirect(url_for('current_schedule'))


@app.route('/load-work-order/<int:lot_number>', methods=['GET', 'POST'])
@login_required
def load_work_order(lot_number: int) -> str | Response:
    work_order = db.session.execute(
        db.select(WorkOrder).where(
            WorkOrder.pouch_lot_num == lot_number
        )
    ).scalar_one_or_none()
    form = LoadWorkOrderForm()

    if form.validate_on_submit():
        line = form.line.data
        work_order.line = line
        if PouchingSchedule.on_line(line):
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
@login_required
def unload_work_order(lot_number: int) -> Response:
    work_order = db.session.execute(
        db.select(WorkOrder).where(
            WorkOrder.pouch_lot_num == lot_number
        )
    ).scalar_one_or_none()

    if work_order is None:
        flash(f'Work Order #{lot_number} Not Found', 'warning')
        return redirect(url_for('index'))

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


@app.route('/machine/<string:machine>')
def view_machine(machine: str) -> str:
    # pouching = WorkOrders.on_line(line=line)
    # scheduled = WorkOrders.scheduled_jobs
    return render_template('machine-status.html.jinja', title=machine,
                           machine=machine)


@app.route('/performance')
def performance() -> str:
    type_comparison = (
        db.session.query(
            db.func.sum(WorkOrder.pouch_lot_num),
            WorkOrder.product
        ).group_by(
            WorkOrder.product
        ).order_by(
            WorkOrder.product
        ).all()
    )
    product_comparison = (
        db.session.query(
            db.func.sum(WorkOrder.pouch_lot_num),
            WorkOrder.status
        ).group_by(
            WorkOrder.status
        ).order_by(
            WorkOrder.status
        ).all()
    )
    dates = (
        db.session.query(
            db.func.sum(WorkOrder.pouch_lot_num),
            WorkOrder.add_datetime
        ).group_by(
            WorkOrder.add_datetime
        ).order_by(
            WorkOrder.add_datetime
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
