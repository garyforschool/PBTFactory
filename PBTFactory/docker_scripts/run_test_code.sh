cp -r /workdir/project /workdir/project_copy
pip install -e /workdir/project_copy 2> /dev/null

pytest -W ignore::DeprecationWarning /workdir/test_code.py