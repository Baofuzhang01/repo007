#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import tempfile
import time
from pathlib import Path


ALLOWED_KEYS = {
    "CF_ACCOUNT_ID",
    "CF_KV_NAMESPACE_ID",
    "CF_API_TOKEN",
    "TARGET_CF_ACCOUNT_ID",
    "TARGET_CF_KV_NAMESPACE_ID",
    "TARGET_CF_API_TOKEN",
    "SERVER_WORKER2_TRIGGER_API",
    "SERVER_WORKER2_HEARTBEAT_SOURCE_ACCOUNT_ID",
    "SERVER_WORKER2_HEARTBEAT_SOURCE_NAMESPACE_ID",
    "SERVER_WORKER2_HEARTBEAT_SOURCE_API_TOKEN",
    "CF_TUNNEL_API_TOKEN",
    "CLOUDFLARE_TUNNEL_TOKEN",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="/etc/seat-qianduan.env")
    args = parser.parse_args()
    path = Path(args.path)
    updates = json.load(__import__("sys").stdin)

    if not updates or not set(updates).issubset(ALLOWED_KEYS) or any(not str(value) for value in updates.values()):
        raise SystemExit("expected approved Cloudflare settings with non-empty values")

    original = path.read_text(encoding="utf-8")
    remaining = dict(updates)
    output = []
    for line in original.splitlines():
        key = line.split("=", 1)[0].strip() if "=" in line and not line.lstrip().startswith("#") else ""
        if key in remaining:
            output.append(f"{key}={remaining.pop(key)}")
        else:
            output.append(line)
    if remaining:
        output.extend(["", "# Cloudflare runtime settings"] + [f"{key}={remaining[key]}" for key in sorted(remaining)])

    backup = path.with_name(f"{path.name}.bak.{time.strftime('%Y%m%d%H%M%S')}")
    shutil.copy2(path, backup)
    mode = path.stat().st_mode
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write("\n".join(output) + "\n")
        temporary = Path(handle.name)
    os.chmod(temporary, mode)
    os.replace(temporary, path)
    print(json.dumps({"ok": True, "path": str(path), "backup": str(backup), "updated": sorted(updates)}))


if __name__ == "__main__":
    main()
