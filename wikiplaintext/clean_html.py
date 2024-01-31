__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

import bs4
import regex as re
import warnings

from clean_common import (
    final_clean,
    format_table,
    collapse_whitespace,
    to_superscript,
    to_subscript,
    SuperScriptConverstion, SUPERSCRIPTS_TO_AVOID, SUBSCRIPTS_TO_AVOID,
    _superscript_coma,
    IGNORE_FROM_SECTION,
    POSTPROC_SECTION,
    HTML_NODE_IGNORED,
    LINKS_TO_DISCARD_FUN,
    END_HEADER,
    PROTECTED_SPACE,
)


PREFIX_DL = PROTECTED_SPACE*3 # previously ">"
PREFIX_QUOTE = PROTECTED_SPACE*3
CURRENT_PREFIX = ""


def clean_html(
    html_string,
    language="fr",
    source="wiki",
    add_title=None,
    keep_tables=True,
    hashtag_header=True,
    repeat_headers=True,
    use_superscript=True,
    use_latex=True,
    from_dump=None,
):
    """
    Extract the text from an HTML string.

    :param html_string: HTML string or stream
    :param language: Language of the text
    :param source: Source of the text (wikipedia, wikisource, wiktionary ...)
    :param add_title: Add a title to the text (if the name of the page is usually not included in the HTML)
    :param hashtag_header: Add hashtags before the headers (# for level 1, ## for level 2, etc.) as in markdown format
    :param repeat_headers: Repeat all headers from previous level at the beginning of each section
    :param use_superscript: Use subscript and superscript characters for numbers when relevant
    :param use_latex: keep LaTeX when it's there, for math formulas
    """
    global CURRENT_PREFIX # This is not thread-safe because of this global variable
    CURRENT_PREFIX = ""

    # hashtag_header_internal = True
    # repeat_headers_internal = True
    hashtag_header_internal = hashtag_header
    repeat_headers_internal = repeat_headers

    if source == "wiki":
        source = "wikipedia"
    ignore_from_section = IGNORE_FROM_SECTION.get(source, {}).get(language, [])
    section_dependent_postproc = POSTPROC_SECTION.get(source, {}).get(language, {})
    ignore_node = HTML_NODE_IGNORED.get(language, HTML_NODE_IGNORED["en"])
    kwargs_extract_text_header = dict(
        superscript_conversion = SUPERSCRIPTS_TO_AVOID.get(language, []) if not use_superscript else SuperScriptConverstion.ALL_OR_NONE,
        subscript_conversion = SUBSCRIPTS_TO_AVOID.get(language, SUBSCRIPTS_TO_AVOID.get("", [])) if not use_superscript else SuperScriptConverstion.ALL_OR_NONE,
        use_latex_if_possible = use_latex,
        looks_like_linktodiscard = LINKS_TO_DISCARD_FUN.get(language, lambda text:False),
    )
    kwargs_extract_text = kwargs_extract_text_header | dict(postproc = None)

    soup = bs4.BeautifulSoup(html_string, "html.parser")

    all_possible_wrapping = ["html", "body", "section", "div", "blockquote", "center", "span"]
    all_possible_names = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "dl", "table", "math"]

    def html_iterator(root):
        global CURRENT_PREFIX
        for node in root.find_all(all_possible_wrapping + all_possible_names, recursive=False):
            if ignore_node(node): continue
            if node.name in all_possible_names:
                yield node
                # if node.name == "table":
                #     # Sometimes, subsections can be included in tables, see https://fr.wikipedia.org/wiki/Afrique_du_Sud_aux_Jeux_olympiques_d%27%C3%A9t%C3%A9_de_2016
                #     for subnode in node.find_all("section", recursive=True):
                #         if ignore_node(subnode): continue
                #         for subsubnode in html_iterator(subnode):
                #             yield subsubnode
            else:
                add_quotes = node.name == "blockquote"
                if add_quotes:
                    CURRENT_PREFIX += PREFIX_QUOTE
                for subnode in html_iterator(node):
                    yield subnode
                if add_quotes:
                    CURRENT_PREFIX = CURRENT_PREFIX[:-len(PREFIX_QUOTE)]

    # Adapt to HTML structure, which varies 
    # - between the dumps and the API, between 
    # - wikipedia / wikisource / ...
    if from_dump is None:
        from_dump = bool(soup.find("section"))
    level_whitespace_collapsing = 2
    root = html_iterator(soup)

    # Iterate over all the <p> tags
    full_text = ""
    current_headers = []
    has_text = False
    if add_title:
        header = ("# " if hashtag_header_internal else "") + add_title + END_HEADER + "\n"
        full_text += header
        current_headers = [header]

    in_content = False
    postproc_per_section = []

    for node in root:
        name = node.name
        if not name: continue
        if ignore_node(node): continue

        # First paragraph is sometimes weird...
        if name == "p" and node.get("id") == "mwAg" and node.find("span"):
            text = extract_text_special(node, **kwargs_extract_text)
            if not text: continue
            text = collapse_whitespace(text, level_whitespace_collapsing)
            text = text + "\n"

        # Paragraph
        elif (name in ["p", "math"]):
            if node.name == "math":
                # Wrap into a paragraph
                node = bs4.BeautifulSoup(f"<p>{node}</p>", "html.parser").find("p")
            text = extract_text(node, **kwargs_extract_text)
            if not text: continue
            text = collapse_whitespace(text, level_whitespace_collapsing)
            text = text + "\n"

        # Title
        elif re.match(r"h[1-6]", name):
            level = int(name[1])
            if from_dump:
                text = extract_text(node, **kwargs_extract_text_header, remove_line_breaks=True)
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
            ntext = collapse_whitespace(text, 3)
            if level in [2, 3] and ntext in ignore_from_section:
                break
            
            # Update specific post-processing functions
            # 1. Resize
            while len(postproc_per_section) < level:
                postproc_per_section.append(None)
            postproc_per_section = postproc_per_section[:level]
            # 2. Get the function
            postproc = section_dependent_postproc.get(ntext)
            postproc_per_section[level-1] = postproc
            postproc_default = section_dependent_postproc.get("*")
            # 3. Compose
            functions = [f for f in [postproc_default] + postproc_per_section[::-1] if f is not None]
            if len(functions) == 0:
                kwargs_extract_text["postproc"] = None
            elif len(functions) == 1:
                kwargs_extract_text["postproc"] = functions[0]
            else:
                def compose(functions, text):
                    for f in functions:
                        text = f(text)
                    return text
                kwargs_extract_text["postproc"] = lambda text: compose(functions, text)
            # print("#" * level, ntext, postproc_per_section)

            header = ("#"*level+" " if hashtag_header_internal else "") + text + END_HEADER + "\n"
            if level > len(current_headers):
                current_headers += [""] * (level - len(current_headers))
            current_headers = current_headers[:level-1] + [header]
            if repeat_headers_internal:
                header = "".join(current_headers)
            text = "\n" + header
            in_content = True

        # List
        elif (name in ["ul", "ol", "dl"]):
            text = list_to_text(
                node,
                hashtag_header=hashtag_header_internal,
                repeat_headers=repeat_headers_internal,
                current_headers=current_headers,
                ignore_one_bullet=(not in_content),
                **kwargs_extract_text
            )

        elif name == "table" and keep_tables:
            text = text_to_table(node, **kwargs_extract_text)

        else:
            continue

        has_text = has_text or bool(text)
        if text:
            if CURRENT_PREFIX:
                text = re.sub("(^|\n(?!$))", rf"\1{CURRENT_PREFIX}", text)
            full_text += text

    if not has_text:
        return ""

    full_text = final_clean(full_text,
        remove_hashtag_headers=not hashtag_header and hashtag_header_internal,
        remove_repeated_headers=not repeat_headers and repeat_headers_internal,
    )

    return full_text

