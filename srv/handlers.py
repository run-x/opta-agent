import os
from datetime import datetime
from typing import Literal, Optional, Tuple

import aiohttp
import kopf

OPTA_DOMAIN = "api.app.runx.dev"

OPTA_TOKEN = os.environ.get("OPTA_TOKEN", "MISSING")


def is_valid_opta_pod(labels):
    return labels.get("opta.dev/environment-name") is not None and labels.get("opta.dev/layer-name") is not None


async def fetch_jwt(api_key: str) -> Tuple[dict, str]:
    async with aiohttp.ClientSession() as session:
        # TODO: add opta auth token
        async with session.post(f"https://{OPTA_DOMAIN}/user/apikeys/validate", json={"api_key": api_key}) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise Exception(f"Invalid response when attempting to validate the api token: {json}")
            jwt = resp.headers.get("opta")
            if jwt is None:
                raise Exception(f"Got an invalid jwt back: {jwt}")

            return json, jwt


async def get_service(environment_name, service_name):
    jwt_json, jwt = await fetch_jwt(OPTA_TOKEN)
    org_id = jwt_json["org_id"]
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://{OPTA_DOMAIN}/config/services?name={service_name}&env_name={environment_name}&org_id={org_id}",
            headers={"opta": jwt},
        ) as resp:
            json = await resp.json()
            if len(json) == 0:
                return None
            service = json[0]
            return service


async def update_pod(
    pod_id: str,
    service_id: str,
    status: Optional[str] = None,
    image: Optional[str] = None,
    deleted_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Literal[True]:
    jwt_json, jwt = await fetch_jwt(OPTA_TOKEN)
    org_id = jwt_json["org_id"]
    async with aiohttp.ClientSession() as session:
        body = {
            "id": pod_id,
            "org_id": org_id,
            "service_id": service_id,
            "status": status,
            "image": image,
            "created_at": created_at,
            "updated_at": updated_at,
            "deleted_at": deleted_at,
        }
        async with session.put(f"https://{OPTA_DOMAIN}/kube-health/pods", json=body, headers={"opta": jwt}) as resp:
            json = await resp.json()
            if resp.status != 200 and resp.status != 201:
                raise Exception(f"Invalid response when attempting to validate the api token: {json}")
            return True


async def post_event(
    service_id: str,
    event_type: Optional[str],
    metadata: Optional[dict] = None,
    timestamp: Optional[str] = None,
    message: Optional[str] = None,
) -> Literal[True]:
    jwt_json, jwt = await fetch_jwt(OPTA_TOKEN)
    org_id = jwt_json["org_id"]
    async with aiohttp.ClientSession() as session:
        body = {
            "org_id": org_id,
            "service_id": service_id,
            "event_type": event_type,
            "message": message,
            "metadata": metadata,
            "timestamp": timestamp,
        }
        async with session.post(f"https://{OPTA_DOMAIN}/kube-health/events", json=body, headers={"opta": jwt}) as resp:
            json = await resp.json()
            if resp.status != 200 and resp.status != 201:
                raise Exception(f"Invalid response when attempting to validate the api token: {json}")
            return True


"""
need:
    org_id
    service_id
    status
    image
    memory usage
    cpu usage

questions:
    1. how to get service_id from inside of this pod? -> grab
    2. how to get cpu and memory usage (do i have to query the kubenetes api?)
    3. i can grab the org_id from the /validate response, yeah?
    4. advice on how to test this?
"""


def get_image_from_status(status):
    for container in status["containerStatuses"]:
        if container.get("name") == "k8s-service":
            return container.get("image")
    return None


def get_pod_created_time_from_status(status):
    for condition in status["conditions"]:
        if condition["type"] == "Initialized":
            return condition["lastTransitionTime"]
    return None


@kopf.timer("pods", interval=60.0)
async def update_opta_ui_pod_status(uid, status, labels, logger, **_):
    if not is_valid_opta_pod(labels):
        return
    try:
        logger.info(f"Routine check on pod {uid}")
        environment_name = labels.get("opta.dev/environment-name")
        service_name = labels.get("opta.dev/layer-name")

        service = await get_service(environment_name, service_name)
        if service is None:
            raise Exception(
                f"No service with name {service_name} found in this environment-- has opta apply been run on it after "
                "adding the runx module?"
            )
        service_id = service["id"]
        created_at = get_pod_created_time_from_status(status)

        await update_pod(
            pod_id=uid,
            status=status["phase"],
            service_id=service_id,
            image=get_image_from_status(status),
            created_at=created_at or datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
    except Exception:
        logger.error(f"Failed to update pod {uid}:", exc_info=True)


@kopf.on.delete("pods", retries=5)
async def delete_opta_ui_pod(uid, logger, labels, status, **_):
    if not is_valid_opta_pod(labels):
        return
    try:
        logger.info(f"Deletion detected on pod {uid}")
        environment_name = labels.get("opta.dev/environment-name")
        service_name = labels.get("opta.dev/layer-name")

        service = await get_service(environment_name, service_name)
        if service is None:
            raise Exception(
                f"No service with name {service_name} found in this environment-- has opta apply been run on it after "
                "adding the runx module?"
            )
        service_id = service["id"]
        created_at = get_pod_created_time_from_status(status)

        await update_pod(
            pod_id=uid,
            status=status.get("phase"),
            service_id=service_id,
            image=get_image_from_status(status),
            created_at=created_at or datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            deleted_at=datetime.now().isoformat(),
        )
    except Exception:
        logger.error(f"Failed to delete pod {uid}:", exc_info=True)


@kopf.on.update("deployment", field="spec.replicas")
async def update_deployment_info(uid, old, new, labels, logger, **_):
    try:
        logger.info(f"Replica changed detected on deployment {uid}")
        environment_name = labels.get("opta.dev/environment-name")
        service_name = labels.get("opta.dev/layer-name")
        service = await get_service(environment_name, service_name)
        if service is None:
            raise Exception(
                f"No service with name {service_name} found in this environment-- has opta apply been run on it after "
                "adding the runx module?"
            )
        service_id = service["id"]

        await post_event(
            service_id=service_id,
            event_type="autoscale",
            metadata={"old": int(old), "new": int(new)},
            timestamp=datetime.now().isoformat(),
            message=f"scaled from {old} pods to {new} pods",
        )
    except Exception:
        logger.error(f"Failed to send replica change event for deployment {uid}:", exc_info=True)
