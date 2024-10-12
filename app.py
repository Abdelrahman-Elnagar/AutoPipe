from flask import Flask, render_template, redirect, url_for, flash, request
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os

app = Flask(__name__)

# Configuration
app.config['MONGO_URI'] = 'mongodb://localhost:27017/autopipe'
app.config['SECRET_KEY'] = 'your_secret_key'
mongo = PyMongo(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# MongoDB Collection
users = mongo.db.users

# User class to handle Flask-Login
class User(UserMixin):
    def __init__(self, user_id, email):
        self.id = user_id
        self.email = email

# Load user for Flask-Login session management
@login_manager.user_loader
def load_user(user_id):
    user = users.find_one({'_id': ObjectId(user_id)})
    if user:
        return User(str(user['_id']), user['email'])
    return None

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        existing_user = users.find_one({'email': email})
        
        if existing_user:
            flash('User already exists. Please log in.', 'danger')
            return redirect(url_for('login'))

        # Hash the password and create a new user
        hashed_password = generate_password_hash(password)
        new_user_id = users.insert_one({'email': email, 'password': hashed_password}).inserted_id

        # Log in the user after registration
        login_user(User(str(new_user_id), email))
        return redirect(url_for('dashboard'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            # Log the user in
            login_user(User(str(user['_id']), user['email']))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

# Dashboard route (only accessible when logged in)
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', email=current_user.email)

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Home route (Upload page)
@app.route('/')
@login_required
def index():
    return render_template('upload.html')

# Route to handle file uploads (dashboard functionality)
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    # File upload logic remains here
    pass

if __name__ == '__main__':
    app.run(debug=True)
