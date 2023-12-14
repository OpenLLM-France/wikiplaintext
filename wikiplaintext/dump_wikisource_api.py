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
    ignore_if_exists=True,
    verbose=True,
):
    session = requests.Session()
    base_url = f"https://{language}.wikisource.org"
    api_url = f"{base_url}/w/api.php"
    
    ds = datasets.load_dataset("wikimedia/wikisource", f"{version}.{language}")
    ds = ds["train"]

    subfolder = "frwikisource_namespace_0_0"

    num_skipped = 0

    for i_page, data in enumerate(tqdm(ds, desc="Extract pages", unit="page", disable=not verbose)):
        if max_pages and i_page >= max_pages:
            break

        page_title = data["title"]
        page_id = int(data["id"])

        filename = f"{page_id}_{simple_slugify(page_title)}"

        html_filename, cleaned_filename = [os.path.join(
            output_dir,
            prefix + format,
            subfolder,
            f"{filename}.{format}"
        ) for format in ("html", "txt")]

        if ignore_if_exists:
            dirname = os.path.dirname(cleaned_filename)
            if glob.glob(dirname + f"/{page_id}_*"):
                num_skipped += 1
                print(f"Skipping {page_id} {page_title} ({num_skipped}/{i_page+1})")
                continue

        params = {
            "action": "parse",
            "page": page_title.replace(" ", "_"),
            "format": "json"
        }

        response = session.get(url=api_url, params=params)
        data = response.json()

        if "error" in data:
            print(f"WARNING: Failed to get {base_url}/wiki/{page_title}\nError: {data['error'].get('info', data['error'])}")
            continue
            raise RuntimeError(f"Failed to get {base_url}/wiki/{page_title}\nError: {data['error'].get('info', data['error'])}")

        page_body = data["parse"]["text"]["*"]
        
        def dump_html():
            try:
                os.makedirs(os.path.dirname(html_filename), exist_ok=True)
                with open(html_filename, "w") as f:
                    f.write(page_body)
            except (Exception, KeyboardInterrupt) as err:
                if os.path.exists(html_filename):
                    os.remove(html_filename)
                raise err
            
        if dump_html:
            dump_html()
            def dump_html():
                pass

        if clean_text and (not os.path.isfile(cleaned_filename) or ignore_if_exists):
            try:
                text = clean_html(
                    page_body,
                    language=language,
                    add_title=page_title,
                    keep_tables=["wikitable"] if keep_tables is True else keep_tables,
                )
            except Exception as err:
                dump_html()
                raise RuntimeError(f"Failed to clean {html_filename}") from err
            if not text or not re.search("\n", text):
                print(f"WARNING: no text in {page_title}")
                dump_html()
                continue
            os.makedirs(os.path.dirname(cleaned_filename), exist_ok=True)
            try:
                with open(cleaned_filename, "w") as f:
                    f.write(text)
            except (Exception, KeyboardInterrupt) as err:
                if os.path.exists(cleaned_filename):
                    os.remove(cleaned_filename)
                raise err


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
