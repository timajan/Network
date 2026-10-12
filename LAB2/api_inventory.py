import json
import os

import docker

from cli_inventory import PROJECT_NAME


SSH_HOST = os.getenv("SSH_HOST", "176.98.11.139")
SSH_PORT = int(os.getenv("SSH_PORT", "222"))
SSH_USER = os.getenv("SSH_USER", "sysadmin")


def collect_api_inventory() -> dict:
    docker_host = (
        f"ssh://{SSH_USER}@{SSH_HOST}:{SSH_PORT}"
    )

    client = docker.DockerClient(
        base_url=docker_host,
        use_ssh_client=True,
        timeout=15,
    )

    try:
        containers = client.containers.list(
            all=True,
            filters={
                "label": f"com.docker.compose.project={PROJECT_NAME}"
            },
        )

        result = []

        for container in containers:
            container.reload()
            data = container.attrs

            networks = {}

            for name, network in data["NetworkSettings"]["Networks"].items():
                networks[name] = network.get("IPAddress", "")

            published_ports = []

            for container_port, bindings in data["NetworkSettings"]["Ports"].items():
                if not bindings:
                    continue

                for binding in bindings:
                    published_ports.append(
                        {
                            "container_port": container_port,
                            "host_ip": binding["HostIp"],
                            "host_port": binding["HostPort"],
                        }
                    )

            result.append(
                {
                    "service": container.labels.get(
                        "com.docker.compose.service", ""
                    ),
                    "id": container.id,
                    "image": data["Config"]["Image"],
                    "state": data["State"]["Status"],
                    "started_at": data["State"]["StartedAt"],
                    "networks": networks,
                    "published_ports": published_ports,
                }
            )

        return {
            "hostname": client.info()["Name"],
            "project": PROJECT_NAME,
            "containers": result,
        }

    finally:
        client.close()


if __name__ == "__main__":
    inventory = collect_api_inventory()

    print(json.dumps(inventory, indent=2, ensure_ascii=False))

