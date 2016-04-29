import json

from lxml.html import parse as parse_html
from .utils import get_text_from_selector, all_whitespace_to_space

def get_metadata_from_schol_html(path):
    if (path / 'results.json').exists():
        return

    doc = parse_html(path / 'scholarly.html')

    metadata = {}

    metadata['title']['value'] = [all_whitespace_to_space(get_text_from_selector(doc, '.title-group')[0])]
    metadata['doi']['value'] = [all_whitespace_to_space(get_text_from_selector(doc, '.doi')[0]).replace('doi: ', '')]
    metadata['date']['value'] = ['']
    metadata['journal']['value'] = ['']

    with open(path / 'results.json', 'w') as f:
        json.dump(metadata, f, indent=4)
