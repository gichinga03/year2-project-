from flask import Flask, request, jsonify, render_template, send_file
from flask_socketio import SocketIO, emit
import json
import datetime
import numpy as np
import psutil
import time
import os
from transformers import pipeline
from sklearn.ensemble import IsolationForest
import random
import smtplib
from flask_cors import CORS
from pymongo import MongoClient
import feedparser
from dotenv import load_dotenv
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart




load_dotenv()
app = Flask(__name__)
socketio = SocketIO(app)
CORS(app)  


# Connect to MongoDB Atlas
MONGO_URI = "your_mongo_atlas_connection_string"
uri = "mongodb+srv://gichinga03:Gichinga2003@cluster0.kialttn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri)
db = client["threat_detection_system"]
users_collection = db["users"]


LOG_FILE = "logs.json"
CSV_FILE = "logs_export.csv"
STATS_FILE = "stats.json"

# RSS feed URLs
RSS_FEED_URLS = [
    "https://thehackernews.com/feeds/posts/default",  # Example: The Hacker News
    "https://www.bleepingcomputer.com/feed/",  # Example: Bleeping Computer
    "https://www.securityweek.com/rss",  # Security Week
    # Add more RSS URLs here
]



# ✅ Load AI Models
print("[🚀] Initializing AI Models...")
threat_classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

# ✅ Train Isolation Forest for anomaly detection
print("[📊] Training Anomaly Detector...")
sample_logs = np.array([[100], [101], [102], [500], [503], [404], [403], [401]])
anomaly_detector = IsolationForest(n_estimators=100, contamination=0.05)
anomaly_detector.fit(sample_logs)
print("[✔] AI Models Ready!")

# ✅ Event Code Severity Mapping
EVENT_SEVERITY = {
    100: "Low", 101: "Low", 102: "Low",
    401: "Medium", 403: "Medium", 404: "Medium",
    500: "High", 503: "High"
}

THREAT_ACTIONS = {
    401: {"reason": "Unauthorized login attempt", "action": "Monitor login activity"},
    403: {"reason": "Access denied to a restricted resource", "action": "Check user permissions"},
    500: {"reason": "Critical system error", "action": "Investigate system logs"},
    503: {"reason": "Service unavailable", "action": "Restart the affected service"}
}

# Load JSON Data
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return {}

# Save JSON Data
def save_json(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)


# ✅ User Registration
@app.route("/register", methods=["POST"])
def register_page():
    data = request.json
    first_name = data.get("first_name")
    second_name = data.get("second_name")
    last_name = data.get("last_name")
    email = data.get("email")
    username = data.get("username")
    computer_name = data.get("computer_name")
    virus_total_api = data.get("virus_total_api", None)  # Optional
    other_computers = data.get("other_computers", [])  # Optional
    
    # Check if username already exists in MongoDB
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        return jsonify({"error": "Username already exists"}), 400
    
    # Create a new user object
    new_user = {
        "first_name": first_name,
        "second_name": second_name,
        "last_name": last_name,
        "email": email,
        "username": username,
        "computer_name": computer_name,
        "virus_total_api": virus_total_api,
        "other_computers": other_computers,
        "created_at": datetime.datetime.utcnow()
    }
    
    try:
        users_collection.insert_one(new_user)
        return jsonify({"message": "Registration successful"}), 201
    except Exception as e:
        print(f"Error saving to MongoDB: {str(e)}")
        return jsonify({"error": "Failed to register user"}), 500

# ✅ Login - Verify Email & Computer Name
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    computer_name = data.get("computer_name")

    user = users_collection.find_one({"email": email})

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    stored_computer_name = user["computer_name"]

    if stored_computer_name != computer_name:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "status": "success"}), 200



@app.route("/authenticate", methods=["POST"])
def authenticate():
    data = request.json
    email = data.get("email")
    computer_name = data.get("computer_name")

    user = users_collection.find_one({"email": email})

    if user and user["computer_name"] == computer_name:
        return jsonify({"message": "Authentication successful"}), 200
    return jsonify({"error": "Unauthorized"}), 401



#  Save logs to file
def save_logs(logs):
    with open(LOG_FILE, "w") as file:
        json.dump(logs, file, indent=4)

@app.route("/", methods=["GET"])
def get_logs():
    logs = load_logs()
    return jsonify(logs)  # ✅ Return logs as JSON


def classify_threat(event_code, message):
    prediction = threat_classifier(message)[0]
    ai_label = "THREAT" if prediction["label"] == "POSITIVE" else "SAFE"
    anomaly_detected = anomaly_detector.predict([[event_code]])[0] == -1
    severity = EVENT_SEVERITY.get(event_code, "Low")

    if ai_label == "THREAT" or anomaly_detected:
        severity = "High" if anomaly_detected else "Medium"

    if event_code in THREAT_ACTIONS:
        reason = THREAT_ACTIONS[event_code]["reason"]
        action = THREAT_ACTIONS[event_code]["action"]
    else:
        reason = f"Suspicious activity detected (Event Code {event_code})"
        action = "Review system logs and investigate unusual behavior"

        # Log unknown event codes for refinement
        if event_code not in THREAT_ACTIONS:
            print(f"[⚠] Unknown event code {event_code} detected. Consider adding it to THREAT_ACTIONS.")

    return severity, reason, action, prediction["score"]


