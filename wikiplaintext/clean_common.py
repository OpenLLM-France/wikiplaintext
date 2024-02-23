import regex as re
from enum import Enum

def any_starts_with(list_of_strings, list_of_starts):
    return any(s.startswith(start) for s in list_of_strings for start in list_of_starts) if list_of_strings else False

def final_clean(
    text,
    from_wikicode=False,
    remove_hashtag_headers=False,
    remove_repeated_headers=False,
    ):

    # Remove double spaces
    text = re.sub(r" +", " ", text)

    # Normalize the spaces
    text = re.sub(r"\r", "", text)
    text = re.sub(r"[ \t\f\v]+", " ", text)

    # Normalize bullets
    text = re.sub(r"\n[•]([\u00A0 ])", "\n* ", text)

    # Strip all the lines
    text = re.sub(r" *\n *", "\n", text)

    # Remove empty lines
    text = re.sub(r"\n([^\w]*\n+)*", "\n", text)
    text = text.replace(PROTECTED_SPACE, " ")

    # Add empty lines before/after headers
    # text = re.sub(rf"(?<=\n)([^\n]+){END_HEADER}(?=\n)", rf"\n\1{END_HEADER}\n", text)
    text = re.sub(
        rf"((^|(?<=\n))[^\n]+){END_HEADER}(?=\n)", rf"\n\1{END_HEADER}\n", text)


    # Group headers together
    text = re.sub(rf"((^|(?<=\n)\n)[^\n]+{END_HEADER}\n\n)+(?=\n)",
                  lambda x: x.group(0).replace(":\n\n", ":"),
                  text,
                  flags=re.MULTILINE,
                  )
    # Remove empty sections
    text = re.sub(
        rf"\n([\#]+)[^\#\n]+{END_HEADER}\n(\1[^\n]+{END_HEADER}\n)*(\1[^\#\n]+{END_HEADER}\n|$)",
        r"\n\3",
        text,
    )

    if remove_repeated_headers:
        # Remove repeated headers
        text = re.sub(
            rf"\n([^\n]+{END_HEADER}\n)+([^\n]+{END_HEADER}\n)",
            r"\n\2",
            text,
        )

    if remove_hashtag_headers:
        # Remove hashtag headers
        text = re.sub(rf"(\n|^)\#+ *([^\#\n]+{END_HEADER}\n)", r"\1\2", text)

    text = re.sub(rf"(\n[^\n]+{END_HEADER})+$", "", text.strip())
    text = text.replace(END_HEADER, "")

    # # Never more than 2 consecutive newlines
    # text = re.sub(r"\n{3,}", "\n\n", text)

    if from_wikicode:
        # Remove empty parenthesis
        text = re.sub(r" ?[\[\{\(][^\w]*[\)\}\]]", "", text)

        # Good: remove ", , "/": : ", Bad: also ", :"...
        text = re.sub(r"([,:] +){2,}", r"\1", text)

        # Remove weird starting punctuation marks
        text = re.sub(r"\n *:: ", "\n** ", text)
        text = re.sub(r"\n *([,;:\.] *)+", "\n", text)

        # # Remove empty lines after other colons
        # text = re.sub(r" : *\n+", " :\n", text)
    else:
        # Remove empty parenthesis
        text = re.sub(r" ?[\[\{\(][\)\}\]]", "", text)


    # Normalize unbreakablespaces
    # text = re.sub(r"\u00A0", " ", text)

    # At last, remove leading and trailing newlines
    return text.strip()


def collapse_whitespace(text, level=1):
    """
    Remove double whitespaces

    param text: The text to clean
    param level:
        1: Keep all line breaks
        2: Keep double line breaks
        3: Remove all line breaks
    """
    # Remove tabs
    text = re.sub(r"[\t]", " ", text)
    # Remove double spaces
    text = re.sub(r" *\u00A0+ *", "\u00A0", text)
    if level < 3:
        if level == 2:
            # Remove line breaks unless when there are two in a row
            text = re.sub(r"(?<![ \n])( ?\n)", " ", text)
        # Remove whitespace repetitions
        text = re.sub(r"(\s)\1+", r"\1", text)
        return text.strip()
    text = re.sub(r"[\r\n ]+", " ", text)
    return text.strip()

