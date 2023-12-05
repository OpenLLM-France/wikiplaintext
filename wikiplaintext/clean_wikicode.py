__author__ = "Jérôme Louradour"
__credits__ = ["Jérôme Louradour"]
__license__ = "GPLv3"

import os
import regex as re
import wikitextparser

from clean_common import final_clean

def clean_wikicode(
    text,
    language,
    keep_headers=True,
    keep_notes_as_parenthesis=False,
    keep_tables=False,  # TODO
    orig=None
):
    if language != "fr":
        raise NotImplementedError(f"Language '{language}' not implemented yet")

    global _has_latex
    _has_latex = False

    try:
        text = remove_wiki_tail(text)

        text = remove_wiki_headers(text, keep_headers=keep_headers)

        # Remove '''''bold italic''''', '''bold''', ''italic''
        # Note: this is better than the job done by wikitextparser.remove_markup(..., replace_bolds_and_italics=True)
        #       which remove all the consecutive ''' (for instance in "f'''(x)" -> "f(x)")
        for n in 5, 3, 2:
            # , flags=re.DOTALL)
            text = re.sub(
                rf"('{{{n}}})(?!')(([^'\n<>]|'(?!'))+)(?<!')\1", r"\2", text)

        # Remove html tags
        text = re.sub(r"(?i)<br */?>", "\n", text)
        text = re.sub(r"<![^>]*>", "", text)
        text = re.sub(r"<[^/<>]+/>", "", text)
        if "</" in text:
            # Source: https://www.tutorialstonight.com/html-tags-list-with-examples

            # Remove formatting stuff
            for what in [
                    "h1", "h2", "h3", "h4", "h5", "h6", "header",       # Headers
                    "center", "p",                                      # Formatting paragraph
                    "strong", "em", "mark", "small", "pre", "ins",      # Formatting text
                    "u", "i", "b",
                    "sup", "sub",
                    # Formatting paragraph verbatim
                    "math", "code", "samp", "textarea",
                    "var", "kbd", "pre", "link"                         # Formatting text verbatim
                    "abbr", "s", "dfn", "meter",                        # Indicator
                    "blockquote", "cite", "q",                          # Quotes
                    # "ol", "ul", "li", "dl", "dt", "dd",                 # Lists
                    # TODO: "table" (and related stuff?)
            ]:
                before = after = ""
                if what in ["center", "p"] or what.startswith("h"):
                    before = "\n"
                    after = before
                elif what in ["blockquote", "cite", "q"]:
                    before = "«\u00A0"
                    after = "\u00A0»"
                elif what in ["code", "samp", "textarea"]:  # , "math"?
                    before = "\n```"
                    after = "```\n"
                elif what in ["var", "kbd", "pre"]:
                    before = "`"
                    after = "`"
                elif what == "sup":
                    before = "{{exp|"
                    after = "}}"
                elif what == "sub":
                    before = "{{ind|"
                    after = "}}"
                # text = re.sub(rf"<({what})[^<>]*>([^<>]*)</\1>", r"\n\2\n", text)
                i = re.search(rf"(?i)<\s*{what}[^<>]*>", text)
                while i:
                    j = re.search(r"(?i)</\s*"+what+r"\s*>", text[i.end():])
                    if not j:
                        break
                    content = text[i.end():i.end()+j.start()].strip()
                    if what == "math":
                        content = escape_latex(content)
                    text = text[:i.start()] + before + content + \
                        after + text[i.end()+j.end():]
                    i = re.search(rf"(?i)<\s*{what}[^<>]*>", text)

            # Remove other tags
            #   V1: does not match <> inside <>
            #     text = re.sub(r"<([^ <>]+)( [^<>]+)?>[^<>]*</(?i)\1>", "", text)
            #   V2: can remove too much
            #     text = re.sub(r"<([^ <>]+)( [^<>]+)?>.+?</(?i)\1>", "", text, flags=re.DOTALL)
            i = re.search(r"<[^<>]+>", text)
            offset = 0
            search_start = 0
            while i:
                search_start = offset + i.end()
                complete_what = i.group(0).strip("<>").strip()
                if complete_what:
                    add_as_parenthesis = keep_notes_as_parenthesis and (
                        complete_what == 'ref group="note"')
                    what = re.escape(complete_what.split()[0])
                    j = re.search(rf"(?i)</\s*{what}\s*>", text[search_start:])
                    if j:
                        content = text[offset+i.end():search_start +
                                       j.start()].rstrip(".")
                        if add_as_parenthesis and "(" not in content and ")" not in content and "." not in content:
                            text = text[:offset+i.start()] + " (" + \
                                content + ")" + text[search_start+j.end():]
                            offset = offset + i.start() + 2 + len(content)
                        else:
                            # Remove the text
                            text = text[:offset+i.start()] + \
                                text[search_start+j.end():]
                            offset = offset + i.start()
                    else:
                        offset = search_start
                else:
                    offset = search_start
                i = re.search(r"<[^<>]+>", text[offset:])

        # if re.search("<[^<>]+>", text):
        #     found = list(re.findall("<[^<>]+>", text))
        #     print(f"WARNING: remaining '{found}'\n  in {orig}")

        # Remove links to Images, Categories, etc. [[Fichier:...]], [[Catégorie:...]],
        # text = re.sub(r"\[\[[^\[\]]+:[^\]]*\]\]", "", text)
        # Note1: some "]" can be inside "[[ ... ]]"
        # Note2: somethings should be kept, like "[[Wikipédia:API|prononcé]]", "[[wikt:valentinage|valentinage]]", "[[s:Discours de blah|blah]]""...
        text = re.sub("\[\[:?\w+:[\w'\- ]+\|([\w'\- ]+)\]\]", r"[[\1]]", text)
        i = re.search(r"\[\[[^\[\] ]+:", text)
        MAX_LEN = 1e10
        while i:
            offset = i.end()
            j = re.search(r"\]\]", text[offset:])
            j2 = re.search(r"\n", text[offset:])
            if not j or (j2 and j.start() > MAX_LEN):
                j = j2
            if not j2:
                break
            k = re.search(r"\[\[", text[offset:])
            while k and k.start() < j.start():
                offset += j.end()
                j_prev = j
                j = re.search(r"\]\]", text[offset:])
                j2 = re.search(r"\n", text[offset:])
                if not j or (j2 and j.start() > MAX_LEN):
                    j = j2
                if not j:
                    j = j_prev
                    # This is probably a bug in the wikipedia dump ("]]" is missing -> we skip up to the next line break)
                    # offset = i.end()
                    # j = re.search(r"\n", text[offset:])
                    # This is bad on Trou_noir
                    print("WARNING: Removing", text[i.start():offset+j.end()])
                    break
                k = re.search(r"\[\[", text[offset:])
            # print("Removing", text[i.start():offset+j.end()])
            text = text[:i.start()] + text[offset+j.end():]
            i = re.search(r"\[\[[^\[\] ]+:", text)

        text = wikitextparser.remove_markup(
            text,
            replace_templates=False,
            replace_parser_functions=False,
            replace_bolds_and_italics=False,
            # wikitextparser._wikitext._table_to_text,
            replace_tables=table_to_text if keep_tables else lambda x: "",
            # replace_parameters=True,
            # replace_tags=True,
            # replace_external_links=True,
            # replace_wikilinks=True,
            # unescape_html_entities=True,
            # replace_tables= wikitextparser._wikitext._table_to_text,
        )

        # Format LaTeX curly brackets (1/2)
        while re.search(r"\\[a-z]+\s*\{", text):
            text2 = re.sub(r"(\\[a-z]+\s*)((\{[^\{\}]*\})+)", lambda match: match.group(
                1) + escape_latex(match.group(2)), text)
            if text == text2:
                break
            text = text2

        # Remove infoboxes and so on ({{Sous-page de documentation}}...)
        while re.search(r"\{\{", text):
            text2 = re.sub(r"(\s?)\{\{([^\{\}]*)\}\}([\s,\\.:;\\?!]?)",
                           lambda x: process_template_fr(x, orig), text)
            if text == text2:
                break
            # Avoid infinite loop
            assert text != text2, f"Entered an infinite loop! around {text[max(0,text.index('{{')-10):text.index('{{')+200]}"
            text = text2

        i = re.search(r"\{\{", text)
        while i:
            j = re.search(r"\}\}", text[i.end():])
            if not j:
                break
            content = text[i.end():i.end()+j.start()]
            content = process_template_fr(content, orig)
            text = text[:i.start()] + content + text[i.end()+j.end():]

        if "{{" in text:
            i = text.index("{{")
            print(
                (f"WARNING: Remaining curly brackets: '{text[max(0,i-10):i+200]}' in {orig}"))

        # Recover LaTeX curly brackets (2/2)
        if _has_latex:
            text = text.replace("OUVRELATEX", "{")
            text = text.replace("FERMELATEX", "}")

        if "[[" in text:
            i = text.index("[[")
            print(
                f"WARNING: Remaining double brackets: '{text[max(0,i-10):i+200]}' in {orig}")

        text = remove_emoji(text)

        return final_clean(text)

    except (Exception, KeyboardInterrupt) as err:
        raise RuntimeError(f"Failed to process {orig}") from err


