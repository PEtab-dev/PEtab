#!/bin/sh

# Build a pdflatex document from the documentation

# format A3
pandoc documentation_data_format.rst \
    -o documentation_data_format.pdf \
    -V geometry:margin=1.5in -V geometry:a3paper -V fontsize=10pt \
    --toc \
    --pdf-engine pdflatex

# format A2 landscape

# pandoc documentation_data_format.rst \
#     -o documentation_data_format.pdf \
#     -V geometry:margin=.5in -V geometry:a4paper -V geometry:landscape -V fontsize=10pt \
#     --toc \
#     --pdf-engine pdflatex
