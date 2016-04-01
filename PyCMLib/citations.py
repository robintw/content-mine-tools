import lxml
from lxml.html import parse as parse_html
from lxml.cssselect import CSSSelector
import bisect
import re

from .utils import all_whitespace_to_space

def pf_get_citation(folder, doi="", title="", n_sentences=0):
    d = {}

    res = get_all_uses_of_citation(str(folder / 'scholarly.html'), doi=doi, title=title, n_sentences=n_sentences)

    #print(res)
    if res is not None:
        for i, match in enumerate(res):
            d["match_%d" % i] = match

        return d
    else:
        return {}

def get_all_text(el):
    return "".join(el.itertext()).strip()

def get_doi_element(html, doi):
    sel = CSSSelector('.pub-id')
    res = sel(html)

    matches = [r for r in res if r.text_content().strip() == doi]
    if len(matches) == 0:
        return

    assert len(matches) == 1

    return matches[0]

def get_title_element(html, title):
    sel = CSSSelector('.article-title')

    res = sel(html)

    matches = [r for r in res if title.lower() in all_whitespace_to_space(r.text_content()).lower()]
    if len(matches) == 0:
        return

    assert len(matches) == 1

    return matches[0]

def get_all_uses_of_citation(fname_or_etree, doi="", title="", n_sentences=0):
    #print("Looking for %s in %s" % (doi, fname_or_etree))
    if type(fname_or_etree) is not lxml.etree._ElementTree:
        html = parse_html(fname_or_etree)
    else:
        html = fname_or_etree

    if doi != "":
        doi_element = get_doi_element(html, doi)
        if doi_element is None:
            return

        div = doi_element.getparent()
    elif title != "":
        title_element = get_title_element(html, title)

        if title_element is None:
            return

        div = title_element.getparent()

    #print(all_whitespace_to_space(div.text_content()))

    li = div.getparent()
    ref_id = li.find('a').attrib['name']

    #print(ref_id)

    sel = CSSSelector('a[href="#%s"]' % ref_id)
    res = sel(html)
    #print(res)
    text = [get_sentence(r, n_around=n_sentences) for r in res]

    if len(text) == 0:
        # It is the in the list of references, but we can't find the citation
        # This is probably because it was something like reference number 4
        # and was cited as [2-5]
        # So we return some text that explains the error
        text = ['ERROR: In reference list, but cannot find citation. Check manually.']

    return text

def get_sentence(el, n_around=0):
    """Given an <a> element from a HTML document, get a string of the full sentence it is in"""
    el.text = '**REF**'
    #print(el.text)
    p = el.getparent()
    text = p.text_content()
    text = all_whitespace_to_space(text)

    #print(text)

    ref_loc = text.find('**REF**')

    #print(ref_loc)

    ends_of_sentences_pos = [m.end() for m in list(re.finditer(r'(?<!et al)\. ', text))]

    #print(ends_of_sentences_pos)
    ind = bisect.bisect(ends_of_sentences_pos, ref_loc)
    #print("IND = %d" % ind)
    #print(ends_of_sentences_pos)
    #print(ref_loc)

    #print("ind: %d" % ind)
    #print("n_around: %d" % n_around)
    #print("len list: %d" % len(ends_of_sentences_pos))
    # start_ind = ind - n_around
    # stop_ind = ind + n_around

    #print("Start: %d" % start_ind)
    #print("Stop: %d" % stop_ind)
    #print('-----------')

    # if start_ind < 0:
    #     start_ind = 0
    # elif start_ind >= len(ends_of_sentences_pos):
    #     start_ind = len(ends_of_sentences_pos) - 1
    #
    # if stop_ind < 0:
    #     stop_ind = 0
    # elif stop_ind >= len(ends_of_sentences_pos):
    #     stop_ind = len(ends_of_sentences_pos) - 1
    #
    # #print("Start: %d" % start_ind)
    #print("Stop: %d" % stop_ind)
    #print('-----------')

    if ind == len(ends_of_sentences_pos):
        # The bisect function put ours AFTER the end of the list
        # So we can't do any sentences after, we just do them before
        chosen_ind = ind - n_around
        chosen_ind = chosen_ind if chosen_ind > 0 else 0
        sl = slice(ends_of_sentences_pos[ind - n_around], None)
    elif ind <= 0:
        # The bisect function put ours at the BEGINNING of the list
        # So we can't do any BEFORE this one
        chosen_ind = ind + n_around
        chosen_ind = chosen_ind if chosen_ind < len(ends_of_sentences_pos) else len(ends_of_sentences_pos) - 1
        sl = slice(None, ends_of_sentences_pos[ind + n_around])
    else:
        sl = slice(ends_of_sentences_pos[ind - (n_around + 1)], ends_of_sentences_pos[ind + n_around])

    t = text[sl]

    return t.strip()

    # if ind == len(ends_of_sentences_pos):
    #     return text[ends_of_sentences_pos[ind-1]:].strip()
    # elif ind <= n_around:
    #     return text[:ends_of_sentences_pos[ind]].strip()
    # else:
    #     return text[ends_of_sentences_pos[ind-1]:ends_of_sentences_pos[ind]].strip()
