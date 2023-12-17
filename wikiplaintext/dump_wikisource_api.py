#!/usr/bin/env python3

__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

""" Extract plain text from wikisource latest html dumps """

import datasets
import argparse
import urllib.parse
import os, shutil
from tqdm import tqdm

from clean_html import clean_html
from scrape_utils import get_latest_versions, get_links, download_file, simple_slugify





import os, shutil
from tqdm import tqdm
import regex as re
import glob

import json
import bs4
import requests




def dump_wiki_html_plaintext(
    version,
    output_dir,
    language="fr",
    prefix="",
    clean_text=True,
    dump_html=False,
    keep_tables=True,
    max_pages=None,
    # subset=None,
    verbose=True,
):
    session = requests.Session()
    base_url = f"https://{language}.wikisource.org"
    api_url = f"{base_url}/w/api.php"
    
    ds = datasets.load_dataset("wikimedia/wikisource", f"{version}.{language}")
    ds = ds["train"]

    subfolder = "frwikisource_namespace_0_0"

    for i_page, data in enumerate(tqdm(ds, desc="Extract pages", unit="page", disable=not verbose)):
        if max_pages and i_page >= max_pages:
            break

        page_title = data["title"]
        page_id = int(data["id"])

        clean_and_dump(
            page_title,
            prefix,
            subfolder,
            language,
            session,
            api_url,
            base_url,
            keep_tables,
            page_id_check=page_id,
        )

previously_done = []

def clean_and_dump(
        page_title,
        prefix,
        subfolder,
        language,
        session,
        api_url,
        base_url,
        keep_tables,
        page_id_check=None,
        level=0,
    ):
    global previously_done

    page_title2 = urllib.parse.unquote(page_title).replace(" ", "_")
    if page_title2 in previously_done:
        return
    previously_done.append(page_title2)

    page_id, page_title, page_body = get_html(session, api_url, base_url, page_title)
    if page_id is None:
        return
    if page_id_check is not None and page_id_check != page_id:
        print(f"WARNING: Page id mismatch: {page_id} != {page_id_check} for {page_title}")
    if page_title in previously_done:
        # Avoid infinite loops with circular links
        return
    previously_done.append(page_title)

    filename = f"{page_id}_{simple_slugify(page_title)}"

    html_filename, cleaned_filename = [os.path.join(
        output_dir,
        prefix + format,
        subfolder,
        f"{filename}.{format}"
    ) for format in ("html", "txt")]

    if not os.path.isfile(html_filename):
        with open(html_filename, "w") as f:
            f.write(page_body)

    # if os.path.exists(html_filename):
    #     with open(html_filename, "r") as f:
    #         page_body = f.read()

    # Extract all the subpages
    if level < 3:
        for page_sub_title in find_intra_links(page_body):
            clean_and_dump(
                page_sub_title,
                prefix,
                subfolder,
                language,
                session,
                api_url,
                base_url,
                keep_tables,
                level=level+1,
            )

    if os.path.exists(cleaned_filename):
        # print(f"Skipping {page_title} -> {cleaned_filename}...")
        return
    
    # print(f"Cleaning {page_title} -> {cleaned_filename}...")

    text = clean_html(
        page_body,
        language=language,
        add_title=page_title,
        keep_tables=keep_tables,
        from_dump=True,
        hashtag_header=True,
        repeat_headers=False,
    )

    if not text or not re.search("\n", text):
        # print(f"WARNING: no text in {page_title}")
        return

    os.makedirs(os.path.dirname(cleaned_filename), exist_ok=True)
    try:
        with open(cleaned_filename, "w") as f:
            f.write(text)
    except (Exception, KeyboardInterrupt) as err:
        if os.path.exists(cleaned_filename):
            os.remove(cleaned_filename)
        raise err


def get_html(session, api_url, base_url, page_title):
    params = {
        "action": "parse",
        "page": urllib.parse.unquote(page_title).replace(" ", "_"),
        "format": "json"
    }

    response = session.get(url=api_url, params=params)
    response = response.json()
    if "error" in response:
        print(f"WARNING: Failed to get {base_url}/wiki/{page_title}\nError: {response['error'].get('info', response['error'])}")
        return None, None, None

    page_id = response["parse"]["pageid"]
    page_title = response["parse"]["title"]
    page_body = response["parse"]["text"]["*"]    
    return page_id, page_title, page_body


def do_dump_html(page_body, html_filename):
    try:
        os.makedirs(os.path.dirname(html_filename), exist_ok=True)
        with open(html_filename, "w") as f:
            f.write(page_body)
    except (Exception, KeyboardInterrupt) as err:
        if os.path.exists(html_filename):
            os.remove(html_filename)
        raise err


def find_intra_links(page_body):

    soup = bs4.BeautifulSoup(page_body, "html.parser")
    links = soup.find_all("a")
    links = [link.get("href") for link in links]
    links = [link for link in links if link is not None]

    intra_links = [link for link in links if link.startswith("/wiki/")]
    intra_links = ["/".join(link.split("/")[2:]) for link in intra_links if ":" not in link.split("/")[2]]

    return intra_links


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract plain text from Wikipedia latest dumps',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--output_dir", default="Wikipedia", help="Output directory")
    parser.add_argument("--language", default="fr", help="language code")
    parser.add_argument("--what", default="wikisource", help="what to import (wiki, wiktionary, wikibooks, wikinews, wikisource, wikiversity, wikivoyage)")
    parser.add_argument("--version", default="latest",
                        help="Version to download. Example: 20231120")
    parser.add_argument("--no_clean", action="store_true", default=False,
                        help="Do not perform text cleaning. Only download dump")
    parser.add_argument("--no_tables", default=False, action="store_true", help="Don't keep tables")
    parser.add_argument("--dump_html", action="store_true", default=False,
                        help="Also dump the HTML files")
    parser.add_argument("--no_verbose", action="store_true", default=False)
    args = parser.parse_args()


    BASE_URL = f"https://dumps.wikimedia.org/other/enterprise_html/runs"
    MIRROR_URL = BASE_URL
    VERBOSE = not args.no_verbose

    versions = get_latest_versions(BASE_URL) if args.version in [None, "latest"] else [args.version]

    for version in versions:
        output_dir = os.path.join(args.output_dir, version)

        dump_wiki_html_plaintext(
            version,
            output_dir=output_dir,
            language=args.language,
            prefix=f"{args.language}{args.what}_",
            verbose=VERBOSE,
            max_pages=None,
            clean_text=not args.no_clean,
            dump_html = args.dump_html,
            keep_tables=not args.no_tables,
        )

        break
