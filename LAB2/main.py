import csv
import json
from datetime import datetime, timezone

from cli_inventory import collect_cli_inventory
from api_inventory import collect_api_inventory
from compare import compare_inventories
from network_check import check_network_configuration
from http_check import check_http
from network_map import build_network_map
from port_check import check_ports


def main():
    timestamp = datetime.now(timezone.utc).isoformat()

    print("[1/7] Collecting Docker CLI inventory...")
    cli_inventory = collect_cli_inventory()

    print("[2/7] Collecting Docker API inventory...")
    api_inventory = collect_api_inventory()

    print("[3/7] Comparing CLI and API...")
    comparison = compare_inventories(
        cli_inventory,
        api_inventory,
    )

    print("[4/7] Checking network configuration...")
    network_check = check_network_configuration(api_inventory)

    print("[5/7] Checking HTTP...")
    http_check = check_http()

    print("[6/7] Building network map...")
    network_map = build_network_map(api_inventory)

    print("[7/7] Checking published ports...")
    port_results = check_ports()
    
    # Зберігаємо повну інвентаризацію
    inventory = {
        "timestamp": timestamp,
        "hostname": api_inventory["hostname"],
        "project": api_inventory["project"],
        "cli": cli_inventory,
        "api": api_inventory,
        "comparison": comparison,
        "network_check": network_check,
        "http_check": http_check,
        "network_map": network_map,
        "port_check": port_results,
    }

    with open("inventory.json", "w", encoding="utf-8") as file:
        json.dump(
            inventory,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # Формуємо результати перевірок
    rows = [
        {
            "timestamp": timestamp,
            "check": "cli_api_comparison",
            "status": comparison["status"],
            "details": (
                f"CLI={comparison['cli_count']}, "
                f"API={comparison['api_count']}, "
                f"differences={len(comparison['differences'])}"
            ),
        },
        {
            "timestamp": timestamp,
            "check": "network_configuration",
            "status": network_check["status"],
            "details": (
                f"containers={network_check['containers_checked']}, "
                f"errors={len(network_check['errors'])}"
            ),
        },
        {
            "timestamp": timestamp,
            "check": "http_check",
            "status": http_check["status"],
            "details": (
                f"http_ok={http_check['http_ok']}, "
                f"counter_increased={http_check['counter_increased']}"
            ),
        },
    ]

    expected_ports = {
        "proxy": "80/tcp -> 127.0.0.1:18080",
        "app": "",
        "db": "",
    }

    port_errors = [
        result
        for result in port_results
        if result["docker_port_output"]
   	!= expected_ports.get(result["service"])
    ]

    rows.append({
        "timestamp": timestamp,
    	"check": "docker_port",
    	"status": "PASS" if not port_errors else "FAIL",
    	"details": (
        	f"containers={len(port_results)}, "
        	f"errors={len(port_errors)}"
    	),
    })

    rows.append({
    	"timestamp": timestamp,
    	"check": "network_map",
    	"status": "PASS" if network_map else "FAIL",
        "details": (
            f"networks={len(network_map)}, "
            f"attachments={sum(len(items) for items in network_map.values())}"
    	),
    })

    # Додаємо результати окремих HTTP-запитів
    for request in http_check["requests"]:
        rows.append(
            {
                "timestamp": timestamp,
                "check": f"http_request_{request['request_number']}",
                "status": (
                    "PASS"
                    if request["status_code"] == 200
                    else "FAIL"
                ),
                "details": (
                    f"status_code={request['status_code']}, "
                    f"elapsed_ms={request['elapsed_ms']}, "
                    f"instance={request['instance']}, "
                    f"counter={request['counter']}, "
                    f"error={request['error']}"
                ),
            }
        )

    with open("report.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["timestamp", "check", "status", "details"],
        )

        writer.writeheader()
        writer.writerows(rows)

    print("\n=== SUMMARY ===")
    print(f"CLI/API comparison: {comparison['status']}")
    print(f"Network configuration: {network_check['status']}")
    print(f"HTTP check: {http_check['status']}")

    print("\nGenerated files:")
    print(" - inventory.json")
    print(" - report.csv")


if __name__ == "__main__":
    main()
