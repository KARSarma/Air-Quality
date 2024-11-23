# Provider block for Google Cloud
provider "google" {
  credentials = file("/Users/swapnavippaturi/Downloads/key.json")
  project     = var.project_id  # GCP Project ID
  region      = var.region      # GCP Region
}

# Variables for project and environment configuration

variable "serviceAccount" {
  description = "The service account email"
  type        = string
}

# Create a random ID for uniqueness in bucket name
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Create a Cloud Storage bucket for Composer DAGs
resource "google_storage_bucket" "bucketname" {
  name           = "${var.bucket_name}-${random_id.bucket_suffix.hex}"  # Ensure globally unique name
  location       = var.region
  force_destroy  = true  # Automatically delete bucket contents when destroying
}

# Create IAM service account for Composer
resource "google_service_account" "composer_service_account" {
  account_id   = "composer-service-account"
  display_name = "Composer Service Account"
}

# Grant necessary roles to the Composer service account
resource "google_project_iam_member" "composer_service_account_roles" {
  for_each = toset([
    "roles/composer.admin",      # Admin for Cloud Composer
    "roles/storage.admin",       # Admin for Cloud Storage
    "roles/iam.serviceAccountUser",  # IAM Service Account User role
    "roles/logging.logWriter",   # Logs access
    "roles/monitoring.viewer"    # Monitoring access
  ])

  project = var.project_id
  member  = "serviceAccount:${google_service_account.composer_service_account.email}"
  role    = each.value
}

