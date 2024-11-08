import pandas as pd
import os
import logging
from google.cloud import storage
from io import BytesIO

# Configure logging for anomaly detection
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSVStacker:
    def __init__(self, bucket_name, folder_path):
        self.bucket_name = bucket_name
        self.folder_path = folder_path
        self.dataframes = []
        self.stacked_df = None
        self.storage_client = storage.Client()

    def load_csv_files(self):
        blobs = self.storage_client.list_blobs(self.bucket_name, prefix=self.folder_path)
        csv_files = [blob for blob in blobs if blob.name.endswith('.csv')]
        
        if not csv_files:
            logger.warning(f"No CSV files found in bucket '{self.bucket_name}' with prefix '{self.folder_path}'.")
            return ["No CSV files found"]

        anomalies = []
        for blob in csv_files:
            if blob.size == 0:
                anomaly = f"File '{blob.name}' is empty and was skipped."
                logger.warning(anomaly)
                anomalies.append(anomaly)
                continue

            # Load the CSV file into a DataFrame
            data = blob.download_as_bytes()
            df = pd.read_csv(BytesIO(data))
            self.dataframes.append(df)
            logger.info(f"Loaded file '{blob.name}' successfully.")
        
        if not self.dataframes:
            anomalies.append("No valid data files were loaded.")
            logger.error("No valid data files were loaded.")
        
        return anomalies

    def detect_column_consistency(self):
        if not self.dataframes:
            logger.error("No DataFrames loaded to check for column consistency.")
            return ["No DataFrames loaded to check for column consistency"]

        anomalies = []
        first_columns = self.dataframes[0].columns
        for i, df in enumerate(self.dataframes[1:], start=1):
            if not df.columns.equals(first_columns):
                anomaly = f"Column mismatch detected in DataFrame {i}."
                logger.error(anomaly)
                anomalies.append(anomaly)
        if not anomalies:
            logger.info("All columns are consistent.")
        return anomalies

    def detect_data_anomalies(self):
        anomalies = []
        for i, df in enumerate(self.dataframes):
            for column in ["date", "parameter", "value"]:
                if column not in df.columns:
                    anomaly = f"Missing critical column '{column}' in DataFrame {i}."
                    logger.error(anomaly)
                    anomalies.append(anomaly)

            for _, row in df.iterrows():
                if row["parameter"] in ["pm25", "pm10", "o3", "no2", "so2", "co"] and row["value"] < 0:
                    anomaly = f"Invalid negative value detected for {row['parameter']}: {row['value']} on {row['date']} in DataFrame {i}."
                    logger.warning(anomaly)
                    anomalies.append(anomaly)
        return anomalies

    def stack_dataframes(self):
        if not self.dataframes:
            logger.error("No DataFrames to stack. Please load CSV files first.")
            return ["No DataFrames to stack"]
        
        self.stacked_df = pd.concat(self.dataframes, ignore_index=True)
        logger.info("DataFrames stacked successfully.")
        return []

    def save_as_pickle(self, output_path):
        if self.stacked_df is None:
            anomaly = "No DataFrame to save. Please stack the dataframes first."
            logger.error(anomaly)
            return [anomaly]
        
        self.stacked_df.to_pickle(output_path)
        logger.info(f"Stacked DataFrame saved as '{output_path}'.")
        return []

def stack_csvs_to_pickle():
    bucket_name = os.getenv("GCS_BUCKET_NAME")  # Set your GCS bucket name here
    folder_path = os.getenv("GCS_FOLDER_PATH")  # Set your folder path here
    output_pickle_file = os.getenv("GCS_OUTPUT_PICKLE_FILE")  # Set your output pickle file path

    csv_stacker = CSVStacker(bucket_name, folder_path)
    anomalies = []

    # Step 1: Load files and detect file-level anomalies
    anomalies.extend(csv_stacker.load_csv_files())

    # Step 2: Detect column consistency anomalies
    anomalies.extend(csv_stacker.detect_column_consistency())

    # Step 3: Detect data-related anomalies
    anomalies.extend(csv_stacker.detect_data_anomalies())

    # If no anomalies are detected, proceed with stacking and saving
    if not anomalies:
        anomalies.extend(csv_stacker.stack_dataframes())
        anomalies.extend(csv_stacker.save_as_pickle(output_pickle_file))
        logger.info("No anomalies detected. Process completed successfully.")
    else:
        logger.error("Anomalies detected; skipping stacking and saving.")

    return anomalies  # Return list of all detected anomalies

if __name__ == "__main__":
    detected_anomalies = stack_csvs_to_pickle()
    if detected_anomalies:
        logger.error(f"Detected Anomalies: {detected_anomalies}")
    else:
        logger.info("No anomalies detected. Process completed successfully.")
