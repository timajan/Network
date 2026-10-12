import json

from cli_inventory import collect_cli_inventory
from api_inventory import collect_api_inventory


def normalize_container(container: dict) -> dict:
    """Нормалізація даних контейнера для порівняння."""

    return {
        "id": container["id"],
        "service": container["service"],
        "image": container["image"],
        "state": container["state"],
        "networks": dict(sorted(container["networks"].items())),
        "published_ports": sorted(
            container["published_ports"],
            key=lambda port: (
                port["container_port"],
                port["host_ip"],
                str(port["host_port"]),
            ),
        ),
    }


def compare_inventories(cli_data: dict, api_data: dict) -> dict:
    """Порівняння контейнерів за повними Docker ID."""

    cli_containers = {
        container["id"]: normalize_container(container)
        for container in cli_data["containers"]
    }

    api_containers = {
        container["id"]: normalize_container(container)
        for container in api_data["containers"]
    }

    differences = []

    cli_ids = set(cli_containers)
    api_ids = set(api_containers)

    # Контейнери, присутні тільки в одному джерелі
    for container_id in sorted(cli_ids - api_ids):
        differences.append({
            "container_id": container_id,
            "field": "container",
            "cli": "present",
            "api": "missing",
        })

    for container_id in sorted(api_ids - cli_ids):
        differences.append({
            "container_id": container_id,
            "field": "container",
            "cli": "missing",
            "api": "present",
        })

    # Порівняння спільних контейнерів
    for container_id in sorted(cli_ids & api_ids):
        cli_container = cli_containers[container_id]
        api_container = api_containers[container_id]

        for field in (
            "service",
            "image",
            "state",
            "networks",
            "published_ports",
        ):
            if cli_container[field] != api_container[field]:
                differences.append({
                    "container_id": container_id,
                    "field": field,
                    "cli": cli_container[field],
                    "api": api_container[field],
                })

    return {
        "status": "MATCH" if not differences else "MISMATCH",
        "cli_count": len(cli_containers),
        "api_count": len(api_containers),
        "differences": differences,
    }


if __name__ == "__main__":
    print("Collecting CLI inventory...")
    cli_inventory = collect_cli_inventory()

    print("Collecting API inventory...")
    api_inventory = collect_api_inventory()

    print("Comparing results...")
    result = compare_inventories(cli_inventory, api_inventory)

    print(json.dumps(result, indent=2, ensure_ascii=False))
