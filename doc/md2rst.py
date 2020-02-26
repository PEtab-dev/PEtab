import m2r
from petab.util import read, absolute_links

txt = absolute_links(read("../README.md"))
txt = m2r.convert(txt)
with open("_static/README.rst", 'w') as f:
    f.write(txt)
