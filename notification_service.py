from flask import Flask, jsonify, request, render_template
import firebase_admin
from firebase_admin import credentials, firestore
import requests

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("harbour-final-firebase-private-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Send Notification Function
def send_notification(company_name, title, apply_link):
    notification_message = f"{company_name} has openings for {title}. Click now to apply!"
    payload = {
        "app_id": "56c94a7a-618b-41d6-8db3-955968baf359",  # Your OneSignal App ID
        "included_segments": ["All"],  # Sends notification to all users
        "headings": {"en": "Job Opening Notification"},
        "contents": {"en": notification_message},
        "url": apply_link  # Redirects to apply link when clicked
    }

    # Send notification
    response = requests.post(
        "https://onesignal.com/api/v1/notifications",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Basic ZjJiNDZhNmUtOTZkYy00ZjYwLTgyZjQtNDAyYTAzOTljNzdk"  # Your REST API Key
        },
        json=payload
    )

    return response

# Endpoint to send notifications based on date
@app.route('/send-notifications', methods=['POST'])
def send_notifications():
    data = request.json
    date = data.get('date')

    if not date:
        return jsonify({"error": "Date is required"}), 400

    # Fetch jobs from Firebase based on the provided date
    jobs_ref = db.collection("Jobs").where("date-posted", "==", date)
    jobs = jobs_ref.stream()

    # Prepare to send notifications
    notifications_sent = []

    for job in jobs:
        job_info = job.to_dict()
        company_name = job_info.get('company', 'Unknown Company')
        title = job_info.get('job-title', 'Job Title')
        apply_link = job_info.get('apply-link', '#')  # Default to '#' if not present
        
        # Send the notification
        response = send_notification(company_name, title, apply_link)
        notifications_sent.append({"job_id": job.id, "status": response.status_code})

    return jsonify({"message": "Notifications sent", "details": notifications_sent})

# Route to serve the HTML page
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)  # Run on a different port
