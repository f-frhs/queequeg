#  Makefile for Queequeg
#

# must be specified by a user
WORDNETDICT=/src/wordnet/dict

VERSION=0.91
PACKAGE=queequeg-$(VERSION)

all:	# do nothing default

clean:
	-rm -f *.pyc *.bak *.o core ,* *~ tags TAGS "#"* ".#"*
	-rm -f htdocs/*~ htdocs/"#"* htdocs/".#"*
	-rm ./dict.cdb ./dict.txt

dict:
	python ./convdict.py index.special $(WORDNETDICT)

localdict: dict.cdb dict.txt
	-mkdir LOCAL
	mv dict.cdb dict.txt LOCAL/
	ln -s LOCAL/dict.cdb LOCAL/dict.txt .
