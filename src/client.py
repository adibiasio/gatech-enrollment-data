import re
import ray
import math

import pandas as pd

from datetime import datetime
from itertools import chain
from tqdm import tqdm
from utils import *
from zoneinfo import ZoneInfo

CRAWLER_URL = "https://gt-scheduler.github.io/crawler-v2/"
SEAT_URL = "https://gt-scheduler.azurewebsites.net/proxy/class_section?"


def fetch_nterms(n, include_summer=True) -> list[str]:
    """
    Gets the term names for the n most recent terms.
    """
    url = f"{CRAWLER_URL}"
    data = fetch(url=url)
    if not data:
        return

    nterms = []
    terms = [t["term"] for t in data["terms"]]
    for term in reversed(sorted(terms)):
        if len(nterms) >= n:
            break
        if not include_summer and "Summer" in parse_term(term):
            continue
        nterms.append(term)

    return nterms


def fetch_data(term) -> dict[str, any]:
    url = f"{CRAWLER_URL}{term}.json"
    data = fetch(url=url)
    if not data:
        return

    # format period times
    data["caches"]["periods"] = [
        (t.split(" - ")[0][:2] + ":" + t.split(" - ")[0][2:], 
        t.split(" - ")[1][:2] + ":" + t.split(" - ")[1][2:]) if t != "TBA" else ("", "")
        for t in data["caches"]["periods"]
    ]

    processed = {
        "courses": data["courses"],
        "updatedAt": data["updatedAt"],
        **data["caches"],
    }

    return processed


def parse_course_data(data, subjects, lower=0, upper=math.inf) -> list[str]:
    """
    Gets relevant course data for all courses of the specified subjects offered during the given term.
    """
    courses = {} # {course: [crns]}
    parsed_data = {} # {crn : data}
    for course in data["courses"].keys():
        match = re.match(r"([A-Za-z]+)\s(\d+)(\D*)", course)
        sub, num, _ = match.groups()
        num = int(num)
        valid_subject = len(subjects) == 0 or sub.upper() in subjects
        valid_number = lower <= num <= upper
        if valid_subject and valid_number:
            # course format: https://github.com/gt-scheduler/crawler/blob/f7079cb50b7094d63e1f24c07fd8f237767dff2d/src/types.ts#L81
            # section format: https://github.com/gt-scheduler/crawler/blob/f7079cb50b7094d63e1f24c07fd8f237767dff2d/src/types.ts#L119
            try:
                crns = []
                for sname, section in data["courses"][course][1].items():
                    crn = section[0]
                    crns.append(crn)
                    
                    primary = []
                    additional = []
                    for instructor in section[1][0][4]:
                        if "(P)" in instructor:
                            primary.append(instructor[:-4])
                        else:
                            additional.append(instructor)
                    
                    parsed_data.update({crn: {
                        "Section": sname,
                        "Start Time": data["periods"][section[1][0][0]][0],
                        "End Time": data["periods"][section[1][0][0]][1],
                        "Days": section[1][0][1],
                        "Building": ' '.join(section[1][0][2].split()[:-1]) if section[1][0][2] != "TBA" else "",
                        "Room": section[1][0][2].split()[-1] if section[1][0][2] != "TBA" else "",
                        "Primary Instructor(s)": ', '.join(primary),
                        "Additional Instructor(s)": ', '.join(additional),
                    }})
                courses.update({course: crns})

            except: pass
            finally:
                pass
                # courses.append(course)

    return courses, parsed_data


def fetch_enrollment_from_crn(term, crn) -> dict[str, int]:
    """
    Gets enrollment data of the specified crn offered during the given term.
    """
    url = f"{SEAT_URL}term={term}&crn={crn}"
    data = fetch(url=url, as_text=True)
    if not data:
        return

    enrollment_info = {
        "Enrollment Actual": None,
        "Enrollment Maximum": None,
        "Enrollment Seats Available": None,
        "Waitlist Capacity": None,
        "Waitlist Actual": None,
        "Waitlist Seats Available": None
    }

    for key in enrollment_info.keys():
        pattern = rf"{key}:</span> <span\s+dir=\"ltr\">(\d+)</span>"
        match = re.search(pattern, data)
        if match:
            enrollment_info[key] = int(match.group(1))

    return enrollment_info


