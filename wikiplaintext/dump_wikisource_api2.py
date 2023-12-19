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




def dump_wikisource_html_plaintext(
    output_dir,
    language="fr",
    prefix="",
    keep_tables=True,
    max_pages=None,
    # subset=None,
    verbose=True,
):    
    subfolder = "frwikisource_namespace_0_0"

    html_folder = os.path.join(
        output_dir,
        prefix + "html",
        subfolder
    )

    txt_folder = os.path.join(
        output_dir,
        prefix + "txt",
        subfolder
    )

    assert os.path.exists(html_folder), f"Please download the HTML dump in {html_folder}"

    files = sorted([f for f in os.listdir(html_folder) if f.endswith(".html")])

    assert len(files) > 0, f"Please download the HTML dump in {html_folder}"

    for i_page, xml_file in enumerate(tqdm(files, desc="Format HTML pages", unit="page", disable=not verbose)):
        if max_pages and i_page >= max_pages:
            break

        txt_file = os.path.join(txt_folder, os.path.splitext(xml_file)[0] + ".txt")

        title = os.path.splitext(os.path.basename(xml_file))[0]
        _, title = title.split("_", 1)
        title = title.replace("_", " ").replace("--", "/")

        if os.path.exists(txt_file):
            with open(txt_file, "r") as f:
                text = f.read()
            if text:
                title_candidate = text.split("\n", 1)[0].lstrip("#").strip()
                if title_candidate and title_candidate != title:
                    print(f"WARNING: title mismatch in {xml_file}: {title} -> {title_candidate}")
                    title = title_candidate

        xml_file = os.path.join(html_folder, xml_file)
        with open(xml_file, "r") as f:
            page_body = f.read()

        try:
            text = clean_html(
                page_body,
                dump_wikisource="wikisource",
                language=language,
                add_title=title,
                keep_tables=keep_tables,
                from_dump=True,
                hashtag_header=True,
                repeat_headers=False,
            )
        except Exception as err:
            raise RuntimeError(f"Error while cleaning {xml_file}") from err

        if not text or not re.search("\n", text):
            if os.path.exists(txt_file):
                print(f"WARNING: no more text in {txt_file}")    
                os.remove(txt_file)
            # print(f"WARNING: no text in {page_title}")
            continue

        os.makedirs(os.path.dirname(txt_file), exist_ok=True)
        try:
            with open(txt_file, "w") as f:
                f.write(text)
        except (Exception, KeyboardInterrupt) as err:
            if os.path.exists(txt_file):
                os.remove(txt_file)
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
    parser.add_argument("--no_tables", default=False, action="store_true", help="Don't keep tables")
    parser.add_argument("--no_verbose", action="store_true", default=False)
    args = parser.parse_args()


    BASE_URL = f"https://dumps.wikimedia.org/other/enterprise_html/runs"
    VERBOSE = not args.no_verbose

    versions = get_latest_versions(BASE_URL) if args.version in [None, "latest"] else [args.version]

    for version in versions:
        output_dir = os.path.join(args.output_dir, version)

        dump_wikisource_html_plaintext(
            output_dir=output_dir,
            language=args.language,
            prefix=f"{args.language}{args.what}_",
            verbose=VERBOSE,
            max_pages=None,
            keep_tables=not args.no_tables,
        )

        break
