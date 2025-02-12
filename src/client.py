import re
import ray
import math

import pandas as pd

from tqdm import tqdm
from itertools import chain
from utils import fetch, DataPath, save_df


CRAWLER_URL = "https://gt-scheduler.github.io/crawler-v2/"
SEAT_URL = "https://gt-scheduler.azurewebsites.net/proxy/class_section?"


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


def fetch_course_data(term, subjects, lower=0, upper=math.inf) -> list[str]:
    """
    Gets course data for all courses of the specified subjects offered during the given term.
    """
    url = f"{CRAWLER_URL}{term}.json"
    data = fetch(url=url)
    if not data:
        return

    courses = [] # course names
    locations = {} # {crn : location}
    for course in data["courses"].keys():
        match = re.match(r"([A-Za-z]+)\s(\d+)(\D*)", course)
        sub, num, _ = match.groups()
        num = int(num)
        valid_subject = len(subjects) == 0 or sub.upper() in subjects
        valid_number = lower <= num <= upper
        if valid_subject and valid_number:
            # course format: [name[str], sections[dict], prereqs[list], description[str]]
            # section format: {str: [crn[str], [[int, days[str], location[str], int, profs[list], ...]], ...]}
            try:
                section = data["courses"][course][1]
                locations.update({section[i][0] : section[i][1][0][2] for i in section if section[i][1][0][2] != "TBA"})
            except: pass
            finally:
                courses.append(course)

    return courses, locations


def fetch_section_crns(term, course_name) -> dict[str, str]:
    """
    Gets all CRNs of the specified course offered during the given term.
    
    Returns:
    Dict: section[str]: crn[str]
    """
    url = f"{CRAWLER_URL}{term}.json"
    data = fetch(url=url)
    if not data:
        return

    crn_list = {}
    course = data["courses"].get(course_name, [None, {}])[1]

    for section, details in course.items():
        if details[2] != 0:
            crn_list[section] = details[0]

    return crn_list


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


def append_room_data(df, locations):
    # check for locations as indexed into precomputed gt-scheduler saved mappings
    # if not present in mapping, then resort to faiss on the remaining ones (slower solution)
    
    # https://chatgpt.com/share/67a7da60-41a8-800d-b663-67fb1c583afc
    # pretrain sentence transformer on data from HB
    # use transformer to map gt scheduler building names for an appropriate mapping
    
    # ideas for trial run to get the mapping:
    # remove the words building, college, and of
    # then find most number of common words
    # also, room number must be valid for the chosen building
    locations = pd.DataFrame(list(locations.items()), columns=["CRN", "location"])
    locations[['Building Name', 'Room']] = locations['location'].str.rsplit(n=1, expand=True)
    locations = locations.drop(columns=["location"])
    
    gt_scheduler_names = pd.read_csv(DataPath("gt-scheduler-buildings.csv"))
    locations = locations.merge(gt_scheduler_names, on="Building Name", how="left")

    # TODO: add failsafe faiss for mismatches here
    # ...

    # Use building code and room tuple to index into and fetch capacity data
    capacities = pd.read_csv(DataPath("capacities.csv"))
    capacities['idx'] = list(zip(capacities['Building Code'].astype(str).str.lstrip('0'), capacities['Room']))
    locations['idx'] = list(zip(locations['Building Code'].str.lstrip('0'), locations['Room']))
    capacities.set_index('idx', inplace=True)
    locations["Capacity"] = locations["idx"].map(capacities["Capacity"])
    locations = locations.reset_index().drop(columns=["idx"])
    return df.merge(locations, on="CRN", how="left").drop(columns=["index"])


def formatted_df(data, locations):
    df = pd.DataFrame([d for d in data if d is not None])
    df = append_room_data(df=df, locations=locations)
    df["Utilization"] = df["Enrollment Actual"] / df["Capacity"]
    df = df.sort_values(by=["Term", "Course"])    
    return df


def process_course(term, course):
    crns = fetch_section_crns(term=term, course_name=course)

    sections = []
    for section, crn in crns.items():    
        enrollment = fetch_enrollment_from_crn(term=term, crn=crn)
        sections.append({
            "Term": parse_term(term),
            "Subject": course.split(" ")[0],
            "Course": course,
            "Section": section,
            "CRN": crn,
            **enrollment
        })

    return sections


@ray.remote
def process_course_remote(term, course):
    return process_course(term=term, course=course)


def compile_csv(nterms, subjects, lower, upper, include_summer, one_file, path="", use_ray=False):
    terms = fetch_nterms(nterms, include_summer)

    term_dfs = []
    for term in terms:
        print(f"Processing {parse_term(term)} data...")
        courses, locations = fetch_course_data(term=term, subjects=subjects, lower=lower, upper=upper)

        data = []
        if use_ray:
            pass
            if not ray.is_initialized():
                ray.init(ignore_reinit_error=True)

            futures = [process_course_remote.remote(term, course) for course in courses]
            with tqdm(total=len(futures)) as pbar:
                while futures:
                    done, futures = ray.wait(futures, num_returns=1, timeout=None)
                    for _ in done:
                        data.extend(list(chain.from_iterable(ray.get(done))))
                        pbar.update(1)
        else:
            for course in tqdm(courses):
                data.extend(process_course(term, course))

        # TODO: add support for seperate csv generation in one run
        #       propogate changes in both script & app
        df = formatted_df(data=data, locations=locations)
        if not one_file:
            save_df(df, path, f"enrollment_data_{'_'.join(parse_term(term).lower().split())}.csv")
        else:
            term_dfs.append(df)

    if one_file:
        save_df(pd.concat(term_dfs), path, "enrollment_data.csv")


if __name__ == '__main__':
    pass
