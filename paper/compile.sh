#!/bin/bash

#FILENAME=full_paper

# 

# for FILENAME in short_paper gc full_paper 
for FILENAME in short_paper
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

