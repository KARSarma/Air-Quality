from airflow import DAG
from scipy import stats
from airflow.operators.python import PythonOperator
from datetime import datetime
import numpy as np
from airflow import configuration as conf
from google.cloud import storage
import io
import os
import pandas as pd
from google.cloud import storage
import logging
from airflow.providers.http.operators.http import HttpOperator

#from airflow.providers.google.cloud.operators.functions import GoogleCloudFunctionInvokeFunctionOperator
from airflow.utils.dates import days_ago
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.email import EmailOperator
from airflow.operators.dummy import DummyOperator
from datetime import timedelta,datetime
from airflow.utils.dates import days_ago
#from dags.DataPreprocessing.src.data_air import download_data_function
from my_operators.data_loader import stack_csvs_to_pickle
from my_operators.data_split import split
from my_operators.pivoting_data import pivot_parameters as pivoting_data_train
from my_operators.removal_of_uneccesary_cols import remove_uneccesary_cols as removal_of_uneccesary_cols_train
from my_operators.anamoly_detection import anamoly_detection_val as anamoly_detection_train
from my_operators.check_missing_values import handle_missing_vals as check_missing_values_train
from my_operators.feature_eng import feature_engineering as feature_eng_train
from my_operators.test.pivoting_data import pivot_parameters as pivoting_data_test
from my_operators.test.removal_of_uneccesary_cols import remove_uneccesary_cols as removal_of_uneccesary_cols_test
from my_operators.test.anamoly_detection import anamoly_detection_val as anamoly_detection_test
from my_operators.test.check_missing_values import handle_missing_vals as check_missing_values_test
from my_operators.test.feature_eng import feature_engineering as feature_eng_test
from my_operators.check_schema_original_airpollution import  main_generate_schema_and_statistics as main_check_schema_original
from my_operators.test.check_output_data_schema import main_generate_schema_and_statistics as main_test_schema
from my_operators.check_output_data_schema import main_generate_schema_and_statistics as main_train_schema
from my_operators.data_bias_check_final import bias_main as data_biasing
from airflow.utils.email import send_email_smtp
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

conf.set('core', 'enable_xcom_pickling', 'True')
conf.set('core', 'enable_parquet_xcom', 'True')


 
def custom_send_email_smtp(to, subject, html_content, **kwargs):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "anirudhak881@gmail.com"      # Replace with your email address
    receiver_email = "anirudhak881@gmail.com"  # Replace with recipient email
    password = "ksmhwqrzhjllqsaz"             # Replace with your app-specific password
    msg = MIMEText(html_content, "html")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(to) if isinstance(to, list) else to
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, password)
            server.sendmail(sender_email, to, msg.as_string())
            print("Email sent successfully.")
    except Exception as e:
                    print(f"Error sending email: {e}")
# Replace the default send_email_smtp with custom_send_email_smtp
send_email_smtp = custom_send_email_smtp

def check_anomalies_and_send_email(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='download_data_from_api')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("Branching to send_anomaly_alert_api")
        return 'send_anomaly_alert_api'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline'

def check_anomalies_loading_data(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='load_data_pickle')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("send_anomaly_alert_load_data")
        return 'send_anomaly_alert_load_data'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline_load_data'

def check_anomalies_split_data(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='split_train_test')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("send_anomaly_alert_train_test")
        return 'send_anomaly_alert_train_test'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline_train_test'

def check_anomalies_pivoting_data_train(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='pivot_data_train')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("send_anomaly_alert_pivot_data_train")
        return 'send_anomaly_alert_pivot_data_train'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline_pivot_data_train'

def check_anomalies_pivoting_data_test(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='pivot_data_test')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("send_anomaly_alert_pivot_data_test")
        return 'send_anomaly_alert_pivot_data_test'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline_pivot_data_test'

def check_anomalies_removal_data_train(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='data_remove_cols_train')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("send_anomaly_alert_remove_cols_train")
        return 'send_anomaly_alert_remove_cols_train'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline_remove_cols_train'

def check_anomalies_removal_data_test(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='data_remove_cols_test')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("send_anomaly_alert_remove_cols_test")
        return 'send_anomaly_alert_remove_cols_test'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline_remove_cols_test'

