from airflow import DAG
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago

# Define default arguments
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# Define the DAG
with DAG(
    dag_id='test_smtp_email',
    default_args=default_args,
    schedule_interval=None,  # Manual trigger
    catchup=False,
    description='DAG to test SMTP email functionality',
) as dag:

    # Define the EmailOperator
    send_test_email = EmailOperator(
        task_id='send_test_email',
        to='anirudhak881@gmail.com',  # Replace with your test email
        subject='Test Email from Airflow',
        html_content="""<p>This is a test email sent from Airflow's EmailOperator.</p>
                        <p>If you received this email, the SMTP setup is working correctly.</p>""",
        conn_id='gmail_smtp',  # Update with your connection ID
    )

    send_test_email
