#!/usr/bin/env python3

__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

""" Extract plain text from Wikipedia latest dumps """

import os
import shutil
import hashlib
from tqdm import tqdm
import regex as re

import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup
import bz2
from slugify import slugify

from clean_wikicode import clean_wikicode, set_template_logs, flush_template_logs


def dump_wikipedia_plaintext(
    mirror_url,
    jobs,
    output_dir,
    key="articlesmultistreamdump",
    max_files=None,
    ignore=lambda x: "-index" in x,
    ignore_if_exists=True,
    language="fr",
    clean_text=True,
    keep_notes_as_parenthesis=False,
    keep_tables=False,
    verbose=True,
):
    assert key in jobs, f"Cannot find {key} in {sorted(list(jobs.keys()))}"
    assert "files" in jobs[key], f"Cannot find files in {jobs[key].keys()}"

    files = jobs[key]["files"]
    all_files = list(files.items())
    all_files = [x for x in all_files if not ignore(x[0])]
    # NOCOMMIT, key=lambda x: (int(x[1].get("size", 0)), x[0]))
    all_files = sorted(all_files)

    bz2_dir = os.path.join(output_dir, key)

    for i, (basename, file) in enumerate(tqdm(all_files, desc="Extract Wikipedia", unit="dump file", disable=not verbose)):
        if max_files and i >= max_files:
            break

        bz2_filename = os.path.join(bz2_dir, basename)
        subfolder = os.path.splitext(basename)[0].split("-")[-1]
        if re.match(r"^p\d+p\d+$", subfolder):
            start, end = subfolder[1:].split("p")
            start = f"{int(start):09d}"
            end = f"{int(end):09d}"
            subfolder = f"{start}_{end}"
        raw_dir = os.path.join(output_dir, key + "_raw", subfolder)
        processed_dir = os.path.join(output_dir, key + "_processed", subfolder)

        if os.path.exists(raw_dir) and ignore_if_exists:
            if verbose:
                print(f"{raw_dir} already processed (skipping)")

        else:

            url = file["url"].lstrip("/")
            md5 = file["md5"]
            if url.split("/")[0] == mirror_url.split("/")[-1]:
                url = "/".join(url.split("/")[1:])
            file_url = f"{mirror_url}/{url}"

            download_file(file_url, bz2_filename, expected_md5=md5,
                          ignore_if_exists=ignore_if_exists, verbose=verbose)

            extract_pages_from_xml_bz2(bz2_filename, raw_dir, verbose=verbose)

            os.remove(bz2_filename)

        if not clean_text:
            continue
        if os.path.exists(processed_dir) and ignore_if_exists:
            if verbose:
                print(f"{processed_dir} already processed (skipping)")

        else:
            clean_wiki_files(
                raw_dir, processed_dir,
                language=language,
                keep_notes_as_parenthesis=keep_notes_as_parenthesis,
                keep_tables=keep_tables,
            )

    if os.path.exists(bz2_dir):
        shutil.rmtree(bz2_dir)


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
            print(f"{file_url} already downloaded")

        if expected_md5:
            with open(local_filename, "rb") as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            if md5 != expected_md5:
                raise RuntimeError(
                    f"MD5 mismatch. Expected {expected_md5} but got {md5}"
                )

    except (Exception, KeyboardInterrupt) as err:
        if os.path.exists(local_filename):
            os.remove(local_filename)
        raise err


def extract_pages_from_xml_bz2(
    filename,
    output_dir,
    ignore_page_title=lambda title: re.search(r"[^ ]:", title),
    max_file_per_folder=10000,
    verbose=True
):
    """
    Read an xml inside a bz2 file
    """
    if verbose:
        print(f"Parsing {filename}")
    try:
        num_pages_extracted = 0
        subfolder = "." if not max_file_per_folder else None
        with bz2.open(filename, "rb") as compressed_file:
            p = ET.parse(compressed_file)
            root = p.getroot()
            for page in tqdm(root, desc="Extract pages", unit="page", disable=not verbose):
                if not page.tag.endswith("page"):
                    continue
                prefix = page.tag[:-len("page")]
                if page.find(f"{prefix}redirect") is not None:
                    # Page is redirected
                    continue
                page_title = page.find(f"{prefix}title").text
                if ignore_page_title(page_title):
                    continue
                page_id = int(page.find(f"{prefix}id").text)
                if subfolder is None:
                    subfolder = f"{page_id:09d}"

                revision = page.find(f"{prefix}revision")
                # revision_id = int(revision.find(f"{prefix}id").text)
                text = revision.find(f"{prefix}text").text

                if not text or not text.strip():
                    continue

                # os.path.join(output_dir, f"{page_id // 10000:03d}")
                output_subdir = output_dir
                output_filename = os.path.join(
                    output_subdir,
                    subfolder,
                    f"{page_id}_{simple_slugify(page_title)}.txt"
                    # f"{page_id}_{revision_id}_{simple_slugify(page_title)}.txt"
                )
                os.makedirs(os.path.dirname(output_filename), exist_ok=True)
                with open(output_filename, "w") as f:
                    f.write(text)
                num_pages_extracted = num_pages_extracted + 1
                if max_file_per_folder and num_pages_extracted % max_file_per_folder == 0:
                    subfolder = None

    except (Exception, KeyboardInterrupt) as err:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        raise err


