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

    def generate_scatter_with_regression(self, data):
        """Generate a scatter plot with a regression line."""
        img = io.BytesIO()
        plt.figure(figsize=(8, 4))
        
        # Ensure that there are at least 2 columns to plot
        if data.shape[1] > 1:
            sns.regplot(x=data.iloc[:, 0], y=data.iloc[:, 1], marker='o', color='purple', line_kws={"color": "red"})
            plt.title(f'Scatter Plot of {data.columns[0]} vs {data.columns[1]}')

            plt.savefig(img, format='png')
            img.seek(0)
            scatter_plot_url = base64.b64encode(img.getvalue()).decode('utf8')
            plt.close()
            return scatter_plot_url
        else:
            # Handle the case where there aren't enough columns for scatter plot
            return None
