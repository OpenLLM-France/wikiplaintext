#!/usr/bin/env python3

__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

import sys
import os
import re
import shlex

this_dir = os.path.dirname(os.path.realpath(__file__))

lib_dir = os.path.join(os.path.dirname(this_dir), "wikiplaintext")
sys.path.append(lib_dir)

from clean_html import clean_html

def relative_filename(filename):
    filename = os.path.sep.join(filename.split(os.path.sep)[-2:])
    return shlex.quote(filename)

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Clean Wikipedia code")
    parser.add_argument("IDs", default=None, nargs="*", help="Wikipedia page IDs to clean")
    parser.add_argument("--wikisource", action="store_true", help="Only HTML from wikisource")
    parser.add_argument("--wikipedia", action="store_true", help="Only HTML from wikipedia")
    parser.add_argument("--dump", action="store_true", help="Only HTML from wikimedia enterprise dump")
    parser.add_argument("--api", action="store_true", help="Only HTML from wikimedia API")
    args = parser.parse_args()

    for input_dir, output_dir in [
        ("wikipedia_dumphtml_redirect", "SHOULD_NOT_OCCUR"),
        ("wikipedia_dumphtml", "wikipedia_dumphtml_cleaned"),
        ("wikipedia_html", "wikipedia_html_cleaned"),
        ("wikisource_html", "wikisource_html_cleaned"),
        ("wikisource_dumphtml", "wikisource_dumphtml_cleaned"),
    ]:
        
        input_dir = os.path.join(this_dir, input_dir)
        output_dir = os.path.join(this_dir, output_dir)

        for file_in in sorted(os.listdir(input_dir)):
            if not re.match("\d", file_in):
                continue

            is_redirection = "redirect" in input_dir
            format_from_dump = "dump" in input_dir
            from_wikisource = "wikisource" in input_dir

            if args.IDs and not max([bool(re.match(prefix, file_in)) for prefix in args.IDs]):
                continue

            if args.wikisource and not from_wikisource:
                continue
            if args.wikipedia and from_wikisource:
                continue
            if args.dump and not format_from_dump:
                continue
            if args.api and format_from_dump:
                continue

            hashtag_header = True
            repeat_headers = not from_wikisource

            # if not is_redirection:
            #     continue
            # if not re.match("1004_", file_in): # Esperanto
            #     continue
            # if not re.match("37047_", file_in) and not re.match("1157_", file_in): # Math & chemical -> good for challenging superscript/subscript
            #     continue
            # if not re.match("10049_", file_in): # Leonard de Vinci -> good for challenging citations
            #     continue

            _, pagename = file_in.split("_", 1)
            pagename = os.path.splitext(pagename)[0].replace("_", " ")

            file_in = os.path.join(input_dir, file_in)
            file_out = os.path.join(output_dir, os.path.splitext(os.path.basename(file_in))[0] + ".txt")

            print("Processing...",
                relative_filename(file_in),
                "\n------------>",
                relative_filename(file_out),
            )
            with open(file_in, "r") as f:
                text = clean_html(f.read(),
                    language="fr",
                    # verbose=args.verbose,
                    add_title=pagename,
                    hashtag_header=hashtag_header,
                    repeat_headers=repeat_headers,
                )

            if is_redirection:
                assert text == "", f"Unexpected result parsed:\n{text}"
            else:
                assert text != "", f"Unexpected empty result"

            if text:
                if not os.path.isdir(output_dir):
                    os.makedirs(output_dir)
                print(text, file = open(file_out, "w"))
            elif os.path.isfile(file_out):
                os.remove(file_out)
