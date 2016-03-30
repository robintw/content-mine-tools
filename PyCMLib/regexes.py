import re

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


def count_multiple_regexes(regexes, fname, flags=0):
    """Counts the number of times that each of multiple regexes
    match the text inside fname, with the given flags.

    `regexes` should be a list containing tuples, either one-element tuples
    containing a regex, or two-element tuples containing (regex, display_name).
    """
    res = {}

    with open(fname) as f:
        text = f.read()
        #print(text)

        if 'scholarly.html' in fname:
            text, sep, ref_list = text.partition('<div tag="ref-list">')

        for item in regexes:
            try:
                regex, name = item
            except (TypeError, ValueError):
                regex = item
                name = item
            res[name] = len(re.findall(regex, text, flags=flags))

    return res


def pf_count_regex(folder, filename="scholarly.html", **kwargs):
    regexes = kwargs['regexes']
    flags = kwargs.get('flags', 0)

    regex_stats = count_multiple_regexes(regexes, str(folder / filename), flags=flags)

    return regex_stats


def pf_count_regex_by_match(folder, filename="scholarly.html", group=False, **kwargs):
    regexes = kwargs['regexes']
    flags = kwargs.get('flags', 0)

    fname = str(folder / filename)
    res = {}

    with open(fname) as f:
        text = f.read()
        #print(text)

        if 'scholarly.html' in fname:
            text, sep, ref_list = text.partition('<div tag="ref-list">')

        for item in regexes:
            try:
                regex, name = item
            except (TypeError, ValueError):
                regex = item

            if not group:
                for m in re.findall(regex, text, flags=flags):
                    res[m.upper()] = res.get(m.upper(), 0) + 1
            else:
                for m in re.finditer(regex, text, flags=flags):
                    group_match = m.groups()[0].upper()
                    res[group_match] = res.get(group_match, 0) + 1

    return res
