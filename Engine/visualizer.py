import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

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
