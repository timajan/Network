import argparse
import csv
import os
import time
from datetime import datetime, timezone

import docker
import requests


PROJECT = "university_lab1"

DOCKER_HOST = (
    f"ssh://{os.getenv('SSH_USER', 'sysadmin')}@"
    f"{os.getenv('SSH_HOST', '176.98.11.139')}:"
    f"{os.getenv('SSH_PORT', '222')}"
)

HTTP_URL = os.getenv(
    "HTTP_URL",
    "http://127.0.0.1:18080"
)

CSV_FILE = "monitoring.csv"

FIELDNAMES = [
    "timestamp",
    "service",
    "container_id",
    "container_status",
    "health_status",
    "http_status",
    "http_elapsed_ms",
    "error",
]


def check_http():
    started = time.perf_counter()

    try:
        response = requests.get(
            HTTP_URL,
            timeout=5,
        )

        elapsed_ms = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        return response.status_code, elapsed_ms, ""

    except requests.RequestException as exc:
        elapsed_ms = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        return None, elapsed_ms, str(exc)


def collect_snapshot(client):
    timestamp = datetime.now(timezone.utc).isoformat()

    http_status, http_elapsed_ms, http_error = check_http()

    rows = []

    containers = client.containers.list(
        all=True,
        filters={
            "label": f"com.docker.compose.project={PROJECT}"
        },
    )

    for container in containers:
        container.reload()

        data = container.attrs

        health_status = (
            data.get("State", {})
            .get("Health", {})
            .get("Status", "not_configured")
        )

        rows.append({
            "timestamp": timestamp,
            "service": container.labels.get(
                "com.docker.compose.service", ""
            ),
            "container_id": container.id[:12],
            "container_status": data["State"]["Status"],
            "health_status": health_status,
            "http_status": http_status,
            "http_elapsed_ms": http_elapsed_ms,
            "error": http_error,
        })

    return rows


def save_rows(rows):
    file_exists = os.path.exists(CSV_FILE)
    needs_header = (
        not file_exists
        or os.path.getsize(CSV_FILE) == 0
    )

    with open(
        CSV_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        if needs_header:
            writer.writeheader()

        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Docker container monitoring"
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=10,
        help="Monitoring interval in seconds",
    )

    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("--interval must be greater than zero")

    client = docker.DockerClient(
        base_url=DOCKER_HOST,
        use_ssh_client=True,
        timeout=15,
    )

    print(f"Monitoring project: {PROJECT}")
    print(f"Interval: {args.interval} seconds")
    print(f"Output: {CSV_FILE}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            try:
                rows = collect_snapshot(client)

                save_rows(rows)

                for row in rows:
                    print(
                        f"[{row['timestamp']}] "
                        f"{row['service']}: "
                        f"{row['container_status']} | "
                        f"health={row['health_status']} | "
                        f"HTTP={row['http_status']}"
                    )

                print("-" * 60)

            except Exception as exc:
                print(f"Monitoring error: {exc}")

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

    finally:
        client.close()


if __name__ == "__main__":
    main()
