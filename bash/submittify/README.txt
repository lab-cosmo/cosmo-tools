A script to prepare papers for submission
=========================================

Several journals have annoying requirements for submission 
(e.g. incorporated bibliography, remove comments, figures renamed
to fig*.*).

Usage:
Before running you need to compile fully your project to PDF, e.g.

$ pdflatex filename.tex; bibtex filename; pdflatex filename.tex

then you create a folder that will hold the submission, e.g. 

$ mkdir submit

you can then run the submittify as

$ submittify.sh filename submit/