def extract_text(node, **kwargs):
    if node.name == "table":
        return text_to_table(node, **kwargs)
    elif node.name in ["ul", "ol", "dl"]:
        return list_to_text(node, **kwargs)
    return extract_text_in_paragraph(node, **kwargs)


def extract_text_in_paragraph(
    node,
    superscript_conversion, #=True,
    subscript_conversion,
    use_latex_if_possible,
    looks_like_linktodiscard, #=lambda text:False,
    postproc=None,
    remove_annotations=True,
    recursive=True,
    treat_line_breaks_as=" ",
    remove_line_breaks=False,
    **karwgs,
    ):

    brackets_to_remove = []
    additional_to_remove = []

    # # Add line breaks before block spans
    # for span in node.find_all("span", recursive=recursive):
    #     if "display:block" in span.get("style", "").replace(" ", ""):
    #         span.insert(0, "\n")
    #         span.append("\n")

    # Process sqrt:
    for subnode in node.find_all(["msqrt", "mroot"], recursive=recursive):
        subsubnodes = subnode.find_all(recursive=False)
        if subnode.name == "mroot" and len(subsubnodes) != 2:
            import pdb; pdb.set_trace() 
        text = re.sub(r"\s", "", subsubnodes[0].get_text() if subnode.name == "mroot" else subnode.get_text())
        needs_parenthesis = len(text.rstrip("|)").lstrip("(|")) > 1
        if needs_parenthesis:
            subnode.insert(0, "(")
        subnode.insert(0, "√")
        if subnode.name == "mroot":
            exponent = re.sub(r"\s", "", subsubnodes[1].get_text())
            subnode.insert(0, to_superscript(exponent, SuperScriptConverstion.WHAT_POSSIBLE))
            subsubnodes[1].replace_with("")
        if needs_parenthesis:
            subnode.append(")")

    # Process fractions
    for subnode in node.find_all(["mfrac"], recursive=recursive):
        subnodes = []
        for subsubnode in subnode.find_all(recursive=False):
            if isinstance(subsubnode, bs4.element.Tag):
                subnodes.append(subsubnode)
        if len(subnodes) != 2:
            import pdb; pdb.set_trace()
            subnodes
        text1 = subnodes[0].get_text()
        text2 = "".join(s.get_text() for s in subnodes[1:])
        text = re.sub(r"\s", "", subnode.get_text())
        parent = subnode.parent
        while re.sub(r"\s", "", parent.get_text()) == text:
            parent = parent.parent
        parent_text = re.sub(r"\s", "", parent.get_text())
        match = re.search(re.escape(text), parent_text)
        if match is None:
            import pdb; pdb.set_trace()
            (text, parent_text)
        char_before = parent_text[match.start()-1] if match.start() > 0 else "X"
        char_after = parent_text[match.end()] if match.end() < len(parent_text) else "X"
        add_spaces_before = char_before not in "([{,.=-−+" 
        add_spaces_after = char_after not in ")]},.=-−+"
        add_parenthesis1 = any(x in text1 for x in ["+", "-"])
        add_parenthesis2 = any(x in text2 for x in ["+", "-"])

        if add_parenthesis1:
            subnodes[0].insert(0, (" " if add_spaces_before else "") + "(")
            subnodes[0].append(")")
        elif add_spaces_before:
            subnodes[0].insert(0, " ")
        subnodes[0].append("/")
        if add_parenthesis2:
            subnodes[1].insert(0, "(")
            subnodes[-1].append(")" + (" " if add_spaces_after else ""))
        elif add_spaces_after:
            subnodes[-1].append(" ")

    if node.find_all("mfenced", recursive=True):
        import pdb; pdb.set_trace()
        ("mfenced", node)

    for subnode in node.find_all(["sup", "sub", "msup", "msub", "msubsup", "munder", "mover", "munderover"], recursive=recursive):
        superscript = subnode.name in ["sup", "msup", "mover"]
        if subnode.name in ["msup", "msub", "msubsup", "munder", "mover", "munderover"]:
            subnodes = []
            for i, subsubnode in enumerate(subnode.find_all(recursive=False)):
                if i > 0:
                    if i > 1:
                        if i > 2:
                            import pdb; pdb.set_trace()
                            subnode
                        if subnode.name in ["msubsup", "munderover"]:
                            superscript = True
                        else:
                            import pdb; pdb.set_trace()
                            subnode
                    subnodes.append((superscript, subsubnode))
        else:
            subnodes = [(superscript, subnode)]
        for superscript, subnode in subnodes:
            subtext = subnode.get_text()
            if subnode.name == "sup" and subnode.find("a"):
                # if "prononciation" in subnode.find("a").parent.get("class", []):
                #     continue
                if looks_like_annotation(subtext):
                    # Safer to remove after
                    new_subtext = subtext
                    brackets_to_remove.append(subtext)
                else:
                    new_subtext = ""
            else:
                subtext = re.sub("\s", "", subtext)
                new_subtext = to_superscript(subtext, superscript_conversion) if superscript else to_subscript(subtext, subscript_conversion)
            if new_subtext == subtext:  
                continue
            subnode.replace_with(new_subtext)

    # Workaround for math
    for subnode in node.find_all("math", recursive=recursive):
        text = subnode.get_text()
        if use_latex_if_possible:
            if "{\displaystyle" in text:
                i = re.search(r"\{\\displaystyle", text)
                offset = i.end()
                try:
                    j = text.index("}", offset)
                except ValueError:
                    warnings.warn("Unbalanced brackets in math formula")
                    j = len(text)
                num_opening_brackets = len(re.findall("{", text[offset:j]))
                while num_opening_brackets:
                    newj = j
                    for _ in range(num_opening_brackets):
                        try:
                            newj = text.index("}", newj+1)
                        except ValueError:
                            warnings.warn("Unbalanced brackets in math formula")
                            break
                    num_opening_brackets = len(re.findall("{", text[j:newj]))
                    j = newj
                text = text[i.end():j]
                text = f"${text.strip()}$"
                subnode.replace_with(text)
                continue
        else:
            text = re.sub(r"\{\\displaystyle.*\}\n+$", "", text)
        startswith_space = re.match(r"\n{3,}", text)
        endswith_space = re.search(r"\n{3,}$", text)
        text = re.sub("\n", "", text)
        text = collapse_whitespace(text.replace(",", ", "))
        if startswith_space or endswith_space:
            previous_text, next_text = get_previous_and_next_text(subnode)
        if startswith_space:
            if not re.search(r"\($", previous_text):
                text = " " + text
        if endswith_space:
            if not re.match(r"[\.,\)]", next_text):
                text += " "
        treat_line_breaks_as = "\n"
        subnode.replace_with(text)

    # This is a workaround because bs4 does not handle line breaks <br/> correctly
    for line_break in node.findAll('br'):
        line_break.replace_with(treat_line_breaks_as)

    text = node.get_text(**karwgs) if recursive else node.get_text(depth=1, **karwgs)

    if remove_line_breaks:
        text = re.sub(r"(\s*\n\s*)+", " ", text)

    if remove_annotations:

        # All annotations ([1], [Note 1], [N 1], [a], [réf. souhaité], etc.)
        for subnode in node.find_all("a", recursive=recursive):
            if "API" in subnode.parent.get("class", []):
                # Prononciation
                continue
            subtext = subnode.get_text() if recursive else subnode.get_text(depth=1)
            if looks_like_annotation(subtext):
                brackets_to_remove.append(subtext.rstrip(_superscript_coma+","))
            # if "action=edit" in subnode.get("href", ""): # "modifier", ...
            if looks_like_linktodiscard(subtext):
                additional_to_remove.append(subtext)
        for s in brackets_to_remove:
            text = re.sub(rf"([ \u00A0]*)?" + re.escape(s) + rf"(,(?=\[)|{_superscript_coma})?", "", text, count=1)
        for s in additional_to_remove:
            text = re.sub(r"(\s*\[\s*)?\b" + re.escape(s) + r"\b(\s*\])?", "", text, count=1)

    text = text.strip()

    if postproc:
        text = postproc(text)

    return text

