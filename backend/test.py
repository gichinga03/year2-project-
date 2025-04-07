import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import os
import socket
import win32evtlog  # Windows Event Log Access
import win32evtlogutil
import win32security
import win32con

# Function to get security events (logins, warnings, etc.)
def get_security_events(log_type="Security", num_events=5):
    logs = []
    try:
        hand = win32evtlog.OpenEventLog(None, log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        events = win32evtlog.ReadEventLog(hand, flags, 0, num_events)

        for event in events:
            logs.append(f"Event ID: {event.EventID}, Source: {event.SourceName}, Time: {event.TimeGenerated}")
    except Exception as e:
        logs.append(f"[ERROR] Failed to read logs: {e}")
    return logs

# Function to check system resource usage
def get_system_health():
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    status = "Low Risk"
    if cpu_usage > 70 or ram_usage > 75 or disk_usage > 80:
        status = "Medium Risk"
    if cpu_usage > 90 or ram_usage > 90:
        status = "High Risk"
    
    return f"CPU: {cpu_usage}% | RAM: {ram_usage}% | Disk: {disk_usage}% | Status: {status}"

# Function to get active network connections
def get_network_activity():
    connections = psutil.net_connections(kind="inet")
    return [f"{conn.laddr.ip}:{conn.laddr.port} -> {conn.raddr.ip if conn.raddr else 'N/A'}" for conn in connections if conn.status == "ESTABLISHED"]

# Function to get running processes
def get_running_processes():
    return [proc.name() for proc in psutil.process_iter(attrs=['name'])]

# Function to kill a process
def kill_process():
    process_name = process_entry.get()
    for proc in psutil.process_iter(attrs=['name']):
        if proc.info['name'].lower() == process_name.lower():
            proc.terminate()
            messagebox.showinfo("Process Terminated", f"{process_name} has been killed.")
            return
    messagebox.showwarning("Error", f"No process named {process_name} found.")

# Function to disconnect from the internet
def disconnect_internet():
    os.system("ipconfig /release")
    messagebox.showinfo("Network Disconnected", "Internet has been disabled.")

# GUI setup
root = tk.Tk()
root.title("Home Threat Monitoring Dashboard")
root.geometry("600x500")

# Security Status
security_status_label = ttk.Label(root, text="Security Status: Loading...", font=("Arial", 14), foreground="red")
security_status_label.pack(pady=5)

# Recent Security Events
event_label = ttk.Label(root, text="Recent Security Events", font=("Arial", 12, "bold"))
event_label.pack()
event_list = tk.Listbox(root, height=5)
event_list.pack(fill="both", expand=True, padx=10, pady=5)

# Network Activity
network_label = ttk.Label(root, text="Network Activity", font=("Arial", 12, "bold"))
network_label.pack()
network_list = tk.Listbox(root, height=5)
network_list.pack(fill="both", expand=True, padx=10, pady=5)

# Running Processes
process_label = ttk.Label(root, text="Running Processes", font=("Arial", 12, "bold"))
process_label.pack()
process_list = tk.Listbox(root, height=5)
process_list.pack(fill="both", expand=True, padx=10, pady=5)

# Quick Actions
quick_action_label = ttk.Label(root, text="Quick Actions", font=("Arial", 12, "bold"))
quick_action_label.pack()

process_entry = ttk.Entry(root)
process_entry.pack(pady=2)
kill_button = ttk.Button(root, text="Kill Process", command=kill_process)
kill_button.pack(pady=2)

disconnect_button = ttk.Button(root, text="Disconnect Internet", command=disconnect_internet)
disconnect_button.pack(pady=2)

# Function to update UI
def update_dashboard():
    # Update Security Status
    security_status_label.config(text=get_system_health())
    
    # Update Event Logs
    event_list.delete(0, tk.END)
    for log in get_security_events():
        event_list.insert(tk.END, log)

    # Update Network Activity
    network_list.delete(0, tk.END)
    for conn in get_network_activity():
        network_list.insert(tk.END, conn)

    # Update Running Processes
    process_list.delete(0, tk.END)
    for proc in get_running_processes():
        process_list.insert(tk.END, proc)

    root.after(5000, update_dashboard)  # Refresh every 5 seconds

# Initial update
update_dashboard()
root.mainloop()
