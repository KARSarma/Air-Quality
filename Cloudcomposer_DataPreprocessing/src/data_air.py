import requests
import json
import pandas as pd
from google.cloud import storage
import os

# Set up your Google Cloud Storage bucket name
BUCKET_NAME = "airquality-mlops-rg"

# GCP authentication (ensure your environment is authenticated with the correct credentials)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gs://us-central1-airquality-comp-decf5871-bucket/airquality-key.json"

# API details
api_key = "3fbb719154baaed8164cee7d57ba31903cdd19fdd7613e33ace632a0d851894e"
city = "Miami-Fort Lauderdale-Miami Beach"
country_code = "US"
start_date_1 = "2022-01-01T00:00:00Z"
end_date_1 = "2022-12-31T23:59:59Z"
start_date_2 = "2023-01-01T00:00:00Z"
end_date_2 = "2023-12-31T23:59:59Z"

def get_location_id(city, country_code):
    url = "https://api.openaq.org/v2/locations"
    headers = {
        "x-api-key": api_key
    }
    params = {
        "city": city,
        "country": country_code
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and len(data['results']) > 0:
            return data['results'][0]['id']
        else:
            print(f"No location found for {city}, {country_code}")
            return None
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def get_air_pollution_data(location_id, start_date, end_date):
    url = "https://api.openaq.org/v2/measurements"
    headers = {
        "x-api-key": api_key
    }
    params = {
        "location_id": location_id,
        "date_from": start_date,
        "date_to": end_date,
        "limit": 40000,
        "sort": "asc"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

def flatten_data(data):
    flattened_data = []
    for entry in data['results']:
        if isinstance(entry, dict):
            flat_entry = {
                "date": entry.get("date", {}).get("utc", None),
                "location": entry.get("location", None),
                "parameter": entry.get("parameter", None),
                "value": entry.get("value", None),
                "unit": entry.get("unit", None),
                "latitude": entry.get("coordinates", {}).get("latitude", None),
                "longitude": entry.get("coordinates", {}).get("longitude", None),
                "city": entry.get("city", None),
                "country": entry.get("country", None)
            }
            flattened_data.append(flat_entry)
    return flattened_data

def save_to_gcs(data, filename):
    flattened_data = flatten_data(data)
    df = pd.DataFrame(flattened_data)
    
    # Save to temporary local file
    temp_local_path = f"/tmp/{filename}"
    df.to_csv(temp_local_path, index=False)

    # Upload to Google Cloud Storage
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"api_data/{filename}")  # Store under 'csv/' directory in the bucket
    blob.upload_from_filename(temp_local_path)

    print(f"Data saved to GCS as gs://{BUCKET_NAME}/api_data/{filename}")
    # Clean up temporary file
    os.remove(temp_local_path)

def get_available_parameters(location_id):
    url = f"https://api.openaq.org/v2/locations/{location_id}"
    headers = {
        "x-api-key": api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and len(data['results']) > 0:
            parameters = data['results'][0]['parameters']
            return parameters
        else:
            print(f"No parameters found for location ID {location_id}")
            return None
    else:
        print(f"Error fetching parameters: {response.status_code}")
        return None

def download_data_function():
    location_id = 869
    available_parameters = get_available_parameters(location_id)
    if available_parameters:
        print("Available parameters at this location:")
        for param in available_parameters:
            print(param['parameter'])

    if location_id:
        print(f"Location ID for {city}: {location_id}")
        air_pollution_data_1 = get_air_pollution_data(location_id, start_date_1, end_date_1)
        air_pollution_data_2 = get_air_pollution_data(location_id, start_date_2, end_date_2)

        if air_pollution_data_1:
            save_to_gcs(air_pollution_data_1, "air_pollution_data_1.csv")
        if air_pollution_data_2:
            save_to_gcs(air_pollution_data_2, "air_pollution_data_2.csv")

if __name__ == "__main__":
    download_data_function()
