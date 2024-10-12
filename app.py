from flask import Flask, render_template, redirect, url_for, flash, request
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
import io
import pandas as pd

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
files = mongo.db.files

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
# Dashboard route (show user's uploaded files)
@app.route('/dashboard')
@login_required
def dashboard():
    user_files = list(files.find({'user_id': current_user.id}))  # Convert cursor to list
    return render_template('dashboard.html', files=user_files)



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
# Route to handle file uploads
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file:
        # Save file content in MongoDB
        file_content = file.read()  # Read the file content in binary format
        file_id = files.insert_one({
            'filename': file.filename,
            'content': file_content,
            'user_id': current_user.id,
            'uploaded_at': pd.Timestamp.now()
        }).inserted_id

        flash(f'File {file.filename} uploaded successfully!', 'success')
        return redirect(url_for('dashboard'))
    
# Route to visualize an uploaded file
@app.route('/visualize/<file_id>')
@login_required
def visualize(file_id):
    # Fetch the file from MongoDB
    file_data = files.find_one({'_id': ObjectId(file_id), 'user_id': current_user.id})
    
    if not file_data:
        flash('File not found or you do not have access to this file.', 'danger')
        return redirect(url_for('dashboard'))

    # Convert the file content back to a pandas DataFrame
    file_content = file_data['content']
    df = pd.read_csv(io.BytesIO(file_content))

    # Visualize or process the file content (you can implement your visualizer)
    # For example, return the first few rows of the DataFrame
    return render_template('result.html', tables=[df.head().to_html(classes='data')])

if __name__ == '__main__':
    app.run(debug=True)
