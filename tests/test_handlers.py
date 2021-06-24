from srv.handlers import OPTA_DOMAIN, fetch_jwt, get_service, post_event, update_pod
from typing import Any
import pytest
from aioresponses import aioresponses

TEST_ORG_ID = "afd787b1-c64a-4134-a834-219f10b5acda"
TEST_ENVIRONMENT_ID = "7044f2d9-50d3-48b7-b466-86830630085c"
TEST_SERVICE_ID = "86b22777-368d-4bd5-b0e9-827fe95d7367"


@pytest.mark.asyncio
async def test_fetch_jwt():
    with aioresponses() as mocked:
        opta_token = "fake-token"
        fake_key = "fake-key"
        mocked.post(
            f"https://{OPTA_DOMAIN}/user/apikeys/validate",
            payload={
                "api_key": fake_key,
                "org_id": TEST_ORG_ID,
                "expires_at": None,
            },
            headers={"opta": opta_token},
            status=200,
        )

        json, jwt = await fetch_jwt(fake_key)
        assert json == {
            "api_key": fake_key,
            "org_id": TEST_ORG_ID,
            "expires_at": None,
        }
        assert jwt == opta_token


@pytest.mark.asyncio
async def test_get_service():
    with aioresponses() as mocked:
        opta_token = "fake-token"
        fake_key = "fake-key"
        mocked.post(
            f"https://{OPTA_DOMAIN}/user/apikeys/validate",
            payload={
                "api_key": fake_key,
                "org_id": TEST_ORG_ID,
                "expires_at": None,
            },
            headers={"opta": opta_token},
            status=200,
        )

        service_name = "fake-service"
        environment_name = "fake-env"
        org_id = TEST_ORG_ID
        mocked.get(
            f"https://{OPTA_DOMAIN}/config/services?name={service_name}&env_name={environment_name}&org_id={org_id}",
            payload=[
                {
                    "environment_id": TEST_ENVIRONMENT_ID,
                    "id": TEST_SERVICE_ID,
                    "latest_failed_deploy_time": "Fri, 03 Jan 2020 08:00:00 GMT",
                    "latest_opta_version": "12.4",
                    "latest_spec": "\n            test: yaml2\n            ",
                    "latest_successful_deploy_time": None,
                    "name": service_name,
                },
            ],
            status=200,
        )

        service = await get_service(environment_name, service_name)
        assert service == {
            "environment_id": TEST_ENVIRONMENT_ID,
            "id": TEST_SERVICE_ID,
            "latest_failed_deploy_time": "Fri, 03 Jan 2020 08:00:00 GMT",
            "latest_opta_version": "12.4",
            "latest_spec": "\n            test: yaml2\n            ",
            "latest_successful_deploy_time": None,
            "name": service_name,
        }


@pytest.mark.asyncio
async def test_update_pod():
    with aioresponses() as mocked:
        opta_token = "fake-token"
        fake_key = "fake-key"
        mocked.post(
            f"https://{OPTA_DOMAIN}/user/apikeys/validate",
            payload={
                "api_key": fake_key,
                "org_id": TEST_ORG_ID,
                "expires_at": None,
            },
            headers={"opta": opta_token},
            status=200,
        )

        mocked.put(
            f"https://{OPTA_DOMAIN}/kube-health/pods",
            payload={
                "cpu_usage": 10,
                "created_at": "2020-01-01T00:00:00-08:00",
                "deleted_at": None,
                "id": "fake-id",
                "image": "image-name",
                "memory_usage": 12,
                "org_id": "5cc8e35b-c25a-414e-bf98-52bd27c46f4e",
                "service_id": TEST_SERVICE_ID,
                "status": "running",
                "updated_at": "2020-01-02T03:00:00-08:00",
            },
            status=200,
        )

        res = await update_pod(
            pod_id="fake-id",
            service_id=TEST_SERVICE_ID,
            status="running",
            image="image-name",
            deleted_at=None,
            updated_at="2020-01-02T03:00:00-08:00",
            created_at="2020-01-01T00:00:00-08:00",
        )

        assert res == True


@pytest.mark.asyncio
async def test_post_event():
    with aioresponses() as mocked:
        opta_token = "fake-token"
        fake_key = "fake-key"
        mocked.post(
            f"https://{OPTA_DOMAIN}/user/apikeys/validate",
            payload={
                "api_key": fake_key,
                "org_id": TEST_ORG_ID,
                "expires_at": None,
            },
            headers={"opta": opta_token},
            status=200,
        )

        mocked.post(
            f"https://{OPTA_DOMAIN}/kube-health/events",
            payload={
                "event_type": "autoscale",
                "id": "8859101c-3399-4314-a34f-8185f97eeb51",
                "message": "scaled from 2 pods to 4 pods",
                "metadata": {
                    "old": 2,
                    "new": 4,
                },
                "org_id": "5cc8e35b-c25a-414e-bf98-52bd27c46f4e",
                "service_id": TEST_SERVICE_ID,
                "timestamp": "2020-01-01T00:00:00-08:00",
            },
            status=200,
        )

        res = await post_event(
            service_id=TEST_SERVICE_ID,
            event_type="autoscale",
            metadata={
                "old": 2,
                "new": 4,
            },
            timestamp="2020-01-01T00:00:00-08:00",
            message="scaled from 2 pods to 4 pods",
        )

        assert res == True
