#!/usr/bin/env python3

__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

import sys
import os
import re
import shlex
import urllib.parse
import random

def plaintext_to_markdown(
    text,
    website_main="wikipedia",
    linebreaks=2,
    add_toc=False,
    add_urls=False
    ):
    """
    Convert plaintext (extracted by dump_wiki_htmp.py) to markdown.

    Args:
        text (str): Plaintext
        website_main (str): Website name (e.g. "wikipedia", "wikisource", "wiktionary") to use as links for headers. Or None if no link is needed.
        add_toc (bool): Add a Table Of Content section at the beginning of the markdown text.
    Returns:
        (str, str): (Markdown text, url)
    """
    lines = text.split("\n")

    assert linebreaks in [0, 1, 2, "0", "1", "2", "random"], f"Invalid linebreaks: {linebreaks}"
    if linebreaks == "random":
        linebreaks = random.choice([0, 1, 2])
    else:
        linebreaks = int(linebreaks)

    linebreak_after_list = linebreaks > 0
    linebreak_after_table = linebreaks > 0

    linebreak_between_lines = linebreaks > 1
    linebreak_before_list = linebreaks > 1
    linebreak_before_header = linebreaks > 0
    linebreak_after_header = linebreaks > 1
    

    # Add :
    # - table headers
    # - new lines after table
    # - new lines after list
    # - new lines after lines
    new_lines = []
    was_list = False
    was_table = False
    was_header = True
    headers = []
    url = None
    toc = []
    markdown_subsections = []
    section_urls = []

    for line in lines:
        if not line:
            continue
        line = line+"\n"
        line_before = ""
        line_after = ""

        # Process lists
        if re.match(r"[\*> ]+ ", line):

            if re.match(r" + ", line):
                if new_lines and new_lines[-1].lstrip().startswith("*"):
                    if linebreak_before_list:
                        line_before = "\n"
            was_list = True
            if re.match(r"\*+ ", line):
                last_bullet = re.match(r"\*+", line).end()
                bullet = line[:last_bullet]
                line = line[last_bullet:]
                line = f"{' '*(len(bullet)-1)*3}*{line}"
            elif re.match(r"\*+>+ ", line):
                last_bullet = re.match(r"\*+", line).end()
                bullet = line[:last_bullet]
                line = line[last_bullet:]
                line = f"{' '*(len(bullet))*3}{line}"
            if was_table:
                if linebreak_after_table:
                    line_before = "\n"
                was_table = False
            was_header = False

        # Process tables
        elif re.match("^\|.*\|\n", line):
            if not was_table:
                # Add header separator
                num_columns = len(line.split("|")) - 2
                line_after = "|" + " - |" * num_columns + "\n"
            was_table = True
            if was_list:
                if linebreak_after_list:
                    line_before = "\n"
                was_list = False
            was_header = False

        else:

            # Process headers
            if re.match(r"^\#+ ", line):
                hashtags, line = line.split(" ", 1)
                title = line.strip()
                markdown_subsection = re.sub(r" +", "-", re.sub(r"[^\w ]", "", title.lower()))
                url_subsection = urllib.parse.quote(title.replace(' ','_'))
                level = len(hashtags)
                if level > 3:
                    line = f"**{title}**\n"
                else:
                    
                    if level > 1:
                        section_url = f"{url}#{url_subsection}"
                    else:
                        if not url:
                            url = f"https://fr.{website_main}.org/wiki/{url_subsection}"
                        section_url = url
                    
                    header_line = f"{hashtags}"
                    if add_urls:
                        header_line += f" [{line.strip()}]({section_url})\n"
                    else:
                        header_line += f" {line.strip()}\n"

                    ilevel = level - 1
                    do_print = False
                    while ilevel >= len(headers):
                        headers.append(None)
                    do_print = (headers[ilevel] != header_line)
                    headers[ilevel] = header_line

                    if do_print:
                        if markdown_subsection in markdown_subsections:
                            i = 1
                            while markdown_subsection + f"-{i}" in markdown_subsections:
                                i += 1
                            markdown_subsection += f"-{i}"
                        if section_url in section_urls:
                            # No way to link to the second subsection with the same title in Wikipedia (?)
                            header_line = f"{hashtags} {line.strip()}\n"
                        markdown_subsections.append(markdown_subsection)
                        section_urls.append(section_url)
                        headers = headers[:ilevel+1]
                        line = header_line
                        toc_line = f"[{title}](#{markdown_subsection})"
                        if level > 1:
                            toc_line = f"{' '*(level-2)*3}* " + toc_line
                        toc.append(toc_line)
                    else:
                        continue

                if linebreak_after_header:
                    line_after = "\n"
                if linebreak_before_header and not was_header and not linebreak_between_lines:
                    line_before = "\n"
                was_header = True

            else:

                # Add new lines after simple lines
                if linebreak_between_lines:
                    line_after = "\n"
                was_header = False

            # Add new lines after lists and tables
            if was_list:
                if linebreak_after_list:
                    line_before = "\n"
                was_list = False
            if was_table:
                if linebreak_after_table:
                    line_before = "\n"
                was_table = False


        new_lines.append(line_before + line + line_after)

    toc = '\n'.join(toc)
    prefix = f"{toc}\n---\n" if add_toc else ""

    return prefix + "".join(new_lines), url

if __name__ == "__main__":

    import argparse
    import tqdm

    parser = argparse.ArgumentParser(description="Convert Wikipedia plaintext to real markdown")
    parser.add_argument("input", help="Default input folder or file")
    parser.add_argument("output", help="Default output folder or file")
    parser.add_argument("--linebreaks", default="2", choices=["0", "1", "2", "random"], help="Number of linebreaks to add after lists and tables")
    parser.add_argument("--add_toc", action="store_true", help="Add Table of Content")
    parser.add_argument("--add_urls", action="store_true", help="Add URL in headers")
    parser.add_argument("--website_main", default="wikipedia", choices= [], help="Website name (e.g. 'wikipedia', 'wikisource', 'wiktionary') to use as links for headers.")
    args = parser.parse_args()

    def get_output_filename(fn):
        return os.path.join(args.output, os.path.basename(os.path.normpath(fn)) + ".md")

    if os.path.isdir(args.input):
        assert not os.path.isfile(args.output), f"Invalid output: {args.output}"
        def get_files():
            for root, dirs, files in os.walk(args.input):
                for file in tqdm.tqdm(files):
                    if file.endswith(".txt"):
                        yield os.path.join(root, file)
    elif os.path.isfile(args.input):
        def get_files():
            yield args.input
        if not os.path.isdir(args.output):
            def get_output_filename(fn):
                return args.output
    else:
        raise Exception(f"Invalid input: {args.input}")
    
    for file in get_files():
        text = open(file, "r", encoding="utf8").read()
        markdown, url = plaintext_to_markdown(
            text,
            website_main=args.website_main,
            linebreaks=args.linebreaks,
            add_toc=args.add_toc,
            add_urls=args.add_urls,
        )
        output_file = get_output_filename(file)
        print("Writing", output_file)
        dirname = os.path.dirname(output_file)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        open(output_file, "w", encoding="utf8").write(markdown)
