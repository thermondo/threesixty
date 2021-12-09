MSGLANGS = $(wildcard */locale/*/LC_MESSAGES/*.po)
MSGOBJS = $(MSGLANGS:.po=.mo)

SCSSFILES = $(wildcard */static/*/*.scss)
SASSJOBS = $(SCSSFILES:.scss=.css)

sass: $(SASSJOBS)

%.css: %.scss
	sassc $*.scss > $@

gettext: $(MSGOBJS)

%.mo: %.po
	msgfmt -c -o $@ $*.po
