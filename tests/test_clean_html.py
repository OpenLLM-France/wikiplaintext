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
from plaintext_to_markdown import plaintext_to_markdown

def relative_filename(filename, quote = True):
    filename = os.path.sep.join(filename.split(os.path.sep)[-2:])
    if quote:
        filename = shlex.quote(filename)
    return filename


def augmented_plaintext_to_markdown(
        text,
        markdown_file_out,
        website_main,
        rfile_out,
        rfile_in,
):
    (text_markdown, url) = plaintext_to_markdown(
        text,
        website_main,
        add_toc=True,
        add_urls=True,
    )
    prefix = f"""\
`This is the markdown version of `[`{urllib.parse.unquote(url)}`]({url})

`Plaintext version:..............`[`{os.path.basename(rfile_out)}`](../{rfile_out})

`Original HTML version:..........`[`{os.path.basename(rfile_in)}`](../{rfile_in})


"""
    os.makedirs(os.path.dirname(markdown_file_out), exist_ok=True)
    with open(markdown_file_out, "w") as f:
        f.write(prefix + text_markdown)

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
    example_try_no_superscript = [
        "1157_",    
        "11817_"
    ]
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
            add_example_no_superscript = False
            for prefix in example_try_no_superscript:
                if re.match(prefix, file_in):
                    assert add_example is not None
                    add_example_no_superscript = True
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
            kwargs = dict(
                language="fr",
                source=source,
                add_title=pagename,
                hashtag_header=hashtag_header,
                repeat_headers=repeat_headers,
                keep_tables=True,
                use_superscript=True,
                use_latex=False,
            )
            with open(file_in, "r") as f:
                html_body = f.read()
            text = clean_html(html_body, **kwargs)

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
                assert text
                filename = f"{website_main}_{add_example}".rstrip("_")
                markdown_file_out = os.path.join(this_dir, "examples_markdown", filename + ".md")
                rfile_out = relative_filename(file_out, quote=False)
                rfile_in = relative_filename(file_in, quote=False)
                if markdown_file_out not in has_generated_examples:
                    has_generated_examples.append(markdown_file_out)
                    print(
                        "------------>",
                        relative_filename(markdown_file_out),
                        "\n"
                        
                    )
                    augmented_plaintext_to_markdown(
                        text, markdown_file_out,
                        website_main, rfile_out, rfile_in,
                    )

                if add_example_no_superscript:
                    kwargs["use_superscript"] = False
                    kwargs["use_latex"] = True
                    text = clean_html(html_body, **kwargs)
                    markdown_file_out = os.path.join(this_dir, "examples_markdown", filename + "_nosuperscript.md")
                    if markdown_file_out not in has_generated_examples:
                        has_generated_examples.append(markdown_file_out)
                        print(
                            "------------>",
                            relative_filename(markdown_file_out),
                            "\n"
                        )
                        augmented_plaintext_to_markdown(
                            text, markdown_file_out,
                            website_main, rfile_out, rfile_in,
                        )
