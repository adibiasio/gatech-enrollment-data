import pandas as pd

from client import SchedulerClient
from datetime import datetime
from logger import setup_logger
from utils import *
from zoneinfo import ZoneInfo


class Loader:
    def __init__(self):
        self.client = SchedulerClient()
        self.logger = setup_logger(name="loader")


    def compile_csv(
        self, 
        nterms: int, 
        subjects: set[str],
        ranges: list[tuple[int, int]],
        include_summer: bool,
        one_file: bool,
        save_all: bool,
        save_grouped: bool,
        path: str=""
    ):
        """
        Generates csv file with requested course data.

        Args:
            nterms (int): Number of most recent terms to process.
            subjects (set[str]): Which subjects to fetch courses for.
            ranges (list[tuple[int, int]]): Which course number ranges to process.
            include_summer (bool): Whether to include summer terms in the nterms.
            one_file (bool): Whether to process all term data in one file.
            save_all (bool): Whether to output course data as shown in oscar (no groupings).
            save_grouped (bool): Whether to group crosslisted courses sharing rooms/meeting times.
            path (str, optional): Path to save files to. Defaults to current path.
        """
        terms = self.client.fetch_nterms(nterms, include_summer)
        term_dfs = []
        last_updated_time = ""
        for term in terms:
            self.logger.info(f"Processing {self.client.parse_term(term)} data...")

            data = self.client.fetch_data(term=term)
            if not last_updated_time or not one_file:
                last_updated_time = datetime.strptime(data['updatedAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                    tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d-%H%M")

            data = self.client.process_term(term=term, subjects=subjects, ranges=ranges, data=data)
            df = self.formatted_df(data=data)
            if not one_file:
                name = f"{'_'.join(self.client.parse_term(term).lower().split())}_enrollment_data_{last_updated_time}.csv"
                if save_grouped:
                    save_df(self.group_by_room_and_time(df), path, f'grouped_{name}')
                if save_all:
                    save_df(df, path, name)
            else:
                term_dfs.append(df)

        if one_file:
            df = pd.concat(term_dfs)
            name = f"enrollment_data_{last_updated_time}.csv"
            if save_grouped:
                save_df(self.group_by_room_and_time(df), path, f'grouped_{name}')
            if save_all:
                save_df(df, path, name)


    def formatted_df(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Formats dataframe with additional columns and computes room loss.

        Args:
            data (pd.DataFrame): Course data dataframe.

        Returns:
            pd.DataFrame: Resultant dataframe.
        """
        if len(data) == 0:
            return pd.DataFrame()
        df = pd.DataFrame([d for d in data if d is not None])
        df = self.append_room_data(df=df)
        df["Loss"] = 1.0 - (df["Enrollment Actual"] / df["Room Capacity"])
        df = df.sort_values(by=["Term", "Course"])    
        return df


    def append_room_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supplement course dataframe in room capacity data.

        Args:
            df (pd.DataFrame): Course data dataframe.

        Returns:
            pd.DataFrame: Resultant dataframe with room capacity data.
        """
        # check for locations as indexed into precomputed gt-scheduler saved mappings
        gt_scheduler_names = pd.read_csv(DataPath("gt-scheduler-buildings.csv"))
        locations = pd.DataFrame(df, columns=["CRN", "Building", "Room"]).merge(gt_scheduler_names, on="Building", how="left")

        # Use building code and room tuple to index into and fetch capacity data
        capacities = pd.read_csv(DataPath("capacities.csv"))
        capacities['idx'] = list(zip(capacities['Building Code'].astype(str).str.lstrip('0'), capacities['Room']))
        locations['idx'] = list(zip(locations['Building Code'].str.lstrip('0'), locations['Room']))
        capacities.set_index('idx', inplace=True)
        locations["Room Capacity"] = locations["idx"].map(capacities["Room Capacity"])
        locations = locations.reset_index().drop(columns=["idx", "Building", "Room"])
        return df.merge(locations, on="CRN", how="left").drop(columns=["index"])


    def group_by_room_and_time(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Groups crosslisted courses sharing rooms/meeting times.

        Args:
            data (pd.DataFrame): Course data dataframe.

        Returns:
            pd.DataFrame: Resultant dataframe with crosslisted course groupings.
        """
        def unique(series):
            return ', '.join(set(series))

        # columns to group by
        idx = [
            'Term', 
            'Start Time', 
            'End Time', 
            'Days', 
            'Building', 
            'Building Code', 
            'Room', 
            'Room Capacity',
        ]

        # defined aggregate functions
        agg_fns = {
            "Subject": ("Subject", unique),
            "Course": ("Course", unique),
            "CRN": ("CRN", unique),
            "Primary Instructor(s)": ("Primary Instructor(s)", unique),
            "Additional Instructor(s)": ("Additional Instructor(s)", unique),
            "Enrollment Actual": ("Enrollment Actual", "sum"),
            "Enrollment Maximum": ("Enrollment Maximum", "sum"),
            "Enrollment Seats Available": ("Enrollment Seats Available", "sum"),
            "Waitlist Capacity": ("Waitlist Capacity", "sum"),
            "Waitlist Actual": ("Waitlist Actual", "sum"),
            "Waitlist Seats Available": ("Waitlist Seats Available", "sum"),
            "Loss": ("Loss", "sum"),
            "Count": ("CRN", "count"),
        }

        for col in data.columns:
            if col not in agg_fns and col not in idx:
                agg_fns.update({col: (col, unique)})

        grouped = data.groupby(idx, dropna=False).agg(**agg_fns).reset_index()
        return grouped


if __name__ == '__main__':
    pass
