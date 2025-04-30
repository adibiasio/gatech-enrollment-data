import aiohttp
import asyncio
import os

import pandas as pd

from tqdm import tqdm


class SessionManager:
    """
    A custom context manager for managing aiohttp ClientSession.
    It ensures the session is closed automatically if created within the context.
    """
    def __init__(self, session=None):
        self.session = session
        self.close = session is None  # don't close pre-existing sessions

    async def __aenter__(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        if self.session is not None and self.close:
            await self.session.close()


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


async def process_response(response: aiohttp.ClientResponse, as_text: bool) -> dict | str:
    """
    Processes http response from aiohttp session.

    Args:
        response (aiohttp.ClientResponse): The response.
        as_text (bool): Whether to return response in plaintext format.

    Raises:
        Exception: If the response failed.

    Returns:
        dict | str: The response in json or plaintext format.
    """
    if response.status != 200:
        raise Exception(f"HTTP error! Status: {response.status}")

    if as_text:
        return await response.text()
    return await response.json()


async def fetch(
    url: str,
    session: bool=None,
    as_text: bool=False,
    use_timeout: bool=False,
    timeout: int=30,
    retries: int=3,
    allow_failure: bool=False,
) -> dict | str:
    """
    Fetches data from the url with retry on timeout and specified timeout duration.
    Uses a custom context manager to ensure session cleanup.

    Args:
        url (str): The url to issue the request.
        session (bool, optional): Pre-existing session to use. Defaults to None.
        as_text (bool, optional): Whether to return response as plaintext. Defaults to False.
        use_timeout (bool, optional): Whether to apply timeouts to requests. Defaults to True.
        timeout (int, optional): The timeout time to use. Defaults to 10.
        retries (int, optional): The number of times to retry requests on timeout. Defaults to 3.
        allow_failure (bool, optional): Whether to allow a request to fail due to timeout. Defaults to False.

    Returns:
        dict | str: Response data.
    """
    async with SessionManager(session) as session:
        for attempt in range(retries + 1):
            try:
                response = await asyncio.wait_for(session.get(url), timeout) if use_timeout else await session.get(url)
                async with response:
                    return await process_response(response, as_text=as_text)

            except asyncio.exceptions.TimeoutError:
                await asyncio.sleep(1) # avoid hammering server
                if attempt + 1 == retries and not allow_failure:
                    tqdm.write(f"Request to {url} timed out. Removing Timeout.")
                    use_timeout = False
                else:
                    tqdm.write(f"Request to {url} timed out. Retrying {attempt + 1}/{retries}...")

            except Exception as error:
                tqdm.write("Error fetching the data:", error)
                break

    tqdm.write(f"Failed to fetch {url} after {retries} attempts.")
    return None


if __name__ == "__main__":
    pass