def table_to_text(table) -> str:
    data = [
        [(cell if cell is not None else '') for cell in row]
        for row in table.data()
    ]
    if not data:
        return ''
    widths = [0] * len(data[0])
    for irow, row in enumerate(data):
        if irow == 0:
            continue
        for ri, d in enumerate(row):
            widths[ri] = max(widths[ri], len(d.strip()))
    caption = table.caption
    if len(widths) == 1:
        return (
            (f'\n{caption} :\n' if caption is not None else '')
            + '\n'
            + '\n'.join(
                "* " + "* ".join(f"{remove_line_breaks(d):{w}}" for (w, d) in zip(widths, r) if w > 0) if irow > 0 else r[0] for irow, r in enumerate(data)
            )
            + '\n'
        )
    return (
        (f'\n{caption} :\n' if caption is not None else '')
        + '\n'
        + '\n'.join(
            "| " + " | ".join(f"{remove_line_breaks(d):{w}}" for (w, d) in zip(widths, r) if w > 0) + " |" for irow, r in enumerate(data)
        )
        + '\n'
    )


def remove_line_breaks(text):
    return text.replace("\n", " ").strip()


def remove_wiki_headers(text, keep_headers):
    if keep_headers:
        # Note : important to use unbreakable spaces
        return re.sub(r"={2,}\s+([^=]*)\s+={2,}", r"\1\u00A0:", text)
    return re.sub(r"={2,}\s+[^=]*\s+={2,}", "", text)


def remove_wiki_tail(text):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if re.match(r"===?\s*(Notes|Notes et références|Références|Voir aussi|Liens externes|Annexes)\s*===?\s*$", line):
            return "\n".join(lines[:i])
    return text


