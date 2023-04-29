from __future__ import annotations

from datetime import datetime as dt

from flask_wtf import FlaskForm
from wtforms import (BooleanField, IntegerField, PasswordField, RadioField,
                     SelectField, StringField, SubmitField)
from wtforms.fields.datetime import DateField, TimeField
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                NumberRange, ValidationError)

from application import db
from application.models import User
from application.products import products


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
            NumberRange(min=500, max=5000)
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
        choices=[
            ('', '--'),
            ('flu', '1169100 - Flu A/B'),
            ('abc', '1451300 - ABC (Flu+SARS)'),
            ('strep_aplus', '1330700 - Strep A+'),
            ('rsv', '1175000 - RSV'),
            ('sars', '1440700 - SARS Antigen'),
            ('strep_inline', '1094000 - Strep Inline'),
            ('other', '< Other >')
        ]
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
        ],
        choices=[
            (None, '--'),
            ('line5', 'Line 5'),
            ('line6', 'Line 6'),
            ('line7', 'Line 7'),
            ('line8', 'Line 8'),
            ('line9', 'Line 9'),
            ('line10', 'Line 10'),
            ('line11', 'Line 11')
        ]
    )

    priority = RadioField(
        'Schedule Time', validators=[
            DataRequired()
        ],
        choices=[
            ('append', 'Next Available Time'),
            ('next', 'After Current Work Order'),
            ('replace', 'Replace Current Work Order'),
            ('custom', 'Custom Start Time:')
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
