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

# -------------------------------
# Retrieve Credentials
# -------------------------------
USERNAME = ""
PASSWORD = ""

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
# Create a temporary directory for user data to avoid conflicts
temp_user_data = tempfile.mkdtemp()
options.add_argument(f"--user-data-dir={temp_user_data}")
# Options for headless/server environments
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless")  # Remove this line if you need to see the browser
options.add_argument("--disable-gpu")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# -------------------------------
# Load the CloudLab login page
# -------------------------------
driver.get("https://www.cloudlab.us/login.php")
wait = WebDriverWait(driver, 10)

try:
    # 1) Log in to CloudLab using the provided credentials.
    username_field = wait.until(EC.presence_of_element_located((By.NAME, "uid")))
    password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "quickvm_login_modal_button")))
    login_button.click()
    print("Login successful!")

    # 2) Navigate to the Experiments tab after logging in.
    experiments_tab = wait.until(EC.element_to_be_clickable((By.ID, "usertab-experiments")))
    experiments_tab.click()
    print("Navigated to Experiments tab")

    # 3) Wait for the experiments table to load using an explicit wait.
    experiment_table = wait.until(EC.visibility_of_element_located((By.TAG_NAME, "table")))
    rows = experiment_table.find_elements(By.TAG_NAME, "tr")
    headers = [th.text for th in rows[0].find_elements(By.TAG_NAME, "th")]
    print("Extracted headers:", headers)

    # 4) Combine data extraction and search for the "management-node" row.
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

    # 5) Convert the data into a DataFrame and filter by creator if applicable.
    df = pd.DataFrame(experiments_data, columns=headers)
    if "Creator" in df.columns:
        df = df[df["Creator"] == USERNAME]
    else:
        print("No 'Creator' column found; skipping user-based filtering.")

    # 6) Save the DataFrame to a CSV file.
    df.to_csv("cloudlab_experiments.csv", index=False)
    print("Data saved to 'cloudlab_experiments.csv'")

    # 7) Locate and click the experiment named "management-node"
    if management_node_link:
        management_node_link.click()
        print("Clicked on 'management-node' experiment. Navigating to details page...")

        # 8) Wait until the expiration element has non-empty text.
        expiration_element = wait.until(
            lambda d: d.find_element(By.ID, "quickvm_expires") if d.find_element(By.ID, "quickvm_expires").text.strip() != "" else False
        )
        expiration_text = expiration_element.text.strip()
        print("Expiration text found:", expiration_text)

        with open("managementNodeDuration.txt", "w") as f:
            f.write(expiration_text + "\n")
        print("Saved management node expiration to 'managementNodeDuration.txt'")
    else:
        print("No row found with name 'management-node'.")

except Exception as e:
    print("Error:", e)

finally:
    driver.quit()
