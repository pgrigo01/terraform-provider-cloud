#Run this script to start the server.
# source myenv/bin/activate
# python3 selectServer.py

#In case the server remains running, we can kill it using the following command:
# lsof -i :8080 to see the process using port 8080
# kill -9 <PID> to kill the process using port 8080
#Then you can rerun the script.


import getpass
import os
import sys
import subprocess  # for helper()
import time
import socket
from threading import Thread
import chromeServer
import firefoxServer
import simpleServer

def wait_for_server(host, port, timeout=90):
    """Wait until a TCP connection to host:port can be made or timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

def helper():
    print("\n=== Command Interface ===")
    print("Available commands:")
    print("terraform <command> : Run terraform <command>command (apply, plan, destroy, show, etc.)")
    print("You can also run any other command directly like clear.")
    print("exit or CTRL+C      : Quit the application")
    
    
    while True:
        cmd = input("\n> ").strip()
        if cmd.lower() == "exit":
            print("Exiting...")
            sys.exit(0)
        elif cmd.startswith("help"):
            helper()
        try:
            # Run any command using shell=True so interactive commands work.
            subprocess.run(cmd, shell=True)
        except Exception as e:
            print(f"Error executing command: {e}")

def main():
    try:
        print("Select the browser server to run:")
        print("1. Chrome Server")
        print("2. Firefox Server")
        print("3. Run Server without authentication")
        choice = input("Enter your choice (1, 2 or 3): ").strip()

        if choice == '1':
            username = input("Enter CloudLab username: ").strip()
            password = getpass.getpass("Enter CloudLab password: ").strip()
            print("Starting Chrome Server...")
            server_thread = Thread(target=chromeServer.runChromeServer, args=(username, password), daemon=True)
            server_thread.start()
        elif choice == '2':
            username = input("Enter CloudLab username: ").strip()
            password = getpass.getpass("Enter CloudLab password: ").strip()
            print("Starting Firefox Server...")
            server_thread = Thread(target=firefoxServer.runFirefoxServer, args=(username, password), daemon=True)
            server_thread.start()
        elif choice == '3':
            server_thread = Thread(target=simpleServer.runSimpleServer, daemon=True)
            server_thread.start()
        else:
            print("Invalid choice. Please enter 1, 2 or 3. ")
            sys.exit(1)

        print("Waiting for the Flask server to start...")
        if wait_for_server("127.0.0.1", 8080):
            print("Flask server is up and running!")
        else:
            print("Flask server did not start within the timeout.")
            sys.exit(1)

        # Launch command interface
        helper()
        
    except KeyboardInterrupt:
        print("\nCaught Ctrl+C! Exiting...")
        os._exit(0)  # Force kill everything, including Flask running in thread
if __name__ == "__main__":
    main()


