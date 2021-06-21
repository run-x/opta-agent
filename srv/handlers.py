from datetime import datetime
import os
from typing import Optional, Tuple

import aiohttp
import kopf

OPTA_DOMAIN = "api.app.runx.dev"

OPTA_TOKEN = os.environ.get("OPTA_TOKEN", "MISSING")


def is_valid_opta_pod(labels):
    return labels.get("opta.dev/environment-name") is not None and labels.get("opta.dev/layer-name") is not None


async def fetch_jwt() -> Tuple[dict, str]:
    global OPTA_TOKEN
    if OPTA_TOKEN == "MISSING":
        raise Exception("OPTA_TOKEN is not set")
    async with aiohttp.ClientSession() as session:
        # TODO: add opta auth token
        async with session.post(f"https://{OPTA_DOMAIN}/user/apikeys/validate", json={"api_key": OPTA_TOKEN}) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise Exception(f"Invalid response when attempting to validate the api token: {json}")
            jwt = resp.headers.get("opta")
            if jwt is None:
                raise Exception(f"Got an invalid jwt back: {jwt}")

            return json, jwt


async def get_service(environment_name, service_name):
    jwt_json, jwt = await fetch_jwt()
    org_id = jwt_json["org_id"]
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://{OPTA_DOMAIN}/config/services?name={service_name}&env_name={environment_name}&org_id={org_id}",
            headers={"opta": jwt},
        ) as resp:
            json = await resp.json()
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
):
    jwt_json, jwt = await fetch_jwt()
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
        async with session.put(
            f"https://{OPTA_DOMAIN}/kube-health/pods",
            json=body,
            headers={"opta": jwt},
        ):
            return


async def post_event(
    service_id: str,
    event_type: Optional[str],
    metadata: dict = None,
    timestamp: str = None,
    message: Optional[str] = None,
):
    jwt_json, jwt = await fetch_jwt()
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
        async with session.post(
            f"https://{OPTA_DOMAIN}/kube-health/events",
            json=body,
            headers={"opta": jwt},
        ):
            return


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


@kopf.on.create("pods")
async def create_opta_ui_pod(uid, status, labels, logger, **_):
    if not is_valid_opta_pod(labels):
        return
    try:
        environment_name = labels.get("opta.dev/environment-name")
        service_name = labels.get("opta.dev/layer-name")

        service = await get_service(environment_name, service_name)
        service_id = service["id"]
        created_at = get_pod_created_time_from_status(status)
        await update_pod(
            pod_id=uid,
            status=status.get("phase"),
            service_id=service_id,
            image=get_image_from_status(status),
            created_at=created_at or datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
    except Exception:
        logger.info(f"Failed to create pod {uid}")


@kopf.on.update("pods", field="status.phase")
async def update_opta_ui_pod_status(uid, status, labels, logger, new, **_):
    if not is_valid_opta_pod(labels):
        return
    try:
        environment_name = labels.get("opta.dev/environment-name")
        service_name = labels.get("opta.dev/layer-name")

        service = await get_service(environment_name, service_name)
        service_id = service["id"]
        created_at = get_pod_created_time_from_status(status)

        await update_pod(
            pod_id=uid,
            status=new,
            service_id=service_id,
            image=get_image_from_status(status),
            created_at=created_at or datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
    except Exception:
        logger.info(f"Failed to update pod {uid}")


@kopf.on.delete("pods")
async def delete_opta_ui_pod(uid, logger, labels, status, **_):
    if not is_valid_opta_pod(labels):
        return
    try:
        environment_name = labels.get("opta.dev/environment-name")
        service_name = labels.get("opta.dev/layer-name")

        service = await get_service(environment_name, service_name)
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
        logger.info(f"Failed to delete pod {uid}")


@kopf.on.update("deployment", field="spec.replicas")
async def update_deployment_info(old, new, labels, logger, **_):
    try:
        environment_name = labels.get("opta.dev/environment-name")
        service_name = labels.get("opta.dev/layer-name")
        service = await get_service(environment_name, service_name)
        service_id = service["id"]

        await post_event(
            service_id=service_id,
            event_type="autoscale",
            metadata={
                "old": int(old),
                "new": int(new),
            },
            timestamp=datetime.now().isoformat(),
            message=f"scaled from {old} pods to {new} pods",
        )
    except Exception as e:
        logger.error(e)
