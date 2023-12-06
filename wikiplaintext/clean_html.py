__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

import bs4
import regex as re

from clean_common import final_clean, _ignore_from_section


def clean_html(
    html_string,
    language="fr",
    verbose=False,
):

    for d in [_ignore_from_section]:
        if language not in d:
            raise NotImplementedError(
                f"Language {language} not supported (not in {sorted(list(d.keys()))})")

    ignore_from_section = _ignore_from_section[language]

    # Return a string with only the text inside the <p></p> tags

    soup = bs4.BeautifulSoup(html_string, "html.parser")

    root = soup.descendants.__next__()

    # Iterate over all the <p> tags
    full_text = ""
    for node in root:
        name = node.name
        is_paragraph = (name in ["p", "blockquote"])
        is_list = (name in ["ul", "ol"])
        is_title = (name in ["h1", "h2", "h3", "h4", "h5", "h6"])

        # classes = node.get("class", [])

        if not is_paragraph and not is_title and not is_list:
            continue

        if is_title:  # Header
            for subnode in node.descendants:
                text = subnode.get_text().strip()
                if text:
                    break
            if not text:
                continue
            if text in ignore_from_section:
                break
            text = "\n" + text + "\u00A0:\n\n"
        elif is_list:  # List
            text = ""
            for subnode in node.find_all("li"):
                t = get_text_without_annotations(subnode)
                if t:
                    text += "* " + t + "\n"
        else:  # Paragraph
            text = get_text_without_annotations(node)
            text = text + "\n"
            # text = remove_notes_and_citations(text, language=language)

        full_text += text

    full_text = final_clean(full_text)

    return full_text


def get_text_without_annotations(node):
    text = node.get_text()
    to_be_removed = []
    # All annotations ([1], [a], [])
    for subnode in node.find_all("a"):
        if "API" in subnode.parent.get("class", []):
            # Prononciation
            continue
        subtext = subnode.get_text()
        if re.match(r"^(\[[^\]]+\],?)+$", subtext):
            to_be_removed.append(subtext)
    to_be_removed = to_be_removed[::-1]
    for s in to_be_removed:
        text = re.sub(r"([ \u00A0]|(?<=\]),)?" + re.escape(s), "", text)
    return text.strip()


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Clean HTML")
    parser.add_argument("html_file", help="HTML file to clean")
    args = parser.parse_args()

    with open(args.html_file, "r") as f:
        html_string = f.read()
        text = clean_html(html_string)
        print(text)
