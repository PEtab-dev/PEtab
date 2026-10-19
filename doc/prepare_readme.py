"""Prepare README.md for inclusion in the Sphinx documentation."""
import re
from pathlib import Path


def read(fname):
    """Read a file."""
    return open(fname).read()


def absolute_links(txt):
    """Replace relative petab github links by absolute links."""
    raw_base = "(https://raw.githubusercontent.com/petab-dev/petab/main/"
    embedded_base = "(https://github.com/petab-dev/petab/blob/main/"
    # iterate over links
    for var in re.findall(r'\[.*?\]\((?!http).*?\)', txt):
        if re.match(r'.*?.(png|svg)\)', var):
            # link to raw file
            rep = var.replace("(", raw_base)
        else:
            # link to github embedded file
            rep = var.replace("(", embedded_base)
        txt = txt.replace(var, rep)
    return txt


def prepare_readme(source: str, target: str):
    txt = absolute_links(read(source))
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    with open(target, 'w') as f:
        f.write(txt)


if __name__ == '__main__':
    prepare_readme('../README.md', '_generated/README.md')
