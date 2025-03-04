#!/usr/bin/env python3
import requests

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
DOMAIN = "terraform-cloudlab"  # DuckDNS subdomain 
TOKEN = "956737ca-e761-4fe8-a713-ebbb2a813339"   # Duck DNS token

# Endpoint to detect public IP
PUBLIC_IP_ENDPOINT = "https://ifconfig.me"


# ------------------------------------------------------------------------------
# FUNCTION: get_public_ip   
# ------------------------------------------------------------------------------
def get_public_ip():
    """
    Fetches the current public IP address of this VM by calling a public service.
    Returns None if there's an error.
    """
    try:
        response = requests.get(PUBLIC_IP_ENDPOINT, timeout=5)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        print(f"[ERROR] Could not fetch public IP from {PUBLIC_IP_ENDPOINT}: {e}")
        return None

# ------------------------------------------------------------------------------
# FUNCTION: update_duckdns
# ------------------------------------------------------------------------------
def update_duckdns():
    """
    Detect the VM's public IP, then update the DuckDNS record for DOMAIN exactly once.
    """
    current_ip = get_public_ip()
    if not current_ip:
        print("[WARN] Skipping DuckDNS update because IP is None.")
        return

    update_url = (
        f"https://www.duckdns.org/update"
        f"?domains={DOMAIN}"
        f"&token={TOKEN}"
        f"&ip={current_ip}"
    )

    try:
        response = requests.get(update_url, timeout=5)
        print(f"[INFO] DuckDNS update response: {response.text}, IP used: {current_ip}")
    except Exception as e:
        print(f"[ERROR] Could not update DuckDNS: {e}")

# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Perform a single DuckDNS update, then exit.
    update_duckdns()
