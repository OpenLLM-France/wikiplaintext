__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

import bs4
import regex as re
import warnings

from clean_common import final_clean, _ignore_from_section, END_HEADER
from clean_common import to_superscript, to_subscript, _superscript_coma, collapse_whitespace


def clean_html(
    html_string,
    language="fr",
    add_title=None,
    hashtag_header=True,
    repeat_headers=True,
    use_superscript=True,
):
    """
    Extract the text from an HTML string.

    :param html_string: HTML string or stream
    :param language: Language of the text
    :param add_title: Add a title to the text (if the name of the page is usually not included in the HTML)
    :param hashtag_header: Add hashtags before the headers (# for level 1, ## for level 2, etc.)
    :param repeat_headers: Repeat all headers from previous level at the beginning of each section
    :param use_superscript: Use subscript and superscript characters for numbers when relevant
    """

    if language not in _ignore_from_section:
        warnings.warn(f"Language {language} not supported (not in {sorted(list(_ignore_from_section.keys()))})")

    ignore_from_section = _ignore_from_section.get(language, [])

    soup = bs4.BeautifulSoup(html_string, "html.parser")

    from_dump = False
    if soup.find("section"):
        # From the dumps
        from_dump = True
        def root_generator():
            for section in soup.find_all("section"):
                for node in section.find_all(["p", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "dl"], recursive=False):
                    yield node
        root = root_generator()
    else:
        # From the API
        root = soup.find("div")

    # Iterate over all the <p> tags
    full_text = ""
    current_headers = []
    has_text = False
    if add_title:
        header = ("# " if hashtag_header else "") + add_title + END_HEADER + "\n"
        full_text += header
        current_headers = [header]

    for node in root:
        name = node.name
        if not name: continue

        # First paragraph is sometimes weird...
        if name == "p" and node.get("id") == "mwAg" and node.find("span"):
            text = extract_text_special(node, use_superscript=use_superscript)
            if not text:
                continue
            text = text + "\n"

        # Paragraph
        elif (name in ["p", "blockquote"]):
            text = extract_text(node, use_superscript=use_superscript)
            text = text + "\n"

        # Title
        elif re.match(r"h[1-6]", name):
            level = int(name[1])
            if from_dump:
                text = extract_text(node, use_superscript=use_superscript)
            else:
                for subnode in node.descendants:
                    if isinstance(subnode, bs4.element.Tag):
                        text = subnode.get_text().strip()
                    else:
                        text = subnode.strip()
                    if text:
                        break
                if not text:
                    continue
            
            if level in [2, 3] and text in ignore_from_section:
                break
            header = ("#"*level+" " if hashtag_header else "") + text + END_HEADER + "\n"
            if level > len(current_headers):
                current_headers += [""] * (level - len(current_headers))
            current_headers = current_headers[:level-1] + [header]
            if repeat_headers:
                header = "".join(current_headers)
            text = "\n" + header

        # List
        elif (name in ["ul", "ol", "dl"]):
            text = extract_text_in_list(
                node,
                hashtag_header=hashtag_header,
                repeat_headers=repeat_headers,
                use_superscript=use_superscript,
                current_headers=current_headers,
            )

        else:
            continue

        full_text += text
        has_text = True

    if not has_text:
        return ""

    full_text = final_clean(full_text, with_header_level=hashtag_header)

    return full_text