resource "google_composer_environment" "airquality" {
  name   = "airquality-composer"
  region = "us-central1"

  config {
    software_config {
      image_version = "composer-2.9.7-airflow-2.9.3"  # Use a valid image version
      pypi_packages = {
        "gs://airquality-mlops-rg/composer_requirements/requirements.txt" = ""
      }
      env_variables = {
        # Your previously defined environment variables
        LOAD_BUCKET_NAME                 = "airquality-mlops-rg"
        FOLDER_PATH                      = "api_data/"
        LOAD_OUTPUT_PICKLE_FILE          = "processed/air_pollution.pkl"
        BIAS_CHECK_INPUT_PATH            = "gs://airquality-mlops-rg/processed/air_pollution.pkl"
        BIAS_CHECK_OUTPUT_PATH           = "gs://airquality-mlops-rg/processed/resampled_data.pkl"
        BIAS_CHECK_SENSITIVE_FEATURE     = "month"
        BIAS_CHECK_THRESHOLD             = "0.2"
        DATA_SPLIT_BUCKET_NAME           = "airquality-mlops-rg"
        DATA_SPLIT_INPUT_FILE_PATH       = "processed/resampled_data.pkl"
        DATA_SPLIT_TRAIN_OUTPUT_FILE_PATH= "processed/train/train_data.pkl"
        DATA_SPLIT_TEST_OUTPUT_FILE_PATH = "processed/test/test_data.pkl"
        SCHEMA_STATS_BUCKET_NAME         = "airquality-mlops-rg"
        SCHEMA_STATS_INPUT_FILE_PATH     = "processed/resampled_data.pkl"
        SCHEMA_FILE_OUTPUT_PATH          = "processed/Schema.pkl"
        STATS_FILE_OUTPUT_PATH           = "processed/Stats.pkl"
        DATA_BUCKET_NAME                 = "airquality-mlops-rg"
        TRAIN_DATA_PIVOT_INPUT           = "processed/train/train_data.pkl"
        TRAIN_DATA_PIVOT_OUTPUT          = "processed/train/pivot_data.pkl"
        TRAIN_DATA_RM_COL_INPUT          = "processed/train/pivot_data.pkl"
        TRAIN_DATA_RM_COL_OUTPUT         = "processed/train/remove_col_data.pkl"
        TRAIN_DATA_MISS_VAL_INPUT        = "processed/train/remove_col_data.pkl"
        TRAIN_DATA_MISS_VAL_OUTPUT       = "processed/train/missing_val_data.pkl"
        TRAIN_DATA_ANMLY_INPUT          = "processed/train/missing_val_data.pkl"
        TRAIN_DATA_ANMLY_OUTPUT         = "processed/train/anamoly_data.pkl"
        TRAIN_DATA_FEA_ENG_INPUT         = "processed/train/anamoly_data.pkl"
        TRAIN_DATA_FEA_ENG_OUTPUT        = "processed/train/feature_eng_data.pkl"
        TRAIN_SCHEMA_FILE_PATH           = "processed/train/output_schema.pkl"
        TRAIN_STATS_FILE_PATH            = "processed/train/output_stats.pkl"
        TRAIN_DATASET_FILE_PATH          = "processed/train/feature_eng_data.pkl"
        TEST_DATA_PIVOT_INPUT            = "processed/test/test_data.pkl"
        TEST_DATA_PIVOT_OUTPUT           = "processed/test/pivot_data.pkl"
        TEST_DATA_RM_COL_INPUT           = "processed/test/pivot_data.pkl"
        TEST_DATA_RM_COL_OUTPUT          = "processed/test/remove_col_data.pkl"
        TEST_DATA_MISS_VAL_INPUT         = "processed/test/remove_col_data.pkl"
        TEST_DATA_MISS_VAL_OUTPUT        = "processed/test/missing_val_data.pkl"
        TEST_DATA_ANMLY_INPUT           = "processed/test/missing_val_data.pkl"
        TEST_DATA_ANMLY_OUTPUT          = "processed/test/anamoly_data.pkl"
        TEST_DATA_FEA_ENG_INPUT          = "processed/test/anamoly_data.pkl"
        TEST_DATA_FEA_ENG_OUTPUT         = "processed/test/feature_eng_data.pkl"
        TEST_SCHEMA_FILE_PATH           = "processed/test/output_schema.pkl"
        TEST_STATS_FILE_PATH            = "processed/test/output_stats.pkl"
        TEST_DATASET_FILE_PATH          = "processed/test/feature_eng_data.pkl"
        # SMTP Configuration
       #AIRFLOW__SMTP__SMTP_HOST        = "smtp.gmail.com"
        #AIRFLOW__SMTP__SMTP_PORT        = "587"
        #AIRFLOW__SMTP__SMTP_USER        = "your_email@gmail.com"
        #AIRFLOW__SMTP__SMTP_PASSWORD    = "your_app_password"  # Use an app-specific password
        #AIRFLOW__SMTP__SMTP_MAIL_FROM   = "your_email@gmail.com"
        #AIRFLOW__SMTP__SMTP_DEFAULT_SENDER = "your_email@gmail.com"
        #AIRFLOW__SMTP__SMTP_DEFAULT_RECIPIENT = "recipient@example.com"
        #AIRFLOW__SMTP__SMTP_TLS         = "True"
        #AIRFLOW__SMTP__SMTP_STARTTLS    = "True"
        #AIRFLOW__SMTP__SMTP_SSL         = "False"
      }
    }
  }
}

# Optional: Set up the network and subnetwork (if required)
resource "google_compute_network" "composer_network" {
  name                    = "composer-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "composer_subnetwork" {
  name          = "composer-subnetwork"
  network       = google_compute_network.composer_network.name
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
}

/*
resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project_id}-function-source"
  location = var.region
  force_destroy = true
}

resource "google_storage_bucket_object" "function_archive" {
  name   = "function-source.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = "${path.module}/function-source.zip"
}

resource "google_cloudfunctions_function" "cloud_function" {
  name        = "fetch-air-quality-data"
  runtime     = "python39"
  available_memory_mb = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.function_archive.name
  trigger_http          = true
  entry_point           = "collect_air_quality_data" # Name of the function in main.py
  environment_variables = {
    API_KEY       = var.API_KEY
    gcs-bucket    = var.gcs-bucket
    location_city = var.location_city
    initial_date1 = var.initial_date1
    final_date1   = var.final_date1
    initial_date2 = var.initial_date2
    final_date2   = var.final_date2
  }
}

resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = google_cloudfunctions_function.cloud_function.project
  region         = google_cloudfunctions_function.cloud_function.region
  cloud_function = google_cloudfunctions_function.cloud_function.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}
*/