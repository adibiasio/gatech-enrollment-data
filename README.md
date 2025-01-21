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

