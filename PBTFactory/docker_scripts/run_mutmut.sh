mkdir -p /usr/src/project
cp -r $PROJECT_ROOT/* /usr/src/project

pip install -e /usr/src/project 2> /dev/null

# Collect coverage data
pytest -W ignore::DeprecationWarning /workdir/tests/test*.py --cov --cov-branch --cov-report=html:/workdir/mutmut_report/cov_report --cov-report=json:/workdir/mutmut_report/cov_report/coverage.json
python /workdir/run_mutmut.py