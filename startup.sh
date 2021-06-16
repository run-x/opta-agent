set -exo pipefail

export PYTHONPATH=$(pwd)

source $(pipenv --venv)/bin/activate

# TODO should be separated into prestart and start scripts
cd srv

kopf run handlers.py --liveness=http://0.0.0.0:8080/healthz  --verbose
