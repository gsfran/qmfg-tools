from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired


class NewWorkOrder(FlaskForm):

    product = SelectField(
        'Product Type', validators=[DataRequired()],
        choices=[
            ('flu', 'Flu -- 1169100'),
            ('abc', 'ABC -- 1451300'),
            ('strep_aplus', 'Strep A+ -- 1330700'),
            ('rsv', 'RSV -- 1175000'),
            ('sars', 'SARS -- 1440700'),
            ('strep_inline', 'Strep InLine -- 1094000'),
            ('other', 'Other')
            ]
        )

    lot_id = StringField('Lot ID', validators=[DataRequired()])

    lot_number = StringField('Pouch Lot #', validators=[DataRequired()])
    
    strip_lot_number = StringField('Strip Lot #', validators=[DataRequired()])

    status = SelectField(
        'Save to', validators=[DataRequired()],
        choices=[
            ('Parking Lot', 'Parking Lot'),
            ('on Line 5', 'Line 5'),
            ('on Line 6', 'Line 6'),
            ('on Line 7', 'Line 7'),
            ('on Line 8', 'Line 8'),
            ('on Line 9', 'Line 9'),
            ]
        )

    submit = SubmitField('Save Work Order')