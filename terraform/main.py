import requests
import json
import pandas as pd
import os
from google.cloud import storage
from datetime import datetime

api_key = os.getenv("API_KEY")
city = os.getenv("location_city")
country_code = "US"
start_date_1= os.getenv("initial_date1")  
end_date_1 = os.getenv("final_date1")
start_date_2= os.getenv("initial_date2")  
end_date_2 = os.getenv("final_date2")

# Initialize Google Cloud Storage client
client = storage.Client()
bucket_name = os.getenv("gcs-bucket")  # Replace with your GCS bucket name

def get_location_id(city, country_code):
    url = "https://api.openaq.org/v2/locations"
    headers = {"x-api-key": api_key}
    params = {"city": city, "country": country_code}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and len(data['results']) > 0:
            return data['results'][0]['id']
        else:
            return None
    else:
        return None

def get_air_pollution_data(location_id, start_date, end_date):
    url = "https://api.openaq.org/v2/measurements"
    headers = {"x-api-key": api_key}
    params = {
        "location_id": location_id,
        "date_from": start_date,
        "date_to": end_date,
        "limit": 40000,
        "sort": "asc"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
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
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)
    flattened_data = flatten_data(data)
    df = pd.DataFrame(flattened_data)
    blob.upload_from_string(df.to_csv(index=False), 'text/csv')
    print(f"Data saved to GCS as {filename}")

def collect_air_quality_data(request):
    location_id = 869  # You can replace with dynamic ID fetching if needed

    if location_id:
        air_pollution_data_1 = get_air_pollution_data(location_id, start_date_1, end_date_1)
        air_pollution_data_2 = get_air_pollution_data(location_id, start_date_2, end_date_2)

        if air_pollution_data_1:
            save_to_gcs(air_pollution_data_1, f"air_pollution_data_1_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        if air_pollution_data_2:
            save_to_gcs(air_pollution_data_2, f"air_pollution_data_2_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")

    return "Data Collection Completed", 200
