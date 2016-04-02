#!/usr/bin/env python
import requests
import logging


def get_result_count(url, params):
    """Count the total number of results that will be returned for a CrossRef
    query, by setting the number of rows to 0 (to get no results), and checking
    the metadata.
    """
    params['rows'] = 0

    r = requests.get(url, params=params)

    j = r.json()

    return int(j['message']['total-results'])


def filter_dict_to_string(filt):
    """Convert a dict of filter keys and values into a string that can
    be passed to the CrossRef API.

    Converts _'s in the filter keys to -'s, as CrossRef uses -'s but they
    are not valid characters in Python identifiers.
    """
    return ",".join(["%s:%s" % (k.replace('_', '-'), v) for k, v in filt.items()])


def _get_dois(filter_string, just_doi=False, just_count=False):
    """Get a list of DOIs (either full DOI URLs or just the DOI itself if
    `just_doi` is True), given a CrossRef API filter string.
    """
    base_url = "http://api.crossref.org/works"

    if just_doi:
        field = 'DOI'
    else:
        field = 'URL'

    doi_list = []

    # Set the params for the query
    params = {'filter': filter_string}

    count = get_result_count(base_url, params)

    if just_count:
        print(count)
        return

    logging.debug('Total result count %d' % count)

    if count < 1000:
        # We can get them all in one go
        params['rows'] = 1000
        r = requests.get(base_url, params=params)

        doi_list = [i[field] for i in r.json()['message']['items']]
    else:
        # We need to use cursors etc
        # Call once with cursor set to *
        params['rows'] = 500

        params['cursor'] = '*'
        r = requests.get(base_url, params=params)

        logging.debug('Getting %s' % r.url)
        cursor = r.json()['message']['next-cursor']

        doi_list = [i[field] for i in r.json()['message']['items']]

        params['cursor'] = cursor

        while True:
            r = requests.get(base_url, params=params)

            logging.debug('Getting %s' % r.url)

            new_dois = [i[field] for i in r.json()['message']['items']]

            doi_list += new_dois

            logging.debug("Received %d items" % len(r.json()['message']['items']))

            if len(r.json()['message']['items']) < params['rows']:
                break

            cursor = r.json()['message']['next-cursor']
            params['cursor'] = cursor

    return doi_list

valid_filters = ["has-assertion",
                 "from-print-pub-date",
                 "until-deposit-date",
                 "from-created-date",
                 "issn",
                 "until-online-pub-date",
                 "full-text.application",
                 "until-created-date",
                 "license.version",
                 "from-deposit-date",
                 "funder",
                 "assertion-group",
                 "from-online-pub-date",
                 "from-issued-date",
                 "directory",
                 "affiliation",
                 "license.url",
                 "from-index-date",
                 "full-text.version",
                 "full-text.type",
                 "has-orcid",
                 "has-archive",
                 "type",
                 "is-update",
                 "publisher-name",
                 "update-type",
                 "from-pub-date",
                 "has-license",
                 "funder-doi-asserted-by",
                 "has-full-text",
                 "doi",
                 "orcid",
                 "prefix",
                 "has-funder",
                 "award.funder",
                 "clinical-trial-number",
                 "member",
                 "container-title",
                 "license.delay",
                 "has-affiliation",
                 "from-update-date",
                 "has-award",
                 "until-print-pub-date",
                 "has-funder-doi",
                 "until-index-date",
                 "has-update",
                 "until-update-date",
                 "until-issued-date",
                 "funder-name",
                 "until-pub-date",
                 "award.number",
                 "has-references",
                 "type-name",
                 "alternative-id",
                 "archive",
                 "updates",
                 "category-name",
                 "has-clinical-trial-number",
                 "assertion",
                 "article-number",
                 "has-update-policy"]


def get_dois(**kwargs):
    """Get a list of DOIs using the CrossRef API.

    Keyword arguments can be any of the valid filter names (see the list at
    https://github.com/CrossRef/rest-api-doc/blob/master/rest_api.md#filter-names),
    or the `valid_filters` list in this module.

    Other keywords accepted are:

     - just_doi: bool
       Returns just the raw DOI, rather than the full DOI URL
     - just_count: bool
       Returns just the total count of items matching the filters

    Examples:

    get_dois(type="journal-article", issn="1932-6203",
             from_pub_date='2015', until_pub_date='2015')

    get_dois(type='journal-article', issn='1932-6203', just_count=True)
    """
    # Check which of the kwargs are valid filter names
    filter_args = {k: v for k, v in kwargs.items() if k.replace('_', '-') in valid_filters}
    non_filter_args = {k: v for k, v in kwargs.items() if k.replace('_', '-') not in valid_filters}

    # Convert the filter arguments to a filter string for use in the API
    filter_string = filter_dict_to_string(filter_args)

    logging.debug(filter_string)

    return _get_dois(filter_string, **non_filter_args)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Simple tool to get a list of'
                                                 'DOIs from the CrossRef API')

    parser.add_argument('outputfile', action='store', type=str)

    parser.add_argument('-d', '--just-doi',
                        help='Output just the raw DOI, not the DOI URL',
                        action='store_true')

    parser.add_argument('--logging',
                        help='Logging level, one of ERROR, WARN, INFO, DEBUG etc'
                             'Defaults to ERROR',
                        action='store')

    for i in sorted(valid_filters):
        parser.add_argument('--%s' % i,
                            help='Search by %s' % i,
                            action='store')

    args = parser.parse_args()

    filtered_args = {k: v for k, v in vars(args).items() if v is not None}

    output_file = filtered_args.pop('outputfile')
    logging_level = filtered_args.pop('logging', 'ERROR')

    logging.basicConfig(level=logging_level)

    # Do the actual work!
    dois = get_dois(**filtered_args)

    with open(output_file, 'w') as f:
        for doi in dois:
            f.write(doi + "\n")

if __name__ == '__main__':
    main()
