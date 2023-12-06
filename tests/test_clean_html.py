#!/usr/bin/env python3

__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

import sys
import os
import re

this_dir = os.path.dirname(os.path.realpath(__file__))

input_dir = os.path.join(this_dir, "wikipedia_html")
output_dir = os.path.join(this_dir, "wikipedia_html_cleaned")

lib_dir = os.path.join(os.path.dirname(this_dir), "wikiplaintext")
sys.path.append(lib_dir)

from clean_html import clean_html

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Clean Wikipedia code")
    parser.add_argument("--verbose", default=False, action="store_true")
    args = parser.parse_args()

    for file_in in sorted(os.listdir(input_dir)):
        if not re.match("\d", file_in):
            continue

        # if not re.match("1004_", file_in):
        #     continue

        file_in = os.path.join(input_dir, file_in)
        file_out = os.path.join(output_dir, os.path.splitext(os.path.basename(file_in))[0] + ".txt")

        print("Processing...", os.path.basename(file_in))
        with open(file_in, "r") as f:
            text = clean_html(f,
                language="fr",
                verbose=args.verbose,
            )

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        print(text, file = open(file_out, "w"))