def process_template_fr(match, orig=None):
    global _template_logs_data, _template_logs_idx, _template_logs_flush_every
    global _has_latex
    if isinstance(match, str):
        inside = match
        before = after = ""
    else:
        before = match.group(1)
        inside = match.group(2)
        after = match.group(3)
    fields = inside.split("|")
    fields = [f.strip() for f in fields if f.strip()]
    if len(fields) == 0 or fields[0] == "...":
        return ""
    first = fields[0].replace("_", " ").strip().rstrip("-").strip(".").lower()

    nfirst = fields[0].lower().replace(" ", "_")+":"+str(len(fields))

    # TODO:
    # {{population suisse|CH-GL|Glaris Nord}} -> 19428
    # {{population suisse|CH-GL|ofs=1632}} -> 12515

    output = None
    if first in [
        "sfn", "ouvrage",  # References
        "ébauche",  # Tags
        "drapeau",  "flagicon", "usa",  # Emoji (flags)
        "maillot",  # Emoji (others)
        "tableau", "climat",  # tables
        "attention",
        "ancre",
        "portail",
        "confusion",
        "note", "clr", "refinc",
        "sommaire",
        "g",
    ] or \
        first.startswith("redirect") or \
        first.startswith("article") or \
        first.startswith("homon") or \
        first.startswith("carte") or \
        first.startswith("historique") or \
        first.startswith("titre") or \
        first.startswith("sous-titre") or \
        first.startswith("détail") or \
        first.startswith("média") or \
        first.startswith("loupe") or \
        first.startswith("médaille") or \
        "colonne" in first or "catégorie" in first or "frise" in first or \
        "protection" in first or "protégé" in first or "tête" in first or \
            "pertinence" in first:
        # assert len(fields) > 1, f"Failed to process {{{{{inside}}}}}"
        output = ""
    for start in ["palette", "autre", "élu", "#tag", "voir"]:
        if first.startswith(start):
            output = ""
            break

    if output is None:
        if re.search(r"^[a-z]* ?\bà\b", first):  # à vérifier, à sourcer, etc.
            output = ""
        # Flags (USA-d, FRA-d, JPN-d, etc.)
        elif re.match(r"^ *[A-Z]{3}-[a-z] *$", inside):
            output = ""
        elif len(fields) == 1 and first in ["références"]:  # Internal links
            output = ""
        elif len(fields) == 1 and first.startswith("default"):  # DEFAULTSORT:Esther, Joy
            output = ""
        elif len(fields) == 1 and first.endswith("homonymes"):  # surnoms homonymes
            output = ""

        elif first in ["formule"] and len(fields) >= 2:
            output = fields[1]

        elif first == "exergue" and len(fields) >= 2:
            output = "«\u00A0" + fields[1].strip() + "\u00A0»"
            if len(fields) > 2:
                output += "\n—\u00A0" + ", ".join(fields[2:4]).strip()
            output += "\n"

        elif first == "vers":
            if len(fields) > 1:
                output = fields[1].strip()
                if output.startswith("texte="):
                    output = output.split("=", 1)[-1]
                for i, post in enumerate(fields[2:]):
                    if "=" in post:
                        post = post.split("=", 1)[-1]
                    if i == 0:
                        output += "\n—\u00A0" + post
                    else:
                        output += ", " + post
            output += "\n"

        elif first.startswith("cita"):
            # {{Citation étrangère|langue=it|Nachue...}}
            if len(fields) >= 3 and "=" in fields[1]:
                fields = fields[1:]
            if len(fields) == 1:
                output = ""
            else:
                citation = "«\u00A0"+fields[1].strip()+"\u00A0»"
                if len(fields) > 2:
                    citation += "\n—\u00A0" + \
                        ", ".join([f.strip() for f in fields[2:4]]).strip()
                output = citation
        elif first == "début citation" and len(fields) == 1:
            output = "«\u00A0"
        # {{fin citation|Le 6 novembre 1916, combats du 24 au 30 octobre 1916 à Verdun, rive droite secteur de Douaumont}}
        elif first == "fin citation":
            output = "\u00A0»" + ((" —\u00A0" + ", ".join(fields[1:]).replace(
                "\n", " ").strip()+"\n") if len(fields) >= 1 else "")

        elif first in ["incise"]:
            if len(fields) == 1:
                output = ""
            else:
                suffix = "\u00A0—"
                if len(fields) == 3 and fields[2] in ["fin"]:
                    suffix = ""
                output = "—\u00A0" + fields[1] + suffix

        elif fields[0].startswith("--"):
            output = "—"
            if len(fields) > 1:
                output += "\u00A0" + ", ".join(fields[1:2]).strip()
                if isinstance(match, str):
                    ending = fields[0] in ["--"]
                else:
                    ending = bool(after and re.match("\s", after[0]))
                    if ending and after[0] == "\n":
                        ending = "."
                if ending:
                    output += "\u00A0—" if (ending is True) else ending

        # Things like {{,}}, {{'}}
        elif len(fields) == 1 and re.match(r"^[^\w]*$", first):
            if first in ["'"]:
                output = fields[0]
            else:
                output = ""

        elif fields[0] in ['"', "graphie"]:
            opening = {
                '"': "«",
                "graphie": "‹",
            }.get(fields[0], '"')
            ending = {
                '"': "»",
                "graphie": "›",
            }.get(fields[0], '"')
            output = opening + "\u00A0" + \
                ", ".join(fields[1:2]).strip() + "\u00A0" + ending

        # {{Jumelage|Huesca|Espagne|année=1964|jour=7|mois=mai}}
        elif first == "jumelage" and len(fields) >= 2:
            output = fields[1]
            if len(fields) >= 3 and "=" not in fields[2]:
                output += " (" + fields[2] + ")"
            for f in fields[2:]:
                if f.lower().startswith("année="):
                    output += ", depuis " + f.split("=")[-1].strip()

        # {{s|XIX}} -> XIXe siècle, {{s-|XVI|e}} -> XVIe siècle {{s mini-|XVI|e}} -> XVIe
        elif first.rstrip("-") in ["", "s", "s mini", "-s", "-s mini", "sap", "sav"]:
            fields = normalize_field_with_indices(fields[1:])
            fields = [f for f in fields if f.strip() not in (
                "e", "er", "ème", "", "-", "siècle", "s", "S")]
            before_jc = (first in ["", "sav"] or first.startswith("-"))
            if len(fields) == 1:
                try:
                    output = to_century(
                        fields[0], use_unit="mini" not in first, before_jc=before_jc, orig=inside)
                    if first in ["sap"]:
                        output += " après J.-C."  # "ap. J.-C."
                except Exception as err:
                    nfirst += ":FAIL:Err1"
            elif len(fields) == 2:  # {{s|XVIII|XIX}}
                try:
                    output = to_century(fields[0], use_unit=False, orig=inside) \
                        + " et " \
                        + to_century(fields[-1], before_jc=before_jc,
                                     suffix="s", orig=inside)
                except Exception as err:
                    nfirst += ":FAIL:Err2"
            else:
                nfirst += ":FAIL:"+str(len(fields))
                output = to_ieme(" ".join(fields))

        # {{sp-|I|et le|IV}} -> Ier et le IVe siècle / {{sp-|VI|e|-|VII|e|s}} -> VIe - VIIe siècles
        elif first.rstrip("-") in ["sp", "-sp", "s2", "-s2"]:
            before_jc = first.startswith("-")  # or "-" in fields
            if len(fields) == 1:
                output = fields[0]
            else:
                fields = normalize_field_with_indices(fields[1:])
                fields = [f for f in fields if f.strip() not in (
                    "e", "er", "ème", "", "siècle")]
                suffix = ""
                if fields[-1] == "s":
                    suffix = "s"
                    fields.pop(-1)
                while "s" in fields:
                    fields.remove("s")
                if fields[0] == "-":
                    fields.pop(0)
                if fields[-1] == "-":
                    fields.pop(-1)
                if len(fields) in [2, 3]:
                    try:
                        if len(fields) == 2:
                            suffix = "s"
                        output = to_century(fields[0], use_unit=False, orig=inside) \
                            + " " + ("et" if len(fields) == 2 else fields[1].replace("-", "–")) + " " \
                            + to_century(fields[-1], before_jc=before_jc, suffix=suffix, orig=inside)
                    except Exception as err:  # {{sp|XV|e|au|6=s|XVII|e}}
                        nfirst += ":FAIL:Err"
                else:
                    nfirst += ":FAIL:"+str(len(fields))
                    output = to_ieme(" ".join(fields))

        # {{5e|armée}} -> 5e armée, {{1er }} -> 1er  (should be upper letter affer), {{1er mai}}
        elif re.match("^\d+[eèr]+ *$", first) and len(fields) <= 2:
            nfirst = "ORDINAL:"+str(len(fields))
            fields[0] = to_ieme(fields[0].lower())
            output = " ".join(fields)

        # {{1er mai}}
        elif re.match("^\d+[eèr]+ +", first) and len(fields) <= 2:
            nfirst = "ORDINAL_PREFIX:"+str(len(fields))
            number, other = fields[0].replace("_", " ").split(" ", 1)
            fields[0] = to_ieme(number.lower()) + " " + other
            output = " ".join(fields)

        # {{machin 1er}}
        elif re.match("^.+ \d+[eèr]+ *$", first) and len(fields) <= 2:
            nfirst = "ORDINAL_SUFFIX:"+str(len(fields))
            subfields = fields[0].replace("_", " ").split(" ")
            fields[0] = " ".join(subfields[:-1]) + " " + \
                to_ieme(subfields[-1].lower())
            output = " ".join(fields)

        elif first in ["e", "er", "r", "ème", "eme", "°", "o"] and len(fields) == 1:
            output = to_ieme(fields[0])

        elif first in ["r"]:  # {{r.|270|310}} -> 270-310 (range)
            if len(fields) in [2, 3]:
                output = "-".join(fields[1:])
            else:
                nfirst += ":FAIL"

        # TODO: list languages
        # {{japonais|Mausolée impérial Tama|多摩 御陵|''Tama Goryō''}} / {{japonais|''Tama-no-Higashi-no-Misasagi''|多摩 東 陵}}
        elif first in ["japonais"]:
            if len(fields) == 1:
                output = fields[0]
            else:
                output = fields[1]
                if len(fields) > 2:
                    output += " ("+", ".join(fields[2:])+")"

        elif first in [
            "lang", "transl", "langue", "en langue", "en lang",
            "ancrage",
            "lnobr",
            "anglais",
            "code aviation",
        ] or first.startswith("lang-"):  # {lang|de|...} -> ..., {lang|ar|dir=rtl|...} -> ..., {lang-ar|...} -> ...
            output = fields[-1]
            if output.startswith("texte="):
                _, output = output.split("=", 1)

        elif first in ["arabe"]:
            output = fields[1]
            if len(fields) > 2:
                prefix = first
                if not prefix.startswith("en "):
                    prefix = "en " + prefix
                output += " ("+prefix+" : "+", ".join(fields[2:])+")"

        elif first.startswith("en "):  # {{en espagnol|}} {{en italien|}}
            output = fields[0]
            if len(fields) > 1:
                output += " : " + ", ".join(fields[1:])
            output = "(" + output.strip() + ")"

        elif first.split()[0] in ["grec", "latin"]:
            output = " / ".join(fields[1:])

        # {{ord|1}} -> 1er
        elif first in ["ord", "ordinal"] and len(fields) >= 2:
            number = fields[1]
            if number == "1":
                number = "1ᵉʳ"
            else:
                number = number + "ᵉ"
            output = (number + " " + " ".join(fields[2:])).strip()

        elif len(fields) == 1 and re.match("^[er]+ *$", first):  # {{e}}
            output = to_exp(fields[0])

        elif first in ["n°"] or first.startswith("numéro"):
            output = "n° " + "-".join(fields[1:]).strip()

        elif first in ["N°"] or first.startswith("Numéro"):
            output = "N° " + "-".join(fields[1:]).strip()

        # {{exp|XXX}} -> ^XXX / {{ind|K}} -> _XXX
        elif first in ["exp", "exposant"]:
            output = " ".join([to_exp(x) for x in fields[1:]]).strip()

        elif first in ["ind"]:  # {{ind|K}} -> _XXX
            output = " ".join([to_ind(x) for x in fields[1:]]).strip()

        elif len(fields) == 1 and re.match("\d+$", first):
            nfirst = "CARDINAL:"+str(len(fields))
            output = "^" + " ".join(fields)

        elif first == "mathpi":
            output = "π"
        elif first in ["=", "*", "+"] and len(fields) == 1:
            output = first.re

        elif first in ["racine", "sqrt"]:
            if len(fields) == 1:
                output = "√"
            else:
                if len(fields) == 3:
                    prefix = to_exp(fields[2].replace("n=", ""))
                elif len(fields) == 2:
                    prefix = ""
                else:
                    nfirst += ":FAIL"
                    prefix = None
                if prefix is not None:
                    output = prefix + "√" + fields[1].strip()

        elif first in ["pourcentage"]:
            try:
                output = to_percents(fields[1:])
            except Exception as err:
                nfirst += ":FAIL:" + \
                    str(type(err)).replace("<class '", "").replace("'>", "")

        elif first in ["frac", "sfrac"] and len(fields) in [2, 3, 4]:
            if len(fields) == 2:
                fields = [fields[0], "1"] + fields[1:]
            if output is None:
                output = to_exp(fields[1]) + "⁄" + to_ind(fields[2])

        elif first in ["fchim", "formule chimique"]:
            nfirst = "fchim:"+str(len(fields) % 2)
            output = to_chemical_formula("|".join(fields[1:]))
        elif first in ["o2", "co2"]:
            output = to_chemical_formula(first.upper()[:-1]+"|"+first[-1])
        elif first in ["h2o"]:
            output = to_chemical_formula("H|2|O")

        elif first in ["musique"] and len(fields) == 2:
            output = fields[1]
            if output == "b":
                output = "♭"
            if output == "#":
                output = "♯"

        # {{formatnum:123456789}} -> 123 456 789
        elif first.startswith("formatnum:") and len(fields) == 1:
            nfirst = "FORMATNUM:"+str(len(fields))
            alright = True
            try:
                number = str(int(fields[0].split(":", 1)[-1])).strip()
            except Exception as err:
                try:
                    number = str(float(fields[0].split(":", 1)[-1])).strip()
                except Exception as err:
                    nfirst = "FORMATNUM:FAIL:" + \
                        str(len(fields))+":"+str(type(err)
                                                 ).replace("<class '", "").replace("'>", "")
                    print(f"WARNING: Failed to process {{{{{inside}}}}}")
                    number = fields[0].split(":", 1)[-1].strip()
                    alright = False
            if alright:
                output = formatnum(number, language="fr")
            else:
                output = number

        elif len(fields) <= 3 and first in _currencies:
            if len(fields) == 1:
                output = _currencies[first]
            else:
                output = fields[1] + " " + _currencies[first]

        elif len(fields) <= 3 and max([first.startswith(beg) for beg in _currencies]):
            for beg in _currencies:
                if first.startswith(beg) and (beg != "livre" or first == "livre sterling"):
                    if len(fields) == 1:
                        output = _currencies[beg]
                    else:
                        output = fields[1] + " " + _currencies[beg]

        elif first in ["heure"]:
            try:
                output = to_time(fields[1:])
            except Exception as err:
                nfirst += ":FAIL:" + \
                    str(type(err)).replace("<class '", "").replace("'>", "")

        elif first.startswith("année") and len(fields) > 1:
            output = " ".join(fields[1:])

        elif first in ["unité", "unité/2", "tmp", "nombre", "nb", "nobr", "nobr rom", "math", "température", "temp"] or first.startswith("date"):
            if first in ["nombre", "nb", "nobr", "nobr rom"]:
                fields[1:] = normalize_field_with_indices(fields[1:], [])
            elif not first.startswith("unité"):
                fields[1:] = normalize_field_with_indices(fields[1:], "all")
            expected_len = {
                # "unité":[2,3],
                # "nombre":[2,3],
                # "date":4,
            }.get(first)
            format_fields = {
                # "unité": format_unit_fields,
            }.get(first)
            if first.startswith("unité"):
                format_fields = format_unit_fields
            if first.startswith("date"):
                format_fields = format_date_fields
            expected_len_strict = expected_len
            try:
                assert not expected_len_strict or len(
                    fields) == expected_len, f"Failed to process {{{{{inside}}}}} ({expected_len_strict=}, {expected_len=}, {len(fields)})"
                if not expected_len:
                    expected_len = len(fields)
                assert len(
                    fields) >= expected_len, f"Failed to process {{{{{inside}}}}}"
                if format_fields is not None:
                    fields = format_fields(fields)
                output = " ".join(fields[1:expected_len+1])
            except Exception as err:
                nfirst += ":FAIL:" + \
                    str(type(err)).replace("<class '", "").replace("'>", "")

        elif first in ["dunité"] and len(fields) in [3, 4]:
            fields = format_unit_fields(fields)
            output = fields[1] + " × " + " ".join(fields[2:])

        elif first in ["tunité"] and len(fields) in [4, 5]:
            fields = format_unit_fields(fields)
            output = fields[1] + " × " + fields[2] + \
                " × " + " ".join(fields[3:])

        # Ignored formatting
        elif max([first.startswith(beg) for beg in
                  ["énoncé", "mvar", "retrait", "liste", "soulign", "surlign", "barr", "légende"]]):
            # TODO underline / overline / strike
            if len(fields) == 1:
                output = ""
            else:
                output = " ".join(fields[1:]).strip()

        # TODO: check if other start/end table like that
        elif first in ["fs player"]:
            d = to_dict(fields[1:])
            selected = []
            for kin, kout in [("no", "n° "), ("name", None), ("pos", "position"), ("nat", "nationalité")]:
                if kin in d:
                    if kout:
                        selected.append(kout + " " + d[kin])
                    else:
                        selected.append(d[kin])
            output = "* " + ", ".join(selected)
        elif first.startswith("fs "):  # {{Fs start}} / {{Fs end}}
            output = ""

        elif first in ["feff joueur"]:
            d = to_dict(fields[1:])
            selected = []
            for kin, kout in [("num", "n° "), (["prénom", "nom"], None), ("pos", None), ("nat", None)]:
                if not isinstance(kin, list):
                    kin = [kin]
                value = " ".join([d.get(k, "") for k in kin]).strip()
                if value:
                    if kout:
                        selected.append(kout + " " + value)
                    else:
                        selected.append(value)
            output = "* " + ", ".join(selected)
        elif first.startswith("feff "):  # {{Feff début}} / {{Feff fin}}
            output = ""

        elif "JC" in fields[0] and len(fields) == 1:
            if first.replace(" ", "") == "avjc":
                output = "avant J.-C."  # "av. J.-C."
            elif first.replace(" ", "") == "apjc":
                output = "après J.-C."  # "ap. J.-C."
            else:
                raise NotImplementedError(f"Unknown JC {fields[0]}")

        # p., cf., ...
        elif first in ["cf", "p", "chap", "syn", "vol", "et al"]:
            output = (f"{first}." + " " + " ".join(fields[1:])).strip()

        elif first in ["nb p"] and len(fields) == 2:  # {{nb p.|1}} -> 1 p.
            output = fields[1] + " " + first.split()[-1]+"."

        elif first in ["ch"]:
            output = (f"chap." + " " + " ".join(fields[1:])).strip()

        elif first in ["etc", ", etc"]:
            output = ", etc."

        elif first in ["ex"]:
            output = "ex. :"

        # https://fr.wikipedia.org/wiki/Mod%C3%A8le:Exemple
        elif first in ["exemple"] and len(fields) >= 2:
            for f in fields[1:]:
                if f.startswith("1="):
                    fields[1] = f[2:]
                    break
            output = "\nExemple:\n"+fields[1]+"\n"

        elif first in ["coll"] and len(fields) >= 2:  # collection...
            output = (" ".join(fields[1:])).strip()

        elif first.startswith("col") and len(fields) == 1:  # col-2...
            output = ""

        elif first in ["états-unis"] and len(fields) == 1:
            output = fields[0]

        # {{ISBN|978-2-221-10003-3}} -> (ISBN 978-2-221-10003-3)
        elif first in ["isbn"]:
            output = "(" + " ".join([fields[0].upper()
                                     ] + fields[1:]).strip() + ")"

        elif first in _languages:
            output = "(" + " ".join(fields).strip() + ")"

        elif first in _genders and len(fields) == 1:
            output = "(" + _genders[first] + ")"

        # {{noble|Alexandre VI (pape)}}
        elif first in ["noble", "monarque"] or first.startswith("souverain"):
            output = " ".join([f.split("(")[0] for f in fields[1:]]).strip()

        # Référence nécessaire, pas clair, passage évasif, c'est-à-dire? ...
        elif max([first.startswith(beg) for beg in [
            "comment", "quand", "où", "qui", "quoi", "lequel", "lesquel", "laquel", "pourquoi"
        ]]) or \
                first in ["refnec", "citnec", "pas clair", "c'est-à-dire"] or "réf" in first or "ref" in first or first.startswith("passage") or first.startswith("style"):
            fields[1:] = normalize_field_with_indices(fields[1:], ignore="all")
            if len(fields) == 1:
                output = ""
            else:
                output = fields[1].strip()

        elif first in ["apib", "phonétique"]:  # prononciation
            output = ", ".join(fields[1:])

        elif first in ["msapi"]:  # prononciation
            output = "[" + "".join(fields[1:]).lstrip("[").rstrip("]") + "]"

        elif first in ["prononciation"]:
            if len(fields) >= 3:
                # The first one is a file, the second is a description of the file
                output = " "+fields[2]+" "
            else:
                output = ""

        # prononciation
        elif first.startswith("ipa") or first in ["api-fr", "prononciation api"]:
            output = "[" + ", ".join(fields[1:2]).lstrip("[").rstrip("]") + "]"

        elif (first.startswith("abré") or first.startswith("abbr")) and len(fields) > 1:  # prononciation
            output = fields[1]
            if len(fields) > 2 and "discrète" not in fields[0]:
                output += " (" + ", ".join(fields[2:]) + ")"

        # {{page h'|hôtel-Dieu}}
        elif first.startswith("page ") and len(fields) in [2, 3]:
            # other link format
            output = fields[-1].strip()

        elif first.endswith("api"):
            output = ""

        elif first in ["écrit"]:
            d = to_dict(fields[1:])
            titre_fr = d.get("titre fr", "").strip()
            titre = d.get("titre", "").strip()
            year_fr_suffix = (", "+d.get("année fr", "").strip()).rstrip(", ")
            year_suffix = (", "+d.get("année", "").strip()).rstrip(", ")
            language_prefix = d.get("langue", "").strip()
            if language_prefix:
                language_prefix = "("+language_prefix+") "
            output = ""
            if titre_fr:
                output = titre_fr + (year_fr_suffix or year_suffix)
                if titre:
                    output += " (" + language_prefix + titre + \
                        (year_suffix or year_fr_suffix) + ")"
            elif titre:
                output = titre + (year_fr_suffix or year_suffix)

        elif first.startswith("lien"):
            d = to_dict(fields[1:])
            nfirst += ":"+",".join(sorted(d.keys()))
            for k in ["fr", "texte", "trad"]:
                if k in d:
                    output = d[k]
                    break
            if output is None:
                if len(fields) > 1 and "=" not in fields[1]:
                    output = fields[1]
                else:
                    output = ""

        elif first.startswith("population"):
            if "dernière année" in first and "france" in first:
                output = "2020"  # UGLY Cheat
            elif max([s in first for s in ["section", "graphique", "intro", "tableau"]]):
                output = ""
            else:
                _has_latex = True
                output = "OUVRELATEXOUVRELATEX" + \
                    "|".join(fields) + "FERMELATEXFERMELATEX"

        elif first.startswith("pourcent") or first.startswith("epci"):
            _has_latex = True
            output = "OUVRELATEXOUVRELATEX" + \
                "|".join(fields) + "FERMELATEXFERMELATEX"

        elif first in ["hms", "uss"]:
            output = " ".join(fields[0:2])

        # Those ones must be at last (could catch other special cases otherwise)

        # At last (other début / fin not ignored)
        elif first.startswith("début") or first.startswith("fin"):
            output = ""

        # {{XXIe}}
        elif re.match("^[LIVX]+[èmer]+ *$", fields[0]) and len(fields) <= 2:
            nfirst = "ROMAN_ORDINAL:"+str(len(fields))
            fields[0] = to_ieme(fields[0])
            if len(fields) == 2 and fields[1] == "s":
                fields = fields[:1]
            output = " ".join(fields)

        # {{Ier siècle}}
        elif re.match("^[LIVX]+[èmer]+ +", fields[0].replace("_", " ")) and len(fields) <= 2:
            nfirst = "ROMAN_ORDINAL_PREFIX:"+str(len(fields))
            number, other = fields[0].replace("_", " ").split(" ", 1)
            fields[0] = to_ieme(number) + " " + other
            output = " ".join(fields)

        # {{Ier siècle}}
        elif re.match("^-[LIVX]+[èmer]+ siècle", fields[0].replace("_", " ")) and len(fields) <= 2:
            nfirst = "ROMAN_NEGATIVE_ORDINAL_PREFIX_CENTURY:"+str(len(fields))
            number, other = fields[0][1:].replace("_", " ").split(" ", 1)
            fields[0] = to_ieme(number) + " " + other
            output = " ".join(fields) + " avant J.-C."

        # {{François Ier}}
        elif re.match("^.+ [LIVX]+[èmer]+ *$", fields[0].replace("_", " ")) and len(fields) <= 2:
            nfirst = "ROMAN_ORDINAL_PREFIX:"+str(len(fields))
            subfields = fields[0].replace("_", " ").split(" ")
            fields[0] = " ".join(subfields[:-1]) + " " + to_ieme(subfields[-1])
            output = " ".join(fields)

        # {{XXIe}}
        elif re.match("^[LIVX]+ *$", fields[0]) and len(fields) <= 2:
            nfirst = "ROMAN_CARDINAL:"+str(len(fields))
            output = " ".join(fields)

        # Mlle, Mgr, ... (should be upper letter affer)
        elif len(fields) == 1 and (re.match(r"^[A-Z][a-z]+\s*\.?\s*$", fields[0]) or re.match(r"^[M]\.\s*$", fields[0])):
            output = " ".join(fields)

    if output is None:
        keep_it = (before.endswith(" ") and after and after[0] in " .,;:!?")

        # Last chance to force keep!!
        if first in ["ufc"]:
            keep_it = True
            output = " ".join(fields).strip()
        elif keep_it:
            nfirst += ":KEEP"
        else:
            nfirst += ":DISCARD"
    else:
        keep_it = (output != "")
    new = nfirst not in _template_logs_data
    if new:
        if not isinstance(match, str):
            start, end = match.span()
            start = max(0, start-30)
            end += 30
            example = match.string[start:end].replace("\n", "\\")[:200]
        else:
            # example = match.replace("\n","\\n")[:200]
            example = None
        if example is not None:
            pageref = os.path.splitext(os.path.basename(orig))[
                0] if orig else ""
            _template_logs_data[nfirst] = [1, keep_it, unescape_latex(
                output).replace("\n", "\\") if output else output, example, pageref]
    else:
        _template_logs_data[nfirst][0] += 1

    if _template_logs_filename:
        _template_logs_idx += 1
        if _template_logs_idx % _template_logs_flush_every == 0:
            flush_template_logs()

    if output is None:
        # if "\n" in inside and not keep_it:
        #     print(f"WARNING: {'keeping' if keep_it else 'discarding'} '{{{{{inside}}}}}'\n  in {orig}")

        if keep_it:
            output = " ".join(fields).strip()
        else:
            output = ""

    if output:
        return before + output + after

    # In case of empty output, we remove empty lines
    if before.endswith("\n") and after and after[0] in "\n":
        before = before[:-1]
    elif before.endswith(" ") and after and after[0] in " .,;:!?":
        before = before[:-1]
    elif before and before[-1] in "\n(" and after.startswith(" "):
        after = after[1:]
    return before + after