class SuperScriptConverstion(Enum):
    WHAT_POSSIBLE = 0
    ALL_OR_NONE = 1
    NONE = 2

def to_superscript(d, conversion=SuperScriptConverstion.WHAT_POSSIBLE):
    """
    Convert a string to superscript

    param d: The string to convert
    param conversion:
        WHAT_POSSIBLE: Convert only what is possible
        ALL_OR_NONE: Convert all or none
        NONE: Just use "^{...}"
        list of strings: returns unchanged if d is in the list, otherwise use "^{...}"
    """
    if not d: return ""
    if conversion == SuperScriptConverstion.ALL_OR_NONE:
        out = ""
        for i in d:
            o = _superscript.get(i, i)
            if i == o and i not in _superscript.values():
                # print(f"Ignoring superscript {d} -> {to_superscript(d)} (cannot convert {i})")
                return to_superscript(d, SuperScriptConverstion.NONE)
            out += o
        return out
    if isinstance(conversion, list):
        if d in conversion:
            return d
        return to_superscript(d, SuperScriptConverstion.NONE)
    if conversion == SuperScriptConverstion.NONE:
        if len(d) == 1:
            return f"$^{d}$"
        return f"$^{{{d}}}$"
    if len(d) > 1:
        return "".join([to_superscript(x) for x in d])
    return _superscript.get(d, d)


def to_subscript(d, conversion=SuperScriptConverstion.WHAT_POSSIBLE):
    if not d: return ""
    if conversion == SuperScriptConverstion.ALL_OR_NONE:
        out = ""
        for i in d:
            o = _subscript.get(i, i)
            if i == o and i not in _subscript.values():
                # print(f"Ignoring subscript {d} -> {to_superscript(d)} (cannot convert {i})")
                return to_subscript(d, SuperScriptConverstion.NONE)
            out += o
        return out
    if isinstance(conversion, list):
        if d in conversion:
            return d
        return to_subscript(d, SuperScriptConverstion.NONE)
    if conversion == SuperScriptConverstion.NONE:
        if len(d) == 1:
            return f"$_{d}$"
        return f"$_{{{d}}}$"
    if len(d) > 1:
        return "".join([to_subscript(x) for x in d])
    return _subscript.get(d, d)


def format_table(table, ignore_one_cell=True) -> str:
    """
    Return a table in markdown format, removing empty columns.
    Use list format if there is only one column in the end.
    """
    data = [
        [(cell if cell is not None else '') for cell in row]
        for row in table.data()
    ]
    if not data:
        return ""
    widths = [0] * len(data[0])
    for irow, row in enumerate(data):
        if irow == 0 and irow < len(data) - 3:
            continue
        for ri, d in enumerate(row):
            while ri >= len(widths):
                widths.append(0)
            widths[ri] = max(
                widths[ri] if ri < len(widths) else 0
                , len(d.strip())
            )
    caption = table.caption
    lwidths = len([w for w in widths if w])
    if lwidths == 0:
        return ""
    caption = (f'\n{caption}\u00A0:\n' if caption is not None else '')
    if lwidths == 1:
        new_data = []
        for row in data:
            row = [c for (w, c) in zip(widths, row) if w > 0]
            if not len(row): continue
            assert len(row) == 1
            for r in row[0].split("\n"):
                r = r.strip()
                if r:
                    new_data.append([r])
        rows = new_data
    else:
        rows = data
    if ignore_one_cell and (len(rows) == 1 and len(rows[0]) <= int(ignore_one_cell)) or (0 < len(rows) <= int(ignore_one_cell) and len(rows[0]) == 1):
        # Ignore tables with one element
        return ""
    if lwidths == 1:
        return (
            caption
            + '* ' + '\n* '.join([row[0] for row in rows])
            + '\n'
        )
    return (
        caption
        + '\n'
        + '\n'.join(
            re.sub(
                r"^(\|[^\|]+\|+) \|$",
                r"\1|",
                "| " + " | ".join(f"{remove_line_breaks(d)}" for (w, d) in zip(widths, r) if w > 0) + " |"
            ) for r in rows
        )
        + '\n'
    )


