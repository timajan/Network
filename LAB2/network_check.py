import json

from api_inventory import collect_api_inventory


PROJECT = "university_lab1"

FRONTEND = f"{PROJECT}_frontend"
BACKEND = f"{PROJECT}_backend"


def check_network_configuration(inventory: dict) -> dict:
    containers = inventory["containers"]
    errors = []

    expected_networks = {
        "proxy": {FRONTEND},
        "app": {FRONTEND, BACKEND},
        "db": {BACKEND},
    }

    expected_counts = {
        "proxy": 1,
        "app": 2,
        "db": 1,
    }

    # Перевіряємо кількість контейнерів кожного сервісу
    for service, expected_count in expected_counts.items():
        actual_count = sum(
            container["service"] == service
            for container in containers
        )

        if actual_count != expected_count:
            errors.append(
                f"Service {service}: expected {expected_count} "
                f"containers, got {actual_count}"
            )

    # Перевіряємо мережі та опубліковані порти
    for container in containers:
        service = container["service"]
        container_id = container["id"][:12]

        if service not in expected_networks:
            errors.append(
                f"Unknown service: {service} ({container_id})"
            )
            continue

        actual_networks = set(container["networks"])
        required_networks = expected_networks[service]

        if actual_networks != required_networks:
            errors.append(
                f"{service} ({container_id}): "
                f"expected networks {sorted(required_networks)}, "
                f"got {sorted(actual_networks)}"
            )

        published_ports = container["published_ports"]

        if service != "proxy" and published_ports:
            errors.append(
                f"{service} ({container_id}) "
                f"must not publish host ports"
            )

        if service == "proxy":
            expected_port = {
                "container_port": "80/tcp",
                "host_ip": "127.0.0.1",
                "host_port": "18080",
            }

            if published_ports != [expected_port]:
                errors.append(
                    f"proxy ({container_id}): "
                    f"unexpected published ports: {published_ports}"
                )

    return {
        "status": "PASS" if not errors else "FAIL",
        "containers_checked": len(containers),
        "checks": {
            "expected_services": expected_counts,
            "expected_networks": {
                service: sorted(networks)
                for service, networks in expected_networks.items()
            },
            "proxy_port": "127.0.0.1:18080->80/tcp",
        },
        "errors": errors,
    }


if __name__ == "__main__":
    inventory = collect_api_inventory()
    result = check_network_configuration(inventory)

    print(json.dumps(result, indent=2, ensure_ascii=False))
