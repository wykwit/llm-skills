.PHONY: install uninstall lint link

install:
	./tools/install.sh

uninstall:
	./tools/uninstall.sh

lint:
	./tools/lint.py

link:
	./tools/link.sh --prune
