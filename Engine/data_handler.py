import os
import pandas as pd

class DataHandler:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder

    def save_file(self, file):
        """Save the uploaded file to the upload folder."""
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

        filepath = os.path.join(self.upload_folder, file.filename)
        file.save(filepath)
        return filepath

    def load_data(self, filepath):
        """Load CSV data from the given filepath."""
        data = pd.read_csv(filepath)
        return data

    def get_summary_statistics(self, data):
        """Return summary statistics of the data."""
        return data.describe()
