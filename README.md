# Georgia Tech Enrollment Data [![Python Versions](https://img.shields.io/badge/python-3.11-blue)]()

This project is dedicated towards retrieving historical data on course enrollment at the Georgia Institute of Technology.

This program processes input based on the specified flags and generates an output CSV file with the corresponding enrollment data. It allows users to customize the number of terms, filter by a subject, and provide a file path for saving the output.

## Installation

Step 1: Clone this repository and navigate to its root directory
```
git clone https://github.com/adibiasio/gatech-enrollment-data
cd gatech-enrollment-data
```

Step 2: Make a virtual environment and activate it
```
python -m venv .venv
source .venv/bin/activate
```

Step 3: Install required dependencies.
```
pip install -r requirements.txt
```

Step 4: Run the script!
```
python3 app.py
```

## Usage

Run the program from the command line using the following syntax:

```bash
python app.py [-t <num_terms>] [-s <subject>] [-l <lower_bound>] [-u <upper_bound>] [-p <filepath>]
```

### Flags

| Flag          | Description                                       | Default Value              |
|---------------|---------------------------------------------------|----------------------------|
| `-t <int>`    | Specifies the number of terms to process.         | `4`                        |
| `-s <string>` | Specifies the subject of the output.              | `None` (All returned)      |
| `-l <int>`    | Specifies the lower bound for the course number.  | `0`                        |
| `-u <int>`    | Specifies the upper bound for the course number.  | `inf`                      |
| `-p <string>` | Specifies the file path for saving the CSV.       | `""` (current directory)   |


## Sample Run
```
(.venv) root@andrew:~# python3 app.py -t 6 -s CS -u 4698
2025-01-21 01:12:05,901 INFO worker.py:1821 -- Started a local Ray instance.
Processing Spring 2025 data...
100%| ███████████████████████████████████████████████████| 73/73 [01:03<00:00,  1.15it/s]
Processing Fall 2024 data...
100%| ███████████████████████████████████████████████████| 72/72 [01:09<00:00,  1.04it/s]
Processing Summer 2024 data...
100%| ███████████████████████████████████████████████████| 39/39 [00:27<00:00,  1.44it/s]
Processing Spring 2024 data...
100%| ███████████████████████████████████████████████████| 69/69 [00:45<00:00,  1.53it/s]
Processing Fall 2023 data...
100%| ███████████████████████████████████████████████████| 70/70 [00:29<00:00,  2.38it/s]
Processing Summer 2023 data...
100%| ███████████████████████████████████████████████████| 37/37 [00:19<00:00,  1.92it/s]
Enrollment data saved to CS_enrollment_data.csv!
(.venv) root@andrew:~#
```