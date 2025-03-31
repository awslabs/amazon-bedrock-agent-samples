test:
	pip install -r dev.requirements.txt
	cd src
	python -m unittest discover tests

format:
	black .
	docformatter --in-place *py

lint:
	pylint **/[^_]*.py --ignore=_version.py && echo "PYLINTING PASS"
	# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics