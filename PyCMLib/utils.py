import re
from lxml.cssselect import CSSSelector


def all_whitespace_to_space(s):
    return re.sub(r'\s+', " ", s, flags=re.MULTILINE).strip()


def get_all_text(el):
    return "".join(el.itertext()).strip()


def get_text_from_selector(doc, sel_text):
    """Gets the full text (incl text of all children) from a CSS selector.

    Returns a list of strings, one for each separate match"""
    sel = CSSSelector(sel_text)
    res = sel(doc)

    return [get_all_text(r) for r in res]
