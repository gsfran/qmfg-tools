from __future__ import annotations

from datetime import datetime as dt

from flask_wtf import FlaskForm
from wtforms import (IntegerField, RadioField, SelectField, StringField,
                     SubmitField)
from wtforms.fields.datetime import DateField, TimeField
from wtforms.validators import (DataRequired, Length, NumberRange,
                                ValidationError)


class NewWorkOrderForm(FlaskForm):

    product = SelectField(
        'Product', validators=[DataRequired()],
        choices=[
            ('flu', 'Flu - 1169100'),
            ('abc', 'ABC - 1451300'),
            ('strep_aplus', 'Strep A+ - 1330700'),
            ('rsv', 'RSV - 1175000'),
            ('sars', 'SARS - 1440700'),
            ('strep_inline', 'Strep Inline - 1094000'),
            ('other', 'Other')
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

    def validate_lot_number(
        form: NewWorkOrderForm, lot_number: StringField
        ) -> None:
        try:
            int(lot_number.data)
        except ValueError:
            raise ValidationError('Please enter a valid number.')

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