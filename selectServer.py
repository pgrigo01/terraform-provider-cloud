#selectServer.py
import sys
import chromeServer
import firefoxServer
def main():
    print("Select the browser server to run:")
    print("1. Chrome Server")
    print("2. Firefox Server")

    choice = input("Enter your choice (1 or 2): ").strip()

    if choice == '1':
        print("Starting Chrome Server...")
        chromeServer.runChromeServer()
        
    elif choice == '2':
        print("Starting Firefox Server...")
        firefoxServer.runFirefoxServer()
    else:
        print("Invalid choice. Please enter 1 or 2.")
        sys.exit(1)

if __name__ == "__main__":
    main()
