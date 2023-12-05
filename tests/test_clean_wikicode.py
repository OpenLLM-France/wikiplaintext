#!/usr/bin/env python3

__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

import sys
import os
import re

import argparse

this_dir = os.path.dirname(os.path.realpath(__file__))

lib_dir = os.path.join(os.path.dirname(this_dir), "wikiplaintext")
sys.path.append(lib_dir)

from clean_wikicode import clean_wikicode, set_template_logs, flush_template_logs

if __name__ == "__main__":

    # Put strings in there for quick testing
    texts = [
    ]

    for text in texts:
        print("=====================================")
        print(">>>", text)
        print("<<<", clean_wikicode(text, language="fr", orig=text))

    if texts:
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Clean Wikipedia code")
    parser.add_argument("--keep_notes_as_parenthesis", default=False, action="store_true", help="Keep notes as parenthesis")
    parser.add_argument("--keep_tables", default=False, action="store_true", help="Keep tables")
    args = parser.parse_args()

    input_dir = os.path.join(this_dir, "wikipedia_code")
    output_dir = os.path.join(this_dir, "wikipedia_code_cleaned")
    if args.keep_tables:
        output_dir += "_wTables"
    if args.keep_notes_as_parenthesis:
        output_dir += "_wNotes"

    set_template_logs(os.path.join(output_dir, "template_logs.txt"))

    for file_in in sorted(os.listdir(input_dir)):
        if not re.match("\d", file_in):
            continue

        file_in = os.path.join(input_dir, file_in)
        print("Processing...", os.path.basename(file_in))
        with open(file_in, "r") as f:
            text = f.read()
        
        text = clean_wikicode(text,
            language="fr",
            keep_notes_as_parenthesis=args.keep_notes_as_parenthesis,
            keep_tables=args.keep_tables,
            orig=file_in
        )
        
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        print(text, file = open(os.path.join(output_dir, os.path.basename(file_in)), "w"))

    flush_template_logs()
