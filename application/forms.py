from __future__ import annotations

from copy import deepcopy
from datetime import datetime as dt
from datetime import timedelta

from flask_wtf import FlaskForm
from wtforms import (BooleanField, IntegerField, PasswordField, RadioField,
                     SelectField, StringField, SubmitField)
from wtforms.fields.datetime import DateField, TimeField
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                NumberRange, ValidationError)

from application import db
from application.machines import machine_list
from application.models import User
from application.products import products
from application.schedules import (_YEAR_WEEK_FORMAT, current_year_week,
                                   get_schedule_from_json)


class LoginForm(FlaskForm):

    username = StringField(
        'Username',
        validators=[
            DataRequired()
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired()
        ]
    )

    remember_me = BooleanField(
        'Remember Me'
    )

    submit = SubmitField(
        'Login'
    )


class RegistrationForm(FlaskForm):

    username = StringField(
        'Username', validators=[
            DataRequired()
        ]
    )

    email = StringField(
        'Email', validators=[
            DataRequired(), Email()
        ]
    )

    password = PasswordField(
        'Password', validators=[
            DataRequired()
        ]
    )

    password_confirm = PasswordField(
        'Repeat Password', validators=[
            DataRequired(), EqualTo('password')
        ]
    )

    submit = SubmitField(
        'Register'
    )

    def validate_username(self, username: StringField) -> None:
        user = db.session.execute(
            db.select(User).where(
                User.username == username.data
            )
        ).scalar_one_or_none()
        if user is not None:
            raise ValidationError('Username unavailable.')

    def validate_email(self, email: StringField) -> None:
        user = db.session.execute(
            db.select(User).where(
                User.email == email.data
            )
        ).scalar_one_or_none()
        if user is not None:
            raise ValidationError('Email address unavailable.')


class ProductDetailsForm(FlaskForm):

    product = StringField(
        'Product'
    )

    product_name = StringField(
        'Product Name', validators=[
            DataRequired()
        ]
    )

    short_name = StringField(
        'Short Name', validators=[
            DataRequired()
        ]
    )

    item_number = StringField(
        'Pouch Item Number', validators=[
            DataRequired(), Length(7, 7)
        ]
    )

    standard_rate = IntegerField(
        'Standard Rate [/hr]', validators=[
            DataRequired(),
            NumberRange(min=500, max=15000)
        ]
    )

    submit = SubmitField('Save')

    @staticmethod
    def validate_item_number(
        form: ProductDetailsForm, item_number: StringField
    ) -> None:
        try:
            int(item_number.data)
        except ValueError:
            raise ValidationError('Please enter a valid number.')


class NewWorkOrderForm(FlaskForm):

    product = SelectField(
        'Product', validators=[
            DataRequired()
        ],
        choices=(
            [('', 'Select Product')] +
            [(
                k_, f"{prod_['item_number']} - {prod_['product_name']}"
            ) for k_, prod_ in products.items()]
        )
    )

    lot_id = StringField(
        'Lot ID', validators=[
            DataRequired(), Length(2, 5)
        ]
    )

    lot_number = StringField(
        'Pouch Lot #', validators=[
            DataRequired(), Length(6, 6)
        ]
    )

    strip_lot_number = StringField(
        'Strip Lot #', validators=[
            DataRequired(), Length(6, 6)
        ]
    )

    strip_qty = IntegerField(
        'Strip Qty.', validators=[
            DataRequired(), NumberRange(min=1, max=999999)
        ]
    )

    submit = SubmitField('Add Work Order')

    @staticmethod
    def validate_lot_number(
        form: NewWorkOrderForm, lot_number: StringField
    ) -> None:
        try:
            int(lot_number.data)
        except ValueError:
            raise ValidationError('Please enter a valid lot number.')

    @staticmethod
    def validate_strip_lot_number(
        form: NewWorkOrderForm, strip_lot_number: StringField
    ) -> None:
        try:
            int(strip_lot_number.data)
        except ValueError:
            raise ValidationError('Please enter a valid lot number.')