def send_simple_message():
    sender_email = "threatdetectai@gmail.com"
    sender_password = "ncisbzykghiaryzc"  # ⚠️ Use an App Password, NOT your Gmail password
    receiver_email = "gichinga03@gmail.com"

    subject = "🚨 High Severity Threat Detected!"
    body = (
        "A high severity threat has been detected on your system.\n"
        "Please check the threat detection dashboard immediately."
    )

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("[📧] Alert email sent successfully!")
    except Exception as e:
        print(f"[⚠️] Failed to send alert email: {e}")





@app.route("/add_log", methods=["POST"])
def add_log():
    logs = load_json(LOG_FILE)
    data = request.json
    severity, reason, action, confidence = classify_threat(int(data["event_code"]), data["message"])

    log_entry = {
        "event_code": data["event_code"],
        "provider_name": data.get("provider_name", "Unknown"),
        "computer_name": data.get("computer_name", "Unknown"),
        "message": data["message"],
        "severity": severity,
        "reason": reason,
        "suggested_action": action,
        "ai_confidence": confidence,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    logs.append(log_entry)
    save_json(LOG_FILE, logs)
    socketio.emit("new_log", log_entry)
    
    if severity == "High":
        socketio.emit("alert", {"message": f"🚨 {reason} - {action}"})
        try:
            send_simple_message()
            print("[📧] Alert email sent successfully!")
        except Exception as e:
            print(f"[⚠️] Failed to send alert email: {e}")

    return jsonify({"message": "Log stored", "severity": severity}), 201



# ✅ API for Blocking Requests
@app.route("/block_threat", methods=["POST"])
def block_threat():
    data = request.json
    socketio.emit("block_request", {"ip_address": data.get("ip_address"), "process_name": data.get("process_name")})
    return jsonify({"message": "Blocking request sent to agent"}), 200



# ✅ Performance Metrics
@app.route("/performance_metrics")
def performance_metrics():
    start_time = time.time()
    prediction = threat_classifier("Test message")[0]
    processing_time = time.time() - start_time
    anomaly_count = sum(1 for log in load_json(LOG_FILE) if log["severity"] == "High")

    return jsonify({
        "AI Model Confidence": f"{prediction['score']:.2%}",
        "Processing Speed": f"{processing_time:.4f} seconds",
        "CPU Usage": f"{psutil.cpu_percent()}%",
        "Memory Usage": f"{psutil.virtual_memory().percent}%",
        "Detected Anomalies": anomaly_count
    })




# Function to load logs
def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as file:
            return json.load(file)
    return []



@app.route("/send_stats", methods=["POST"])
def receive_stats():
    data = request.json  # Expecting JSON data
    print(f"Received System Stats: {data}")
    return jsonify({"status": "success"}), 200


#settings user page 


# Function to handle user settings
@app.route("/settings", methods=["GET", "POST"])
def user_settings():
    if request.method == "GET":
        username = request.args.get("username")
        if not username:
            return jsonify({"error": "Username is required"}), 400
            
        user = users_collection.find_one({"username": username})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Remove sensitive data before sending
        user.pop("_id", None)
        return jsonify(user)
        
    # Handle POST request for updates
    data = request.json
    username = data.get("username")
    
    # Find the user by username in the database
    user = users_collection.find_one({"username": username})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Update user information based on the provided data
    update_data = {}
    if "new_password" in data:
        update_data["password"] = data["new_password"]
    if "new_email" in data:
        update_data["email"] = data["new_email"]
    if "first_name" in data:
        update_data["first_name"] = data["first_name"]
    if "second_name" in data:
        update_data["second_name"] = data["second_name"]
    if "last_name" in data:
        update_data["last_name"] = data["last_name"]
    if "virus_total_api" in data:
        update_data["virus_total_api"] = data["virus_total_api"]
    if "other_computers" in data:
        update_data["other_computers"] = data["other_computers"]
    
    # Update the user's settings in the database
    users_collection.update_one(
        {"username": username}, 
        {"$set": update_data}
    )
    
    return jsonify({"message": "Settings updated successfully"})



@app.route("/api/rss", methods=["GET"])
def fetch_rss():
    rss_data = []

    try:
        for url in RSS_FEED_URLS:
            feed = feedparser.parse(url)
            articles = []

            for entry in feed.entries:
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "pubDate": entry.published,
                    "description": entry.summary,
                })

            rss_data.append({
                "source": url,
                "articles": articles
            })
        
        return jsonify(rss_data), 200

    except Exception as e:
        return jsonify({"message": "Failed to fetch RSS feeds", "error": str(e)}), 500



# Route to check if the server is online
@app.route('/')
def home():
    return jsonify({"status": "Server is online"}), 200


if __name__ == "__main__":
    print("[🌐] Server Running at http://127.0.0.1:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