def extract_text(
    node,
    remove_annotations=True,
    use_superscript=True,
    remove_display_style=True,
    recursive=True,
    **karwgs,
    ):

    to_be_removed = []

    if use_superscript:

        new_html = None
        has_modified = False
        for subnode in node.find_all(["sup", "sub"], recursive=recursive):
            superscript = subnode.name == "sup"
            subtext = subnode.get_text()
            if superscript and subnode.find_all("a"):
                if looks_like_annotation(subtext):
                    # Safer to remove after
                    new_subtext = subtext
                    to_be_removed.append(subtext)
                else:
                    new_subtext = ""
            else:
                new_subtext = to_superscript(subtext, all_or_none=True) if superscript else to_subscript(subtext, all_or_none=True)
            if new_subtext == subtext:  
                continue
            subhtml = str(subnode)
            new_subhtml = re.sub(rf">(\s*){re.escape(subtext)}(\s*)<", rf">\1{re.escape(new_subtext)}\2<", subhtml)
            if new_subhtml == subhtml:
                continue
            if new_html is None:
                new_html = str(node)
            if subhtml in new_html:
                new_html = new_html.replace(subhtml, new_subhtml)
                has_modified = True
        if has_modified:
            node = bs4.BeautifulSoup(new_html, features="lxml").descendants.__next__()

    text = node.get_text(**karwgs) if recursive else node.get_text(depth=1, **karwgs)

    if remove_annotations:

        # All annotations ([1], [Note 1], [N 1], [a], [réf. souhaité], etc.)
        for subnode in node.find_all("a", recursive=recursive):
            if "API" in subnode.parent.get("class", []):
                # Prononciation
                continue
            subtext = subnode.get_text() if recursive else subnode.get_text(depth=1)
            if looks_like_annotation(subtext):
                to_be_removed.append(subtext.rstrip(_superscript_coma+","))
        for s in to_be_removed:
            text = re.sub(rf"([ \u00A0]*)?" + re.escape(s) + rf"(,(?=\[)|{_superscript_coma})?", "", text, count=1)

    text = text.strip()

    if remove_display_style and "{\displaystyle" in text:
        new_text = ""
        for line in text.split("\n"):
            if "{\displaystyle" in line and line.rstrip().endswith("}"):
                f = line.split("{\displaystyle")
                if len(f) == 2:
                    new_text += f[0].strip()
            else:
                new_text += line
        text = new_text


    return text


def looks_like_annotation(text):
    return bool(re.match(rf"^(\[[^\]]+\][,{_superscript_coma}]?)+$", text))


def extract_text_special(node, **kwargs):
    text = ""
    has_special = False
    for n in node:
        if n.name is None:
            text += n
        elif n.name in ["span"] and "mw:Nowiki" in n.get("typeof", ""):
            has_special = True
            continue
        else:
            text += extract_text(n, **kwargs)
    if not has_special:
        return extract_text(node, **kwargs)
    return text


def extract_text_in_list(
    node,
    hashtag_header=True,
    repeat_headers=True,
    use_superscript=True,
    current_headers=[],
    prefix="",
    ):
    text = ""
    if node.name in ["ul", "ol"]:
        for subnode in node.find_all("li", recursive=False):
            # Recursive call
            subtext = ""
            for subsubnode in subnode.find_all(["ul", "ol", "dl"], recursive=False):
                subtext += extract_text_in_list(
                    subsubnode,
                    hashtag_header=hashtag_header,
                    repeat_headers=repeat_headers,
                    use_superscript=use_superscript,
                    current_headers=current_headers,
                    prefix=prefix+"*",
                )
            if subtext:
                t = extract_text_in_list_header_text(subnode, use_superscript=use_superscript)
            else:
                t = extract_text(subnode, use_superscript=use_superscript)
            if t:
                text += prefix + "*" + " " + t + "\n"
            text += subtext

    # Descriptive list
    elif node.name == "dl":
        for subnode in node.find_all(["dt", "dd"], recursive=False):
            # Recursive call
            subtext = ""
            for subsubnode in subnode.find_all(["ul", "ol", "dl"], recursive=False):
                subtext += extract_text_in_list(
                    subsubnode,
                    hashtag_header=hashtag_header,
                    repeat_headers=repeat_headers,
                    use_superscript=use_superscript,
                    current_headers=current_headers,
                    prefix=prefix+">",
                )
            if subtext:
                t = extract_text_in_list_header_text(subnode, use_superscript=use_superscript)
            else:
                t = extract_text(subnode, use_superscript=use_superscript)
            if t and subnode.name == "dt":
                level = len(current_headers)+1
                header = (prefix + "#"*level +" " if hashtag_header else "") + t.rstrip("\u00A0 :") + END_HEADER + "\n"
                if repeat_headers:
                    header = "".join(current_headers) + header
                text += "\n" + header
            elif t and subnode.name == "dd":
                t = collapse_whitespace(t)
                text += prefix + ">" + " " + "\n> ".join(t.split("\n")) + "\n"
            text += subtext
    else:
        raise ValueError("Unexpected node name", node.name)
    return text


def extract_text_in_list_header_text(*args, **kwargs):
    # return extract_text(*args, recursive=False, **kwargs)
    return extract_text(*args, separator="␣", strip=True, **kwargs).split("␣")[0    ]

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Clean HTML")
    parser.add_argument("html_file", help="HTML file to clean")
    args = parser.parse_args()

    with open(args.html_file, "r") as f:
        html_string = f.read()
        text = clean_html(html_string)
        print(text)
