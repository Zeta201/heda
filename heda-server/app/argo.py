import asyncio
import json
import os
from fastapi import WebSocket, WebSocketDisconnect
import httpx
import yaml
from datetime import datetime
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from dotenv import load_dotenv


load_dotenv()

ARGO_NAMESPACE = os.environ.get("ARGO_NAMESPACE")
DOCKER_HUB_USERNAME = os.environ.get("DOCKER_HUB_USERNAME")
# Kubernetes in-cluster Argo server
ARGO_SERVER = os.environ.get("ARGO_SERVER")
POLL_INTERVAL = os.environ.get("POLL_INTERVAL")

def load_k8s_token():
    try:
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

ARGO_TOKEN = load_k8s_token()

def load_kube_config_safe():
    try:
        # Works inside Kubernetes
        config.load_incluster_config()
    except ConfigException:
        # Works locally (minikube / kind / ~/.kube/config)
        config.load_kube_config()

load_kube_config_safe()


def submit_workflow(repo_url: str, commit_sha: str) -> str:
   
    # Generate a unique image tag per commit
    # short_sha = commit_sha[:7]
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    image_tag = f"docker.io/{DOCKER_HUB_USERNAME}/heda-experiment:{timestamp}"

    # Load workflow YAML
    with open("/app/app/workflows/experiment.yaml") as f:
        workflow = yaml.safe_load(f)

    # Inject parameters
    workflow["spec"]["arguments"]["parameters"] = [
        {"name": "repo_url", "value": repo_url},
        {"name": "commit_sha", "value": commit_sha},
        {"name": "image_tag", "value": image_tag},
    ]

    # Create workflow CRD
    api = client.CustomObjectsApi()

    result = api.create_namespaced_custom_object(
        group="argoproj.io",
        version="v1alpha1",
        namespace=ARGO_NAMESPACE,
        plural="workflows",
        body=workflow,
    )

    return result["metadata"]["name"]


async def websocket_stream_workflow_run(websocket: WebSocket, workflow_name: str):
    await websocket.accept()

    url = f"{ARGO_SERVER}/api/v1/workflows/{ARGO_NAMESPACE}/{workflow_name}/log?logOptions.container=main"
    headers = {"Authorization": f"Bearer {ARGO_TOKEN}"} if ARGO_TOKEN else {}

    seen = set()  # (podName, content)

    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        try:
            while True:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    await websocket.send_json({
                        "event": "error",
                        "message": f"Argo API returned {resp.status_code}"
                    })
                    break

                for line in resp.text.splitlines():
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                        result = data.get("result")
                        if not result:
                            continue

                        key = (result.get("podName"), result.get("content"))
                        if key in seen:
                            continue

                        seen.add(key)

                        await websocket.send_json({
                            "event": "log",
                            "pod": result.get("podName"),
                            "line": result.get("content"),
                        })
                    except json.JSONDecodeError:
                        continue

                # OPTIONAL: stop when workflow is completed
                # You can query workflow status here and break if Succeeded/Failed

                await asyncio.sleep(POLL_INTERVAL)

        except WebSocketDisconnect:
            print(f"WebSocket disconnected for workflow {workflow_name}")

        except Exception as e:
            await websocket.send_json({"event": "error", "message": str(e)})

        finally:
            await websocket.close()

