import pandas as pd
import ujson as json
from pathlib import Path

from tqdm import tqdm

from .metadata import get_metadata_from_schol_html

print(json.__file__)

from joblib import Parallel, delayed

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


def process_article(folder, processing_function, **kwargs):
    """Processes the article in a given CM folder.

    Checks to see if it is a valid CM folder (has a results.json file), and
    has any other files required (eg. fulltext.xml or scholarly.html).

    Then runs a given processing method (here it counts matches against multiple
    regex, and returns a dict of article metadata & statistics results.
    """
    # If no scholarly.html then skip
    if not (folder / 'scholarly.html').exists():
        return

    # If no results.json then create it from scholarly.html
    if not (folder / 'results.json').exists():
        get_metadata_from_schol_html(folder)

    # Get the metadata first
    results = get_article_metadata(folder)

    processing_results = processing_function(folder, **kwargs)

    results.update(processing_results)

    return results


def process_all_articles(glob_string, processing_function, **kwargs):
    # example glob string = 'mdpi-rs/**/**'
    p = Path()
    folders = p.glob(glob_string)

    #results = [process_article(folder, processing_function, **kwargs) for folder in tqdm(folders)]

    results = Parallel(n_jobs=-1, verbose=2)(delayed(process_article)(folder, processing_function, **kwargs) for folder in folders)

    # Parallel(n_jobs=2)(delayed(sqrt)(i ** 2) for i in range(10))
    
    
    # Filter out the None's...there must be a better way to do this!
    results = filter(None, results)
    results = pd.DataFrame(list(results))
    results['date'] = pd.to_datetime(results.date)

    return results
