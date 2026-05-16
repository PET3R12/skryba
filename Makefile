install:
	poetry install --no-root

format:
	poetry run ruff format .
	poetry run ruff check . --fix

check:
	poetry run ruff format --check .

test:
	poetry run pytest ./tests -vv

run-tts:
	poetry run python ./skryba/tts_services/eleven_labs.py

run-app:
	poetry run streamlit run ./run_app.py

run-app-client:
	poetry run streamlit run ./run_app.py --client.toolbarMode "viewer"
