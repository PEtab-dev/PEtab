#!/bin/sh

# Build a pdflatex document from the tutorial

pandoc tutorial.rst \
    -o tutorial.pdf \
    -V geometry:margin=1.5in -V geometry:a4paper -V fontsize=10pt \
    --toc \
    --pdf-engine pdflatex
