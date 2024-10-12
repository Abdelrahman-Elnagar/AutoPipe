# routes.py
from flask import Blueprint, render_template

# Create a Blueprint
main = Blueprint('main', __name__)

# Define a route
@main.route('/')
def home():
    return render_template('index.html')

@main.route('/about')
def about():
    return render_template('about.html')
