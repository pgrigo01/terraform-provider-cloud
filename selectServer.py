import getpass
import sys
import subprocess  # for helper()
import time
import socket
from threading import Thread
import chromeServer
import firefoxServer

def wait_for_server(host, port, timeout=30):
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
    # Command loop
    print("\n=== Command Interface ===")
    print("Available commands:")
    print("- terraform <command> : Run terraform command (apply, plan, destroy, etc)")
    print("- exit : Quit the application")
    while True:
        cmd = input("\n> ")
        if cmd.lower() == "exit":
            print("Exiting...")
            sys.exit(0)
        elif cmd.lower().startswith("terraform "):
            terraform_cmd = cmd.split(" ", 1)[1]
            try:
                result = subprocess.run(["terraform", terraform_cmd],
                                        capture_output=True,
                                        text=True)
                print(result.stdout)
                if result.stderr:
                    print("Error:", result.stderr)
            except Exception as e:
                print(f"Error executing command: {str(e)}")
        else:
            print("Unknown command")

def main():
    print("Select the browser server to run:")
    print("1. Chrome Server")
    print("2. Firefox Server")
    choice = input("Enter your choice (1 or 2): ").strip()

    if choice == '1':
        username = input("Enter CloudLab username: ").strip()
        password = getpass.getpass("Enter CloudLab password: ").strip()
        print("Starting Chrome Server...")
        # Start the server in a background thread passing credentials
        server_thread = Thread(target=chromeServer.runChromeServer, args=(username, password), daemon=True)
        server_thread.start()

        # Wait until the Flask server is available on port 8080
        print("Waiting for the Flask server to start...")
        if wait_for_server("127.0.0.1", 8080):
            print("Flask server is up and running!")
        else:
            print("Flask server did not start within the timeout.")
            sys.exit(1)

    elif choice == '2':
        username = input("Enter CloudLab username: ").strip()
        password = getpass.getpass("Enter CloudLab password: ").strip()
        print("Starting Firefox Server...")
        server_thread = Thread(target=firefoxServer.runFirefoxServer, args=(username, password), daemon=True)
        server_thread.start()
        print("Waiting for the Flask server to start...")
        if wait_for_server("127.0.0.1", 8080):
            print("Flask server is up and running!")
        else:
            print("Flask server did not start within the timeout.")
            sys.exit(1)
    else:
        print("Invalid choice. Please enter 1 or 2.")
        sys.exit(1)

    # Now that the server is confirmed to be running, launch the command interface.
    helper()

if __name__ == "__main__":
    main()
