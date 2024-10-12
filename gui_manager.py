import streamlit as st
from Engine.data_handler import DataHandler
from Engine.visualizer import Visualizer

class GUIManager:
    """
    Handles the GUI interface using Streamlit. 
    It allows users to upload CSV files, load data, and view the visualizations created by the backend.
    """
    def __init__(self):
        self.data_handler = None
        self.visualizer = None

    def run(self):
        """ Main interface to run the Streamlit GUI. """
        st.title("AutoPipe Data Visualizer")
        st.write("Upload a CSV file to visualize the data's characteristics and anomalies.")

        # File Upload Section
        uploaded_file = st.file_uploader("Choose a file", type=['csv'])
        if uploaded_file:
            # Initialize data handler and load the data
            self.data_handler = DataHandler(uploaded_file)
            data = self.data_handler.load_data()

            if data is not None:
                st.success("File loaded successfully!")
                summary, missing = self.data_handler.get_summary()

                # Show basic data summary
                st.subheader("Basic Data Summary")
                st.write(summary)
                
                st.subheader("Missing Values Summary")
                st.write(missing)

                # Initialize Visualizer
                self.visualizer = Visualizer(data)

                # Visualization Options
                st.subheader("Select Visualizations to Display")
                if st.checkbox("Show Histograms"):
                    self.visualizer.plot_histogram()

                if st.checkbox("Show Missing Value Heatmap"):
                    self.visualizer.plot_missing_values()

                if st.checkbox("Show Outliers (Boxplot)"):
                    self.visualizer.plot_outliers()

                if st.checkbox("Show Correlation Heatmap"):
                    self.visualizer.plot_correlation_heatmap()
