import json
import shlex

from cli_inventory import collect_cli_inventory
from ssh_client import execute_command


def check_ports():
    inventory = collect_cli_inventory()
    results = []

    for container in inventory["containers"]:
        container_id = container["id"]

        # docker port може повертати ненульовий код,
        # якщо контейнер не має опублікованих портів.
        # Тому перевіряємо порти через docker port,
        # а відсутність прив'язок обробляємо окремо.
        command = (
            f"docker port {shlex.quote(container_id)} "
            "2>/dev/null || true"
        )

        output = execute_command(command)

        results.append({
            "service": container["service"],
            "container_id": container_id[:12],
            "docker_port_output": output,
            "published_ports": container["published_ports"],
        })

    return results


if __name__ == "__main__":
    results = check_ports()

    print(json.dumps(results, indent=2, ensure_ascii=False))
