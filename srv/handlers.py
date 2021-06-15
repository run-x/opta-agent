import os
from typing import Tuple

import aiohttp
import kopf

if os.environ.get("OPTA_STAGING"):
    OPTA_DOMAIN = "api.staging.runx.dev"
else:
    OPTA_DOMAIN = "api.app.runx.dev"


def is_opta_pod(labels):
    return labels["opta-manage"] is not None


async def fetch_jwt(api_key: str) -> Tuple[dict, str]:
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
        _, jwt = await fetch_jwt("TODO: get api token")
        # TODO: add opta auth token
        async with session.put(f"https://{OPTA_DOMAIN}/pods", json=body, headers={"opta": jwt}) as resp:
            return resp.json()


@kopf.on.create("pods")
async def create_opta_ui_pod(uid, meta, labels, spec, **kwargs):
    if not is_opta_pod(labels):
        return
    print("on create:", uid)
    pass


@kopf.on.update("pods")
async def update_opta_ui_pod(uid, meta, labels, **kwargs):
    if not is_opta_pod(labels):
        return
    print("on update:", uid)
    pass


@kopf.on.delete("pods")
async def delete_opta_ui_pod(uid, meta, labels, **kwargs):
    if not is_opta_pod(labels):
        return

    print("on delete:", uid)
    pass
