#  Makefile for Queequeg
#

# must be specified by a user
WORDNETDICT=/home/ben/projects/queequeg/WordNet-3.0/dict

VERSION=0.91
PACKAGE=queequeg-$(VERSION)

all:	# do nothing default

test:
	perl t/queequeg.t

clean:
	-rm -f *.pyc
	-rm README

veryclean: 	clean
	-rm -f ./dict.txt

dict:	$(WORDNETDICT)
	python ./convdict.py index.special $(WORDNETDICT)

HTMLDOC=htdocs/index-e.html

README:	$(HTMLDOC)
	lynx -dump $(HTMLDOC) > $@
