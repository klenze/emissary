TEX = pdflatex

TARGET = Intro.pdf
SHELL=/bin/bash

all: ${TARGET}

clean:
	rm -f *.aux *.log *.out

LATEX   = pdflatex -interaction batchmode -halt-on-error -file-line-error
.PHONY: quick test push

%.aux: %.tex
	${LATEX} -draftmode $^
%.pdf: %.tex %.aux
	${LATEX} $<
	@echo "all ok."

.PRECIOUS: %.aux
