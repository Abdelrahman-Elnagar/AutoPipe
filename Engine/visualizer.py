import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

class DataVisualizer:
    def __init__(self):
        pass

    def generate_histogram(self, data):
        """Generate a histogram of the first column of the data."""
        img = io.BytesIO()
        plt.figure(figsize=(8, 4))
        sns.histplot(data.iloc[:, 0], kde=True, color='blue')
        plt.title(f'Distribution of {data.columns[0]}')

        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close()
        return plot_url
