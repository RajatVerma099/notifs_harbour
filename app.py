from flask import Flask, jsonify, render_template, request
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import os

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("harbour-final-firebase-private-key.json")  # Provide the path to your Firebase key here
firebase_admin.initialize_app(cred)
db = firestore.client()

# Send Notification Endpoint
@app.route('/send-notifications', methods=['POST'])
def send_notifications():
    data = request.json
    date = data.get('date')  # Date should be in 'yyyy-mm-dd' format
    print(f"Received date for notification: {date}")

    if not date:
        return jsonify({"error": "No date provided"}), 400

    # Fetch all job documents
    all_jobs_ref = db.collection("Jobs")
    all_jobs = all_jobs_ref.stream()

    # Store all jobs in a temporary list
    jobs_list = []
    for job in all_jobs:
        job_data = job.to_dict()
        job_data["id"] = job.id  # Store the job ID in the job data
        jobs_list.append(job_data)
        print(f"Fetched Job ID: {job.id}, Job Data: {job_data}")  # Print each job fetched

    # Filter jobs for the specific date, using 'date-posted'
    filtered_jobs = [job for job in jobs_list if job.get('date-posted', '').strip() == date.strip()]

    # Debug: Print filtered jobs
    print(f"Filtered jobs for date {date}: {filtered_jobs}")

    if not filtered_jobs:
        print("No jobs found for this date.")
        return jsonify({"message": "No jobs found for the given date."}), 200

    job_ids = [job['id'] for job in filtered_jobs]
    print(f"Jobs found for the date {date}: {job_ids}")

    # Send notifications for each job
    for job in filtered_jobs:
        job_id = job['id']
        company_name = job.get('company', 'Unknown Company')
        title = job.get('job-title', 'Job Title')
        apply_link = job.get('apply-link', '#')

        notification_message = f"{company_name} has openings for {title}. Click now to apply!"

        # Prepare the payload for OneSignal
        payload = {
            "app_id": "56c94a7a-618b-41d6-8db3-955968baf359",  # Your OneSignal App ID
            "included_segments": ["All"],  # Sends notification to all users
            "headings": {"en": "Job Opening Notification"},
            "contents": {"en": notification_message},
            "url": apply_link  # Redirects to apply link when clicked
        }

        # Send notification
        response = requests.post("https://onesignal.com/api/v1/notifications",
                                  headers={
                                      "Content-Type": "application/json; charset=utf-8",
                                      "Authorization": "Basic ZjJiNDZhNmUtOTZkYy00ZjYwLTgyZjQtNDAyYTAzOTljNzdk"  # Your REST API Key
                                  },
                                  json=payload)

        if response.status_code != 200:
            print(f"Failed to send notification for job ID {job_id}: {response.json()}")

    return jsonify({"message": "Notifications sent for the specified date."}), 200

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Default to port 5000 if PORT is not set
    app.run(host='0.0.0.0', port=port)