def check_anomalies_missing_vals_train(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='handle_missing_vals_train')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("send_anomaly_alert_remove_cols_train")
        return 'send_anomaly_alert_remove_cols_train'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline_handle_missing_vals_train'

def check_anomalies_missing_vals_test(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='handle_missing_vals_test')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("send_anomaly_alert_handle_missing_vals_test")
        return 'send_anomaly_alert_handle_missing_vals_test'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline_handle_missing_vals_test'

def check_anomalies_anamoly_detection_val_train(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='anamolies_vals_train')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("send_anomaly_alert_anamolies_vals_train")
        return 'send_anomaly_alert_anamolies_vals_train'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline_anamolies_vals_train'

def check_anomalies_anamoly_detection_val_test(**kwargs):
    anomalies = kwargs['ti'].xcom_pull(task_ids='anamolies_vals_test')
    logging.info(f"Anomalies detected: {anomalies}")
    if anomalies:  # If anomalies are detected, trigger the email
        logging.info("send_anomaly_alert_anamolies_vals_test")
        return 'send_anomaly_alert_anamolies_vals_test'
    logging.info("Branching to continue_pipeline")
    return 'continue_pipeline_anamolies_vals_test'


default_args = {
    'owner': 'MLOPS',
    'start_date': datetime(2024, 10, 21),
    'retries': 1, # Number of retries in case of task failure
    'retry_delay': timedelta(minutes=1), # Delay before retries
}

dag = DAG(
    'datapipeline_new',
    default_args=default_args,
    description='Data Preprocessing pipeline using Airflow DAG',
    schedule_interval=None,
    catchup=False
)

branch_outliers_vals_train = BranchPythonOperator(
    task_id='check_anomalies_anamoly_detection_val_train',
    python_callable=check_anomalies_anamoly_detection_val_train,
    provide_context=True,
    dag=dag
)

branch_outliers_vals_test = BranchPythonOperator(
    task_id='check_anomalies_anamoly_detection_val_test',
    python_callable=check_anomalies_anamoly_detection_val_test,
    provide_context=True,
    dag=dag
)

branch_missing_vals_train = BranchPythonOperator(
    task_id='check_anomalies_missing_vals_train',
    python_callable=check_anomalies_missing_vals_train,
    provide_context=True,
    dag=dag
)

branch_missing_vals_test = BranchPythonOperator(
    task_id='check_anomalies_missing_vals_test',
    python_callable=check_anomalies_missing_vals_test,
    provide_context=True,
    dag=dag
)

branch_removal_data_train = BranchPythonOperator(
    task_id='check_anomalies_removal_data_train',
    python_callable=check_anomalies_removal_data_train,
    provide_context=True,
    dag=dag
)

branch_removal_data_test = BranchPythonOperator(
    task_id='check_anomalies_removal_data_test',
    python_callable=check_anomalies_removal_data_test,
    provide_context=True,
    dag=dag
)

branch_task = BranchPythonOperator(
    task_id='check_anomalies_and_send_email',
    python_callable=check_anomalies_and_send_email,
    provide_context=True,
    dag=dag
)

branch_task_load_data = BranchPythonOperator(
    task_id='check_anomalies_loading_data',
    python_callable=check_anomalies_loading_data,
    provide_context=True,
    dag=dag
)

branch_task_split = BranchPythonOperator(
    task_id='check_anomalies_split_data',
    python_callable=check_anomalies_split_data,
    provide_context=True,
    dag=dag
)

branch_pivot_data_train = BranchPythonOperator(
    task_id='check_anomalies_pivoting_data_train',
    python_callable=check_anomalies_pivoting_data_train,
    provide_context=True,
    dag=dag
)

branch_pivot_data_test = BranchPythonOperator(
    task_id='check_anomalies_pivoting_data_test',
    python_callable=check_anomalies_pivoting_data_test,
    provide_context=True,
    dag=dag
)

