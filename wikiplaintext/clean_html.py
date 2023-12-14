__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

import bs4
import regex as re
import warnings

from clean_common import (
    final_clean,
    _ignore_from_section,
    END_HEADER,
    to_superscript,
    to_subscript,
    format_table,
    _superscript_coma,
    collapse_whitespace,
)


def clean_html(
    html_string,
    language="fr",
    add_title=None,
    keep_tables=["wikitable"],
    hashtag_header=True,
    repeat_headers=True,
    use_superscript=True,
):
    """
    Extract the text from an HTML string.

    :param html_string: HTML string or stream
    :param language: Language of the text
    :param add_title: Add a title to the text (if the name of the page is usually not included in the HTML)
    :param hashtag_header: Add hashtags before the headers (# for level 1, ## for level 2, etc.) as in markdown format
    :param repeat_headers: Repeat all headers from previous level at the beginning of each section
    :param use_superscript: Use subscript and superscript characters for numbers when relevant
    """

    if language not in _ignore_from_section:
        warnings.warn(f"Not supported for language {language} : filtering out irrelevant sections (only supported for {sorted(list(_ignore_from_section.keys()))})")
    if language not in _filter_part_function:
        warnings.warn(f"Not supported for language {language} : filtering out irrelevant parts (only supported for {sorted(list(_filter_part_function.keys()))})")

    ignore_from_section = _ignore_from_section.get(language, [])
    filter_part_function = _filter_part_function.get(language, lambda x: False)

    soup = bs4.BeautifulSoup(html_string, "html.parser")

    all_possible_wrapping = ["html", "body", "section", "div"]
    all_possible_names = ["p", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "dl", "table"]

    def html_iterator(root):
        for node in root.find_all(all_possible_wrapping + all_possible_names, recursive=False):
            if filter_part_function(node): continue
            if node.name in all_possible_names:
                yield node
            else:
                for subnode in html_iterator(node):
                    yield subnode

    # Adapt to HTML structure, which varies 
    # - between the dumps and the API, between 
    # - wikipedia / wikisource / ...
    from_dump = bool(soup.find("section"))
    level_whitespace_collapsing = 2
    if from_dump:
        # From the dumps
        prefix = soup.find("head").get("prefix")
        from_wikipedia = "wikipedia.org" in prefix
        if from_wikipedia:
            def html_iterator(soup):
                for section in soup.find_all("section"):
                    if filter_part_function(section): continue
                    subnodes = section.find_all(all_possible_names, recursive=False)
                    for node in subnodes:
                        yield node                
        root = html_iterator(soup)
    else:
        # From the API
        root = soup.find("div")
        subdiv = root.find("div")
        from_wikipedia = subdiv and "bandeau-container" in subdiv.get("class", [])
        # Note : from_wikipedia can be False for some Wikipedia pages
        if not from_wikipedia:
            root = html_iterator(soup)

    # Iterate over all the <p> tags
    full_text = ""
    current_headers = []
    has_text = False
    if add_title:
        header = ("# " if hashtag_header else "") + add_title + END_HEADER + "\n"
        full_text += header
        current_headers = [header]

    in_content = False

    for node in root:
        name = node.name
        if not name: continue
        if filter_part_function(node): continue

        # First paragraph is sometimes weird...
        if name == "p" and node.get("id") == "mwAg" and node.find("span"):
            text = extract_text_special(node, use_superscript=use_superscript)
            if not text: continue
            text = collapse_whitespace(text, level_whitespace_collapsing)
            text = text + "\n"

        # Paragraph
        elif (name in ["p", "blockquote"]):
            text = extract_text(node, use_superscript=use_superscript)
            if not text: continue
            if name in ["p"]:
                text = collapse_whitespace(text, level_whitespace_collapsing)
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
            
            if level in [2, 3] and collapse_whitespace(text) in ignore_from_section:
                break
            header = ("#"*level+" " if hashtag_header else "") + text + END_HEADER + "\n"
            if level > len(current_headers):
                current_headers += [""] * (level - len(current_headers))
            current_headers = current_headers[:level-1] + [header]
            if repeat_headers:
                header = "".join(current_headers)
            text = "\n" + header
            in_content = True

        # List
        elif (name in ["ul", "ol", "dl"]):
            text = list_to_text(
                node,
                use_superscript=use_superscript,
                hashtag_header=hashtag_header,
                repeat_headers=repeat_headers,
                current_headers=current_headers,
                ignore_one_bullet=(not in_content),
            )

        elif name == "table" and keep_tables and max([k in node.get("class", []) for k in keep_tables]):
            text = text_to_table(
                node,
                use_superscript=use_superscript,
                ignore_one_cell=True,
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
    treat_line_breaks_as=" ",
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

    for line_break in node.findAll('br'):
        line_break.replaceWith(treat_line_breaks_as)

    # text = node.get_text(**karwgs) if recursive else node.get_text(depth=1, **karwgs)
    # if "separator" not in karwgs:
    #     karwgs["separator"] = "\n"
    # if "strip" not in karwgs:
    #     karwgs["strip"] = True
    text = node.get_text(**karwgs) if recursive else node.get_text( depth=1, **karwgs)

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


def list_to_text(
    node,
    hashtag_header=True,
    repeat_headers=True,
    use_superscript=True,
    current_headers=[],
    prefix="",
    ignore_one_bullet=True,
    ):
    text = ""
    if node.name in ["ul", "ol"]:
        bullets = node.find_all("li", recursive=False)
        if ignore_one_bullet and len(bullets) == 1:
            return ""
        for bullet in bullets:
            # Recursive call
            subtext = ""
            for subsubnode in bullet.find_all(["ul", "ol", "dl"], recursive=False):
                subtext += list_to_text(
                    subsubnode,
                    hashtag_header=hashtag_header,
                    repeat_headers=repeat_headers,
                    use_superscript=use_superscript,
                    current_headers=current_headers,
                    prefix=prefix+"*",
                    ignore_one_bullet=False,
                )
            if subtext:
                t = extract_text_in_list_header_text(bullet, use_superscript=use_superscript)
            else:
                t = extract_text(bullet, use_superscript=use_superscript)
            if t:
                text += prefix + "*" + " " + t + "\n"
            text += subtext

    # Descriptive list
    elif node.name == "dl":
        for bullet in node.find_all(["dt", "dd"], recursive=False):
            # Recursive call
            subtext = ""
            for subsubnode in bullet.find_all(["ul", "ol", "dl"], recursive=False):
                subtext += list_to_text(
                    subsubnode,
                    hashtag_header=hashtag_header,
                    repeat_headers=repeat_headers,
                    use_superscript=use_superscript,
                    current_headers=current_headers,
                    prefix=prefix+">",
                    ignore_one_bullet=False,
                )
            if subtext:
                t = extract_text_in_list_header_text(bullet, use_superscript=use_superscript)
            else:
                t = extract_text(bullet, use_superscript=use_superscript)
            if t and bullet.name == "dt":
                level = len(current_headers)+1
                header = (prefix + "#"*level +" " if hashtag_header else "") + t.rstrip("\u00A0 :") + END_HEADER + "\n"
                if repeat_headers:
                    header = "".join(current_headers) + header
                text += "\n" + header
            elif t and bullet.name == "dd":
                t = collapse_whitespace(t)
                text += prefix + ">" + " " + "\n> ".join(t.split("\n")) + "\n"
            text += subtext
    else:
        raise ValueError("Unexpected node name", node.name)
    return text


def extract_text_in_list_header_text(*args, **kwargs):
    # return extract_text(*args, recursive=False, **kwargs)
    return extract_text(*args, separator="␣", strip=True, **kwargs).split("␣")[0    ]


class HtmlTable:
    def __init__(self, node, use_superscript=True):
        self.node = node
        self.caption = node.find("caption")
        if self.caption:
            self.caption = extract_text(self.caption, use_superscript=use_superscript)
        self.body = node.find("tbody")
        if not self.body:
            self.caption = None
            self.rows = []
            return
        assert self.body, "Missing table body"
        self.rows = []
        header_colspans = []
        for irow, row in enumerate(self.body.find_all("tr", recursive=False)):
            self.rows.append([])
            colspans = []
            for cell in row.find_all(["th", "td"], recursive=False):
                colspan = cell.get("colspan", 1)
                if isinstance(colspan, str):
                    try:
                        colspan = int(colspan)
                    except ValueError:
                        colspan = 1
                colspans.append(colspan)
                text = extract_text(cell, use_superscript=use_superscript).strip()
                if not text:
                    text = cell.get_text().strip()
                    if looks_like_annotation(text):
                        text = ""
                if colspan > 1:
                    if irow==0 or cell.name != "th":
                        self.rows[-1] += [text] * (colspan - 1)
                    else:
                        self.rows[-1] += [""] * (colspan - 1)
                self.rows[-1].append(text)
            if irow == 0:
                header_colspans = colspans
            if len(colspans) == 1:
                self.rows[-1] = [self.rows[-1][-1] + " " + "|"*(colspans[0]-1)]
        # Sometimes there is a big first row, acting as a caption
        if len(header_colspans) == 1 and header_colspans[0] > 1 and not self.caption:
            self.caption = self.rows[0][-1].rstrip("|").rstrip()
            self.rows = self.rows[1:]

    def data(self):
        return self.rows


def text_to_table(node, use_superscript=True, ignore_one_cell=True):
    return format_table(
        HtmlTable(node, use_superscript=use_superscript),
        ignore_one_cell=ignore_one_cell,
    )


_filter_part_function = {
    "fr": lambda x: any_starts_with(x.get("class"), ["bandeau-", "infobox"])
}

def any_starts_with(list_of_strings, list_of_starts):
    return any(s.startswith(start) for s in list_of_strings for start in list_of_starts) if list_of_strings else False


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Clean HTML")
    parser.add_argument("html_file", help="HTML file to clean")
    args = parser.parse_args()

    with open(args.html_file, "r") as f:
        html_string = f.read()
        text = clean_html(html_string)
        print(text)
