import os

import paramiko


SSH_HOST = os.getenv("SSH_HOST", "176.98.11.139")
SSH_PORT = int(os.getenv("SSH_PORT", "222"))
SSH_USER = os.getenv("SSH_USER", "sysadmin")


def execute_command(command: str) -> str:
    client = paramiko.SSHClient()

    # Використовуємо вже відомі SSH host keys
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())

    try:
        client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USER,
            timeout=10,
            auth_timeout=10,
            allow_agent=True,
            look_for_keys=True,
        )

        stdin, stdout, stderr = client.exec_command(
            command,
            timeout=10,
        )

        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")

        if exit_code != 0:
            raise RuntimeError(
                f"Command failed ({exit_code}): {error}"
            )

        return output.strip()

    finally:
        client.close()


if __name__ == "__main__":
    print("=== HOSTNAME ===")
    print(execute_command("hostname"))

    print("\n=== DOCKER VERSION ===")
    print(execute_command("docker version --format '{{.Server.Version}}'"))

    print("\n=== COMPOSE CONTAINERS ===")
    print(
        execute_command(
            "docker ps -a --no-trunc "
            "--filter label=com.docker.compose.project=university_lab1 "
            "--format '{{.ID}} {{.Image}} {{.State}}'"
        )
    )
