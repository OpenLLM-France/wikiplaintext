import os
from tqdm import tqdm
import regex as re
import hashlib

import requests
from bs4 import BeautifulSoup


def get_links(url, regex=None):
    # Get the html
    response = requests.get(url)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download {url} (Status code {response.status_code})")
    html = response.text

    # Parse the html with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    links = []
    for link in soup.find_all("a"):
        href = link.get("href", "")
        # href is a string like "20210901/"
        if not regex or re.match(regex, href):
            links.append(href.rstrip("/"))

    return links


def get_latest_versions(url, maximum=2):
    latests = get_links(url, regex = r"^\d{8}") # href is a string like "20210901/"

    # Most recent first
    latests = sorted(latests, reverse=True)

    # Return only the latest ones
    return latests[:maximum]


def download_file(file_url, local_filename, expected_md5=None, ignore_if_exists=True, verbose=True):
    try:
        if not os.path.isfile(local_filename) or not ignore_if_exists:
            # Send a GET request to the URL and stream the response
            response = requests.get(file_url, stream=True)

            # Check if the request was successful (status code 200)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to download {file_url}. Status code {response.status_code}")

            # Get the total file size in bytes
            total_size = int(response.headers.get("content-length", 0))

            if verbose:
                print(f"Downloading {file_url} -> {local_filename}")
            # Initialize a progress bar with the total file size
            progress_bar = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=f"Download",
                disable=not verbose,
            )

            # Open a local file for writing in binary mode
            os.makedirs(os.path.dirname(local_filename), exist_ok=True)
            with open(local_filename, "wb") as f:
                # Iterate over the content of the response in chunks
                for data in response.iter_content(chunk_size=1024):
                    # Write the chunk to the local file
                    f.write(data)
                    # Update the progress bar with the number of bytes written
                    progress_bar.update(len(data))

            # Close the progress bar
            progress_bar.close()

        elif verbose:
            print(f"{file_url} already downloaded in {local_filename} (skipping)")

        if False: # expected_md5: # Disabled because of possible memory error (md5 hash has to be computed smartly, and it will take time...)
            with open(local_filename, "rb") as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            if md5 != expected_md5:
                raise RuntimeError(
                    f"MD5 mismatch. Expected {expected_md5} but got {md5}"
                )

    except (Exception, KeyboardInterrupt) as err:
        # if os.path.exists(local_filename):
        #     os.remove(local_filename)
        raise err



def simple_slugify(title):
    # Spaces are replaced by underscores
    title = re.sub(r"\s+", "_", title)
    title = re.sub("/", "--", title)
    title = re.sub("::", "__", title) # double ":" will be a problem when packaging datasets in parquet
    # Upper case is kept, but accents are removed
    # title = str(unicodedata.normalize('NFKD', title).encode('ascii', 'ignore'), 'utf-8')
    if len(title) > 100 and "," in title:
        title = title.split(",")[0]
    return title