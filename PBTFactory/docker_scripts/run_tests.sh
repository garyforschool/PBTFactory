export PYTHONPATH=/usr/src/project
python -m pytest -W ignore::DeprecationWarning -x --timeout 150 /workdir/tests/test*.py