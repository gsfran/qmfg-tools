from __future__ import annotations

from datetime import datetime as dt
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, ValidationError
from wtforms.fields.datetime import DateField, TimeField


class NewWorkOrderForm(FlaskForm):

    product = SelectField(
        'Product Type', validators=[DataRequired()],
        choices=[
            ('flu', 'Flu - 1169100'),
            ('abc', 'ABC - 1451300'),
            ('strep_aplus', 'Strep A+ - 1330700'),
            ('rsv', 'RSV - 1175000'),
            ('sars', 'SARS - 1440700'),
            ('strep_inline', 'Strep InLine - 1094000'),
            ('other', 'Other')
            ]
        )

    lot_id = StringField('Lot ID', validators=[DataRequired()])
    lot_number = StringField('Pouch Lot #', validators=[DataRequired()])
    strip_lot_number = StringField('Strip Lot #', validators=[DataRequired()])
    strip_qty = StringField('Strip Qty.', validators=[DataRequired()])

    
    submit = SubmitField('Save Work Order')

    def validate_lot_number(form: NewWorkOrderForm, lot_number: int):
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

    def validate_strip_qty(
        form: NewWorkOrderForm, strip_qty: StringField
        ) -> None:
        try:
            int(strip_qty.data)
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
    
    start_date = DateField(
        'Start Date', default=dt.now().date()
    )
    
    start_time = TimeField(
        'Start Time',  default=dt.now().time()
    )
    
    submit = SubmitField('Load to Poucher')