# HTML_MATH_BLOCKS = [
#     "mi", "mn", "mo",
#     "mtext", "mrow",
#     "msqrt", "mroot",
#     "mfrac",
#     "msup", "msub", "msubsup", "munderover", "munder", "mover",
#     "mstyle",
#     # "mfenced",
# ]


def get_previous_and_next_text(node):
    parent = node.parent
    previous_text = ""
    next_text = ""
    while not previous_text and not next_text:
        if not parent:
            break
        siblings = list(parent.children)
        for i, sibling in enumerate(siblings):
            if sibling == node:
                for k in range(i-1, -1, -1):
                    text = siblings[k].get_text() if isinstance(siblings[k], bs4.element.Tag) else str(siblings[k])
                    if text:
                        previous_text = text
                        break
                for k in range(i+1, len(siblings)):
                    text = siblings[k].get_text() if isinstance(siblings[k], bs4.element.Tag) else str(siblings[k])
                    if text:
                        next_text = text
                        break
                break
        node = parent
        parent = parent.parent
    return previous_text, next_text

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
    current_headers=[],
    prefix="",
    ignore_one_bullet=True,
    **kwargs,
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
                    current_headers=current_headers,
                    prefix=prefix+"*",
                    ignore_one_bullet=False,
                    **kwargs,
                )
            if subtext:
                t = extract_text_in_list_header_text(bullet, **kwargs)
            else:
                t = extract_text(bullet, **kwargs)
            t = collapse_whitespace(t, 3)
            if t:
                text += prefix + "*" + " " + t + "\n"
            text += subtext

    # Descriptive list
    elif node.name == "dl":
        prefix2 = prefix.replace("*", "")
        for bullet in node.find_all(["dt", "dd"], recursive=False):
            # Recursive call
            subtext = ""
            for subsubnode in bullet.find_all(["ul", "ol", "dl"], recursive=False):
                subtext += list_to_text(
                    subsubnode,
                    hashtag_header=hashtag_header,
                    repeat_headers=repeat_headers,
                    current_headers=current_headers,
                    prefix=prefix+PREFIX_DL,
                    ignore_one_bullet=False,
                    **kwargs
                )
            if subtext:
                t = extract_text_in_list_header_text(bullet, **kwargs)
            else:
                t = extract_text(bullet, **kwargs)
            t = collapse_whitespace(t, 3)
            if t and bullet.name == "dt":
                level = len(current_headers)+1
                header = (prefix2 + "#"*level +" " if hashtag_header else "") + t.rstrip("\u00A0 :") + END_HEADER + "\n"
                if repeat_headers:
                    header = "".join(current_headers) + header
                text += "\n" + header
            elif t and bullet.name == "dd":
                # Once upon a time, collapse_whitespace was used only here (why?)
                text += prefix2 + PREFIX_DL + " " + "\n> ".join(t.split("\n")) + "\n"
            text += subtext
    else:
        raise ValueError("Unexpected node name", node.name)
    return text