_template_logs_filename = None
_template_logs_idx = 0
_template_logs_flush_every = 1000
_template_logs_data = {}


def set_template_logs(fn, flush_every=1000):
    global _template_logs_filename, _template_logs_flush_every, _template_logs_idx, _template_logs_data
    _template_logs_filename = fn
    _template_logs_flush_every = flush_every
    _template_logs_idx = 0
    _template_logs_data = {}


def flush_template_logs():
    fid = open(_template_logs_filename, "w")
    for k in sorted(_template_logs_data.keys(), key=lambda k: _template_logs_data[k][0], reverse=True):
        n, ki, o, example, pageref = _template_logs_data[k]
        o = o if o is not None else "UNKNOWN"
        print(
            f"{n:6d} {k[:20]:20} {'KEEP' if ki else 'DISCARD':7} {o[:30]:30} {pageref:40} {example}", file=fid)


_has_latex = False


def escape_latex(text):
    global _has_latex
    _has_latex = _has_latex or ("{" in text or "}" in text)
    return text.replace("{", "OUVRELATEX").replace("}", "FERMELATEX")


def unescape_latex(text):
    text = text.replace("OUVRELATEX", "{")
    text = text.replace("FERMELATEX", "}")
    return text


def to_century(contents, use_unit=True, before_jc=False, suffix="", language="fr", orig=None):
    assert language == "fr"
    unit = " siècle" if use_unit else ""
    res = ""
    if contents.startswith("-"):
        contents = contents[1:]
        if before_jc is None:
            before_jc = True
    for content in contents.split("-"):
        content = content.strip("èmers").upper()
        if res:
            res += " et "
            if unit and not unit.endswith("s"):
                unit += "s"
        assert re.match(r"^[LIVX]+$", content) or re.match(r"^\d+$",
                                                           content), f"Failed to process '{content}' ({orig})"
        if content == "I":
            res += "Iᵉʳ"
        else:
            res += content + "ᵉ"
    if suffix:
        unit += suffix
    if use_unit:
        if before_jc:
            unit += " avant J.-C."  # "av. J.-C."
    return res + unit


