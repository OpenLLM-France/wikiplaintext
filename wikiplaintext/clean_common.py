import regex as re

END_HEADER = "␣:"

_ignore_from_section = {
    "fr": [
        "Notes",
        "Notes et références",
        "Références",
        "Voir aussi",
        "Liens externes",
        # "Bibliographie",
        "Annexes",
        "Articles connexes",
    ],
}


def final_clean(text, from_wikicode=False, with_header_level=False):

    # Remove double spaces
    text = re.sub(r" +", " ", text)

    # Normalize the spaces
    text = re.sub(r"\r", "", text)
    text = re.sub(r"[ \t\f\v]+", " ", text)

    # Strip all the lines
    text = re.sub(r" *\n *", "\n", text)

    # Remove empty lines
    text = re.sub(r"\n([^\w]*\n+)*", "\n", text)

    # Add empty lines before/after headers
    # text = re.sub(rf"(?<=\n)([^\n]+){END_HEADER}(?=\n)", rf"\n\1{END_HEADER}\n", text)
    text = re.sub(
        rf"((^|(?<=\n))[^\n]+){END_HEADER}(?=\n)", rf"\n\1{END_HEADER}\n", text)

    # Group headers together
    text = re.sub(rf"((^|(?<=\n)\n)[^\n]+{END_HEADER}\n\n)+(?=(\n|$))",
                  lambda x: x.group(0).replace(":\n\n", ":"),
                  text,
                  flags=re.MULTILINE, # TODO check if useful
                  )
    if with_header_level:
        # Remove empty sections
        text = re.sub(
            rf"\n([\#]+)[^\#\n]+{END_HEADER}\n(\1[^\n]+{END_HEADER}\n)*(\1[^\#\n]+{END_HEADER}\n)",
            r"\n\3",
            text,
            flags=re.MULTILINE, # TODO check if useful
        )
    text = re.sub(rf"(\n[^\n]+{END_HEADER})+$", "", text.strip())

    text = text.replace(END_HEADER, "\u00A0:")

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

    # Normalize spaces
    text = re.sub(r"\u00A0", " ", text)

    # At last, remove leading and trailing newlines
    return text.strip()


def collapse_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


def to_superscript(d, all_or_none=False):
    if len(d) > 1:
        if all_or_none:
            out = ""
            for i in d:
                o = to_superscript(i)
                if i == o and i != " " and i not in _superscript.values():
                    # print(f"Ignoring superscript {d} -> {to_superscript(d)} (cannot convert {i})")
                    return f"^{{{d}}}"
                out += o
            return out
        return "".join([to_superscript(x) for x in d])
    return _superscript.get(d, d)


def to_subscript(d, all_or_none=False):
    if len(d) > 1:
        if all_or_none:
            out = ""
            for i in d:
                o = to_subscript(i)
                if i == o and i != " " and i not in _subscript.values():
                    # print(f"Ignoring subscript {d} -> {to_superscript(d)} (cannot convert {i})")
                    return f"_{{{d}}}"
                out += o
            return out
        return "".join([to_subscript(x) for x in d])
    return _subscript.get(d, d)

# A good reference to find superscripts is https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts

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
    "•": "•",
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
    "e": "ₑ",
    "h": "ₕ",
    "i": "ᵢ",
    "j": "ⱼ",
    "k": "ₖ",
    "l": "ₗ",
    "m": "ₘ",
    "n": "ₙ",
    "o": "ₒ",
    "p": "ₚ",
    "r": "ᵣ",
    "s": "ₛ",
    "t": "ₜ",
    "u": "ᵤ",
    "v": "ᵥ",
    "x": "ₓ",
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
}
