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
file_bp = Blueprint('file', __name__)

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

    # Fetch only the current file for the user
    current_user_file = file_data  # since you already fetched the specific file data

    # Pass visualizations to the template
# Pass the DataFrame to the template
    return render_template('result.html', 
                        current_file=current_user_file,
                        tables=[df.head().to_html(classes='data', index=False)], 
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
@app.route('/impute/<file_id>')
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
    
    # Perform all imputation techniques and store results
    imputed_df, best_method = run_all_imputations(df)

    # Create a new document for the imputed data in MongoDB
    mongo.db.files.insert_one({
        'filename': f"{file_data['filename']}_imputed.csv",
        'content': imputed_df.to_csv(index=False),
        'user_id': current_user.id,
        'uploaded_at': pd.Timestamp.now(),
        'method': best_method
    })

    # Visualize the comparison of imputation techniques
    for method, imputed_df in imputed_results.items():
        scores[method] = evaluate_imputation(df, imputed_df)

    # Create a comparison bar chart for imputation scores
    comparison_chart = create_comparison_chart(scores)

    # Generate visualizations
    missing_values_heatmap = plot_missing_values_heatmap(df, imputed_df)
    distribution_plots = plot_distribution_comparison(df, imputed_df)
    boxplot_plots = plot_boxplot_comparison(df, imputed_df)
    missing_value_counts_plot = plot_missing_value_counts(df, imputed_df)

    # Pass visualizations to the template
    return render_template('imputation_result.html', 
                           tables=[df.head().to_html(classes='data')], 
                           comparison_chart=comparison_chart,
                           best_method=best_method,
                           missing_values_heatmap=missing_values_heatmap,
                           distribution_plots=distribution_plots,
                           boxplot_plots=boxplot_plots,
                           missing_value_counts_plot=missing_value_counts_plot)



# New Route for Imputation Result Page
@file_bp.route('/imputation_result')
@login_required
def imputation_result():
    # Logic to render the imputation results
    return render_template('imputation_result.html')

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

def plot_missing_values_heatmap(df_before, df_after):
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    sns.heatmap(df_before.isnull(), cbar=False, ax=axes[0], cmap='viridis')
    axes[0].set_title('Before Imputation')
    sns.heatmap(df_after.isnull(), cbar=False, ax=axes[1], cmap='viridis')
    axes[1].set_title('After Imputation')

    # Save to a BytesIO object
    img = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return base64.b64encode(img.getvalue()).decode('utf8')

def plot_distribution_comparison(df_before, df_after):
    missing_columns = df_before.columns[df_before.isnull().any()]
    columns_to_plot = missing_columns[:3]
    plot_urls = []

    for column in columns_to_plot:
        if pd.api.types.is_numeric_dtype(df_before[column]):
            plt.figure(figsize=(10, 6))
            sns.kdeplot(df_before[column], label='Before Imputation', color='blue', shade=True)
            sns.kdeplot(df_after[column], label='After Imputation', color='red', shade=True)
            plt.title(f'Distribution of {column} Before vs. After Imputation')
            plt.legend()

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()
            plot_urls.append(base64.b64encode(img.getvalue()).decode('utf8'))
        else:
            print(f"Skipping column '{column}' because it is not numeric.")
    
    return plot_urls

def plot_boxplot_comparison(df_before, df_after):
    missing_columns = df_before.columns[df_before.isnull().any()]
    plot_urls = []

    for column in missing_columns[:3]:
        if pd.api.types.is_numeric_dtype(df_before[column]):
            fig, ax = plt.subplots(1, 2, figsize=(12, 6))
            sns.boxplot(data=df_before, y=column, ax=ax[0], color='lightblue')
            ax[0].set_title(f'Before Imputation: {column}')
            sns.boxplot(data=df_after, y=column, ax=ax[1], color='lightgreen')
            ax[1].set_title(f'After Imputation: {column}')

            img = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()
            plot_urls.append(base64.b64encode(img.getvalue()).decode('utf8'))
        else:
            print(f"Skipping column '{column}' because it is not numeric.")
    
    return plot_urls

def plot_missing_value_counts(df_before, df_after):
    missing_before = df_before.isnull().sum()
    missing_after = df_after.isnull().sum()

    missing_counts = pd.DataFrame({
        'Before Imputation': missing_before,
        'After Imputation': missing_after
    })

    img = io.BytesIO()
    missing_counts.plot(kind='bar', figsize=(12, 6), color=['blue', 'green'])
    plt.title('Missing Values Count Before vs. After Imputation')
    plt.ylabel('Count of Missing Values')
    
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return base64.b64encode(img.getvalue()).decode('utf8')

if __name__ == '__main__':
    app.run(debug=True)