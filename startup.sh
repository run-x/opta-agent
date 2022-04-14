set -exo pipefail

export PYTHONPATH=$(pwd)

source $(pipenv --venv)/bin/activate

# TODO should be separated into prestart and start scripts
cd srv

if [[ -n ${VERBOSE} ]]; then
	echo "Running verbose mode"
	kopf run handlers.py --liveness=http://0.0.0.0:8080/healthz  --verbose --log-format=full --namespace=!kube-system,!linkerd
fi

if [[ -n ${DEBUG} ]]; then
	echo "Running debug mode"
	kopf run handlers.py --liveness=http://0.0.0.0:8080/healthz  --debug --log-format=full --namespace=!kube-system,!linkerd
fi

kopf run handlers.py --liveness=http://0.0.0.0:8080/healthz --log-format=full --namespace=!kube-system,!linkerd
