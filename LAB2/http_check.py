import json
import os
import time

import requests


HTTP_URL = os.getenv(
    "HTTP_URL",
    "http://127.0.0.1:18080"
)


def check_http() -> dict:
    results = []

    for request_number in range(1, 3):
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

            try:
                body = response.json()
            except ValueError:
                body = {}

            results.append(
                {
                    "request_number": request_number,
                    "status_code": response.status_code,
                    "elapsed_ms": elapsed_ms,
                    "instance": body.get("instance"),
                    "counter": body.get("requests"),
                    "error": None,
                }
            )

        except requests.RequestException as exc:
            elapsed_ms = round(
                (time.perf_counter() - started) * 1000,
                2,
            )

            results.append(
                {
                    "request_number": request_number,
                    "status_code": None,
                    "elapsed_ms": elapsed_ms,
                    "instance": None,
                    "counter": None,
                    "error": str(exc),
                }
            )

    first, second = results

    http_ok = all(
        result["status_code"] == 200
        for result in results
    )

    counter_ok = (
        isinstance(first["counter"], int)
        and isinstance(second["counter"], int)
        and second["counter"] > first["counter"]
    )

    return {
        "status": "PASS" if http_ok and counter_ok else "FAIL",
        "url": HTTP_URL,
        "http_ok": http_ok,
        "counter_increased": counter_ok,
        "requests": results,
    }


if __name__ == "__main__":
    result = check_http()

    print(json.dumps(result, indent=2, ensure_ascii=False))