def remove_line_breaks(text):
    return collapse_whitespace(text, 3)



# Good references to find superscripts and subscripts:
# - https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts
# - https://www.w3.org/TR/xml-entity-names/020.html

_superscript_coma = "˒"
_superscript = {
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
    "0": "⁰",
    "a": "ᵃ",
    "b": "ᵇ",
    "c": "ᶜ",
    "d": "ᵈ",
    "e": "ᵉ",
    "è": "ᵉ",
    "f": "ᶠ",
    "g": "ᵍ",
    "h": "ʰ",
    "i": "ⁱ",
    "j": "ʲ",
    "k": "ᵏ",
    "l": "ˡ",
    "m": "ᵐ",
    "n": "ⁿ",
    "o": "ᵒ",
    "p": "ᵖ",
    "q": "𐞥",
    "r": "ʳ",
    "s": "ˢ",
    "t": "ᵗ",
    "u": "ᵘ",
    "v": "ᵛ",
    "w": "ʷ",
    "x": "ˣ",
    "y": "ʸ",
    "z": "ᶻ",
    "A": "ᴬ",
    "B": "ᴮ",
    "C": "ꟲ",
    "D": "ᴰ",
    "E": "ᴱ",
    "G": "ᴳ",
    "H": "ᴴ",
    "I": "ᴵ",
    "J": "ᴶ",
    "K": "ᴷ",
    "L": "ᴸ",
    "M": "ᴹ",
    "N": "ᴺ",
    "O": "ᴼ",
    "P": "ᴾ",
    "Q": "ꟴ",
    "R": "ᴿ",
    # "S": "ˢ",
    "T": "ᵀ",
    "U": "ᵁ",
    "V": "ⱽ",
    "W": "ᵂ",
    # "X": "ˣ",
    # "Y": "ʸ",
    "Z": "ᙆ",
    "+": "⁺",
    "-": "⁻",
    "−": "⁻",
    "–": "⁻",
    "=": "⁼",
    "/": "ᐟ",
    "(": "⁽",
    ")": "⁾",
    ".": "‧",
    ",": _superscript_coma,
    "α": "ᵅ",
    "β": "ᵝ",
    "γ": "ᵞ",
    "δ": "ᵟ",
    "ε": "ᵋ",
    "θ": "ᶿ",
    "ι": "ᶥ",
    "υ": "ᶷ",
    "φ": "ᵠ",
    "χ": "ᵡ",
    "^": "ˆ",
    # Below: letter that are not superscript but are used as such
    "*": "*", "•": "•",
    "′": "′", "″": "″", "‴": "‴", "⁗": "⁗",
    "˙": "˙", "¨": "¨",
    "¯": "¯",
    " ": " ",
}

_subscript = {
    "1": "₁",
    "2": "₂",
    "3": "₃",
    "4": "₄",
    "5": "₅",
    "6": "₆",
    "7": "₇",
    "8": "₈",
    "9": "₉",
    "0": "₀",
    "a": "ₐ",
    # "b": "♭",
    # "c": "꜀",
    # "d": "d",
    "e": "ₑ",
    # "f": "f",
    # "g": "g",
    "h": "ₕ",
    "i": "ᵢ",
    "j": "ⱼ",
    "k": "ₖ",
    "l": "ₗ",
    "m": "ₘ",
    "n": "ₙ",
    "o": "ₒ",
    "p": "ₚ",
    # "q": "q",
    "r": "ᵣ",
    "s": "ₛ",
    "t": "ₜ",
    "u": "ᵤ",
    "v": "ᵥ",
    # "w": "w",
    "x": "ₓ",
    # "y": "y",
    # "z": "z",
    "+": "₊",
    "-": "₋",
    "−": "₋",
    "–": "₋",
    "=": "₌",
    "(": "₍",
    ")": "₎",
    "/": "⸝",
    # "α": "α",
    "β": "ᵦ",
    "γ": "ᵧ",
    # "δ": "δ",
    # "ε": "ε",
    # "θ": "θ",
    "ρ": "ᵨ",
    # "ι": "ι",
    # "υ": "υ",
    "φ": "ᵩ",
    "χ": "ᵪ",
    "•": "•",
    " ": " ",
}

