import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import threading
import time
from datetime import datetime
import psutil
import os
import platform
import subprocess

class FlaskServerMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Flask Server Monitor")
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        # server status vars
        self.is_server_running = False
        self.server_pid = None
        self.monitoring = False
        self.installation_path = None
        self.venv_path = None

        self.setup_ui()
        self.load_last_path()
        self.start_monitoring()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Status.TLabel", font=("Arial", 12))
        style.configure("Timestamp.TLabel", font=("Helvetica", 10))
        style.configure("Header.TLabel", font=("Helvetica", 14, "bold"))

        # Main controller
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Label(main_frame, text="Flask Server Monitor", style="Header.TLabel")
        header.pack(pady=(0, 20))

        # Installation Path section
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(0, 20))

        path_input_frame = ttk.Frame(path_frame)
        path_input_frame.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 5))

        self.path_entry = ttk.Entry(path_input_frame, width=40)
        self.path_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 5))

        browse_button = ttk.Button(path_frame, text="Browse", command=self.browse_installation)
        browse_button.pack(side=tk.RIGHT)

        # Status
        status_frame = ttk.LabelFrame(main_frame, text="Server Status",padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 20))

        self.status_label = ttk.Label(status_frame, text="Checking status...", style="Status.TLabel")
        self.status_label.pack()

        self.timestamp_label = ttk.Label(status_frame, text="Last checked: Never", style="Timestamp.TLabel")
        self.timestamp_label.pack()

        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))

        self.start_button = ttk.Button(button_frame, text="Start Server", command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop Server", command=self.stop_server)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Server Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Scrollbar for Logs
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def save_last_path(self):
        config_dir = os.path.expanduser("~/.funding-rate-arbitrage")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "config.txt")

        with open(config_path, "w") as f:
            f.write(self.installation_path or "")

    def load_last_path(self):
        config_path = os.path.join(
            os.path.expanduser("~/.funding-rate-arbitrage"), 
            "config.txt"
        )
        try:
            with open(config_path, "r") as f:
                last_path = f.read().strip()
                if os.path.exists(last_path):
                    self.installation_path = last_path
                    self.path_entry.insert(0, last_path)
                    self.update_venv_path()
        except FileNotFoundError:
            pass
    
    def browse_installation(self):
        path = filedialog.askdirectory(
            title="Select Funding Rate Arbitrage Installation Directory",
            initialdir=os.path.expanduser("~")
        )
        if path:
            self.installation_path = path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.update_venv_path()
            self.save_last_path()
        else:
            messagebox.showerror("Invalid Directory", "Selected directory does not appear to be a valid installation. "
                                 "Please select the directory containing the funding-rate-arbitrage project."
                                )
    def verify_installation_path(self):
        required_files = ['setup.py', 'requirements.txt']
        for file in required_files:
            if not os.path.exists(os.path.join(self.installation_path, file)):
                return False
        return True
    
    def update_venv_path(self):
        if not self.installation_path:
            return
        if platform.system() == "Windows":
            self.venv_path = os.path.join(self.installation_path, "venv", "Scripts")
            self.python_path = os.path.join(self.venv_path, "python.exe")
        else: # MacOS or Linux
            self.venv_path = os.path.join(self.installation_path, "venv", "bin")
            self.python_path = os.path.join(self.venv_path, "python")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def check_server_status(self):
        try:
            response = requests.get("http://localhost:6969/settings/find", timeout=2)
            if response.status_code == 200 or response.json() == {"error":"Error getting settings"}:
                return True
            return False
        except requests.RequestException:
            return False
    
    def update_status_display(self, is_running):
        if is_running:
            self.status_label.config(text="Server is running", foreground="green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Server is not running", foreground="red")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.timestamp_label.config(text=f"Last checked: {timestamp}")

    def monitor_server(self):
        while self.monitoring:
            is_running = self.check_server_status()
            if is_running != self.is_server_running:
                self.is_server_running = is_running
                self.root.after(0, self.update_status_display, is_running)
                self.log_message("Server started" if is_running else "Server stopped")
            time.sleep(2)

    def start_monitoring(self):
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_server)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def start_server(self):
        if not self.installation_path:
            messagebox.showerror("Invalid Installation Path", "Please select the directory containing the funding-rate-arbitrage project.")
            return
        try:
            self.update_venv_path()
            if platform.system() == "Windows":
                command = [os.path.join(self.venv_path, "project-run-ui.exe")]
            else:
                command = [self.venv_path, "project-run-ui"]

            proceses = subprocess.Popen(
                command, 
                cwd=self.installation_path
            )
            self.server_pid = proceses.pid
            self.log_message(f"Starting server with PID: {self.server_pid}")
        except Exception as e:
            self.log_message(f"Error starting server: {str(e)}")

    def stop_server(self):
        try:
            if self.server_pid:
                parent = psutil.Process(self.server_pid)
                children = parent.children(recursive=True)

                # Gracefully stop the server
                for child in children:
                    child.terminate()
                parent.terminate()

                gone, alive = psutil.wait_procs(children + [parent], timeout=5)

                # Force kill any remaining processes
                for p in alive:
                    p.kill()


                self.log_message("Server Stopped")
                self.server_pid = None
            else:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info['cmdline']
                        if cmdline and "project-run-ui" in ' '.join(cmdline):
                            proc.terminate()
                            self.log_message(f"Found and terminated server process: {proc.pid}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                    
               
        except Exception as e:
            self.log_message(f"Error stopping server: {str(e)}")

    def on_closing(self):
        self.monitoring = False
        if self.is_server_running:
            self.stop_server()
        self.save_last_path()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = FlaskServerMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()