def to_chemical_formula(formula):
    elements = re.split("([\(\)\[\]\{\}])", formula)
    formula = ""
    offset = 0
    previous_offset = 0
    for e in elements:
        if e in [")", "]", "}"]:
            offset = previous_offset
            formula += e
            continue
        new_e = ""
        for i, x in enumerate([xi for xi in e.split("|") if xi.strip()]):
            if (i+offset) % 2 == 0:
                new_e += x
            else:
                new_e += to_ind(x)
            previous_offset = i
        formula += new_e
    return formula


def to_time(fields):
    fields = normalize_field_with_indices(fields, ignore=["durée"])
    numbers = []
    suffix = ""
    for f in fields:
        f = f.replace("-", ".")
        try:
            if re.match(r"^[A-Z]+$", f):  # UTC, GMT, CDST, UT, ...
                f = "fuseau="+f
            if f.startswith("fuseau="):
                suffix = " " + f.split("=", 1)[-1].upper()
            # elif "=" in f: # durée=oui
            #     continue
            else:
                x = checked_number_fr(f)
                numbers.append(x)
        except Exception as err:
            numbers = fields
            break
    assert len(numbers) in [1, 2, 3, 4], f"Unexpected time format {fields}"
    output = (
        (numbers[0] + " h " if numbers[0].strip("0") else "") +
        (numbers[1] + " min " if (len(numbers) >= 2 and numbers[1].strip("0")) else "") +
        (numbers[2] + " s " if (len(numbers) >= 3 and numbers[2].strip("0")) else "") +
        (numbers[3] if (len(numbers) >= 4 and numbers[3].strip("0")) else "")
    ).strip()
    if output.endswith(" min"):
        output = output[:-4].strip()
    output += suffix
    return output


