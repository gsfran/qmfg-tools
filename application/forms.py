from __future__ import annotations

from datetime import datetime as dt

from flask_wtf import FlaskForm
from wtforms import (BooleanField, IntegerField, PasswordField, RadioField,
                     SelectField, StringField, SubmitField)
from wtforms.fields.datetime import DateField, TimeField
from wtforms.validators import (DataRequired, Length, NumberRange,
                                ValidationError)


class LoginForm(FlaskForm):

    username = StringField(
        'Username',
        validators=[DataRequired()]
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )

    remember_me = BooleanField(
        'Remember Me'
    )

    submit = SubmitField(
        'Login'
    )


class ProductDetailsForm(FlaskForm):

    product = StringField(
        'Product'
    )

    product_name = StringField(
        'Product Name',
        validators=[DataRequired()]
    )

    short_name = StringField(
        'Short Name',
        validators=[DataRequired()]
    )

    item_number = StringField(
        'Pouch Item Number',
        validators=[DataRequired(), Length(7, 7)]
    )

    standard_rate = IntegerField(
        'Standard Rate [/hr]',
        validators=[
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
        'Product', validators=[DataRequired()],
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
        'Lot ID', validators=[DataRequired(), Length(2, 5)]
    )

    lot_number = StringField(
        'Pouch Lot #', validators=[DataRequired(), Length(6, 6)]
    )

    strip_lot_number = StringField(
        'Strip Lot #', validators=[DataRequired(), Length(6, 6)]
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
            raise ValidationError('Please enter a valid number.')

    @staticmethod
    def validate_strip_lot_number(
        form: NewWorkOrderForm, strip_lot_number: StringField
    ) -> None:
        try:
            int(strip_lot_number.data)
        except ValueError:
            raise ValidationError('Please enter a valid number.')


class LoadWorkOrderForm(FlaskForm):

    line = SelectField(
        'Poucher', validators=[DataRequired()],
        choices=[
            ('5', 'Line 5'),
            ('6', 'Line 6'),
            ('7', 'Line 7'),
            ('8', 'Line 8'),
            ('9', 'Line 9')
        ]
    )
    priority = RadioField(
        validators=[DataRequired()],
        choices=[
            ('replace_job', 'Replace current work order'),
            ('schedule_next', 'Schedule after current work order'),
            ('schedule_append', 'Schedule after all work orders')
        ], default='schedule_append'
    )
    start_date = DateField(
        'Start Date', validators=[DataRequired()],
        default=dt.now().date()
    )
    start_time = TimeField(
        'Start Time', validators=[DataRequired()],
        default=dt.now().time()
    )

    submit = SubmitField('Load to Poucher')


class ConfirmDeleteForm(FlaskForm):

    delete = StringField("Type 'delete' to confirm: ",
                         validators=[DataRequired()])

    submit = SubmitField('Delete')

    @staticmethod
    def validate_delete(form: ConfirmDeleteForm, delete: StringField) -> None:
        if delete.data != 'delete':
            raise ValidationError("Type 'delete' in the field to confirm.")
