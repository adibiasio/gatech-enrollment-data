import requests
import re, os, sys, ray

import pandas as pd

from itertools import chain
from tqdm import tqdm


crawler_url = "https://gt-scheduler.github.io/crawler-v2/"
seat_url = "https://gt-scheduler.azurewebsites.net/proxy/class_section?"

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


def fetch_nterms(n) -> list[str]:
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
            nterms.append(term)
        
        return nterms

    except Exception as error:
        print("Error fetching the data:", error)


def fetch_course_names(term, subject) -> list[str]:
    """
    Gets all courses of the specified subject offered during the given term.
    """
    url = f"{crawler_url}{term}.json"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"HTTP error! Status: {response.status_code}")

        data = response.json()
        return [c for c in data["courses"].keys() if c.startswith(f"{subject} ")]

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
def process_course(term, course, subject):
    crns = fetch_section_crns(term=term, course_name=course)

    sections = []
    for section, crn in crns.items():    
        enrollment = fetch_enrollment_from_crn(term=term, crn=crn)
        sections.append({
            "Term": parse_term(term),
            "Subject": subject,
            "Course": course,
            "Section": section,
            "CRN": crn,
            **enrollment
        })

    return sections


def compile_csv(nterms, subject, path=""):
    terms = fetch_nterms(nterms)

    data = []
    for term in terms:
        print(f"Processing {parse_term(term)} data...")
        courses = fetch_course_names(term=term, subject=subject)[:2]
        futures = [process_course.remote(term, course, subject) for course in courses]

        with tqdm(total=len(futures)) as pbar:
            while futures:
                done, futures = ray.wait(futures, num_returns=1, timeout=1)
                for _ in done:
                    pbar.update(1)

        data.extend(list(chain.from_iterable(ray.get(done))))

    df = pd.DataFrame([d for d in data if d is not None])
    df.to_csv(os.path.join(path, f"{subject}_enrollment_data.csv"), index=False)


def parse_args(args):
    # default args
    nterms = 4
    subject = "CS"
    filepath = ""

    i = 1
    while i < len(args):
        if args[i] == "-t" and i + 1 < len(args):
            try:
                nterms = int(args[i + 1])
                i += 2
            except ValueError:
                print(f"Error: {args[i + 1]} is not a valid integer.")
                sys.exit(1)
        elif args[i] == "-s" and i + 1 < len(args):
            subject = args[i + 1]
            i += 2
        elif args[i] == "-p" and i + 1 < len(args):
            filepath = args[i + 1]
            i += 2
        else:
            print(f"Unknown or incomplete argument: {args[i]}")
            sys.exit(1)

    return nterms, subject, filepath


if __name__ == '__main__':
    if len(sys.argv) < 1:
        print("Usage: python script.py <num_terms> <subject> <filepath>")
        sys.exit(1)

    nterms, subject, filepath = parse_args(sys.argv)
    compile_csv(nterms=nterms, subject=subject, path=filepath)

