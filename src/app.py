import platform
import subprocess, threading
import os, sys

import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Georgia Tech Enrollment Data")
        self.root.geometry("600x400")
        self.github = "https://github.com/adibiasio/gatech-enrollment-data"

        # Default values
        self.num_terms = 4
        self.subject = ''
        self.lower_bound = 0
        self.upper_bound = float('inf')
        self.filepath = ''
        self.skip_summer = False

        self.create_widgets()


    def create_widgets(self):
        paragraph = (
            "This application allows you to customize the settings for the enrollment data script.\n"
            "All options are optional and if unspecified, all subjects / course numbers will be\n"
            "fetched. Optionally, you can skip summer terms.\n"
            "\n"
            "You must choose a file path to save the output files."
        )

        # Preamble
        text_label = tk.Label(self.root, text=paragraph, justify="center", padx=10)
        text_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Grid layout for the rest of the inputs
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)
        
        # Number of terms
        tk.Label(self.root, text="Number of Terms (default 4):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.num_terms_entry = tk.Entry(self.root)
        self.num_terms_entry.insert(0, str(self.num_terms))
        self.num_terms_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Subject
        tk.Label(self.root, text="Subject:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.subject_entry = tk.Entry(self.root)
        self.subject_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # Lower bound
        tk.Label(self.root, text="Course No. Lower Bound:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.lower_bound_entry = tk.Entry(self.root)
        self.lower_bound_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # Upper bound
        tk.Label(self.root, text="Course No. Upper Bound:").grid(row=5, column=0, padx=10, pady=5, sticky="e")
        self.upper_bound_entry = tk.Entry(self.root)
        self.upper_bound_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Filepath and Browse button
        tk.Label(self.root, text="Filepath (required):").grid(row=6, column=0, padx=10, pady=5, sticky="e")
        self.filepath_entry = tk.Entry(self.root)
        self.filepath_entry.grid(row=6, column=1, padx=10, pady=5, sticky="w")
        self.browse_button = tk.Button(self.root, text="Browse", command=self.browse_folder)
        self.browse_button.grid(row=6, column=2, padx=10, pady=5)

        # Skip summer terms
        self.skip_summer_var = tk.IntVar()
        self.skip_summer_checkbox = tk.Checkbutton(self.root, text="Skip Summer Terms", variable=self.skip_summer_var)
        self.skip_summer_checkbox.grid(row=7, column=0, columnspan=3, pady=5)

        # Submit button
        self.submit_button = tk.Button(self.root, text="Run Script", command=self.run_script)
        self.submit_button.grid(row=8, column=0, columnspan=3, pady=10)


    def browse_folder(self):
        # Open a file dialog to choose a file
        filepath = filedialog.askdirectory(title="Select a Folder")
        if filepath:
            self.filepath_entry.delete(0, tk.END)
            self.filepath_entry.insert(0, filepath)


    def fetch_inputs(self):
        try:
            num_terms_str = self.num_terms_entry.get()
            self.num_terms = int(num_terms_str) if num_terms_str else self.num_terms
            if self.num_terms < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Input Error", "Number of Terms must be a positive integer.")
            return False

        self.subject = self.subject_entry.get()
        try:
            low_str = self.lower_bound_entry.get()
            self.lower_bound = int(low_str) if low_str else self.lower_bound
        except ValueError:
            messagebox.showerror("Input Error", "Lower Bound must be an integer.")
            return False

        try:
            up_str = self.upper_bound_entry.get()
            self.upper_bound = int(up_str) if up_str and up_str != 'inf' else float('inf')
        except ValueError:
            messagebox.showerror("Input Error", "Upper Bound must be an integer or 'inf'.")
            return False

        self.skip_summer = self.skip_summer_var.get()
        self.filepath = self.filepath_entry.get()
        if not os.path.isdir(self.filepath):        
            messagebox.showerror("Input Error", "A valid path is required.")
            return False

        return True

    def compile_command(self):
        python_executable = sys.executable
        cmd = f'{python_executable} script.py'
        cmd += f" -t {self.num_terms}"
        cmd += f" -s {self.subject.upper()}" if self.subject else ""
        cmd += f" -l {self.lower_bound}" if self.lower_bound > 0 else ""
        cmd += f" -u {self.upper_bound}" if self.upper_bound > 0 and self.upper_bound != float("inf") else ""
        cmd += " -m" if self.skip_summer == 1 else ""
        cmd += f" -p {self.filepath}" if self.filepath else ""
        return cmd

    def run_script(self):
        if not self.fetch_inputs():
            return

        command = self.compile_command()
        self.exec(command)

    def exec(self, command):
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.Popen(['cmd.exe', '/K', command], creationflags=subprocess.CREATE_NEW_CONSOLE)
                messagebox.showinfo("Info", "Download started. Progress will be shown in an external Terminal.")
            elif system == "Darwin":
                subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "{command}"'])
                messagebox.showinfo("Info", "Download started. Progress will be shown in an external Terminal.")
            else:
                messagebox.showinfo("Input Error", "Unsupported OS")
        except subprocess.CalledProcessError as e:
            print(f"Error while executing the script: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
