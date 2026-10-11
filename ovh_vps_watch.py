"""Surveille le stock des VPS-2 OVHcloud à Gravelines (GRA) et Roubaix (RBX).

Utilise l'API publique OVH (sans authentification) :
  GET https://eu.api.ovh.com/v1/vps/order/rule/datacenter?ovhSubsidiary=FR&planCode=...

Alerte (notification Windows + bip, + Discord si DISCORD_WEBHOOK_URL est défini)
quand un datacenter surveillé passe de "out-of-stock" à disponible.
"""

import json
import os
import subprocess
import time
import urllib.request
import winsound
from datetime import datetime

# VPS-2 2027 = offre actuelle du site, VPS-2 2026 = ancienne gamme encore commandable.
PLAN_CODES = {"vps-2027-model2": "VPS-2 2027", "vps-2025-model2": "VPS-2 2026"}
DATACENTERS = {"GRA": "Gravelines", "EU-WEST-RBX": "Roubaix"}
INTERVAL_SECONDS = 60
API_URL = "https://eu.api.ovh.com/v1/vps/order/rule/datacenter?ovhSubsidiary=FR&planCode={}"
ORDER_URL = "https://www.ovhcloud.com/fr/vps/"


def load_env(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
    """Charge les lignes KEY=VALUE du fichier .env (sans dépendance externe)."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env()
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = os.environ.get("DISCORD_USER_ID")  # utilisateur mentionné à chaque alerte


def fetch_status(plan_code):
    with urllib.request.urlopen(API_URL.format(plan_code), timeout=20) as resp:
        data = json.load(resp)
    return {dc["datacenter"]: dc for dc in data["datacenters"] if dc["datacenter"] in DATACENTERS}


def notify(message):
    print(f"\a>>> {message}")
    winsound.Beep(1000, 700)
    # Notification ballon Windows via PowerShell, pour éviter toute dépendance externe.
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "$n = New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon = [System.Drawing.SystemIcons]::Information;"
        "$n.Visible = $true;"
        f"$n.ShowBalloonTip(10000, 'Restock OVH VPS', '{message.replace(chr(39), '')}', 'Info');"
        "Start-Sleep -Seconds 10; $n.Dispose()"
    )
    subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps])
    if DISCORD_WEBHOOK_URL:
        mention = f"<@{DISCORD_USER_ID}> " if DISCORD_USER_ID else ""
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=json.dumps({
                "content": f"{mention}{message}\n{ORDER_URL}",
                "allowed_mentions": {"users": [DISCORD_USER_ID] if DISCORD_USER_ID else []},
            }).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "ovh-vps-watch"},
        )
        urllib.request.urlopen(req, timeout=20)


def main():
    print(f"Surveillance de {', '.join(PLAN_CODES.values())} à {', '.join(DATACENTERS.values())} "
          f"toutes les {INTERVAL_SECONDS}s (Ctrl+C pour arrêter)")
    previous = {}  # (plan, dc) -> en stock ?
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        for plan, plan_name in PLAN_CODES.items():
            try:
                statuses = fetch_status(plan)
            except Exception as e:  # réseau / API indisponible : on réessaie au prochain tour
                print(f"[{now}] {plan_name}: erreur API ({e})")
                continue
            for dc, info in statuses.items():
                # "status" passe à available dès qu'un seul OS est en stock (souvent Windows) : on suit Linux.
                in_stock = info["linuxStatus"] != "out-of-stock"
                label = f"{plan_name} {DATACENTERS[dc]}"
                detail = f"linux={info['linuxStatus']} windows={info['windowsStatus']}"
                print(f"[{now}] {label}: {'EN STOCK' if in_stock else 'rupture'} ({detail})")
                if in_stock and not previous.get((plan, dc), False):
                    notify(f"{label} dispo ! ({detail})")
                previous[(plan, dc)] = in_stock
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
