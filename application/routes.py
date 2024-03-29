import json
from datetime import datetime as dt
from math import ceil

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from is_safe_url import is_safe_url
from werkzeug import Response
from werkzeug.urls import url_parse

from application import app, db
from application.forms import (DeleteWorkOrderForm, LoadWorkOrderForm,
                               LoginForm, NewWorkOrderForm, ParkWorkOrderForm,
                               ProductDetailsForm, RegistrationForm,
                               ScheduleConfigForm, WeekConfigForm)
from application.machines import Machine
from application.models import User, WorkOrder, WorkWeek
from application.products import Product
from application.schedules import (_YEAR_WEEK_FORMAT, CurrentSchedule,
                                   Schedule, get_workweek_from_db,
                                   save_schedule_dict_to_json,
                                   update_db_workweek)


@app.route('/')
@app.route('/index')
def index() -> Response:
    return redirect(url_for('current_week', machine_family='itrak'))


@app.route('/wk/<string:machine_family>/current')
@app.route('/wk/<string:machine_family>')
def current_week(machine_family: str) -> str:
    schedule = CurrentSchedule(machine_family=machine_family)
    schedule._refresh_work_orders()

    return render_template(
        'schedule-view.html.jinja', title='Current Schedule',
        schedule=schedule
    )


@app.route('/wk/<string:machine_family>/<string:year_week>')
def week_view(machine_family: str, year_week: str) -> str | Response:

    if year_week == dt.strftime(dt.now(), _YEAR_WEEK_FORMAT):
        return redirect(url_for('current_week', machine_family='itrak'))

    schedule = Schedule(year_week, machine_family)
    schedule._refresh_work_orders()
    return render_template(
        'schedule-view.html.jinja', title='View Schedule',
        schedule=schedule
    )


@app.route('/settings/')  # temp, linking settings directly to this page
@app.route('/schedule-change', methods=['GET', 'POST'])
@login_required
def schedule_config() -> str | Response:

    form: ScheduleConfigForm = ScheduleConfigForm()
    if form.validate_on_submit():
        new_schedule = form.to_dict()

        effective_date_str = form.effective_date.data
        if effective_date_str is None:
            raise Exception('Error in effective_date field data.')
        effective_date = dt.strptime(effective_date_str, '%Y-%m-%d').date()

        overwrite = form.overwrite_custom.data

        #  MACHINE FAMILIES CHECKED HERE WHEN FEATURE IS IMPLEMENTED

        save_schedule_dict_to_json(new_schedule)

        weeks_to_update = WorkWeek.later_than(effective_date)
        if weeks_to_update is not None:
            for work_week in weeks_to_update:
                if overwrite or not work_week.customized:
                    update_db_workweek(new_schedule, work_week)

        if overwrite:
            modified_str = 'OVERWRITTEN'
        else:
            modified_str = 'PRESERVED'

        flash(
            f'Schedule changed effective {effective_date} '
            f'(modified weeks {modified_str})', 'success'
        )

        return redirect(
            url_for('current_week', machine_family='itrak')
        )

    return render_template(
        'schedule-change.html.jinja', title='Schedule Change',
        form=form
    )


@app.route(
    '/wk/<string:machine_family>/<string:year_week>/edit/',
    methods=['GET', 'POST']
)
@login_required
def week_config(machine_family: str, year_week: str) -> str | Response:

    form: WeekConfigForm = WeekConfigForm(year_week)
    schedule = Schedule(year_week, machine_family)
    work_week = get_workweek_from_db(year_week)

    if form.validate_on_submit():
        new_schedule = form.to_dict()
        update_db_workweek(new_schedule, work_week)
        work_week.customized = True
        db.session.commit()

        flash(
            f'Saved edits to the week starting {work_week.start_date}',
            'success'
        )

        return redirect(
            url_for('week_view', year_week=year_week,
                    machine_family='itrak')
        )

    return render_template(
        'schedule-edit-week.html.jinja', title='Edit Week',
        schedule=schedule, form=form
    )


