.PHONY: install test simulate check

install:
	python -m pip install -e .

test:
	python -m unittest discover -s tests -v

simulate:
	hullrakshak-sensors --transport simulated --once --classify

check:
	python -m compileall -q host/src tests
	python -m unittest discover -s tests -v