send_anomaly_alert_handle_missing_vals_test = EmailOperator(
    task_id='send_anomaly_alert_handle_missing_vals_test',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for handling missing values in test',
    html_content="""<p>Anomalies detected in the data pipeline while handling missing values in test. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='handle_missing_vals_test') %}
                    {% if anomalies %}
                        <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)

send_anomaly_alert_handle_missing_vals_train = EmailOperator(
    task_id='send_anomaly_alert_handle_missing_vals_train',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for handling missing values in train',
    html_content="""<p>Anomalies detected in the data pipeline while handling missing values in train. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='handle_missing_vals_train') %}
                    {% if anomalies %}
                        <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)

send_anomaly_removal_data_test = EmailOperator(
    task_id='send_anomaly_alert_remove_cols_test',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for removing columns test',
    html_content="""<p>Anomalies detected in the data pipeline while removing columns test. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='data_remove_cols_test') %}
                    {% if anomalies %}
                        <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)

# removal cols anomalies
send_anomaly_removal_data_train = EmailOperator(
    task_id='send_anomaly_alert_remove_cols_train',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for removing columns train',
    html_content="""<p>Anomalies detected in the data pipeline removing columns train. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='data_remove_cols_train') %}
                    {% if anomalies %}
                        <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)  

send_anomaly_alert = EmailOperator(
    task_id='send_anomaly_alert_api',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for API',
    html_content="""<p>Anomalies detected in the data pipeline while using API. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='download_data_from_api') %}
                    {% if anomalies %}
                        {% if anomalies is string %}
                            <ul><li>{{ anomalies }}</li></ul>
                        {% else %}
                            <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                        {% endif %}
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)

send_anomaly_alert_load_data = EmailOperator(
    task_id='send_anomaly_alert_load_data',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for Loading Data',
    html_content="""<p>Anomalies detected in the data pipeline while loading data. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='load_data_pickle') %}
                    {% if anomalies %}
                        <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)

send_anomaly_alert_train_test = EmailOperator(
    task_id='send_anomaly_alert_train_test',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for Splitting train Data',
    html_content="""<p>Anomalies detected in the data pipeline while splitting data. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='split_train_test') %}
                    {% if anomalies %}
                        <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)

send_anomaly_pivot_data_train = EmailOperator(
    task_id='send_anomaly_pivot_data_train',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for pivoting train Data',
    html_content="""<p>Anomalies detected in the data pipeline while pivotting data. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='pivot_data_train') %}
                    {% if anomalies %}
                        <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)

send_anomaly_alert_anamolies_vals_test= EmailOperator(
    task_id='send_anomaly_alert_anamolies_vals_test',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for detecting outliers and negative values test data',
    html_content="""<p> detecting outliers and negative values. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='anamolies_vals_test') %}
                    {% if anomalies %}
                        <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)

send_anomaly_alert_anamolies_vals_train= EmailOperator(
    task_id='send_anomaly_alert_anamolies_vals_train',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for detecting outliers and negative values training data',
    html_content="""<p> detecting outliers and negative values. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='anamolies_vals_train') %}
                    {% if anomalies %}
                        <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)

send_anomaly_pivot_data_test = EmailOperator(
    task_id='send_anomaly_pivot_data_test',
    to='anirudhak881@gmail.com',
    subject='Data Anomaly Alert for pivoting test Data',
    html_content="""<p>Anomalies detected in the data pipeline while pivotting data. Details:</p>
                    {% set anomalies = ti.xcom_pull(task_ids='pivot_data_test') %}
                    {% if anomalies %}
                        <ul>{% for item in anomalies %}<li>{{ item }}</li>{% endfor %}</ul>
                    {% else %}
                        <p>No specific anomaly details available.</p>
                    {% endif %}""",
    conn_id='gmail_smtp',
    dag=dag
)

continue_pipeline = DummyOperator(task_id='continue_pipeline', dag=dag)

continue_pipeline_load_data = DummyOperator(task_id='continue_pipeline_load_data', dag=dag)

continue_pipeline_train_test = DummyOperator(task_id='continue_pipeline_train_test',dag=dag)

continue_pipeline_pivot_data_train = DummyOperator(task_id='continue_pipeline_pivot_data_train',dag=dag)

continue_pipeline_pivot_data_test = DummyOperator(task_id='continue_pipeline_pivot_data_test',dag=dag)

continue_pipeline_remove_cols_train = DummyOperator(task_id='continue_pipeline_remove_cols_train',dag=dag)

