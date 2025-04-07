import sys
# import faiss
import regex
import pdfplumber

# import numpy as np
import pandas as pd

from utils import DataPath, save_df
# from sentence_transformers import SentenceTransformer


def pdf_reader(path, out):
    building_data = []
    room_data = []

    capacity_regex = r"(?=\b\w*\d\w*\b)([\w\d]+)[^\S\n]([\w\d]+)[^\S\n](\d+)"
    room_pattern = regex.compile(capacity_regex) 
    building_pattern = regex.compile(r"(.+)[^\S\n]" + capacity_regex)

    # rooms already visited (to avoid aliases)
    visited = set()

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    line = line.strip()
                    
                    # Match building name and code
                    building_match = building_pattern.search(line)
                    if building_match:
                        building_name, bldg_code, *_ = building_match.groups()
                        if bldg_code not in visited:
                            building_data.append([building_name, bldg_code])
                            visited.add(bldg_code)
                    
                    # Match capacity data
                    room_match = room_pattern.search(line)
                    if room_match:
                        bldg_code, room, capacity = room_match.groups()
                        room_data.append([bldg_code, room, capacity])

    building_df = pd.DataFrame(building_data, columns=["Building Name", "Building Code"])
    room_df = pd.DataFrame(room_data, columns=["Building Code", "Room", "Room Capacity"])

    # TODO: Map gt scheduler building names to building codes using faiss
    # ...
    
    # gt_scheduler_names = pd.read_csv(DataPath("gt-scheduler-buildings.csv"))
    # df_out = pd.merge(room_df, gt_scheduler_names, on="Building Code")
    # write to aliases.csv

    save_df(room_df, out)


def name_matching():
    pass


def parse_args(args):
    # default args
    pdf_path = DataPath("classrooms-data-2025.pdf")
    out_path = DataPath("capacities.csv")

    i = 1
    while i < len(args):
        if args[i] == "-p" and i + 1 < len(args):
            pdf_path = args[i + 1]
            i += 2
        elif args[i] == "-o" and i + 1 < len(args):
            out_path = args[i + 1]
            i += 2
        else:
            print(f"Unknown or incomplete argument: {args[i]}")
            sys.exit(1)

    return pdf_path, out_path


if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Usage: python rooms.py [-p <pdf_path>] [-o <save_path>]")
        sys.exit(1)

    pdf_path, out_path = parse_args(sys.argv)
    pdf_reader(path=pdf_path, out=out_path)
