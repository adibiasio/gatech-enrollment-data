import sys
import regex
import pdfplumber

import pandas as pd

from logger import setup_logger
from utils import DataPath, save_df


logger = setup_logger(name="room-capacity-parser")


def pdf_reader(path: str, out: str):
    """
    Parses room capacity data from pdf published annually by Georgia Tech.

    Also, need to ensure that the gt-scheduler-buildings mapping of gt-scheduler building names to
    gatech building code numbers is up to date. The building names used by GT scheduler can be found
    at the link below, and the building code numbers can be found in the room capacity pdf published
    by Georgia Tech.

    GT Scheduler Building Names: 
    https://github.com/gt-scheduler/crawler/blob/f7079cb50b7094d63e1f24c07fd8f237767dff2d/src/steps/parse.ts#L48

    Args:
        path (str): Path to input room capacity pdf.
        out (str): Path for capacity csv to be saved.
    """
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

    # TODO: Map gt scheduler building names to building codes using faiss
    room_df = pd.DataFrame(room_data, columns=["Building Code", "Room", "Room Capacity"])
    save_df(room_df, out)


def parse_args(args: list[str]) -> tuple[any]:
    """
    Parses list of command line arguments.

    Args:
        args (list[str]): arguments from sys.argv

    Returns:
        tuple[any]: Parsed arguments with correct types.
    """
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
            logger.error(f"Unknown or incomplete argument: {args[i]}")
            sys.exit(1)

    return pdf_path, out_path


if __name__ == "__main__":
    if len(sys.argv) < 1:
        logger.critical("Usage: python rooms.py [-p <pdf_path>] [-o <save_path>]")
        sys.exit(1)

    pdf_path, out_path = parse_args(sys.argv)
    pdf_reader(path=pdf_path, out=out_path)
