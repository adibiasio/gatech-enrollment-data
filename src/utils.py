import os
import requests

import pandas as pd


class DataPath(str):
    base = "data"

    def __new__(cls, path):
        prefix = "../" if os.path.basename(os.getcwd()) == "src" else ""
        full_path = os.path.join(prefix, cls.base, path)
        return super().__new__(cls, full_path)


def save_df(df: pd.DataFrame, path, filename=""):
    if filename:
        path = os.path.join(path, f"{filename}")
    df.to_csv(path, index=False)
    print(f"Data saved to {path}")


def fetch(url, as_text=False):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"HTTP error! Status: {response.status_code}")

        if as_text:
            return response.text

        return response.json()

    except Exception as error:
        print("Error fetching the data:", error)


def parse_term(term):
    # Term Format: YYYYMM (i.e. 202502)
    year, month = term[:4], int(term[4:])
    
    if month < 5:
        semester = "Spring"
    elif month < 8:
        semester = "Summer"
    else:
        semester = "Fall"

    return f"{semester} {year}"

