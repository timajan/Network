import json
import shlex

from ssh_client import execute_command


PROJECT_NAME = "university_lab1"


def get_container_ids() -> list[str]:
    command = (
        "docker ps -a --no-trunc "
        f"--filter {shlex.quote('label=com.docker.compose.project=' + PROJECT_NAME)} "
        "--format '{{.ID}}'"
    )

    output = execute_command(command)

    return output.splitlines() if output else []


def inspect_container(container_id: str) -> dict:
    command = (
        "docker inspect --format '{{json .}}' "
        + shlex.quote(container_id)
    )

    output = execute_command(command)
    data = json.loads(output)

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

    return {
        "service": data["Config"]["Labels"].get(
            "com.docker.compose.service", ""
        ),
        "id": data["Id"],
        "image": data["Config"]["Image"],
        "state": data["State"]["Status"],
        "started_at": data["State"]["StartedAt"],
        "networks": networks,
        "published_ports": published_ports,
    }


def collect_cli_inventory() -> dict:
    container_ids = get_container_ids()

    containers = [
        inspect_container(container_id)
        for container_id in container_ids
    ]

    return {
        "hostname": execute_command("hostname"),
        "project": PROJECT_NAME,
        "containers": containers,
    }


if __name__ == "__main__":
    inventory = collect_cli_inventory()

    print(json.dumps(inventory, indent=2, ensure_ascii=False))
