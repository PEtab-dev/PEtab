#!/bin/sh

# Build a pdflatex document from the tutorial

pandoc v1/tutorial/tutorial.rst \
    -o tutorial_v1.pdf \
    -V geometry:margin=1.5in -V geometry:a4paper -V fontsize=10pt \
    -V urlcolor=cyan \
    --toc \
    --pdf-engine pdflatex
