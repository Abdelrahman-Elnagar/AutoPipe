# Engine/routes/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from Engine.models import db, User  # Adjust the import path for models

# Create a Blueprint for authentication
auth = Blueprint('auth', __name__)

# Define a route for login
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            # Implement login logic here
            flash('Login Successful!', 'success')
            return redirect(url_for('main.home'))
        flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html')

# Define a route for registration
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')
