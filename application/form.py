from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired


class UserDataForm(FlaskForm):

    lot_number = StringField('Work Order #', validators=[DataRequired()])
    product = SelectField(
        'Product', validators=[DataRequired()],
        choices=[
            ('Flu', 'Flu'),
            ('Flu + SARS', 'Flu + SARS'),
            ('Strep A+', 'Strep A+'),
            ('RSV', 'RSV'),
            ('SARS Antigen', 'SARS Antigen')
            ]
        )
    category = SelectField(
        "Category", validators=[DataRequired()],
        choices=[
            ('cat1', 'cat1'),
            ('cat2', 'cat2'),
            ('cat3', 'cat3'),
            ('cat4', 'cat4')
            ]
        )
        
    submit = SubmitField('Submit')