def retain_only_if_proncunciation(text):
    if re.search(r"\\[^\\]+\\", text):
        return text
    return ""

def remove_strings_func(to_remove):
    if not isinstance(to_remove, list):
        to_remove = [to_remove]
    return lambda x: remove_strings(x, to_remove)

def remove_strings(text, to_remove):
    for r in to_remove:
        text = re.sub(r, "", text)
    return collapse_whitespace(text, 1)

# Special processing when in some sections
POSTPROC_SECTION = {
    "wiktionary" : {
        "fr": {
            "*" : remove_strings_func([
                r"\*?\\Prononciation\s*\?\\",
                r"[ \u00A0]?→[\w'’\- \u00A0]+", # → Modifier, → lire en ligne, → voir ..., ...
                r"[^\n]+\bmanqu[^\n]+\(Ajouter\)[^\n]*",
                r"[^\n]+\bmanquante? ou incompl[^\n]*", # "Étymologie" : lambda text: "" if "manquante ou incomplète" in text else text, # Remove missing
            ]),
            "Prononciation" : retain_only_if_proncunciation,            
            "Références" : lambda text: "", # Remove section "Références" (including subsection "Sources", "Bibliographie")
            "Voir aussi" : lambda text: "", # Remove section "See also"
        },
    },
}

# All the text following those sections will be discarded
IGNORE_FROM_SECTION = {
    "wikipedia" : {
        "fr": [
            "Notes",
            "Notes et références",
            "Références", "Référence",
            "Voir aussi", "Pour approfondir",
            "Liens externes",
            "Bibliographie",
            "Annexes",
            "Articles connexes",
        ],
        "en": [
            "Notes",
            "Notes and references",
            "References", "Reference",
            "See also", "Further reading",
            "External links",
            "Bibliography",
            "Annexes",
            "Related articles",
        ],
        "de": [
            "Anmerkungen",
            "Einzelnachweise",
            "Siehe auch", "Literatur",
            "Weblinks",
            "Bibliographie",
            "Annexes", "Fußnoten",
            "Verwandte Artikel",
        ],
        "es": [
            "Notas",
            "Referencias", "Referencia", #"Bibliografía",
            "Véase también",
            "Enlaces externos",
            "Anexos",
            "Artículos relacionados",
        ],
        "it": [
            "Note",
            "Note e riferimenti",
            "Riferimenti",
            "Voci correlate",
            "Bibliografia",
            "Altri progetti",
            "Collegamenti esterni",
        ],
    },
}

# Linked text following those conditions will be discarded
LINKS_TO_DISCARD_FUN = {
    "fr": lambda text: bool(re.search(r"\bmodifier\b", text)),
    "en": lambda text: bool(re.search(r"\bedit\b", text)),
    "de": lambda text: bool(re.search(r"\bbearbeiten\b", text, flags=re.IGNORECASE)),
    "es": lambda text: bool(re.search(r"\beditar\b", text)),
    "it": lambda text: bool(re.search(r"\bmodifica\b", text)),
}

# All HTML object (tables, ...) following those conditions will be discarded
HTML_NODE_IGNORED = {
    "fr": lambda x: any_starts_with(x.get("class"), ["bandeau-", "infobox"]),
    "en": lambda x: any_starts_with(x.get("class"), ["hatnote", "infobox"]),
}

END_HEADER = "␣:"

PROTECTED_SPACE = "␣␣␣"

SUPERSCRIPTS_TO_AVOID = {
    "fr" : ["e", "er", "re", "ère", "ème", "nd", "nde", "me"],
    "es" : ["a", "o", "er", "ra", "ro", "nda", "ndo"],
    "en" : ["st", "nd", "rd", "th"],
    "de": ["er", "re", "nd", "nde"],
    "it": ["a", "o", "er", "ra", "ro", "nda", "ndo"],
}

SUBSCRIPTS_TO_AVOID = {
    "" : [# "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
          "+", "-"
          ],
}