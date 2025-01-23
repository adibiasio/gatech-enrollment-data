import math
import requests
import re, os, ray

import pandas as pd

from itertools import chain
from tqdm import tqdm


crawler_url = "https://gt-scheduler.github.io/crawler-v2/"
seat_url = "https://gt-scheduler.azurewebsites.net/proxy/class_section?"

if not ray.is_initialized():
    ray.init(ignore_reinit_error=True)


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
    url = f"{crawler_url}"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"HTTP error! Status: {response.status_code}")

        data = response.json()
        terms = [t["term"] for t in data["terms"]]
        
        nterms = []
        for term in reversed(sorted(terms)):
            if len(nterms) >= n:
                break
            if "Summer" in parse_term(term):
                continue
            nterms.append(term)

        return nterms

    except Exception as error:
        print("Error fetching the data:", error)


def fetch_course_names(term, subject, lower=0, upper=math.inf) -> list[str]:
    """
    Gets all courses of the specified subject offered during the given term.
    """
    url = f"{crawler_url}{term}.json"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"HTTP error! Status: {response.status_code}")

        data = response.json()

        courses = []
        for course in data["courses"].keys():
            match = re.match(r"([A-Za-z]+)\s(\d+)(\D*)", course)
            sub, num, _ = match.groups()
            num = int(num)
            valid_subject = subject == None or sub == subject
            valid_number = lower <= num <= upper
            if valid_subject and valid_number:
                courses.append(course)

        return courses

    except Exception as error:
        print("Error fetching the data:", error)


def fetch_section_crns(term, course_name) -> dict[str, str]:
    """
    Gets all CRNs of the specified course offered during the given term.
    
    Returns:
    Dict: section[str]: crn[str]
    """
    url = f"{crawler_url}{term}.json"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"HTTP error! Status: {response.status_code}")

        data = response.json()

        crn_list = {}
        course = data["courses"].get(course_name, [None, {}])[1]

        for section, details in course.items():
            if details[2] != 0:
                crn_list[section] = details[0]

        return crn_list

    except Exception as error:
        print("Error fetching the data:", error)


def fetch_enrollment_from_crn(term, crn) -> dict[str, int]:
    """
    Gets enrollment data of the specified crn offered during the given term.
    """
    url = f"{seat_url}term={term}&crn={crn}"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"HTTP error! Status: {response.status_code}")

        data = response.text

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

    except Exception as error:
        print("Error fetching the data:", error)


@ray.remote
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


def compile_csv(nterms, subject, lower, upper, include_summer, path=""):
    terms = fetch_nterms(nterms, include_summer)

    data = []
    for term in terms:
        print(f"Processing {parse_term(term)} data...")
        courses = fetch_course_names(term=term, subject=subject, lower=lower, upper=upper)
        futures = [process_course.remote(term, course) for course in courses]

        with tqdm(total=len(futures)) as pbar:
            while futures:
                done, futures = ray.wait(futures, num_returns=1, timeout=None)
                for _ in done:
                    data.extend(list(chain.from_iterable(ray.get(done))))
                    pbar.update(1)

    df = pd.DataFrame([d for d in data if d is not None]).sort_values(by=["Term", "Course"])
    path = os.path.join(path, f"{subject if subject != None else 'ALL'}_enrollment_data.csv")
    df.to_csv(path, index=False)
    print(f"Enrollment data saved to {path}!")


if __name__ == '__main__':
    pass
