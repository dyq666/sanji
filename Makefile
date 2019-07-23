shell:
	pipenv run ipython

test:
	pipenv run pytest test.py

pep8:
	pipenv run pycodestyle --ignore=E731,W503 ./

install:
	pipenv install
