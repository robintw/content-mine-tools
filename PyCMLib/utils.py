import re

def all_whitespace_to_space(s):
    return re.sub(r'\s+', " ", s, flags=re.MULTILINE).strip()