@app.route('/wo/all')
def view_all_work_orders() -> str:
    work_orders = db.session.execute(
        db.select(WorkOrder).order_by(
            WorkOrder.lot_number.desc()
        )
    ).scalars().all()
    return render_template(
        'view-all-work-orders.html.jinja', title='All Work Orders',
        work_orders=work_orders
    )


@app.route('/wo/view/<int:lot_number>', methods=['GET', 'POST'])
def view_work_order(lot_number: int) -> str | Response:

    work_order = db.session.execute(
        db.select(
            WorkOrder
        ).where(
            WorkOrder.lot_number == lot_number
        )
    ).scalar_one_or_none()

    if work_order is None:
        flash(f'Work Order #{lot_number} Not Found', 'warning')
        return redirect(url_for('index'))

    return render_template(
        'view-work-order.html.jinja', title='Work Order Details',
        work_order=work_order
    )


@app.route('/wo/add', methods=['GET', 'POST'])
@login_required
def add_work_order() -> str | Response:

    form = NewWorkOrderForm()
    if form.validate_on_submit():
        product = Product(form.product.data)
        lot_number = form.lot_number.data
        lot_id = form.lot_id.data
        strip_lot_number = form.strip_lot_number.data
        strip_qty = form.strip_qty.data
        standard_time = ceil(
            int(strip_qty) / int(product.standard_rate)  # type:ignore
        )

        work_order = WorkOrder(
            product=product.key_,
            product_name=product.name,
            short_name=product.short_name,
            item_number=product.item_number,
            standard_rate=product.standard_rate,

            lot_id=lot_id,
            lot_number=lot_number,
            strip_lot_number=strip_lot_number,

            strip_qty=strip_qty,
            remaining_qty=strip_qty,
            standard_time=standard_time,
            remaining_time=standard_time
        )

        db.session.add(work_order)
        db.session.commit()

        flash(
            f'{product.short_name} {form.lot_id.data} '
            f'(Lot {lot_number}) added.',
            'success'
        )
        if product.key_ == 'other':
            return redirect(
                url_for('edit_work_order', lot_number=lot_number)
            )
        return redirect(url_for('current_week', machine_family='itrak'))

    return render_template(
        'add-work-order.html.jinja', title='Add Work Order',
        form=form
    )


