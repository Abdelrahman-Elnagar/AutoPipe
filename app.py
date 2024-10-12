from flask import Flask, render_template, request, redirect, url_for, flash
from Engine.data_handler import DataHandler
from Engine.visualizer import DataVisualizer
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages

# Path to save uploaded files
UPLOAD_FOLDER = 'uploads'
data_handler = DataHandler(UPLOAD_FOLDER)
data_visualizer = DataVisualizer()

# Route for the home page
@app.route('/')
def index():
    return render_template('upload.html')

# Route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file:
        # Save the file using DataHandler
        filepath = data_handler.save_file(file)

        # Load the data
        data = data_handler.load_data(filepath)

        # Generate visualizations
        summary_stats = data_handler.get_summary_statistics(data)
        plot_url = data_visualizer.generate_histogram(data)

        # Flash a message to the user
        flash(f'Successfully uploaded {file.filename}!', 'success')

        return render_template('result.html', tables=[summary_stats.to_html(classes='data')], 
                                               plot_url=plot_url)

if __name__ == '__main__':
    app.run(debug=True)
