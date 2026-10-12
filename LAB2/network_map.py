import json

from api_inventory import collect_api_inventory


def build_network_map(inventory: dict) -> dict:
    network_map = {}

    for container in inventory["containers"]:
        service = container["service"]
        container_id = container["id"][:12]

        for network_name, ip_address in container["networks"].items():
            if network_name not in network_map:
                network_map[network_name] = []

            network_map[network_name].append({
                "service": service,
                "container_id": container_id,
                "ip_address": ip_address,
            })

    for network_name in network_map:
        network_map[network_name].sort(
            key=lambda item: (item["service"], item["container_id"])
        )

    return dict(sorted(network_map.items()))


if __name__ == "__main__":
    inventory = collect_api_inventory()
    result = build_network_map(inventory)

    print(json.dumps(result, indent=2, ensure_ascii=False))