def to_percents(fields):
    fields = normalize_field_with_indices(fields, ignore=["pad"])
    assert len(fields) in [1, 2, 3]
    numerator = checked_number_fr(fields[0], head=float)
    denominator = 1
    round_level = 1
    if len(fields) > 1 and fields[1].strip("0"):
        numerator *= 100
        denominator = checked_number_fr(fields[1], head=float)
    if len(fields) > 2 and fields[2].strip("0"):
        round_level = checked_number_fr(fields[2], head=int)

    percent = round(numerator/denominator, round_level)
    if percent % 1 == 0:
        percent = int(percent)
    return str(percent).replace(".", ",") + " %"


def checked_number_fr(x, head=str):
    if not x:
        return "0"
    if "/" in x:
        a, b = x.split("/")
        a, b = float(a), float(b)
        if head == str:
            return x
        else:
            return head(round(a/b, 1))
    else:
        x = float(x.replace(",", "."))
        if x % 1 == 0:
            return head(int(x))
        elif head == str:
            return str(x).replace(".", ",")
        else:
            return head(str(x))


def normalize_field_with_indices(fields, ignore=[], keep=[], default=""):
    new_fields = []
    new_fields_2 = []
    has_idx = False
    extras = []
    for f in fields:
        if re.match("^\d+=", f):
            idx, v = f.split("=", 1)
            idx = int(idx)-1
            while len(new_fields) <= idx:
                new_fields.append(default)
            new_fields[idx] = v
            has_idx = True
        elif re.match(r"^\w+=", f):
            k, v = f.split("=", 1)
            if (ignore != "all" or k in keep) and k not in ignore:
                extras.append(k+"="+v)
                new_fields_2.append(f)
        else:
            new_fields.append(f)
            new_fields_2.append(f)
    if has_idx:
        return new_fields + extras
    return new_fields_2


