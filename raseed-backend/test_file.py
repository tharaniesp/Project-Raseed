from google.cloud import storage as gcs_storage
import os

# Set the path to your service account key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firebase-service-account.json"

client = gcs_storage.Client()
bucket = client.bucket("project-raseed-b380d.firebasestorage.app")  # ✅ this must match your Firebase UI
blob = bucket.blob("uploads/receipt.jpg")  # ✅ just the path inside the bucket

# Upload a file from your local machine
blob.upload_from_filename("receipt.jpg")

print("✅ Upload successful.")