def extract_text_in_list_header_text(node, **kwargs):
    """
    Trick to extract text from a bullet in a list, to avoid including sublists (otherwise there will be repetitions)
    """
    for descendant in node.find_all(["ul", "ol", "dl"], recursive=False):
        descendant.replace_with("")
    return extract_text(node, **kwargs)


class HtmlTable:
    def __init__(self, node, **kwargs):
        looks_like_linktodiscard = kwargs["looks_like_linktodiscard"]
        self.node = node
        self.caption = node.find("caption")
        if self.caption:
            self.caption = extract_text(self.caption, **kwargs, remove_line_breaks=True)
        self.body = node.find("tbody")
        if not self.body:
            self.caption = None
            self.rows = []
            return
        assert self.body, "Missing table body"
        self.rows = []
        header_colspans = []
        rows = self.body.find_all("tr", recursive=False)
        previous_rowspan = {}
        for irow, row in enumerate(rows):
            self.rows.append([])
            has_content = False
            colspans = []
            cols = row.find_all(["th", "td"], recursive=False)
            icol_offset = 0
            for icol, cell in enumerate(cols):
                last_column = icol == len(cols)-1
                icol += icol_offset

                colspan = cell.get("colspan", 1)
                if isinstance(colspan, str):
                    try:
                        colspan = int(colspan)
                    except ValueError:
                        colspan = 1
                rowspan = cell.get("rowspan", 1)
                if isinstance(rowspan, str):
                    try:
                        rowspan = int(rowspan)
                    except ValueError:
                        rowspan = 1

                # Add previous rowspan
                if previous_rowspan and icol in previous_rowspan:
                    while icol in previous_rowspan:
                        self.rows[-1].append(previous_rowspan[icol][1])
                        previous_rowspan[icol][0] -= 1
                        if previous_rowspan[icol][0] == 0:
                            previous_rowspan.pop(icol)
                        icol_offset += 1
                        icol += 1

                colspans.append(colspan)
                text = extract_text(cell, **kwargs).strip()
                if not text:
                    text = cell.get_text().strip()
                    if "postproc" in kwargs and kwargs["postproc"]:
                        text = kwargs["postproc"](text)
                    if looks_like_annotation(text) or looks_like_linktodiscard(text):
                        text = ""
                has_content = has_content or bool(text)

                self.rows[-1] += [text] * (colspan)
                # if colspan > 1:
                #     if irow==0 or cell.name != "th":
                #         self.rows[-1] += [text] * (colspan - 1)
                #     else:
                #         self.rows[-1] += [""] * (colspan - 1)
                # self.rows[-1].append(text)

                # Add next rowspan for the last column
                if previous_rowspan and last_column:
                    min_colspan = icol+1
                    max_colspan = max(previous_rowspan.keys())
                    for i in range(min_colspan, max_colspan+1):
                        if i in previous_rowspan:
                            self.rows[-1].append(previous_rowspan[i][1])
                            previous_rowspan[i][0] -= 1
                            if previous_rowspan[i][0] == 0:
                                previous_rowspan.pop(i)
                        else:
                            self.rows[-1].append("")
                
                # Update rowspan for the next rows
                if rowspan > 1:
                    for i in range(colspan):
                        if i+icol in previous_rowspan and colspan > 1: # and collapse_whitespace(previous_rowspan[i+icol][1], 3) == collapse_whitespace(text, 3):
                            print(f"WARNING: Overlapping rowspan for {i+icol} (previous {previous_rowspan[i+icol]}, new: {[rowspan-1, text]})")
                            continue
                        assert i+icol not in previous_rowspan, f"Overlapping rowspan for {i+icol} (previous {previous_rowspan[i+icol]}, new: {[rowspan-1, text]})"
                        previous_rowspan[i+icol] = [rowspan-1, text]
                
                icol_offset += colspan - 1
                icol += colspan - 1

            if irow == 0:
                header_colspans = colspans
            if len(colspans) == 1 and colspans[0] > 1:
                self.rows[-1] = [self.rows[-1][-1] + " " + "|"*(colspans[0]-1)]
            if not has_content:
                self.rows.pop()
                
        # Sometimes there is a big first row, acting as a caption
        if len(header_colspans) == 1 and header_colspans[0] > 1 and self.rows and not self.caption:
            self.caption = self.rows[0][-1].rstrip("|").rstrip()
            self.rows = self.rows[1:]

    def data(self):
        return self.rows


