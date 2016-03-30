import lxml
from lxml.html import parse as parse_html
from lxml.cssselect import CSSSelector
import bisect

def pf_get_citation(folder, doi="", title=""):
    d = {}

    res = get_all_uses_of_citation(str(folder / 'scholarly.html'), doi=doi, title=title)

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

def get_all_uses_of_citation(fname_or_etree, doi="", title=""):
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
    text = [get_sentence(r) for r in res]

    if len(text) == 0:
        # It is the in the list of references, but we can't find the citation
        # This is probably because it was something like reference number 4
        # and was cited as [2-5]
        # So we return some text that explains the error
        text = ['ERROR: In reference list, but cannot find citation. Check manually.']

    return text

def get_sentence(el):
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

    if ind == len(ends_of_sentences_pos):
        return text[ends_of_sentences_pos[ind-1]:].strip()
    elif ind == 0:
        return text[:ends_of_sentences_pos[ind]].strip()
    else:
        return text[ends_of_sentences_pos[ind-1]:ends_of_sentences_pos[ind]].strip()
