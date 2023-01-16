from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired, ValidationError


class NewWorkOrder(FlaskForm):
    
    product_dict = {
        'flu': {
            'Item Number': 1169100,
            'Product Name': 'Flu',
        },

        'abc': {
            'Item Number': 1451300,
            'Product Name': 'ABC',
        },

        'strep_aplus': {
            'Item Number': 1330700,
            'Product Name': 'Strep A+',
        },

        'rsv': {
            'Item Number': 1175000,
            'Product Name': 'RSV',
        },

        'sars': {
            'Item Number': 1440700,
            'Product Name': 'SARS',
        },

        'strep_inline': {
            'Item Number': 1094000,
            'Product Name': 'Strep Inline',
        }
    }

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
    
    def validate_lot_number(form, lot_number):
        try:
            int(lot_number.data)
        except ValueError:
            raise ValidationError('Please enter a valid number.')
    
    strip_lot_number = StringField('Strip Lot #', validators=[DataRequired()])
    
    def validate_strip_lot_number(
        form: FlaskForm, strip_lot_number: StringField
        ) -> None:
        try:
            int(strip_lot_number.data)
        except ValueError:
            raise ValidationError('Please enter a valid number.')

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