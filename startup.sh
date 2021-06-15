set -exo pipefail

export PYTHONPATH=$(pwd)

source $(pipenv --venv)/bin/activate

# TODO should be separated into prestart and start scripts
cd srv

kopf run /src/handlers.py --verbose
