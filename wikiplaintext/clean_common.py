import regex as re

def final_clean(text):

    # Remove empty parenthesis
    text = re.sub(r" ?[\[\{\(][^\w]*[\)\}\]]", "", text)

    # Remove double spaces
    text = re.sub(r" +", " ", text)

    # Normalize the spaces
    text = re.sub(r"\r", "", text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    # Good: remove ", , "/": : ", Bad: also ", :"...
    text = re.sub(r"([,:] +){2,}", r"\1", text)

    # Strip all the lines
    text = re.sub(r" *\n *", "\n", text)

    # Remove empty lines
    text = re.sub(r"\n([^\w]*\n+)+", "\n", text)

    # Remove weird starting punctuation marks
    text = re.sub(r"\n *:: ", "\n** ", text)
    text = re.sub(r"\n *([,;:\.] *)+", "\n", text)

    # Add empty lines before/after headers
    text = re.sub(r"\n([^\n]+)\u00A0: *\n+", r"\n\n\1\u00A0:\n\n", text)

    # Remove empty headers
    text = re.sub(
        r"(\n\n[^\n]+\u00A0:){1,}(\n\n[^\n]+\u00A0:\n\n)", r"\2", text)

    # # Remove empty lines after other colons
    # text = re.sub(r" : *\n+", " :\n", text)

    # # Never more than 2 consecutive newlines
    # text = re.sub(r"\n{3,}", "\n\n", text)

    # Normalize spaces
    text = re.sub(r"\u00A0", " ", text)

    # At last, remove leading and trailing newlines
    return text.strip()

def collapse_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()

_ignore_from_section = {
    "fr": [
        "Notes",
        "Notes et références",
        "Références",
        "Voir aussi",
        "Liens externes",
        # "Bibliographie",
        "Annexes",
    ],
}