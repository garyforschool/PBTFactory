FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1

RUN apt update && apt install -y git

RUN pip install --no-cache-dir numpy hypothesis pytest pytest-cov pytest-timeout

RUN pip install git+https://github.com/garyforschool/mutmut.git

WORKDIR /workdir

# COPY . .
COPY run_mutmut.sh /workdir/run_mutmut.sh
COPY run_mutmut.py /workdir/run_mutmut.py
COPY run_tests.sh /usr/src/scripts/run_tests.sh
COPY run_test_code.sh /usr/src/scripts/run_test_code.sh
COPY run_python_code.sh /usr/src/scripts/run_python_code.sh

CMD ["bash"]
