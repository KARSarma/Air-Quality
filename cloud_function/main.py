import flask
import pandas as pd
import pickle5 as pickle
from google.cloud import storage

# Initialize Flask app
app = flask.Flask(__name__)

# Global model variable
model = None

def load_model():
    """
    Loads the ML model from Google Cloud Storage bucket.
    """
    try:
        global model
        if model is None:
            bucket_name = "airquality-mlops-rg"
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            model_path = 'weights/model/model.pkl'
            blob = bucket.blob(model_path)
            model_str = blob.download_as_string()
            model = pickle.loads(model_str)
            print("Loaded")
    except Exception as e:
        print(f"Error loading model: {str(e)}")

# Load model at startup
load_model()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.route('/predict', methods=['POST'])
def predict():
    """Prediction endpoint"""
    if not flask.request.is_json:
        return flask.jsonify({"error": "Expected application/json content-type"}), 400

    try:
        request_json = flask.request.get_json()
        if "instances" not in request_json:
            return flask.jsonify({"error": "Missing 'instances' in request JSON"}), 400

        instances = request_json["instances"]
        df = pd.DataFrame(instances)
        
        if model is None:
            return flask.jsonify({"error": "Model not loaded properly"}), 500

        predictions = model.predict(df).tolist()
        return flask.jsonify({"predictions": predictions}), 200

    except Exception as e:
        return flask.jsonify({"error": str(e)}), 400

def flask_app(request):
    """
    Cloud Function entry point
    """
    with app.test_request_context(
        path=request.path,
        base_url=request.base_url,
        query_string=request.query_string,
        method=request.method,
        headers=request.headers,
        data=request.data,
        environ_base=request.environ
    ):
        return app.full_dispatch_request()
