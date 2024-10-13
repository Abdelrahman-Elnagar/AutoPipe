from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request # type: ignore
from flask_pymongo import PyMongo# type: ignore
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin# type: ignore
from werkzeug.security import generate_password_hash, check_password_hash# type: ignore
from bson.objectid import ObjectId# type: ignore
import matplotlib.pyplot as plt# type: ignore
import seaborn as sns# type: ignore
import base64
import os
import io
import pandas as pd# type: ignore
from bson import ObjectId# type: ignore
import re
from Engine.data_imputation.run_imputation import run_all_imputations

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
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

# Load user for Flask-Login session management
@login_manager.user_loader
def load_user(user_id):
    try:
        user = users.find_one({'_id': ObjectId(user_id)})
        if user:
            return User(str(user['_id']), user['username'])
    except Exception as e:
        flash('Error loading user: {}'.format(str(e)), 'danger')
    return None

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Basic email format validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email format.', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return redirect(url_for('register'))
        
        try:
            existing_user = users.find_one({'email': email})
            if existing_user:
                flash('User already exists. Please log in.', 'danger')
                return redirect(url_for('login'))

            # Hash the password and create a new user
            hashed_password = generate_password_hash(password)
            new_user_id = users.insert_one({'email': email, 'password': hashed_password ,'username': username}).inserted_id

            # Log in the user after registration
            login_user(User(str(new_user_id), email))
            flash('Registration successful! Welcome!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash('Registration failed: {}'.format(str(e)), 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('username and password are required.', 'danger')
            return redirect(url_for('login'))

        try:
            user = users.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                # Log the user in
                login_user(User(str(user['_id']), user['username']))
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials. Please try again.', 'danger')

        except Exception as e:
            flash('Login failed: {}'.format(str(e)), 'danger')
            return redirect(url_for('login'))

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

        # Run all imputation techniques and choose the best one
    '''imputed_df, best_method = run_all_imputations(df)

    # Show the user the imputed data and method used
    flash(f'Best imputation technique: {best_method}', 'success')'''
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
# New Route for Imputation Page
file_bp = Blueprint('file', __name__)
@file_bp.route('/impute/<file_id>')
@login_required
def impute(file_id):
    # Fetch the file from MongoDB
    file_data = mongo.db.files.find_one({'_id': ObjectId(file_id), 'user_id': current_user.id})

    if not file_data:
        flash('File not found or you do not have access to this file.', 'danger')
        return redirect(url_for('file.dashboard'))

    # Convert the file content back to a pandas DataFrame
    file_content = file_data['content']
    df = pd.read_csv(io.BytesIO(file_content))

    # Run all imputation techniques and choose the best one
    imputed_results = {}
    scores = {}
    imputed_df, best_method = run_all_imputations(df)

    # Visualize the comparison of imputation techniques
    for method, imputed_df in imputed_results.items():
        # Store the scores and method names for visualization
        scores[method] = evaluate_imputation(df, imputed_df)

    # Create a comparison bar chart for imputation scores
    comparison_chart = create_comparison_chart(scores)

    # Pass the imputation results, scores, and best method to the template
    return render_template('imputation_result.html', 
                           tables=[df.head().to_html(classes='data')], 
                           comparison_chart=comparison_chart,
                           best_method=best_method)

# Helper to create bar chart for imputation comparisons
def evaluate_imputation(df_original, df_imputed):
    """
    A simple evaluation criterion:
    Measure the number of filled missing values and return a score.
    The more missing values filled, the better the score.
    """
    original_nulls = df_original.isnull().sum().sum()
    imputed_nulls = df_imputed.isnull().sum().sum()

    # The score is the reduction in missing values.
    score = original_nulls - imputed_nulls
    return score

def create_comparison_chart(scores):
    """Create a bar chart comparing imputation techniques."""
    img = io.BytesIO()
    methods = list(scores.keys())
    scores_values = list(scores.values())

    plt.figure(figsize=(8, 4))
    plt.bar(methods, scores_values, color='skyblue')
    plt.title('Imputation Technique Comparison')
    plt.xlabel('Imputation Methods')
    plt.ylabel('Scores (Missing Value Reduction)')
    
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode('utf8')

if __name__ == '__main__':
    app.run(debug=True)


