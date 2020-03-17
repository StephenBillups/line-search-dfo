#!/bin/bash

#FILENAME=full_paper

# 

for FILENAME in short_paper fewer_points convex dissertation generalizations
# for FILENAME in short_paper
do
    rm -f $FILENAME.aux $FILENAME.log $FILENAME.blg $FILENAME.toc
    pdflatex $FILENAME.tex
    pdflatex $FILENAME.tex 
    bibtex $FILENAME.aux 
    bibtex $FILENAME.aux 
    pdflatex $FILENAME.tex 
    pdflatex $FILENAME.tex
    rm -f $FILENAME.aux $FILENAME.log $FILENAME.blg $FILENAME.toc
done

