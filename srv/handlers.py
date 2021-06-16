import os
from typing import Tuple

import aiohttp
import kopf

if os.environ.get("OPTA_STAGING"):
    OPTA_DOMAIN = "api.staging.runx.dev"
else:
    OPTA_DOMAIN = "api.app.runx.dev"

OPTA_TOKEN = os.environ.get("OPTA_TOKEN", "MISSING")


def is_opta_pod(labels):
    return labels["opta-manage"] is not None


async def fetch_jwt(api_key: str) -> Tuple[dict, str]:
    if api_key == "MISSING":
        raise Exception("OPTA_TOKEN is not set")
    async with aiohttp.ClientSession() as session:
        # TODO: add opta auth token
        async with session.post(f"https://{OPTA_DOMAIN}/user/apikeys/validate", json={"api_key": api_key}) as resp:
            if resp.status != 200:
                raise Exception(f"Invalid response when attempting to validate the api token: {resp.json()}")
            jwt = resp.headers.get("opta")
            if jwt is None:
                raise Exception(f"Got an invalid jwt back: {jwt}")

            json = await resp.json()
            return json, jwt


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


async def send_http_request(body):
    async with aiohttp.ClientSession() as session:
        _, jwt = await fetch_jwt(OPTA_TOKEN)
        # TODO: add opta auth token
        async with session.put(f"https://{OPTA_DOMAIN}/pods", json=body, headers={"opta": jwt}) as resp:
            return resp.json()


@kopf.on.create("pods")
async def create_opta_ui_pod(uid, meta, labels, spec, **kwargs):
    print("on create:", uid, meta, labels, spec, kwargs)
    if not is_opta_pod(labels):
        print(f"{uid} is opta pod")
        return
    print(f"{uid} is not opta pod")
    pass


@kopf.on.update("pods")
async def update_opta_ui_pod(uid, meta, labels, **kwargs):
    print("on update:", uid, meta, labels, kwargs)
    if not is_opta_pod(labels):
        print(f"{uid} is opta pod")
        return
    print(f"{uid} is not opta pod")
    pass


@kopf.on.delete("pods")
async def delete_opta_ui_pod(uid, meta, labels, **kwargs):
    print("on delete:", uid, meta, labels, kwargs)
    if not is_opta_pod(labels):
        print(f"{uid} is opta pod")
        return
    print(f"{uid} is not opta pod")
    pass