continue_pipeline_remove_cols_test = DummyOperator(task_id='continue_pipeline_remove_cols_test',dag=dag)

continue_pipeline_handle_missing_vals_test = DummyOperator(task_id='continue_pipeline_handle_missing_vals_test',dag=dag)

continue_pipeline_handle_missing_vals_train = DummyOperator(task_id='continue_pipeline_handle_missing_vals_train',dag=dag)

continue_pipeline_anamolies_vals_test = DummyOperator(task_id='continue_pipeline_anamolies_vals_test',dag=dag)

continue_pipeline_anamolies_vals_train = DummyOperator(task_id='continue_pipeline_anamolies_vals_train',dag=dag)

merge_branch = DummyOperator(task_id='merge_branch', trigger_rule='none_failed_min_one_success',dag=dag)

merge_branch_load_data = DummyOperator(task_id='merge_branch_load_data', trigger_rule='none_failed_min_one_success',dag=dag)

merge_branch_train_test = DummyOperator(task_id='merge_branch_train_test', trigger_rule='none_failed_min_one_success',dag=dag)

merge_branch_pivot_data_train= DummyOperator(task_id='merge_branch_pivot_data_train', trigger_rule='none_failed_min_one_success',dag=dag)

merge_branch_pivot_data_test= DummyOperator(task_id='merge_branch_pivot_data_test', trigger_rule='none_failed_min_one_success',dag=dag)

merge_branch_remove_cols_train= DummyOperator(task_id='merge_branch_remove_cols_train', trigger_rule='none_failed_min_one_success',dag=dag)

merge_branch_remove_cols_test= DummyOperator(task_id='merge_branch_remove_cols_test', trigger_rule='none_failed_min_one_success',dag=dag)

merge_branch_handle_missing_vals_train= DummyOperator(task_id='merge_branch_handle_missing_vals_train', trigger_rule='none_failed_min_one_success',dag=dag)

merge_branch_handle_missing_vals_test= DummyOperator(task_id='merge_branch_handle_missing_vals_test', trigger_rule='none_failed_min_one_success',dag=dag)

merge_branch_anamoly_detection_val_train= DummyOperator(task_id='merge_branch_anamoly_detection_val_train', trigger_rule='none_failed_min_one_success',dag=dag)

merge_branch_anamoly_detection_val_test= DummyOperator(task_id='merge_branch_anamoly_detection_val_test', trigger_rule='none_failed_min_one_success',dag=dag)

# download the data in form of csv using data api 
#download_data_api = PythonOperator(
#    task_id='download_data_from_api',
#    python_callable=download_data_function,
#    dag=dag
#)

    

trigger_cloud_function = HttpOperator(
    task_id='invoke_cloud_function',
    http_conn_id='google_cloud_function_http',
    endpoint='fetch-air-quality-data',
    method='POST',
    headers={"Content-Type": "application/json"},
    data={},  # Payload if required
    dag=dag
)


# load the data and save it in pickle file
data_Loader = PythonOperator(
    task_id='load_data_pickle',
    python_callable=stack_csvs_to_pickle,
    op_args=[
        os.getenv('LOAD_BUCKET_NAME', 'default-bucket'),  # Default value fallback
        os.getenv('FOLDER_PATH', 'api_data/'),            # Default value fallback
        os.getenv('LOAD_OUTPUT_PICKLE_FILE', 'processed/air_pollution.pkl')  # Default value fallback
    ],
    dag=dag
)

data_Bias = PythonOperator(
    task_id='bias_detection_and_mitigation',
    python_callable=data_biasing,
    dag=dag)

# split data into traning and testing
data_Split = PythonOperator(
    task_id='split_train_test',
    python_callable=split,
    dag=dag
)

data_schema_original = PythonOperator(
    task_id = 'check_schema_of_original_air_data',
    python_callable = main_check_schema_original,
    dag = dag
)

# pivot the data to contain pm2.5 parameters for train data
data_train_pivot = PythonOperator(
    task_id='pivot_data_train',
    python_callable=pivoting_data_train,
    dag=dag
)

# pivot the data to contain pm2.5 parameters for test data
data_test_pivot = PythonOperator(
    task_id='pivot_data_test',
    python_callable=pivoting_data_test,
    dag=dag
)