def simple_slugify(title):
    # Spaces are replaced by underscores
    title = re.sub(r"\s+", "_", title)
    title = re.sub("/", "--", title)
    # Upper case is kept, but accents are removed
    # title = str(unicodedata.normalize('NFKD', title).encode('ascii', 'ignore'), 'utf-8')
    return title


def clean_wiki_files(raw_dir, processed_dir, language, keep_notes_as_parenthesis, keep_tables):
    try:
        all_files = []
        for subfolder in sorted(os.listdir(raw_dir)):
            raw_subdir = os.path.join(raw_dir, subfolder)
            processed_subdir = os.path.join(processed_dir, subfolder)
            os.makedirs(processed_subdir, exist_ok=True)
            all_files += [os.path.join(raw_subdir, fn)
                          for fn in sorted(os.listdir(raw_subdir))]

        for file_in in tqdm(all_files, desc="Normalize text", unit="file"):
            file = os.path.basename(file_in)
            subfolder = os.path.basename(
                os.path.dirname(os.path.realpath(file_in)))
            file_out = os.path.join(
                processed_dir, subfolder, slugify(file, lowercase=False))
            with open(file_in, "r") as f:
                text = f.read()
            text = clean_wikicode(
                text,
                language=language,
                keep_notes_as_parenthesis=keep_notes_as_parenthesis,
                keep_tables=keep_tables,
                orig=file_in,
            )
            if not text:
                print(f"WARNING: no text in {file_in}")
                continue
            with open(file_out, "w") as f:
                f.write(text)

    except (Exception, KeyboardInterrupt) as err:
        if os.path.exists(processed_dir):
            shutil.rmtree(processed_dir)
        raise err


def get_latest_versions(url, maximum=2):
    # Get the html
    response = requests.get(url)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download {url}. Status code {response.status_code}")
    html = response.text

    # Parse the html with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    latests = []
    for link in soup.find_all("a"):
        href = link.get("href", "")
        # href is a string like "20210901/"
        if re.match(r"\d{8}", href):
            latests.append(href.rstrip("/"))

    # Most recent first
    latests = sorted(latests, reverse=True)

    # Return only the latest ones
    return latests[:maximum]


def get_file_lists(url, version):
    dumpstatus = f"{url}/{version}/dumpstatus.json"

    # Get the json status

    response = requests.get(dumpstatus)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to download {dumpstatus}. Status code {response.status_code}")
    jobs = response.json()["jobs"]

    status = set([job["status"] for (jobname, job) in jobs.items()])

    if "waiting" in status:
        raise ProcessLookupError("Dump is not ready yet")

    assert status in [{"done"}, {"done", "skipped"}], f"Unexpected status {status}"
    return jobs


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract plain text from Wikipedia latest dumps',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--output_dir", default="Wikipedia", help="Output directory")
    parser.add_argument("--language", default="fr", help="language code")
    parser.add_argument("--version", default="latest",
                        help="Version to download. Example: 20231120")
    parser.add_argument("--no_clean", action="store_true", default=False,
                        help="Do not perform text cleaning. Only download dump")
    parser.add_argument("--mirror",
                        help="Mirror URL. See https://dumps.wikimedia.org/mirrors.html",
                        default="http://mirror.accum.se/mirror/wikimedia.org/dumps (Sweden)"
                        )
    parser.add_argument("--keep_notes_as_parenthesis", default=False, action="store_true", help="Keep notes as parenthesis")
    parser.add_argument("--keep_tables", default=False, action="store_true", help="Keep tables")
    parser.add_argument("--no_verbose", action="store_true", default=False)
    args = parser.parse_args()

    BASE_URL = f"https://dumps.wikimedia.org/{args.language}wiki"
    MIRROR_URL = f"{args.mirror.split()[0]}/{args.language}wiki"
    VERBOSE = not args.no_verbose

    versions = get_latest_versions(BASE_URL) if args.version in [None, "latest"] else [args.version]

    for version in versions:
        if VERBOSE:
            print(f"Downloading version {version}")
        try:
            jobs = get_file_lists(BASE_URL, version)
        except ProcessLookupError as err:
            print(f"WARNING: {err} for {version}")
            continue

        output_dir = os.path.join(args.output_dir, version)

        set_template_logs(os.path.join(output_dir, "template_logs.txt"))

        dump_wikipedia_plaintext(
            MIRROR_URL,
            jobs,
            output_dir=output_dir,
            verbose=VERBOSE,
            max_files=None,
            language=args.language,
            clean_text=not args.no_clean,
            keep_notes_as_parenthesis=args.keep_notes_as_parenthesis,
            keep_tables=args.keep_tables,
        )

        flush_template_logs()

        break
