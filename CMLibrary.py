import os
from glob import glob
import pandas as pd
import json
import re
from pathlib import Path

import lxml
from lxml.html import parse as parse_html
from lxml.cssselect import CSSSelector
import bisect

import re

def all_whitespace_to_space(s):
    return re.sub(r'\s+', " ", s, flags=re.MULTILINE).strip()

def get_article_metadata(folder_path):
    """
    Gets key metadata for an article given the path to a
    CM folder.

    This metadata is returned as a dict, with keys of 'doi',
    'title', 'date' and 'journal'.
    """
    json_filename = str(folder_path / 'results.json')

    with open(json_filename) as f:
        j = json.load(f)

    selected_keys = ['doi', 'title', 'date', 'journal']

    filtered_dict = { k: j[k]['value'][0] for k in selected_keys }

    return filtered_dict


def count_regex_matches(pattern, fname, flags=0):
    """Counts the number of times the regex `pattern` matches
    the text inside file `fname`.

    The given flags (none by default) are used when searching
    with the regular experssion.
    """
    with open(fname) as f:
        text = f.read()
        #print(text)

        count = len(re.findall(pattern, text, flags=flags))

    return count


def count_multiple_regexes(regexes, fname, flags=0):
    """Counts the number of times that each of multiple regexes
    match the text inside fname, with the given flags.

    See count_regex_matches for more details.

    `regexes` should be a list containing tuples, either one-element tuples
    containing a regex, or two-element tuples containing (regex, display_name).

    TODO: This is inefficiently implemented at the moment as we read files
    multiple times!
    """
    res = {}

    for item in regexes:
        try:
            regex, name = item
        except (TypeError, ValueError):
            regex = item
            name = item
        res[name] = count_regex_matches(regex, fname, flags=flags)

    return res


def process_article(folder, processing_function, **kwargs):
    """Processes the article in a given CM folder.

    Checks to see if it is a valid CM folder (has a results.json file), and
    has any other files required (eg. fulltext.xml or scholarly.html).

    Then runs a given processing method (here it counts matches against multiple
    regex, and returns a dict of article metadata & statistics results.
    """
    # If not a valid CM folder then return
    if not (folder / 'results.json').exists() or not (folder / 'fulltext.xml').exists() or not (folder / 'scholarly.html').exists():
        return None

    # Get the metadata first
    results = get_article_metadata(folder)

    processing_results = processing_function(folder, **kwargs)

    results.update(processing_results)

    return results

ac_regexes = [('FLAASH'),
              ('ATCOR'),
              ('SMAC'),
              ('6S', '6S'),
              ('empirical line'),
              (r'\bELM\b')]

prog_regexes = [('python'),
                (r'\bIDL\b', 'IDL'),
                ('Java'),
                ('C\+\+', 'CPP'),
                ('Matlab'),
                ('Py6S')]


def pf_count_regex(folder, **kwargs):
    regexes = kwargs['regexes']

    regex_stats = count_multiple_regexes(regexes, str(folder / 'fulltext.xml'), flags=re.IGNORECASE)

    return regex_stats

def pf_get_citation(folder, doi=None):
    d = {}

    res = get_all_uses_of_citation(str(folder / 'scholarly.html'), doi=doi)



    #print(res)
    if res is not None:
        for i, match in enumerate(res):
            d["match_%d" % i] = match

        return d
    else:
        return {}


def process_all_articles(glob_string, processing_function, **kwargs):
    # example glob string = 'mdpi-rs/**/**'
    p = Path()
    folders = p.glob(glob_string)

    results = [process_article(folder, processing_function, **kwargs) for folder in folders]

    # Filter out the None's...there must be a better way to do this!
    results = filter(None, results)
    results = pd.DataFrame(list(results))
    results['date'] = pd.to_datetime(results.date)

    return results


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

    matches = [r for r in res if all_whitespace_to_space(r.text_content) == title]
    if len(matches) == 0:
        return

    assert len(matches) == 1

    return matches[0]

def get_all_uses_of_citation(fname_or_etree, doi="10.3390/rs6043263", title=""):
    #print("Looking for %s in %s" % (doi, fname_or_etree))
    if type(fname_or_etree) is not lxml.etree._ElementTree:
        html = parse_html(fname_or_etree)
    else:
        html = fname_or_etree

    if doi != "":
        doi_element = get_doi_element(html, doi)
        div = doi_element.getparent()
    elif title != "":
        title_element = get_title_element(html, title)
        div = title_element.getparent()
    #print(all_whitespace_to_space(div.text_content()))

    li = div.getparent()
    ref_id = li.find('a').attrib['name']

    #print(ref_id)

    sel = CSSSelector('a[href="#%s"]' % ref_id)
    res = sel(html)
    #print(res)
    text = [get_sentence(r) for r in res]

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
