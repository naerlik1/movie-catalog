"""Обновляет адреса приложения после смены Wi-Fi. Запускается внутри VM."""
import ipaddress
import json
import subprocess
import sys
from pathlib import Path

addresses = ["localhost", "127.0.0.1", "app"]
interfaces = json.loads(subprocess.check_output(["ip", "-j", "-4", "addr", "show", "dev", "lima0"]))
for interface in interfaces:
    addresses.extend(info["local"] for info in interface["addr_info"])
if len(sys.argv) > 1 and sys.argv[1]:
    addresses.append(str(ipaddress.ip_address(sys.argv[1])))
addresses = list(dict.fromkeys(addresses))

settings = {
    "DJANGO_ALLOWED_HOSTS": ",".join(addresses),
    "CSRF_TRUSTED_ORIGINS": ",".join(f"http://{host}:8084" for host in addresses if host != "app"),
}
path = Path.home() / "movie-catalog" / ".env"
original = path.read_text()
lines = [line for line in original.splitlines() if line.split("=", 1)[0] not in settings]
lines.extend(f"{key}={value}" for key, value in settings.items())
updated = "\n".join(lines) + "\n"
if original != updated:
    path.write_text(updated)
    path.chmod(0o600)
print("Адреса приложения:", ", ".join(addresses))
