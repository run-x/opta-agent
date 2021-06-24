build:
	docker build -t opta-agent:dev .

lint:
	pipenv run python lint.py --apply

test:
	pipenv run coverage run
	pipenv run coverage report