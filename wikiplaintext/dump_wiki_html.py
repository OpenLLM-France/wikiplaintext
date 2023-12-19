#!/usr/bin/env python3

__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

""" Extract plain text from Wikipedia latest html dumps """

import os, shutil
from tqdm import tqdm
import regex as re

import tarfile, gzip
import json
import requests
from slugify import slugify


from clean_html import clean_html
from scrape_utils import get_latest_versions, get_links, download_file, simple_slugify


def dump_wiki_html_plaintext(
    json_folder,
    output_dir,
    language="fr",
    source="wikipedia",
    prefix="",
    clean_text=True,
    per_json=10000,
    dump_html=False,
    dump_html_redirection=False,
    keep_tables=True,
    max_pages=None,
    subset=None,
    ignore_if_exists=True,
    verbose=True,
):
    all_files = sorted(os.listdir(json_folder), key=lambda x: (len(x), x))

    if subset:
        s, n = subset
        all_files = all_files[s::n]

    for i_group, json_file in enumerate(tqdm(all_files, desc="Extract Wikipedia", unit="json file", disable=not verbose)):
        
        if not json_file.endswith(".ndjson"):
            continue
        subfolder = "." if not per_json else os.path.splitext(json_file)[0]
        json_file = os.path.join(json_folder, json_file)
        if verbose:
            print(f"Processing {json_file}")

        assert os.path.isfile(json_file)

        # Get the number of lines in the file
        num_lines = num_lines_in_big_file(json_file)

        with open(json_file, "r") as f:
            for i_page, line in enumerate(tqdm(f, desc="Extract pages", unit="page", total=num_lines, disable=not verbose)):
                if max_pages and i_page >= max_pages:
                    break

                data = json.loads(line)

                # Possible keys:
                # ['name', 'identifier', 'abstract', 'date_created', 'date_modified', 'date_previously_modified',
                #  'version', 'previous_version', 'url', 'namespace', 'in_language',
                #  'main_entity', 'additional_entities', 'categories', 'templates',
                #  'is_part_of', 'article_body',
                #  'license', 'event', 'image']

                page_title = data["name"]
                page_id = int(data["identifier"])
                page_body = data["article_body"]
                page_body = page_body["html"]
                filename = f"{page_id}_{simple_slugify(page_title)}"

                if subfolder is None:
                    subfolder = f"{page_id:09d}"

                is_redirect = data.get("categories") is None

                anomaly_redirection = None
                if is_redirect:
                    if not ("#REDIRECTION" in page_body or "mw:PageProp/redirect" in page_body or "Redirect" in page_body):
                        anomaly_redirection = f"{page_title} has no category but don't seem to be a redirection --> check in ./{prefix}html/redirects/{filename}.html"

                html_filename, cleaned_filename = [os.path.join(
                    output_dir,
                    prefix + format,
                    subfolder if (data.get("categories") and not anomaly_redirection) else "redirects",
                    f"{filename}.{format}"
                ) for format in ("html", "txt")]

                def dump_html():
                    try:
                        os.makedirs(os.path.dirname(html_filename), exist_ok=True)
                        with open(html_filename, "w") as f:
                            f.write(page_body)
                    except (Exception, KeyboardInterrupt) as err:
                        if os.path.exists(html_filename):
                            os.remove(html_filename)
                        raise err

                if (anomaly_redirection or 
                    (dump_html and (not os.path.isfile(html_filename) or ignore_if_exists) and (not is_redirect or dump_html_redirection))
                    ):
                    dump_html()

                if anomaly_redirection:
                    raise RuntimeError(anomaly_redirection)

                if is_redirect:
                    continue

                if clean_text and (not os.path.isfile(cleaned_filename) or ignore_if_exists):
                    try:
                        text = clean_html(
                            page_body,
                            language=language,
                            source=source,
                            add_title=page_title,
                            keep_tables=keep_tables,
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


def download_html_dump(url, version, language, source, output_dir, verbose=True, do_clean=False):
    url_folder = f"{url}/{version}"

    regex=rf"{language}{source}\-NS0\-.*HTML.json.tar.gz$"
    json_targz_file = get_links(url_folder, regex=regex)

    assert len(json_targz_file) == 1, f"Found find {len(json_targz_file)} files corresponding to {regex} in {url_folder} ({json_targz_file})"
    json_targz_file = json_targz_file[0]
    assert json_targz_file.endswith("-HTML.json.tar.gz"), f"Unexpected file {json_targz_file}"

    # Download the file with md5 sum
    url_stats_json = os.path.join(url_folder, json_targz_file[:-len("-HTML.json.tar.gz")] + "-STATS.json")
    response = requests.get(url_stats_json)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to download {url_stats_json}. Status code {response.status_code}")
    expected_md5 = response.json()["md5sum"]

    output_targz_file = os.path.join(output_dir, json_targz_file)
    output_folder = os.path.join(output_dir, f"{language}{source}_ndjson")

    if not os.path.isdir(output_folder):

        download_file(
            os.path.join(url_folder, json_targz_file),
            output_targz_file,
            expected_md5=expected_md5,
            verbose=verbose,
        )

        if verbose:
            print(f"Extracting {output_targz_file} -> {output_folder}/")
        try:
            with tarfile.open(output_targz_file, 'r:gz') as tar:
                # Extract the contents of the archive
                tar.extractall(output_folder)
        except (Exception, KeyboardInterrupt) as err:
            if os.path.exists(output_folder):
                shutil.rmtree(output_folder)
            raise err

        if do_clean: os.remove(output_targz_file)

    return output_folder


def num_lines_in_big_file(filename):
    def blocks(files, size=65536):
        while True:
            b = files.read(size)
            if not b: break
            yield b

    with open(filename, "r") as f:
        return sum(bl.count("\n") for bl in blocks(f))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract plain text from Wikipedia latest dumps',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--output_dir", default="Wikipedia", help="Output directory")
    parser.add_argument("--language", default="fr", help="language code")
    parser.add_argument("--source", default="wiki", help="what to import (wiki, wikisource, wiktionary, wikibooks, wikinews, wikiversity, wikivoyage)")
    parser.add_argument("--version", default="latest",
                        help="Version to download. Example: 20231120")
    parser.add_argument("--no_clean", action="store_true", default=False,
                        help="Do not perform text cleaning. Only download dump")
    parser.add_argument("--no_tables", default=False, action="store_true", help="Don't keep tables")
    parser.add_argument("--dump_html", action="store_true", default=False,
                        help="Also dump the HTML files")
    parser.add_argument("--subset", default=None, help="If you want to run several processes in parallel, launch with 1/4, 2/4, ...")
    parser.add_argument("--no_verbose", action="store_true", default=False)
    args = parser.parse_args()

    subset = args.subset
    if subset is not None:
        try:
            s, n = subset.split("/")
            s, n = int(s), int(n)
            s = s - 1
            assert s >= 0
            assert n > s
            subset = (s, n)
        except Exception as err:
            raise ValueError(f"Invalid subprocess {subset} (should be a fraction, like 1/4, 2/4, ...)") from err

    BASE_URL = f"https://dumps.wikimedia.org/other/enterprise_html/runs"
    MIRROR_URL = BASE_URL
    VERBOSE = not args.no_verbose

    versions = get_latest_versions(BASE_URL) if args.version in [None, "latest"] else [args.version]

    for version in versions:
        output_dir = os.path.join(args.output_dir, version)

        if VERBOSE:
            print(f"Downloading version {version}")
        try:
            json_folder = download_html_dump(
                BASE_URL, version,
                language=args.language,
                source=args.source,
                output_dir=output_dir,
                verbose=VERBOSE,
            )
        except ProcessLookupError as err:
            print(f"WARNING: {err} for {version}")
            continue

        dump_wiki_html_plaintext(
            json_folder,
            output_dir=output_dir,
            language=args.language,
            source=args.source,
            prefix=f"{args.language}{args.source}_",
            verbose=VERBOSE,
            max_pages=None,
            clean_text=not args.no_clean,
            dump_html = args.dump_html,
            keep_tables=not args.no_tables,
            subset=subset,
        )

        break
