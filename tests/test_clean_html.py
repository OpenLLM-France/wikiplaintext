#!/usr/bin/env python3

__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

import sys
import os
import re
import shlex
import urllib.parse

this_dir = os.path.dirname(os.path.realpath(__file__))

lib_dir = os.path.join(os.path.dirname(this_dir), "wikiplaintext")
sys.path.append(lib_dir)

from clean_html import clean_html

def relative_filename(filename, quote = True):
    filename = os.path.sep.join(filename.split(os.path.sep)[-2:])
    if quote:
        filename = shlex.quote(filename)
    return filename

def plaintext_to_markdown(
    text,
    fileout,
    website_main,
    filename_plaintext,
    filename_html,
    ):
    lines = text.split("\n")

    # Add :
    # - table headers
    # - new lines after table
    # - new lines after list
    # - new lines after lines
    new_lines = []
    was_list = False
    was_table = False
    headers = []
    url = None
    toc = []
    markdown_subsections = []
    section_urls = []

    for line in lines:
        line = line+"\n"
        line_before = ""
        line_after = ""

        # Process lists
        if re.match(r"[\*> ]+ ", line):

            if re.match(r" + ", line):
                was_list = True
                if new_lines and new_lines[-1].lstrip().startswith("*"):
                    line_before = "\n"
            else:
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
                line_before = "\n"
                was_table = False

        # Process tables
        elif re.match("^\|.*\|\n", line):
            if not was_table:
                # Add header separator
                num_columns = len(line.split("|")) - 2
                line_after = "|" + " - |" * num_columns + "\n"
            was_table = True
            if was_list:
                line_before = "\n"
                was_list = False

        else:
            # Add new lines after lists and tables
            if was_list or was_table:
                line_before = "\n"
                was_list = was_table = False

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
                    
                    header_line = f"{hashtags} [{line.strip()}]({section_url})\n"

                    ilevel = level - 1
                    do_print = False
                    # if "Formules empiriques" in line:
                    #     import pdb; pdb.set_trace()
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
                        line = ""

            else:

                # Add new lines after simple lines
                if line.strip():
                    line_after = "\n"

        new_lines.append(line_before + line + line_after)

    toc = '\n'.join(toc)

    prefix = f"""\
`This is the markdown version of `[`{urllib.parse.unquote(url)}`]({url})

`Plaintext version:..............`[`{os.path.basename(filename_plaintext)}`](../{filename_plaintext})

`Original HTML version:..........`[`{os.path.basename(filename_html)}`](../{filename_html})


{toc}
---
"""

    os.makedirs(os.path.dirname(fileout), exist_ok=True)
    with open(fileout, "w") as f:
        f.write(prefix)
        for line in new_lines:
            f.write(line)

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Clean Wikipedia code")
    parser.add_argument("IDs", default=None, nargs="*", help="Wikipedia page IDs to clean")
    parser.add_argument("--wikisource", action="store_true", help="Only HTML from wikisource")
    parser.add_argument("--wikipedia", action="store_true", help="Only HTML from wikipedia")
    parser.add_argument("--wiktionary", action="store_true", help="Only HTML from wiktionary")
    parser.add_argument("--dump", action="store_true", help="Only HTML from wikimedia enterprise dump")
    parser.add_argument("--example", action="store_true", help="Only example markdown files")
    parser.add_argument("--api", action="store_true", help="Only HTML from wikimedia API")
    args = parser.parse_args()

    example_prefixes = {
        # 1. Wikipedia

        "9756166_": "table", # Afrique_du_Sud_aux_Jeux_olympiques_d'été_de_2016 -> complex table
        "1157_": "chemistry", # Formule brute
        "11817_": "math", # Racine_carrée
        # "37047_": "math_equations", # Équation_fonctionnelle
        # "10996_": "math_derivatives", # Dérivée
        # "1004_": "classical", # Espéranto

        # 2. Wikisource
        "1314_": "",

        # 3. Wiktionary
        "2285106_": "french_expression", # qui_trop_écoute_la_météo,_passe_sa_vie_au_bistro
        "2798794_": "french_number", # cinquante-six
        "96663_": "foreign_sinogram", # 調
        "10051_": "foreign_germanic", # August
    }
    has_generated_examples = []

    for input_dir, output_dir in [
        ("wikipedia_dumphtml_redirect", "SHOULD_NOT_OCCUR"),
        ("wikipedia_dumphtml", "wikipedia_dumphtml_cleaned"),
        ("wikipedia_html", "wikipedia_html_cleaned"),
        ("wikisource_dumphtml", "wikisource_dumphtml_cleaned"),
        ("wikisource_html", "wikisource_html_cleaned"),
        ("wiktionary_dumphtml", "wiktionary_dumphtml_cleaned"),
    ]:
        
        input_dir = os.path.join(this_dir, input_dir)
        output_dir = os.path.join(this_dir, output_dir)

        is_redirection = "redirect" in input_dir
        format_from_dump = "dump" in input_dir
        from_wikisource = "wikisource" in input_dir
        from_wikipedia = "wikipedia" in input_dir
        from_wiktionary = "wiktionary" in input_dir

        if args.wikisource and not from_wikisource:
            continue
        if args.wikipedia and not from_wikipedia:
            continue
        if args.wiktionary and not from_wiktionary:
            continue
        if args.dump and not format_from_dump:
            continue
        if args.api and format_from_dump:
            continue

        source = "wiki" if from_wikipedia else "wikisource" if from_wikisource else "wiktionary" if from_wiktionary else None
        website_main = "wikipedia" if source == "wiki" else source

        for file_in in sorted(os.listdir(input_dir)):
            if not re.match("\d", file_in):
                continue

            if args.IDs and not max([bool(re.match(prefix, file_in)) for prefix in args.IDs]):
                continue

            add_example = None
            for prefix, name in example_prefixes.items():
                if re.match(prefix, file_in):
                    add_example = name
                    break

            if args.example and add_example is None:
                continue

            hashtag_header = True
            repeat_headers = not from_wikisource

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
                    source=source,
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

            if add_example is not None:
                # filename = os.path.splitext(os.path.basename(file_in))[0]
                # _, filename = filename.split("_", 1)
                filename = add_example
                filename = f"{website_main}_{filename}".rstrip("_")
                markdown_file_out = os.path.join(this_dir, "examples_markdown", filename + ".md")
                if markdown_file_out not in has_generated_examples:
                    has_generated_examples.append(markdown_file_out)
                    print(
                        "------------>",
                        relative_filename(markdown_file_out),
                        "\n"
                    )
                    plaintext_to_markdown(
                        text, markdown_file_out,
                        website_main,
                        relative_filename(file_out, quote=False),
                        relative_filename(file_in, quote=False),
                    )
