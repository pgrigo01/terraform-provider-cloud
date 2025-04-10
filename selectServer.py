#!/usr/bin/env python3

import readline
import getpass
import os
import sys
import subprocess
import time
import socket
from threading import Thread
import chromeServer
import firefoxServer
import simpleServer

# ANSI escape sequences for terminal colors
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"

def wait_for_server(host, port, timeout=90):
    """
    Wait for the Flask server to become available at a given host/port.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

def helper():
    """
    Interactive Command Interface
    """
    print(f"\n{BLUE}{BOLD}=== Command Interface ==={RESET}")
    print(f"{YELLOW}Available commands:{RESET}")
    print(f"  {GREEN}terraform <command>{RESET}  → Run Terraform commands like apply, plan, destroy")
    print(f"  {GREEN}Any other system command{RESET} can also be executed (e.g., ls, clear)")
    print(f"  {RED}Type 'exit' or press CTRL+C to quit the application{RESET}")

    print(f"""{BLUE}
Terraform Workflow Examples:{RESET}

{GREEN}To ADD a new experiment/resource:{RESET}
  - Uncomment or add the resource block in main.tf

    Example:
    resource "cloudlab_simple_experiment" "vm1" {{
        name        = "experiment1"
        routable_ip = true
        image       = "UBUNTU 22.04"
        aggregate   = "emulab.net"
    }}

  - Run: {YELLOW}terraform plan{RESET}
  - Run: {YELLOW}terraform apply{RESET}

{RED}To REMOVE an experiment/resource:{RESET}
  - Comment out the block in main.tf
  - Run: {YELLOW}terraform plan{RESET}
  - Run: {YELLOW}terraform apply{RESET}
""")

    while True:
        # cmd = input(f"{BLUE}>>> {RESET}").strip()
        cmd = input(f"{BLUE}>>> {RESET}").strip()
        if cmd.lower() == "exit":
            print(f"{RED}Exiting...{RESET}")
            sys.exit(0)
        elif cmd.startswith("help"):
            helper()
        try:
            subprocess.run(cmd, shell=True)
        except Exception as e:
            print(f"{RED}Error executing command: {e}{RESET}")

def main():
    """
    Main Server Selector and Launcher
    """
    try:
        print(f"{YELLOW}Select the browser server to run:{RESET}")
        print(f"{YELLOW}1) Chrome Server (CloudLab credentials required){RESET}")
        print(f"{YELLOW}2) Firefox Server (CloudLab credentials required){RESET}")
        print(f"{YELLOW}3) Simple Server (no authentication){RESET}")

        choice = input(f"{YELLOW}Enter your choice (1, 2 or 3): {RESET}").strip()

        if choice == '1':
            username = input(f"{YELLOW}Enter CloudLab username: {RESET}").strip()
            password = getpass.getpass(f"{YELLOW}Enter CloudLab password: {RESET}").strip()
            print(f"{GREEN}Starting Chrome Server...{RESET}")
            server_thread = Thread(target=chromeServer.runChromeServer, args=(username, password), daemon=True)
            server_thread.start()
        elif choice == '2':
            username = input(f"{YELLOW}Enter CloudLab username: {RESET}").strip()
            password = getpass.getpass(f"{YELLOW}Enter CloudLab password: {RESET}").strip()
            print(f"{GREEN}Starting Firefox Server...{RESET}")
            server_thread = Thread(target=firefoxServer.runFirefoxServer, args=(username, password), daemon=True)
            server_thread.start()
        elif choice == '3':
            print(f"{GREEN}Starting Simple Server (no authentication)...{RESET}")
            server_thread = Thread(target=simpleServer.runSimpleServer, daemon=True)
            server_thread.start()
        else:
            print(f"{RED}Invalid choice. Please enter 1, 2, or 3.{RESET}")
            sys.exit(1)

        print(f"{YELLOW}Waiting for the Flask server to start on http://127.0.0.1:8080 ...{RESET}")
        if wait_for_server("127.0.0.1", 8080):
            print(f"{GREEN}Flask server is up and running!{RESET}")
        else:
            print(f"{RED}Flask server did not start within the timeout period.{RESET}")
            sys.exit(1)

        helper()

    except KeyboardInterrupt:
        print(f"\n{RED}Caught CTRL+C! Exiting...{RESET}")
        os._exit(0)

def display_help_message():
    """
    Display usage instructions
    """
    message = f"""
{BOLD}CloudLab Server Launcher Help{RESET}

{BLUE}Available Server Options:{RESET}
  1) Chrome Server (CloudLab credentials required)
  2) Firefox Server (CloudLab credentials required)
  3) Simple Server (no credentials required)

{BLUE}Terraform Workflow:{RESET}
{GREEN}To ADD resources:{RESET}
  • Uncomment or add resources in main.tf
  • Run: terraform plan
  • Run: terraform apply

{RED}To REMOVE resources:{RESET}
  • Comment out resources in main.tf
  • Run: terraform plan
  • Run: terraform apply

{YELLOW}Once the server is running, use the terminal to run terraform or system commands.
Type 'exit' or press CTRL+C to quit.{RESET}
"""
    print(message)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("-h", "--help", "help"):
        display_help_message()
        sys.exit(0)
    main()