def formatnum(number, language="fr"):
    assert language == "fr"
    number = number.replace(".", ",")
    f = number.split(",")
    coma = "," + ",".join(f[1:]) if len(f) > 1 else ""
    number = f[0]
    # Add space every 3 digits
    number = number[::-1]
    # Unbreakable spaces
    number = "\u00A0".join([
        number[i:i+3]
        for i in range(0, len(number), 3)
    ])[::-1]
    return number + coma


def format_unit_fields(f):
    return [format_unit_field(x) for x in f]


def format_unit_field(f):
    if f.startswith("e="):
        return " × 10" + to_exp(f.split("=", 1)[1])
    # Transform floating numbers, and "à="
    return f.replace(".", ",").replace("=", " ")


def format_date_fields(f):
    if min([s.isdigit() for s in f[1:]]):
        return [f[0], "".join([("/" if i > 0 else "") + x.strip().strip("/") for i, x in enumerate(f[1:])])]
    return f


_currencies = {
    "euro": "€",
    "dollar": "$",
    "livre": "£",
    "yen": "¥",
    "rouble": "₽",
    "franc": "₣",
    "mark": "ℳ",
    "peso": "$",
    "dinar": "dinar",  # "د.ج",
    "dirham": "dirham",  # "د.م.",
    "riyal": "riyal",  # "ر.س",
    "rial": "rial",  # "﷼",
    "shekel": "₪",
    "won": "₩",
    "lire": "₤",
}

_genders = {
    "masc": "m",
    "mixte": "x",
    "fém": "f",
    "fem": "f",
}

_languages = {
    "en": "english",
    "zh": "chinese",
    "de": "german",
    "es": "spanish",
    "ru": "russian",
    "ko": "korean",
    "fr": "french",
    "ja": "japanese",
    "pt": "portuguese",
    "tr": "turkish",
    "pl": "polish",
    "ca": "catalan",
    "nl": "dutch",
    "ar": "arabic",
    "sv": "swedish",
    "it": "italian",
    "id": "indonesian",
    "hi": "hindi",
    "fi": "finnish",
    "vi": "vietnamese",
    "iw": "hebrew",
    "uk": "ukrainian",
    "el": "greek",
    "ms": "malay",
    "cs": "czech",
    "ro": "romanian",
    "da": "danish",
    "hu": "hungarian",
    "ta": "tamil",
    "no": "norwegian",
    "th": "thai",
    "ur": "urdu",
    "hr": "croatian",
    "bg": "bulgarian",
    "lt": "lithuanian",
    "la": "latin",
    "mi": "maori",
    "ml": "malayalam",
    "cy": "welsh",
    "sk": "slovak",
    "te": "telugu",
    "fa": "persian",
    "lv": "latvian",
    "bn": "bengali",
    "sr": "serbian",
    "az": "azerbaijani",
    "sl": "slovenian",
    "kn": "kannada",
    "et": "estonian",
    "mk": "macedonian",
    "br": "breton",
    "eu": "basque",
    "is": "icelandic",
    "hy": "armenian",
    "ne": "nepali",
    "mn": "mongolian",
    "bs": "bosnian",
    "kk": "kazakh",
    "sq": "albanian",
    "sw": "swahili",
    "gl": "galician",
    "mr": "marathi",
    "pa": "punjabi",
    "si": "sinhala",
    "km": "khmer",
    "sn": "shona",
    "yo": "yoruba",
    "so": "somali",
    "af": "afrikaans",
    "oc": "occitan",
    "ka": "georgian",
    "be": "belarusian",
    "tg": "tajik",
    "sd": "sindhi",
    "gu": "gujarati",
    "am": "amharic",
    "yi": "yiddish",
    "lo": "lao",
    "uz": "uzbek",
    "fo": "faroese",
    "ht": "haitian creole",
    "ps": "pashto",
    "tk": "turkmen",
    "nn": "nynorsk",
    "mt": "maltese",
    "sa": "sanskrit",
    "lb": "luxembourgish",
    "my": "myanmar",
    "bo": "tibetan",
    "tl": "tagalog",
    "mg": "malagasy",
    "as": "assamese",
    "tt": "tatar",
    "haw": "hawaiian",
    "ln": "lingala",
    "ha": "hausa",
    "ba": "bashkir",
    "jw": "javanese",
    "su": "sundanese",
    "yue": "cantonese",
}


