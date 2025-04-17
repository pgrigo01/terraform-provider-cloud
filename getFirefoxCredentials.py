#!/usr/bin/env python3
import os
import sys
import getpass
import subprocess
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from cryptography.fernet import Fernet

def get_credentials(force_prompt=False):
    """Get credentials from environment, file, or user prompt"""
    username = None
    password = None
    
    # Only check stored credentials if not forcing a prompt
    if not force_prompt:
        username = os.environ.get('CLOUDLAB_USERNAME')
        password = os.environ.get('CLOUDLAB_PASSWORD')
        
        if not username or not password:
            if os.path.exists("credentials.txt"):
                try:
                    with open("credentials.txt", "r") as f:
                        lines = f.readlines()
                        if len(lines) >= 2:
                            username = lines[0].strip()
                            password = lines[1].strip()
                    print("Using credentials from credentials.txt")
                except Exception:
                    pass
    
    # Always prompt if credentials are still missing or force_prompt is True
    if not username or not password or force_prompt:
        print("Please enter your CloudLab credentials:")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ").strip()
        
        # Save for this session
        os.environ['CLOUDLAB_USERNAME'] = username
        os.environ['CLOUDLAB_PASSWORD'] = password
    
    return username, password

def download_certificate(username, password, save_path="."):
    """Download CloudLab certificate using Selenium"""
    print(f"Downloading CloudLab certificate for {username}...")

    options = webdriver.FirefoxOptions()
    temp_user_data = tempfile.mkdtemp()

    # Set Firefox preferences for downloading to current directory
    download_dir = os.path.abspath(save_path)
    options.set_preference("browser.download.folderList", 2)  # Use custom location
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-x509-user-cert,application/x-pem-file,application/x-x509-ca-cert,application/x-x509-server-cert")
    options.set_preference("pdfjs.disabled", True)

    # Disable caching
    options.set_preference("browser.cache.disk.enable", False)
    options.set_preference("browser.cache.memory.enable", False)
    options.set_preference("browser.cache.offline.enable", False)
    options.set_preference("network.http.use-cache", False)

    # Uncomment for headless mode if desired
    # options.add_argument("--headless")

    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)

    try:
        driver.get("https://www.cloudlab.us/login.php")
        wait = WebDriverWait(driver, 10)

        username_field = wait.until(EC.presence_of_element_located((By.NAME, "uid")))
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        username_field.send_keys(username)
        password_field.send_keys(password)
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "quickvm_login_modal_button")))
        login_button.click()

        # Verify login success
        wait.until(EC.element_to_be_clickable((By.ID, "usertab-experiments")))

        # Navigate to credentials page
        driver.get("https://www.cloudlab.us/getcreds.php")

        # Click the SSL certificate link
        ssl_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'getsslcert.php')]")))
        ssl_link.click()

        # Wait for file to finish downloading
        time.sleep(5)
        print(f"Certificate should be downloaded to: {download_dir}")
        return True
    except Exception as e:
        print(f"Error downloading certificate: {e}")
        return False
    finally:
        driver.quit()

def decrypt_certificate(password):
    """Decrypt the certificate using OpenSSL"""
    print("Decrypting CloudLab certificate...")
    pem_file = "cloudlab.pem"
    output_file = "cloudlab-decrypted.pem"
    
    if not os.path.exists(pem_file):
        print(f"Error: {pem_file} not found")
        return False
    
    with open(output_file, "w") as out_file:
        subprocess.run(
            ["openssl", "x509", "-in", pem_file,"-passin", f"pass:{password}"],
            stdout=out_file
        )
    
    with open(output_file, "a") as out_file:
        process = subprocess.run(
            ["openssl", "rsa", "-in", pem_file, "-passin", f"pass:{password}"],
            stdout=out_file,
            stderr=subprocess.PIPE
        )
    
    if process.returncode != 0:
        print("Failed to decrypt private key. Invalid password or format.")
        os.remove(output_file)
        return False
    
    print(f"Certificate decrypted successfully: {output_file}")
    return True

def encrypt_credentials(username, password):
    """Encrypt credentials for future use"""
    key_file = "encryption_key.key"
    creds_file = "credentials.encrypted"
    
    # Generate key if it doesn't exist
    if not os.path.exists(key_file):
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
    else:
        with open(key_file, "rb") as f:
            key = f.read()
    
    cipher = Fernet(key)
    encrypted_username = cipher.encrypt(username.encode())
    encrypted_password = cipher.encrypt(password.encode())
    
    with open(creds_file, "wb") as f:
        f.write(encrypted_username + b"\n" + encrypted_password)
    
    print("Credentials encrypted and saved")
    return True

def main():
    # Try until successful
    force_prompt = False
    success = False
    
    while not success:
        # Get credentials (force prompt if previous attempt failed)
        username, password = get_credentials(force_prompt)
        
        # Check if certificate exists, download if not
        if not os.path.exists("cloudlab.pem"):
            print("Certificate not found, downloading...")
            if download_certificate(username, password):
                success = True
            else:
                print("Failed to download certificate. Incorrect credentials? Try again.")
                force_prompt = True  # Force prompt on next iteration
        else:
            success = True  # Certificate already exists
    
    # Decrypt certificate
    if not decrypt_certificate(password):
        return 1
    
    # Encrypt credentials for future use
    encrypt_credentials(username, password)
    
    print("\nAll credential operations completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())