from flask import Flask, render_template, redirect, url_for, flash, request
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import os
import io
import pandas as pd

app = Flask(__name__, template_folder='GUI/templates')

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

    # Generate visualizations
    histogram_url = create_histogram(df)
    scatter_plot_url = create_scatter_plot(df)

    # Pass visualizations to the template
    return render_template('result.html', 
                           tables=[df.head().to_html(classes='data')], 
                           histogram_url=histogram_url, 
                           scatter_plot_url=scatter_plot_url)

def create_histogram(df):
    """Create a histogram of the first numeric column in the DataFrame."""
    img = io.BytesIO()
    plt.figure(figsize=(8, 4))
    sns.histplot(df.iloc[:, 0], kde=True, color='blue')  # Adjust as needed for your data
    plt.title(f'Histogram of {df.columns[0]}')
    plt.xlabel(df.columns[0])
    plt.ylabel('Frequency')

    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode('utf8')

def create_scatter_plot(df):
    """Create a scatter plot of the first two numeric columns in the DataFrame."""
    img = io.BytesIO()
    plt.figure(figsize=(8, 4))

    # Ensure there are at least two numeric columns
    if df.shape[1] > 1:
        sns.scatterplot(x=df.iloc[:, 0], y=df.iloc[:, 1], color='purple')
        plt.title(f'Scatter Plot of {df.columns[0]} vs {df.columns[1]}')
        plt.xlabel(df.columns[0])
        plt.ylabel(df.columns[1])

        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return base64.b64encode(img.getvalue()).decode('utf8')
    
    # If not enough columns for a scatter plot
    return None


if __name__ == '__main__':
    app.run(debug=True)


