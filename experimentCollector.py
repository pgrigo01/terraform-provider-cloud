import os
import sys
import getpass
import pandas as pd
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def getExperiments(username=None, password=None):
    """
    Logs into CloudLab, extracts experiments table, filters for user's experiments,
    saves data to CSV, and fetches 'management-node' expiration date if exists.

    :param username: CloudLab username (optional, will prompt if not provided)
    :param password: CloudLab password (optional, will prompt if not provided)
    """

    # -------------------------------
    # Retrieve Credentials
    # -------------------------------
    USERNAME = username
    PASSWORD = password

    if not USERNAME or not PASSWORD:
        # Check if credentials are passed as command-line arguments
        if len(sys.argv) > 2:
            USERNAME = sys.argv[1]
            PASSWORD = sys.argv[2]
            print("Using credentials from command-line arguments.")
        elif os.path.exists("credentials.txt"):
            with open("credentials.txt", "r") as f:
                lines = f.readlines()
                USERNAME = lines[0].strip()  # First line: username
                PASSWORD = lines[1].strip()  # Second line: password
            print("Using credentials from credentials.txt.")
        else:
            print("No credentials provided via arguments or file. Prompting user...")
            USERNAME = input("Enter your username: ").strip()
            PASSWORD = getpass.getpass("Enter your password: ").strip()

    # Ensure username and password are not empty
    if not USERNAME or not PASSWORD:
        print("Error: Username or password is empty.")
        sys.exit(1)

    # -------------------------------
    # Setup ChromeDriver
    # -------------------------------
    options = webdriver.ChromeOptions()
    temp_user_data = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_user_data}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")  # Uncomment for headless mode
    options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # -------------------------------
        # Load the CloudLab login page
        # -------------------------------
        driver.get("https://www.cloudlab.us/login.php")
        wait = WebDriverWait(driver, 10)

        # 1) Log in
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "uid")))
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "quickvm_login_modal_button")))
        login_button.click()
        print("Login successful!")

        # 2) Navigate to Experiments
        experiments_tab = wait.until(EC.element_to_be_clickable((By.ID, "usertab-experiments")))
        experiments_tab.click()
        print("Navigated to Experiments tab")

        # 3) Wait for the experiments table
        experiment_table = wait.until(EC.visibility_of_element_located((By.TAG_NAME, "table")))
        rows = experiment_table.find_elements(By.TAG_NAME, "tr")
        headers = [th.text for th in rows[0].find_elements(By.TAG_NAME, "th")]
        print("Extracted headers:", headers)

        # 4) Extract data and search for "management-node"
        experiments_data = []
        management_node_link = None

        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, "td")
            if cols:
                row_data = [c.text for c in cols]
                experiments_data.append(row_data)
                if row_data[0].strip().lower() == "management-node" and management_node_link is None:
                    try:
                        management_node_link = cols[0].find_element(By.TAG_NAME, "a")
                    except Exception:
                        management_node_link = row

        # 5) Convert to DataFrame and filter by creator
        df = pd.DataFrame(experiments_data, columns=headers)
        if "Creator" in df.columns:
            df = df[df["Creator"] == USERNAME]
        else:
            print("No 'Creator' column found; skipping user-based filtering.")

        # 6) Save CSV
        df.to_csv("cloudlab_experiments.csv", index=False)
        print("Data saved to 'cloudlab_experiments.csv'")

        # # 7) Click on 'management-node' and get expiration
        # if management_node_link:
        #     management_node_link.click()
        #     print("Clicked on 'management-node' experiment.")

        #     expiration_element = wait.until(
        #         lambda d: d.find_element(By.ID, "quickvm_expires") if d.find_element(By.ID, "quickvm_expires").text.strip() != "" else False
        #     )
        #     expiration_text = expiration_element.text.strip()
        #     print("Expiration text found:", expiration_text)

        #     with open("managementNodeDuration.txt", "w") as f:
        #         f.write(expiration_text + "\n")
        #     print("Saved management node expiration to 'managementNodeDuration.txt'")
        # else:
        #     print("No 'management-node' row found.")

    except Exception as e:
        print("[ERROR]:", e)

    finally:
        driver.quit()



if __name__ == "__main__":
    getExperiments()  # Call without params, will prompt or use file/args if needed