import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting
from flask import jsonify
from google.cloud import storage  # Import GCS library

# Initialize Google Cloud Storage client outside of the handler function to avoid reinitializing for each request.
storage_client = storage.Client()

def download_file_from_gcs(bucket_name, file_name, destination):
    """Download a file from GCS to the local file system."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.download_to_filename(destination)
    print(f"Downloaded {file_name} from GCS to {destination}")

def generate(pdf_filename, query):
    vertexai.init(project="platinum-banner-303105", location="us-central1")  # Replace with your project ID
    model = GenerativeModel(
        "gemini-1.5-flash-002",  # You can specify a different Gemini model if needed
    )

    # Read and encode the PDF file
    with open(pdf_filename, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode("utf-8")

    document1 = Part.from_data(
        mime_type="application/pdf",
        data=base64.b64decode(pdf_data)
    )

    responses = model.generate_content(
        [document1, query],  # Use the passed question
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=True,
    )

    return responses

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}

safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
]

def process_pdf(request):
    # Parse the request JSON
    request_json = request.get_json(silent=True)
    if not request_json or 'question' not in request_json:
        return jsonify({'error': 'Missing question'}), 400

    question = request_json['question']

    # Download the files from GCS to the local file system
    bucket_name = "chat_app_test_bucket"
    download_file_from_gcs(bucket_name, "filenames.txt", "/tmp/filenames.txt")

    # Read the filenames.txt and process each file
    with open("/tmp/filenames.txt", "r") as f:
        for line in f:
            pdf_file = line.strip()
            print(f"Processing PDF: {pdf_file}")

            # Download the PDF from GCS
            download_file_from_gcs(bucket_name, pdf_file, f"/tmp/{pdf_file}")

            # Get the Gemini response generator
            responses = generate(f"/tmp/{pdf_file}", question)

            # Construct the response text from the generator
            response_text = ""
            print (responses)
            for response in responses:
                print (response.text, end="")
                response_text += response.text
            print ("===============================")
            print (response_text)
            return jsonify({'response': response_text})

    return jsonify({'error': 'No files processed'}), 500
