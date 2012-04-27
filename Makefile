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
	-rm -f ./dict.cdb ./dict.txt

dict:	$(WORDNETDICT)
	python ./convdict.py index.special $(WORDNETDICT)

localdict: dict.cdb dict.txt
	-mkdir LOCAL
	mv dict.cdb dict.txt LOCAL/
	ln -s LOCAL/dict.cdb LOCAL/dict.txt .

HTMLDOC=htdocs/index-e.html

README:	$(HTMLDOC)
	lynx -dump $(HTMLDOC) > $@