def to_ieme(d):
    if len(d) > 1:
        return "".join([to_ieme(x) for x in d])
    if d in ["e", "r"]:
        return to_exp(d)
    if d in ["è", "m"]:
        return ""
    if d in ["°", "o"]:
        return "ᵒ"
    return d


def to_exp(d):
    if len(d) > 1:
        return "".join([to_exp(x) for x in d])
    if d == "1":
        return "¹"
    if d == "2":
        return "²"
    if d == "3":
        return "³"
    if d == "4":
        return "⁴"
    if d == "5":
        return "⁵"
    if d == "6":
        return "⁶"
    if d == "7":
        return "⁷"
    if d == "8":
        return "⁸"
    if d == "9":
        return "⁹"
    if d == "0":
        return "⁰"
    if d == "a":
        return "ᵃ"
    if d == "b":
        return "ᵇ"
    if d == "c":
        return "ᶜ"
    if d == "d":
        return "ᵈ"
    if d == "e":
        return "ᵉ"
    if d == "f":
        return "ᶠ"
    if d == "g":
        return "ᵍ"
    if d == "h":
        return "ʰ"
    if d == "i":
        return "ⁱ"
    if d == "j":
        return "ʲ"
    if d == "k":
        return "ᵏ"
    if d == "l":
        return "ˡ"
    if d == "m":
        return "ᵐ"
    if d == "n":
        return "ⁿ"
    if d == "o":
        return "ᵒ"
    if d == "p":
        return "ᵖ"
    # if d == "q": return "q"
    if d == "r":
        return "ʳ"
    if d == "s":
        return "ˢ"
    if d == "t":
        return "ᵗ"
    if d == "u":
        return "ᵘ"
    if d == "v":
        return "ᵛ"
    if d == "w":
        return "ʷ"
    if d == "x":
        return "ˣ"
    if d == "y":
        return "ʸ"
    if d == "z":
        return "ᶻ"
    if d == "A":
        return "ᴬ"
    if d == "B":
        return "ᴮ"
    # if d == "C": return "ᶜ"
    if d == "D":
        return "ᴰ"
    if d == "E":
        return "ᴱ"
    if d == "G":
        return "ᴳ"
    if d == "H":
        return "ᴴ"
    if d == "I":
        return "ᴵ"
    if d == "J":
        return "ᴶ"
    if d == "K":
        return "ᴷ"
    if d == "L":
        return "ᴸ"
    if d == "M":
        return "ᴹ"
    if d == "N":
        return "ᴺ"
    if d == "O":
        return "ᴼ"
    if d == "P":
        return "ᴾ"
    # if d == "Q": return "Q"
    if d == "R":
        return "ᴿ"
    # if d == "S": return "ˢ"
    if d == "T":
        return "ᵀ"
    if d == "U":
        return "ᵁ"
    if d == "V":
        return "ⱽ"
    if d == "W":
        return "ᵂ"
    # if d == "X": return "ᵡ"
    # if d == "Y": return "ʸ"
    if d == "Z":
        return "ᙆ"
    if d == "+":
        return "⁺"
    if d == "-":
        return "⁻"
    if d == "=":
        return "⁼"
    if d == "(":
        return "⁽"
    if d == ")":
        return "⁾"
    if d == ".":
        return "˙"
    return d


def to_ind(d):
    if len(d) > 1:
        return "".join([to_ind(x) for x in d])
    if d == "1":
        return "₁"
    if d == "2":
        return "₂"
    if d == "3":
        return "₃"
    if d == "4":
        return "₄"
    if d == "5":
        return "₅"
    if d == "6":
        return "₆"
    if d == "7":
        return "₇"
    if d == "8":
        return "₈"
    if d == "9":
        return "₉"
    if d == "0":
        return "₀"
    if d == "a":
        return "ₐ"
    if d == "e":
        return "ₑ"
    if d == "h":
        return "ₕ"
    if d == "i":
        return "ᵢ"
    if d == "j":
        return "ⱼ"
    if d == "k":
        return "ₖ"
    if d == "l":
        return "ₗ"
    if d == "m":
        return "ₘ"
    if d == "n":
        return "ₙ"
    if d == "o":
        return "ₒ"
    if d == "p":
        return "ₚ"
    if d == "r":
        return "ᵣ"
    if d == "s":
        return "ₛ"
    if d == "t":
        return "ₜ"
    if d == "u":
        return "ᵤ"
    if d == "v":
        return "ᵥ"
    if d == "y":
        return "ᵧ"
    if d == "x":
        return "ₓ"
    if d == "+":
        return "₊"
    if d == "-":
        return "₋"
    if d == "=":
        return "₌"
    if d == "(":
        return "₍"
    if d == ")":
        return "₎"
    return d


def to_dict(fields):
    res = {}
    for f in fields:
        if "=" in f:
            k, v = f.split("=", 1)
            res[k] = v
    return res


# Source: https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python
_emoji_pattern = re.compile("["
                            u"\U0001F600-\U0001F64F"  # emoticons
                            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                            u"\U0001F680-\U0001F6FF"  # transport & map symbols
                            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                            u"\U0001f926-\U0001f937"
                            u"\U00010000-\U0010ffff"
                            u"\u2640-\u2642"
                            u"\u2600-\u2B55"
                            u"\u200d"
                            u"\u23cf"
                            u"\u23e9"
                            u"\u231a"
                            u"\ufe0f"  # dingbats
                            u"\u3030"
                            "]+", flags=re.UNICODE)


def remove_emoji(text):
    return _emoji_pattern.sub("", text)


