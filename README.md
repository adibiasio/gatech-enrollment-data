# Georgia Tech Enrollment Data [![Python Versions](https://img.shields.io/badge/python-3.11-blue)]()

This project is dedicated towards retrieving historical data on course enrollment at the Georgia Institute of Technology.

This program processes input based on the specified flags and generates an output CSV file with the corresponding enrollment data. It allows users to customize the number of terms, filter by a subject, and provide a file path for saving the output. Check out a sample output csv file [here](data/(sample%20output)%20fall_2025_enrollment_data_2025-04-30-1739.csv).

## Installation
Step 0: Ensure you have python installed on your system. This project uses version 3.11. If you do not have python installed, you can install it [here](https://www.python.org/downloads/release/python-3110/) for your appropriate operating system. Make sure to select ADD TO PATH during the installation process.

Step 1: Within a terminal, clone this repository and navigate to its root directory
```
git clone https://github.com/adibiasio/gatech-enrollment-data
cd gatech-enrollment-data
```

Step 2: Make a virtual environment and activate it
```
python -m venv .venv
source .venv/bin/activate          # unix and macOS
.venv\Scripts\activate             # windows
```


Step 3: Install required dependencies.
```
pip install -r requirements.txt
```

Step 4: Run the program!
```
python3 src/app.py
```

## Desktop Application
You can run the program via a python tkinter application, with UI inputs instead of command-line arguments.
Effort was made to package this into a standalone desktop app, but complications with .exe files and anti-virus
software led to the decision to leave the app as is.

```
python src/app.py
```

<div align="center">
  <img src="https://github.com/user-attachments/assets/405d2985-f60f-4ccf-97d2-baee3b8afb3d" alt="Centered Image">
</div>

## Script Usage

You can also run the program from the command line using the following syntax:

```bash
python src/script.py [-t <num_terms>] [-s <subject 1> ... <subject n>] [-r <lower>-<upper> ... <lower>-<upper>] [-p <filepath>] [-m] [-o] [-a] [-g]
```

### Flags

| Flag          | Description                                                               | Default Value                  |
|---------------|---------------------------------------------------                        |----------------------------    |
| `-t <int>`    | Specifies the number of terms to process.                                 | `1`                            |
| `-s <string> ... <string>` | Specifies the subjects of the output.                        | None (all returned)            |
| `-r <int>-<int> ... <int>-<int>` | Specifies course number bounds (inclusive).            | `0-inf`                        |
| `-p <string>` | Specifies the file path for saving the CSV.                               | `""` (current directory)       |
| `-m`          | If included, skips all summer terms.                                      | summer terms included          |
| `-o`          | If included, outputs all terms to one file.                               | one file per term              |
| `-g`*          | If included, groups crosslisted courses sharing rooms.                   | does not group                 |
| `-a`*          | If -g is used, include to also output all course data as shown in oscar. | all courses (as seen in oscar) |

*if both flags -g and -a are included, two output files will be generated, one with the grouping and one without.

### Sample Run
```
(.venv) root@andrew:~# python3 src/script.py -t 6 -s CS -r 0-4699 6000-7500
2025-01-21 01:12:05,901 INFO worker.py:1821 -- Started a local Ray instance.
Processing Spring 2025 data...
100%| ███████████████████████████████████████████████████| 73/73 [01:03<00:00,  1.15it/s]
Data saved to spring_2025_enrollment_data_2025-04-07-00:43.csv
Processing Fall 2024 data...
100%| ███████████████████████████████████████████████████| 72/72 [01:09<00:00,  1.04it/s]
Data saved to fall_2024_enrollment_data_2025-04-07-00:43.csv
Processing Summer 2024 data...
100%| ███████████████████████████████████████████████████| 39/39 [00:27<00:00,  1.44it/s]
Data saved to summer_2024_enrollment_data_2025-04-07-00:43.csv
Processing Spring 2024 data...
100%| ███████████████████████████████████████████████████| 69/69 [00:45<00:00,  1.53it/s]
Data saved to spring_2024_enrollment_data_2025-04-07-00:43.csv
Processing Fall 2023 data...
100%| ███████████████████████████████████████████████████| 70/70 [00:29<00:00,  2.38it/s]
Data saved to fall_2023_enrollment_data_2025-04-07-00:43.csv
Processing Summer 2023 data...
100%| ███████████████████████████████████████████████████| 37/37 [00:19<00:00,  1.92it/s]
Data saved to summer_2023_enrollment_data_2025-04-07-00:43.csv
(.venv) root@andrew:~#
```