def text_to_table(node, **kwargs):

    if node.find("table", recursive=True):
        text = ""
        give_up = False
        for body in node.find_all("tbody", recursive=False):
            rows = body.find_all("tr", recursive=False)
            for irow, row in enumerate(rows):
                cols = row.find_all(["th", "td"], recursive=False)
                for cell in cols:
                    if cell.find("table", recursive=False):
                        for table in cell.find_all("table", recursive=False):
                            text += text_to_table(table, **kwargs)
                    elif cell.get_text().strip():
                        if len(cols) == 1:
                            text += extract_text(cell, **kwargs) + "\u00A0:\n"
                        else:
                            text = ""
                            give_up = True
                            break
                if give_up:
                    break
            if give_up:
                break
        if text:
            return text
    if node.get("class") and "wikitable" not in node.get("class"):
        return ""
    if node.get("id") in ["toc"]:
        return ""
    ignore_one_cell = bool(not node.get("class") and get_table_border(node))
    text = format_table(
        HtmlTable(node, **kwargs),
        ignore_one_cell=ignore_one_cell,
    )
    return text

def get_table_border(table):
    style = table.get("style")
    if not style:
        return None
    m = re.search(r"border:([^;]+)", style)
    if not m:
        return None
    return m.group(1).strip()


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Clean HTML")
    parser.add_argument("html_file", help="HTML file to clean")
    args = parser.parse_args()

    with open(args.html_file, "r") as f:
        html_string = f.read()
        text = clean_html(html_string)
        print(text)
