import threading
import time
import psutil
import json
from datetime import datetime

def save_performance_metrics():
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "anomalies_detected": sum(1 for log in load_json(LOG_FILE) if log["severity"] == "High")
    }
    
    # Load existing metrics
    try:
        with open("performance_metrics.json", "r") as f:
            all_metrics = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_metrics = []
    
    # Append new metrics
    all_metrics.append(metrics)
    
    # Save updated metrics
    with open("performance_metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=4)

def main():
    # Initialize the sensor
    sensor = Sensor()
    
    # Initialize the database
    db = Database()
    
    # Initialize the server
    server = Server()
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    
    print("Server started. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Get sensor data
            data = sensor.get_data()
            
            # Save to database
            db.save_data(data)
            
            # Send data to server
            server.send_data(data)
            
            # Save performance metrics
            save_performance_metrics()
            
            # Sleep for 20 seconds
            time.sleep(20)
            
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
        server_thread.join()
        print("Server stopped.") 