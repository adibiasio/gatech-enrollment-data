# import platform
# import subprocess
import os, re, sys
# import traceback

import tkinter as tk
from tkinter import filedialog, messagebox

from script import run


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Georgia Tech Enrollment Data")
        self.root.geometry("600x450")
        self.github = "https://github.com/adibiasio/gatech-enrollment-data"

        # Default values
        self.num_terms = 1
        self.subject = ''
        self.ranges = []
        self.filepath = ''
        self.skip_summer = False
        self.one_file = False

        self.create_widgets()


    def create_widgets(self):
        paragraph = (
            "This application allows you to customize the settings for the enrollment data script.\n"
            "All options are optional and if unspecified, all subjects / course numbers will be\n"
            "fetched. For multiple course ranges, separate with commas. Optionally, you can skip summer terms.\n"
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
        tk.Label(self.root, text="Number of Terms (default 1):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.num_terms_entry = tk.Entry(self.root)
        self.num_terms_entry.insert(0, str(self.num_terms))
        self.num_terms_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Subject
        tk.Label(self.root, text="Subject:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.subject_entry = tk.Entry(self.root)
        self.subject_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # Course Range
        tk.Label(self.root, text="Course Range (i.e. 2110-3000):").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.range_entry = tk.Entry(self.root)
        self.range_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # Filepath and Browse button
        tk.Label(self.root, text="Filepath (required):").grid(row=5, column=0, padx=10, pady=5, sticky="e")
        self.filepath_entry = tk.Entry(self.root)
        self.filepath_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")
        self.browse_button = tk.Button(self.root, text="Browse", command=self.browse_folder)
        self.browse_button.grid(row=5, column=2, padx=10, pady=5)

        # Skip summer terms
        self.skip_summer_var = tk.IntVar()
        self.skip_summer_checkbox = tk.Checkbutton(self.root, text="Skip Summer Terms", variable=self.skip_summer_var)
        self.skip_summer_checkbox.grid(row=6, column=0, columnspan=3, pady=5)

        # Export to one file
        self.one_file_var = tk.IntVar()
        self.one_file_checkbox = tk.Checkbutton(self.root, text="Export to One File", variable=self.one_file_var)
        self.one_file_checkbox.grid(row=7, column=0, columnspan=3, pady=5)

        # Group Data
        self.group_data = tk.StringVar(value="grouped")
        self.grouped_radio = tk.Radiobutton(self.root, text="Group Crosslisted", variable=self.group_data, value="grouped")
        self.all_radio = tk.Radiobutton(self.root, text="Ungrouped", variable=self.group_data, value="all")
        self.both_radio = tk.Radiobutton(self.root, text="Both", variable=self.group_data, value="both")
        self.grouped_radio.grid(row=8, column=0, sticky="w", padx=5)
        self.all_radio.grid(row=8, column=0, sticky="w", padx=5)
        self.both_radio.grid(row=8, column=0, sticky="w", padx=5)

        # Submit button
        self.submit_button = tk.Button(self.root, text="Run Script", command=self.run_script)
        self.submit_button.grid(row=9, column=0, columnspan=3, pady=10)

        # Status
        self.status_label = tk.Label(self.root, text="", justify="center", padx=10)
        self.status_label.grid(row=10, column=0, columnspan=3, pady=10)


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

        pattern = r'^(\d+)-(\d+)$'
        range_strs = [s.strip() for s in self.range_entry.get().split(",")]
        for range_str in range_strs:
            match = re.match(pattern, range_str)
            if match:
              self.ranges.append((int(match.group(1)), int(match.group(2))))
            else:
                messagebox.showerror("Input Error", "Invalid Range Format. Use <int>-<int>, ..., <int>-<int>")
                return False

        self.skip_summer = self.skip_summer_var.get()
        self.one_file = self.one_file_var.get()
        self.filepath = self.filepath_entry.get()
        if not os.path.isdir(self.filepath):        
            messagebox.showerror("Input Error", "A valid path is required.")
            return False

        self.save_all = self.group_data in ("all", "both")
        self.save_grouped = self.group_data in ("grouped", "both")
        return True


    def compile_command(self):
        python_executable = sys.executable
        cmd = f'{python_executable} script.py'
        cmd += f" -t {self.num_terms}"
        cmd += f" -s {' '.join(self.subject.replace(',',' ').split())}" if self.subject else ""
        cmd += f" -r {' '.join([f'{l}-{u}' for l, u in self.ranges])}" if self.ranges else ""
        cmd += " -m" if self.skip_summer == 1 else ""
        cmd += " -o" if self.one_file == 1 else ""
        cmd += f" -p {self.filepath}" if self.filepath else ""
        cmd += " -g" if self.save_grouped else ""
        cmd += " -a" if self.save_all else ""
        return cmd


    def run_script(self):
        if not self.fetch_inputs():
            return
        
        self.submit_button.config(state=tk.DISABLED)
        self.root.update()
        self.status_label.config(text="Running...")
        self.root.update()

        command = self.compile_command().split()[1:]

        try:
            print(f"Running Command:\n{' '.join(command)}")
            run(command, use_ray=False)
        except Exception as e:
            self.status_label.config(text="Oops! An Error Occurred.")
            # NOTE: for debugging purposes
            # with open("enrollment.log", "w") as file:
            #     file.write(traceback.format_exc())
            #     return
        finally:
            self.submit_button.config(state=tk.NORMAL)

        self.status_label.config(text="Data Saved to Path!")


    # def exec(self, command):
    #     # issues with running subprocess with ray and pyinstaller
    #     try:
    #         system = platform.system()
    #         if system == "Windows":
    #             subprocess.Popen(['cmd.exe', '/K', command], creationflags=subprocess.CREATE_NEW_CONSOLE)
    #             messagebox.showinfo("Info", "Download started. Progress will be shown in an external Terminal.")
    #         elif system == "Darwin":
    #             subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "{command}"'])
    #             messagebox.showinfo("Info", "Download started. Progress will be shown in an external Terminal.")
    #         else:
    #             messagebox.showinfo("Input Error", "Unsupported OS")
    #     except subprocess.CalledProcessError as e:
    #         print(f"Error while executing the script: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
