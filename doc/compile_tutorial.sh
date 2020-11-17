#!/bin/sh

# Build a pdflatex document from the documentation

# format A3
pandoc tutorial.rst \
    -o tutorial.pdf \
    -V geometry:margin=0.5in -V geometry:a4paper -V fontsize=10pt \
    --toc \
    --pdf-engine pdflatex
