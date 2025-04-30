import aiohttp
import asyncio
import re
import time

from logger import setup_logger
from tqdm import tqdm
from utils import *


class SchedulerClient:
    CRAWLER_URL = "https://gt-scheduler.github.io/crawler-v2/"
    SEAT_URL = "https://gt-scheduler.azurewebsites.net/proxy/class_section?"
    
    def __init__(self):
        self.logger = setup_logger(name="gt-scheduler-client")


    def parse_term(self, term: str) -> str:
        """
        Parses GT Scheduler term string.

        Args:
            term (str): GT scheduler term string
                in YYYYMM format (i.e. 202502).

        Returns:
            str: readable term format, i.e. Spring 2025.
        """
        year, month = term[:4], int(term[4:])
        
        if month < 5:
            semester = "Spring"
        elif month < 8:
            semester = "Summer"
        else:
            semester = "Fall"

        return f"{semester} {year}"


    def fetch_nterms(self, n: int, include_summer=True) -> list[str]:
        """
        Gets the term names for the n most recent terms.

        Args:
            n (int): number of terms
            include_summer (bool, optional): Whether to count summer terms. Defaults to True.

        Returns:
            list[str]: List of term strings.
        """
        url = f"{self.CRAWLER_URL}"
        data = asyncio.run(fetch(url=url))
        if not data:
            return

        nterms = []
        terms = [t["term"] for t in data["terms"]]
        for term in reversed(sorted(terms)):
            if len(nterms) >= n:
                break
            if not include_summer and "Summer" in self.parse_term(term):
                continue
            nterms.append(term)

        return nterms


    def fetch_data(self, term: str) -> dict[str, any]:
        """
        Gets the term data and metadata for the specified term.

        Args:
            term (str): GT scheduler term string.

        Returns:
            dict[str, any]: Processed GT scheduler term dictionary object.
        """
        url = f"{self.CRAWLER_URL}{term}.json"
        data = asyncio.run(fetch(url=url))
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


    async def _fetch_enrollment(self, term: str, crns: str) -> dict:
        """
        Asynchronous helper method for fetching all enrollment data.

        Args:
            term (str): GT scheduler term string.
            crns (str): Appropriate course CRN.

        Returns:
            dict: Dictionary mapping CRN to html output.
        """
        async def track(coro, bar):
            result = await coro
            bar.update(1)
            return result

        bar = tqdm(total=len(crns))
        urls = [f"{self.SEAT_URL}term={term}&crn={crn}" for crn in crns]
        async with aiohttp.ClientSession() as session:
            tasks = [fetch(url, session=session, as_text=True) for url in urls]
            responses = await asyncio.gather(*[track(task, bar) for task in tasks])
            return {crn : res for crn, res in zip(crns, responses)}


    def fetch_enrollment(self, term: str, crns: list[str]) -> dict[str, dict[str, int]]:
        """
        Gets enrollment data of all specified crns (they must belong to provided term).

        Args:
            term (str): GT scheduler term string.
            crns (list[str]): List of CRN strings.

        Returns:
            dict[str, dict[str, int]]: Mapping of CRN to Enrollment Dictionary.
        """
        responses = asyncio.run(self._fetch_enrollment(term, crns))
        self.logger.debug("asyncio_done", time.time())

        for crn, response in responses.items():
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
                try:
                    match = re.search(pattern, response)
                    if match:
                        enrollment_info[key] = int(match.group(1))
                except:
                    pass

            responses[crn] = enrollment_info
        return responses


    def parse_course_data(self, data: dict, subjects: set[str], ranges: list[tuple[int, int]]) -> tuple[dict, dict]:
        """
        Gets relevant course data for all courses of the specified subjects offered during the given term.
        - course format: https://github.com/gt-scheduler/crawler/blob/f7079cb50b7094d63e1f24c07fd8f237767dff2d/src/types.ts#L81
        - section format: https://github.com/gt-scheduler/crawler/blob/f7079cb50b7094d63e1f24c07fd8f237767dff2d/src/types.ts#L119

        Args:
            data (dict): GT scheduler term data dictionary.
            subjects (set[str]): Set of subject strings.
            ranges (list[tuple[int, int]]): list of course number ranges to apply

        Returns:
            tuple[dict, dict]: courses-to-crn dict and crn-to-data dict
        """
        courses = {} # {course: [crns]}
        parsed_data = {} # {crn : data}
        for course in data["courses"].keys():
            match = re.match(r"([A-Za-z]+)\s(\d+)(\D*)", course)
            sub, num, _ = match.groups()
            num = int(num)
            valid_subject = len(subjects) == 0 or sub.upper() in subjects
            valid_number = any([l <= num <= u for l, u in ranges])
            if valid_subject and valid_number:
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

                except:
                    pass

        return courses, parsed_data


    def process_course(self, term: str, course: str, crns: list[str], data: dict, enrollment: dict) -> list[dict]:
        """
        Aggregating parsed course data, enrollment data, and filter data.

        Args:
            term (str): GT scheduler term string.
            course (str): Course string.
            crns (list[str]): List of CRNs.
            data (dict): parsed course data.
            enrollment (dict): Enrollment mapping (crns-to-enrollment).

        Returns:
            list[dict]: list of output data rows.
        """
        sections = []
        for crn in crns:    
            sections.append({
                "Term": self.parse_term(term),
                "Subject": course.split(" ")[0],
                "Course": course,
                "CRN": crn,
                **data[crn],
                **enrollment[crn],
            })

        return sections


    def process_term(self, term: str, subjects: set[str], ranges: list[tuple[int, int]], data: dict=None) -> list[dict]:
        """
        Compiles data for all courses in the term with the specified filters applied.

        Args:
            term (str): GT scheduler term string.
            subjects (set[str]): Set of subject strings.
            ranges (list[tuple[int, int]]): list of course number ranges to apply
            data (dict, optional): Unparsed course data. Defaults to None.

        Returns:
            list[dict]: list of output data rows.
        """
        if data is None:
            data = self.fetch_data(term=term)

        out = []
        self.logger.debug('parse_course_data', time.time())
        courses, parsed_data = self.parse_course_data(data, subjects=subjects, ranges=ranges)
        self.logger.debug(f'({len(parsed_data)})', 'fetch_enrollment', time.time())
        enrollment = self.fetch_enrollment(term=term, crns=list(parsed_data.keys()))
        self.logger.debug('process_course', time.time())
        for course, crns in courses.items():
            out.extend(self.process_course(term, course, crns, parsed_data, enrollment=enrollment))
        self.logger.debug('done', time.time())

        return out


if __name__ == '__main__':
    pass
