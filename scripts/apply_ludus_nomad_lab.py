#!/usr/bin/env python3
"""Package and apply the Ludus Nomad lab to a Ludus server."""

from __future__ import annotations

import argparse
import os
import re
import ssl
import tarfile
import uuid
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROLES_DIR = ROOT / "ansible" / "roles"
CONFIG_PATH = ROOT / "range-config.nomad-cluster.yml"
DIST_DIR = ROOT / ".dist"
ROLE_NAMES = [
    "ludus_nomad_common",
    "ludus_nomad_server",
    "ludus_nomad_client",
]


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def make_context() -> ssl.SSLContext:
    return ssl._create_unverified_context()


def request(url: str, api_key: str, method: str = "GET", data: bytes | None = None, content_type: str | None = None) -> str:
    headers = {"X-API-Key": api_key}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    with urllib.request.urlopen(req, context=make_context(), timeout=120) as resp:
        return resp.read().decode("utf-8", errors="replace")


def multipart_file(filename: str, payload: bytes, content_type: str) -> tuple[bytes, str]:
    boundary = "----codex" + uuid.uuid4().hex
    body = b"".join(
        [
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode(),
            payload,
            f"\r\n--{boundary}--\r\n".encode(),
        ]
    )
    return body, boundary


def package_role(role_name: str) -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = DIST_DIR / f"{role_name}.tar.gz"
    role_dir = ROLES_DIR / role_name
    with tarfile.open(archive_path, "w:gz") as tf:
        tf.add(role_dir, arcname=role_name)
    return archive_path


def upload_role(server: str, api_key: str, role_name: str) -> None:
    archive_path = package_role(role_name)
    body, boundary = multipart_file(role_name, archive_path.read_bytes(), "application/gzip")
    url = f"{server.rstrip('/')}/ansible/role/fromtar?force=true"
    response = request(url, api_key, method="PUT", data=body, content_type=f"multipart/form-data; boundary={boundary}")
    print(f"uploaded role {role_name}: {response}")


def render_config(enable_demo_job: bool) -> bytes:
    text = CONFIG_PATH.read_text(encoding="utf-8")
    text = re.sub(
        r"(?m)^(\s*nomad_deploy_demo_job:\s*)(true|false)\s*$",
        rf"\1{'true' if enable_demo_job else 'false'}",
        text,
        count=1,
    )
    return text.encode("utf-8")


def upload_config(server: str, api_key: str, config_bytes: bytes) -> None:
    body, boundary = multipart_file("range-config.nomad-cluster.yml", config_bytes, "application/x-yaml")
    url = f"{server.rstrip('/')}/range/config"
    response = request(url, api_key, method="PUT", data=body, content_type=f"multipart/form-data; boundary={boundary}")
    print(f"uploaded config: {response}")


def deploy(server: str, api_key: str) -> None:
    url = f"{server.rstrip('/')}/range/deploy"
    response = request(url, api_key, method="POST", data=b"")
    print(f"deploy: {response}")


def show_status(server: str, api_key: str) -> None:
    status_url = f"{server.rstrip('/')}/range"
    logs_url = f"{server.rstrip('/')}/range/logs"
    print("range:", request(status_url, api_key))
    print("logs:", request(logs_url, api_key))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="https://127.0.0.1:8080")
    parser.add_argument("--api-key", default=os.getenv("LUDUS_API_KEY"))
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--enable-demo-job", action="store_true", default=env_bool("NOMAD_DEPLOY_HELLO_WORLD"))
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("missing --api-key or LUDUS_API_KEY")

    for role_name in ROLE_NAMES:
        upload_role(args.server, args.api_key, role_name)

    config_bytes = render_config(args.enable_demo_job)
    upload_config(args.server, args.api_key, config_bytes)

    if args.deploy:
        deploy(args.server, args.api_key)

    if args.status:
        show_status(args.server, args.api_key)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