@app.route('/wo/edit/<int:lot_number>', methods=['GET', 'POST'])
@login_required
def edit_work_order(lot_number: int) -> str | Response:
    work_order = db.session.execute(
        db.select(WorkOrder).where(
            WorkOrder.lot_number == lot_number
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
        work_order.standard_time = ceil(
            int(work_order.strip_qty) /
            int(work_order.standard_rate)  # type:ignore
        )
        work_order.remaining_time = work_order.standard_time

        db.session.commit()

        return redirect(url_for('current_week', machine_family='itrak'))

    return render_template('edit-work-order.html.jinja', form=form)


@app.route('/wo/park/<int:lot_number>', methods=['GET', 'POST'])
@login_required
def park_work_order(lot_number: int) -> str | Response:

    form = ParkWorkOrderForm()

    work_order = db.session.execute(
        db.select(WorkOrder).where(
            WorkOrder.lot_number == lot_number
        )
    ).scalar_one_or_none()

    if work_order is None:
        flash(f'Work Order #{lot_number} not found', 'warning')
        return redirect(url_for('index'))

    if work_order.machine is None:
        flash(f'Work Order #{lot_number} not scheduled', 'warning')
        return redirect(url_for('index'))

    if form.validate_on_submit():

        flash(
            f'{work_order.short_name} {work_order.lot_id} '
            f'/ {work_order.lot_number} moved to Parking Lot',
            'warning'
        )
        work_order.park()
        db.session.commit()

        return redirect(url_for('current_week', machine_family='itrak'))

    return render_template(
        'park-work-order.html.jinja', title='Park Work Order',
        form=form, work_order=work_order
    )


@app.route('/wo/load/<int:lot_number>', methods=['GET', 'POST'])
@login_required
def load_work_order(lot_number: int) -> str | Response:
    work_order = db.session.execute(
        db.select(WorkOrder).where(
            WorkOrder.lot_number == lot_number
        )
    ).scalar_one_or_none()
    if work_order is None:
        raise Exception(f'Error finding lot number: {lot_number}')

    product: Product = Product(work_order.product)
    machine_family = product.pouch_type
    form: LoadWorkOrderForm = LoadWorkOrderForm(machine_family)

    if form.validate_on_submit():
        date_ = form.start_date.data
        time_ = form.start_time.data
        if date_ is not None and time_ is not None:
            start_dt = dt.combine(date_, time_)
        else:
            start_dt = None
        if form.machine.data:
            machine = Machine.new_(form.machine.data)
        else:
            raise Exception(f'No machine found: {form.machine.data}')
        mode = form.mode.data
        if mode:
            machine.schedule_job(work_order, mode, start_dt)
        else:
            raise Exception(f'No mode found: {form.mode.data}')
        flash(
            f'{work_order.short_name} {work_order.lot_id} '
            f'/ {lot_number} loaded to '
            f'{machine.name}',
            'info'
        )
        return redirect(url_for('current_week', machine_family='itrak'))

    return render_template(
        'load-work-order.html.jinja', title='Load Work Order',
        form=form, work_order=work_order
    )


@app.route('/wo/delete/<int:lot_number>', methods=['GET', 'POST'])
@login_required
def delete_work_order(lot_number: int) -> str | Response:

    form = DeleteWorkOrderForm()
    work_order = db.session.execute(
        db.select(WorkOrder).where(
            WorkOrder.lot_number == lot_number
        )
    ).scalar_one_or_none()

    if work_order is None:
        flash(f'Work Order #{lot_number} Not Found', 'warning')
        return redirect(url_for('index'))

    if form.validate_on_submit():
        db.session.delete(work_order)
        db.session.commit()
        flash(
            f'{work_order.short_name} {work_order.lot_id} '
            f'/ {work_order.lot_number} deleted', 'danger'
        )
        return redirect(url_for('current_week', machine_family='itrak'))

    return render_template(
        'delete-work-order.html.jinja', title='Delete Work Order',
        form=form, work_order=work_order
    )


@app.route('/machine/view/<string:machine>')
def view_machine(machine: str) -> str:
    # pouching = WorkOrders.on_machine(machine=machine)
    # scheduled = WorkOrders.scheduled_jobs
    return render_template('machine-status.html.jinja', title=machine,
                           machine=machine)


@app.route('/user/login', methods=['GET', 'POST'])
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
        flash('Logged in successfully', 'success')
        print(f'{form.remember_me.data=}')

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


@app.route('/user/logout')
@login_required
def logout() -> Response:
    logout_user()
    flash('User logged out', 'primary')
    return redirect(url_for('index'))


@app.route('/user/register', methods=['GET', 'POST'])
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


@app.route('/performance')
def performance() -> str:
    type_comparison = (
        db.session.query(
            db.func.sum(WorkOrder.lot_number),
            WorkOrder.product
        ).group_by(
            WorkOrder.product
        ).order_by(
            WorkOrder.product
        ).all()
    )
    product_comparison = (
        db.session.query(
            db.func.sum(WorkOrder.lot_number),
            WorkOrder.status
        ).group_by(
            WorkOrder.status
        ).order_by(
            WorkOrder.status
        ).all()
    )
    dates = (
        db.session.query(
            db.func.sum(WorkOrder.lot_number),
            WorkOrder.created_dt
        ).group_by(
            WorkOrder.created_dt
        ).order_by(
            WorkOrder.created_dt
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
