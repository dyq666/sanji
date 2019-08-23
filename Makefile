# Makefile must use tab, not 4 space.

shell:
	pipenv run ipython

test:
	pipenv run pytest test.py

# E501 Line lengths are recommended to be no greater than 79 characters (每行字符没什么要求)
# E731 lambda
# W503 Line break occurred before a binary operator (迷之规则)
pep8:
	pipenv run pycodestyle --ignore=E501,E731,W503 ./

install:
	pipenv install

venv:
	pipenv shell
