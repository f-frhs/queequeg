# $Id: Makefile,v 1.5 2003/07/27 13:54:05 euske Exp $
#
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

putwww:
	env RSYNC_RSH=ssh rsync -Cabuvz --backup-dir=/home/users/e/eu/euske/htdocs.old \
		./htdocs/ euske@queequeg.sf.net:/home/groups/q/qu/queequeg/htdocs/

cvscommit:
	env CVS_RSH=ssh cvs -d :ext:euske@cvs.queequeg.sourceforge.net:/cvsroot/queequeg commit;

cvsup:
	env CVS_RSH=ssh cvs -d :ext:euske@cvs.queequeg.sourceforge.net:/cvsroot/queequeg update;

pack: clean
	cd ..; if [ ! -L $(PACKAGE) ]; then ln -s queequeg ./$(PACKAGE); fi
	cd ..; tar c --numeric-owner --exclude LOCAL --exclude CVS --gzip --dereference \
		-f $(PACKAGE).tar.gz $(PACKAGE);