# remove values regarding other gases train data
data_remove_cols_train = PythonOperator(
    task_id='data_remove_cols_train',
    python_callable=removal_of_uneccesary_cols_train,
    dag=dag
)

# remove values regarding other gases test data
data_remove_cols_test = PythonOperator(
    task_id='data_remove_cols_test',
    python_callable=removal_of_uneccesary_cols_test,
    dag=dag
)

# handle missing values train data
handle_missing_vals_train = PythonOperator(
    task_id='handle_missing_vals_train',
    python_callable=check_missing_values_train,
    dag=dag
)

# handle missing values test data
handle_missing_vals_test = PythonOperator(
    task_id='handle_missing_vals_test',
    python_callable=check_missing_values_test,
    dag=dag
)

# handle anamolies for train data
anamolies_vals_train = PythonOperator(
    task_id='anamolies_vals_train',
    python_callable=anamoly_detection_train,
    dag=dag
)

#handle anamolies for test data
anamolies_vals_test = PythonOperator(
    task_id='anamolies_vals_test',
    python_callable=anamoly_detection_test,
    dag=dag
)

# feature engineering for train data
feature_engineering_train = PythonOperator(
    task_id='feature_engineering_train',
    python_callable=feature_eng_train,
    dag=dag
)

data_schema_train_data_feature_eng = PythonOperator(
    task_id = 'schema_train_data_final_processed',
    python_callable = main_train_schema,
    dag = dag
)

data_schema_test_data_feature_eng = PythonOperator(
    task_id = 'schema_test_data_final_processed',
    python_callable = main_test_schema,
    dag = dag
)

# feature engineering for test data
feature_engineering_test = PythonOperator(
    task_id='feature_engineering_test',
    python_callable=feature_eng_test,
    dag=dag
)

# order in which tasks are run
#download_data_apitrigger_cloud_function >> branch_task >> [send_anomaly_alert, continue_pipeline] >> merge_branch \
trigger_cloud_function >> data_Loader >> branch_task_load_data >> [send_anomaly_alert_load_data,continue_pipeline_load_data] >> merge_branch_load_data \
>> data_Bias \
>> data_Split >> branch_task_split >> [send_anomaly_alert_train_test,continue_pipeline_train_test] >> merge_branch_train_test \
>> data_schema_original \
>> data_train_pivot >> branch_pivot_data_train >> [send_anomaly_pivot_data_train,continue_pipeline_pivot_data_train] \
>> merge_branch_pivot_data_train \
>> data_remove_cols_train >> branch_removal_data_train \
>> [send_anomaly_removal_data_train,continue_pipeline_remove_cols_train] >> merge_branch_remove_cols_train \
>> handle_missing_vals_train >> branch_missing_vals_train \
>> [send_anomaly_alert_handle_missing_vals_train,continue_pipeline_handle_missing_vals_train] \
>> merge_branch_handle_missing_vals_train \
>> anamolies_vals_train >> branch_outliers_vals_train >> [send_anomaly_alert_anamolies_vals_train,continue_pipeline_anamolies_vals_train] \
>> merge_branch_anamoly_detection_val_train \
>> feature_engineering_train \
>> data_test_pivot >> branch_pivot_data_test >> [send_anomaly_pivot_data_test,continue_pipeline_pivot_data_test] \
>> merge_branch_pivot_data_test \
>> data_remove_cols_test >> branch_removal_data_test >> [send_anomaly_removal_data_test,continue_pipeline_remove_cols_test] \
>> merge_branch_remove_cols_test \
>> handle_missing_vals_test >> branch_missing_vals_test \
>> [send_anomaly_alert_handle_missing_vals_test,continue_pipeline_handle_missing_vals_test] \
>> merge_branch_handle_missing_vals_test \
>> anamolies_vals_test >> branch_outliers_vals_test >> [send_anomaly_alert_anamolies_vals_test,continue_pipeline_anamolies_vals_test] \
>> merge_branch_anamoly_detection_val_test \
>> feature_engineering_test \
>> data_schema_train_data_feature_eng \
>> data_schema_test_data_feature_eng

if __name__ == "__main__":
    dag.cli()

