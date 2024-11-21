import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
import os
import threading
import queue
from pathlib import Path

class InstallationWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("Funding Rate Arbitrage Instaler")
        self.root.geometry("600x400")

        self.queue = queue.Queue()

        style = ttk.Style()
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))

        self.create_widgets()
        self.current_step = 0
        self.show_step()

        self.check_queue()

    def create_widgets(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        self.header = ttk.Label(self.main_frame, text="Welcome to the Installation Wizard", 
                              style="Header.TLabel")
        self.header.pack(pady=(0, 20))

        # Content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress frame
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.progress_frame, 
                                      variable=self.progress_var,
                                      maximum=100)
        self.progress.pack(fill=tk.X)
        
        # Buttons frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=(20, 0))

        # Back button
        self.back_button = ttk.Button(self.button_frame, 
                                    text="Back",
                                    command=self.back_step)
        self.back_button.pack(side=tk.LEFT)
        
        # Next button
        self.next_button = ttk.Button(self.button_frame, 
                                    text="Next",
                                    command=self.next_step)
        self.next_button.pack(side=tk.RIGHT)
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.pack(pady=(10, 0))
        
        # Create step-specific widgets
        self.create_step_widgets()

    def create_step_widgets(self):
        # Step 1: Check Requirements
        self.step1_frame = ttk.Frame(self.content_frame)
        ttk.Label(self.step1_frame, 
                 text="Step 1: System Requirements Check",
                 style="Header.TLabel").pack(pady=(0, 10))
        self.req_text = tk.Text(self.step1_frame, height=10, width=50)
        self.req_text.pack()
        
        # Step 2: Installation Location
        self.step2_frame = ttk.Frame(self.content_frame)
        ttk.Label(self.step2_frame,
                 text="Step 2: Choose Installation Location",
                 style="Header.TLabel").pack(pady=(0, 10))
        self.location_frame = ttk.Frame(self.step2_frame)
        self.location_frame.pack(fill=tk.X)
        self.location_entry = ttk.Entry(self.location_frame, width=50)
        self.location_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.browse_button = ttk.Button(self.location_frame,
                                      text="Browse",
                                      command=self.browse_location)
        self.browse_button.pack(side=tk.LEFT)
        
        # Step 3: Installation
        self.step3_frame = ttk.Frame(self.content_frame)
        ttk.Label(self.step3_frame,
                 text="Step 3: Installing",
                 style="Header.TLabel").pack(pady=(0, 10))
        # Make install_text readonly and add scrollbar
        self.install_text_frame = ttk.Frame(self.step3_frame)
        self.install_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.install_text_scrollbar = ttk.Scrollbar(self.install_text_frame)
        self.install_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.install_text = tk.Text(self.install_text_frame, height=10, width=50,
                                  yscrollcommand=self.install_text_scrollbar.set)
        self.install_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.install_text_scrollbar.config(command=self.install_text.yview)
        
        # Step 4: Completion
        self.step4_frame = ttk.Frame(self.content_frame)
        ttk.Label(self.step4_frame,
                 text="Installation Complete!",
                 style="Header.TLabel").pack(pady=(0, 10))
        self.completion_text = ttk.Label(self.step4_frame,
                                       text="The installation has finished successfully.\n"
                                            "Click 'Finish' to launch the application.")
        self.completion_text.pack(pady=20)
    
    def check_requirements(self):
        self.req_text.delete(1.0, tk.END)
        requirements_met = True
        
        # Check Git
        try:
            subprocess.run(["git", "--version"], 
                         capture_output=True,
                         check=True)
            self.req_text.insert(tk.END, "✓ Git is installed\n")
        except:
            self.req_text.insert(tk.END, "✗ Git is not installed\n")
            requirements_met = False
        
        # Check Python
        try:
            subprocess.run(["python", "--version"],
                         capture_output=True,
                         check=True)
            self.req_text.insert(tk.END, "✓ Python is installed\n")
        except:
            self.req_text.insert(tk.END, "✗ Python is not installed\n")
            requirements_met = False
        
        return requirements_met
    
    def browse_location(self):
        directory = filedialog.askdirectory()
        if directory:
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, directory)
    
    def run_installation(self):
        install_path = self.location_entry.get()
        
        def installation_thread():
            try:
                # Clone repository
                self.queue.put(("status", "Cloning repository..."))
                self.queue.put(("progress", 10))
                self.run_process_with_output(
                    ["git", "clone", "-b", "backend_flask_server",
                    "https://github.com/50shadesofgwei/funding-rate-arbitrage.git",
                    os.path.join(install_path, "funding-rate-arbitrage")]
                )
                
                # Setup virtual environment
                self.queue.put(("status", "Creating virtual environment..."))
                self.queue.put(("progress", 30))
                venv_path = os.path.join(install_path, "funding-rate-arbitrage", "venv")
                self.run_process_with_output(
                    [sys.executable, "-m", "venv", venv_path]
                )
                
                # Install dependencies
                self.queue.put(("status", "Installing dependencies..."))
                self.queue.put(("progress", 50))
                pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
                self.run_process_with_output(
                    [pip_path, "install", "-e", "."],
                    cwd=os.path.join(install_path, "funding-rate-arbitrage")
                )
                
                # Rename example.env
                self.queue.put(("status", "Setting up configuration..."))
                self.queue.put(("progress", 80))
                example_env = os.path.join(install_path, "funding-rate-arbitrage", "example.env")
                env_file = os.path.join(install_path, "funding-rate-arbitrage", ".env")
                if os.path.exists(example_env):
                    os.rename(example_env, env_file)
                
                self.queue.put(("status", "Installation complete!"))
                self.queue.put(("progress", 100))
                self.queue.put(("complete", None))
                
            except Exception as e:
                self.queue.put(("error", str(e)))
        
        thread = threading.Thread(target=installation_thread)
        thread.start()
    
    def run_process_with_output(self, cmd, cwd=None, env=None):
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=cwd,
            env=env,
        )
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.queue.put(("output", output.strip()))
        rc = process.poll()
        if rc != 0:
            raise subprocess.CalledProcessError(rc, cmd)

    def check_queue(self):
        try:
            while True:
                msg_type, msg_content = self.queue.get_nowait()
                if msg_type == "status":
                    self.status_label.config(text=msg_content)
                    self.install_text.insert(tk.END, f"\n=== {msg_content} ===\n")
                elif msg_type == "output":  
                    self.install_text.insert(tk.END, f"{msg_content}\n")
                    self.install_text.see(tk.END)  
                elif msg_type == "progress":
                    self.progress_var.set(msg_content)
                elif msg_type == "error":
                    messagebox.showerror("Installation Error", msg_content)
                    self.back_button.config(state=tk.NORMAL)
                    self.next_button.config(state=tk.DISABLED)
                    self.status_label.config(text="Installation failed. Click 'Back' to try again.")
                elif msg_type == "complete":
                    self.next_step()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)
    
    def show_step(self):
        # Hide all frames
        self.step1_frame.pack_forget()
        self.step2_frame.pack_forget()
        self.step3_frame.pack_forget()
        self.step4_frame.pack_forget()
        
        # Show current step
        if self.current_step == 0:
            self.step1_frame.pack(fill=tk.BOTH, expand=True)
            self.check_requirements()
            self.back_button.config(state=tk.DISABLED)
            self.next_button.config(text="Next", state=tk.NORMAL)
        elif self.current_step == 1:
            self.step2_frame.pack(fill=tk.BOTH, expand=True)
            if not self.location_entry.get():
                self.location_entry.insert(0, os.path.expanduser("~"))
            self.back_button.config(state=tk.NORMAL)
            self.next_button.config(text="Install", state=tk.NORMAL)
        elif self.current_step == 2:
            self.step3_frame.pack(fill=tk.BOTH, expand=True)
            self.back_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.install_text.delete(1.0, tk.END)  # Clear previous output
            self.status_label.config(text="")  # Clear any previous error messages
            self.run_installation()
        elif self.current_step == 3:
            self.step4_frame.pack(fill=tk.BOTH, expand=True)
            self.back_button.config(state=tk.DISABLED)
            self.next_button.config(text="Finish", state=tk.NORMAL)
        
        # Update progress
        self.progress_var.set(self.current_step * 25)
    
    def back_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.show_step()
    
    def next_step(self):
        if self.current_step == 0 and not self.check_requirements():
            messagebox.showerror("Requirements Not Met",
                               "Please install the required software before continuing.")
            return
        
        if self.current_step == 3:
            messagebox.showinfo("Complete", "Installation complete open bot monitor to run and close the bot.")
            return
        
        self.current_step += 1
        self.show_step()

def main():
    root = tk.Tk()
    app = InstallationWizard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
