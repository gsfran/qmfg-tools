from application import app
from flask import render_template, url_for, redirect, flash, get_flashed_messages
from application.form import UserDataForm
from application.models import TestDataBase
from application import db
import json


@app.route('/')
def index():
    entries = TestDataBase.query.order_by(TestDataBase.date.desc()).all()
    return render_template('index.html', entries=entries)

@app.route('/add', methods=["GET", "POST"])
def add_entry():
    form = UserDataForm()
    if form.validate_on_submit():
        entry = TestDataBase(type=form.type.data, category=form.category.data, amount=form.amount.data)
        db.session.add(entry)
        db.session.commit()
        flash(f'{form.type.data} has been added to {form.type.data}s', 'success')
        return redirect(url_for('index'))
    return render_template('add.html', title="Add expenses", form=form)

@app.route('/delete-post/<int:entry_id>')
def delete(entry_id):
    entry = TestDataBase.query.get_or_404(int(entry_id))
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    pass