class LoadWorkOrderForm(FlaskForm):

    machine = SelectField(
        'Poucher', validators=[
            DataRequired()
        ]
    )

    mode = RadioField(
        'Schedule Method', validators=[
            DataRequired()
        ],
        choices=[
            ('append', 'Next Available Time'),
            ('insert', 'Expedite (After Current)'),
            ('replace', 'Replace Current Job'),
            ('custom', 'Specify a Time:')
        ], default='append'
    )

    start_date = DateField(
        'Start Date', validators=[
            DataRequired()
        ],
        default=dt.now().date()
    )

    start_time = TimeField(
        'Start Time', validators=[
            DataRequired()
        ],
        default=dt.now().time()
    )

    submit = SubmitField('Load to Poucher')

    def __init__(
        self: LoadWorkOrderForm,
        machine_family: str | None,
        *args, **kwargs
    ) -> None:
        if machine_family is None:
            raise Exception('Machine family not specified.')
        super().__init__(*args, **kwargs)
        self.machine.choices = [(None, 'Select Machine')] + [(
            mach_.short_name, mach_.name
        ) for mach_ in machine_list(machine_family)]


class ConfirmDeleteForm(FlaskForm):

    delete = StringField(
        "Type 'delete' to confirm: ", validators=[
            DataRequired()
        ]
    )

    submit = SubmitField('Delete')

    @staticmethod
    def validate_delete(form: ConfirmDeleteForm, delete: StringField) -> None:
        if delete.data != 'delete':
            raise ValidationError("Type 'delete' in the field to confirm.")


class EditDefaultsForm(FlaskForm):

    monday = BooleanField('Monday')
    monday_start = TimeField()
    monday_end = TimeField()

    tuesday = BooleanField('Tuesday')
    tuesday_start = TimeField()
    tuesday_end = TimeField()

    wednesday = BooleanField('Wednesday')
    wednesday_start = TimeField()
    wednesday_end = TimeField()

    thursday = BooleanField('Thursday')
    thursday_start = TimeField()
    thursday_end = TimeField()

    friday = BooleanField('Friday')
    friday_start = TimeField()
    friday_end = TimeField()

    saturday = BooleanField('Saturday')
    saturday_start = TimeField()
    saturday_end = TimeField()

    sunday = BooleanField('Sunday')
    sunday_start = TimeField()
    sunday_end = TimeField()

    mode_select = RadioField(
        validators=[
            DataRequired()
        ]
    )

    submit = SubmitField('Save')

    def __init__(self: EditDefaultsForm, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)

        if not self.submit.data:
            self._populate_defaults()
            self._populate_mode_select()

    def _populate_defaults(self: EditDefaultsForm) -> None:
        current_defaults = get_schedule_from_json()
        for day_ in current_defaults:

            scheduled = current_defaults[day_].get('scheduled')
            times = current_defaults[day_].get('times')
            if type(scheduled) != bool or type(times) != dict:
                raise Exception(
                    'Type mismatch in schedule json, check formatting.'
                )

            start_time_str = dt.strptime(times['start'], '%H:%M')
            end_time_str = dt.strptime(times['end'], '%H:%M')

            setattr(getattr(self, day_), 'data', scheduled)
            setattr(getattr(self, f'{day_}_start'), 'data', start_time_str)
            setattr(getattr(self, f'{day_}_end'), 'data', end_time_str)

    def _populate_mode_select(self: EditDefaultsForm) -> None:
        current_week_start_date = dt.strptime(
            f'{current_year_week()}-Mon', f'{_YEAR_WEEK_FORMAT}-%a'
        ).date()
        next_week_start_date = (dt.strptime(
            f'{current_year_week()}-Mon', f'{_YEAR_WEEK_FORMAT}-%a'
        ) + timedelta(days=7)).date()

        self.mode_select.choices = [
            (
                'start_this_week',
                f'Effective this week ({current_week_start_date})'
            ),
            (
                'start_next_week',
                f'Effective next week ({next_week_start_date})'
            )
        ]


class EditExistingWeekForm(FlaskForm):
    ...
