# variables.tf

variable "project_id" {
  description = "The ID of the project where resources will be created"
  type        = string
}

variable "region" {
  description = "Region where resources will be created"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "Name of the GCS bucket for data storage"
  type        = string
}

variable "composer_env_name" {
  description = "Name of the Cloud Composer environment"
  type        = string
}

variable "API_KEY" {
  description = "API key for OpenAQ API"
  type        = string
}

variable "gcs-bucket" {
  description = "bucket_name"
  type        = string
}
variable "initial_date1" {
  description = "initial_date"
  type        = string
}
variable "initial_date2" {
  description = "initial_date2"
  type        = string
}
variable "final_date1" {
  description = "final_date1"
  type        = string
}
variable "final_date2" {
  description = "final_date2"
  type        = string
}
variable "location_city" {
  description = "location_city "
  type        = string
}