def append_room_data(df):
    # check for locations as indexed into precomputed gt-scheduler saved mappings
    # if not present in mapping, then resort to faiss on the remaining ones (slower solution)
    
    # https://chatgpt.com/share/67a7da60-41a8-800d-b663-67fb1c583afc
    # pretrain sentence transformer on data from HB
    # use transformer to map gt scheduler building names for an appropriate mapping
    
    # ideas for trial run to get the mapping:
    # remove the words building, college, and of
    # then find most number of common words
    # also, room number must be valid for the chosen building
    
    gt_scheduler_names = pd.read_csv(DataPath("gt-scheduler-buildings.csv"))
    locations = pd.DataFrame(df, columns=["CRN", "Building", "Room"]).merge(gt_scheduler_names, on="Building", how="left")

    # TODO: add failsafe faiss for mismatches here
    # ...

    # Use building code and room tuple to index into and fetch capacity data
    capacities = pd.read_csv(DataPath("capacities.csv"))
    capacities['idx'] = list(zip(capacities['Building Code'].astype(str).str.lstrip('0'), capacities['Room']))
    locations['idx'] = list(zip(locations['Building Code'].str.lstrip('0'), locations['Room']))
    capacities.set_index('idx', inplace=True)
    locations["Room Capacity"] = locations["idx"].map(capacities["Room Capacity"])
    locations = locations.reset_index().drop(columns=["idx", "Building", "Room"])
    return df.merge(locations, on="CRN", how="left").drop(columns=["index"])


def formatted_df(data):
    if len(data) == 0:
        return pd.DataFrame()
    df = pd.DataFrame([d for d in data if d is not None])
    df = append_room_data(df=df)
    df["Utilization"] = df["Enrollment Actual"] / df["Room Capacity"]
    df = df.sort_values(by=["Term", "Course"])    
    return df


def process_course(term, course, crns, data):
    sections = []
    for crn in crns:    
        enrollment = fetch_enrollment_from_crn(term=term, crn=crn)
        sections.append({
            "Term": parse_term(term),
            "Subject": course.split(" ")[0],
            "Course": course,
            "CRN": crn,
            **data[crn],
            **enrollment,
        })

    return sections


@ray.remote
def process_course_remote(term, course, crns, data):
    return process_course(term=term, course=course, crns=crns, data=data)


def compile_csv(nterms, subjects, lower, upper, include_summer, one_file, path="", use_ray=False):
    terms = fetch_nterms(nterms, include_summer)

    term_dfs = []
    last_updated_time = ""
    for term in terms:
        print(f"Processing {parse_term(term)} data...")
        core_data = fetch_data(term=term)
        if not last_updated_time or not one_file:
            last_updated_time = datetime.strptime(core_data['updatedAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d-%H%M")
        courses, parsed_data = parse_course_data(core_data, subjects=subjects, lower=lower, upper=upper)

        data = []
        if use_ray:
            if not ray.is_initialized():
                ray.init(ignore_reinit_error=True)

            futures = [process_course_remote.remote(term, course, crns, parsed_data) for course, crns in courses.items()]
            with tqdm(total=len(futures)) as pbar:
                while futures:
                    done, futures = ray.wait(futures, num_returns=1, timeout=None)
                    for _ in done:
                        data.extend(list(chain.from_iterable(ray.get(done))))
                        pbar.update(1)
        else:
            for course, crns in tqdm(courses.items()):
                data.extend(process_course(term, course, crns, parsed_data))

        df = formatted_df(data=data)
        if not one_file:
            save_df(df, path, f"{'_'.join(parse_term(term).lower().split())}_enrollment_data_{last_updated_time}.csv")
        else:
            term_dfs.append(df)

    if one_file:
        save_df(pd.concat(term_dfs), path, f"enrollment_data_{last_updated_time}.csv")


if __name__ == '__main__':
    pass
