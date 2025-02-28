import os
import getpass
import time
import pandas as pd
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# -------------------------------
# Setup Chrome options with a unique user data directory
# -------------------------------
options = webdriver.ChromeOptions()
# Create a temporary directory for user data to avoid conflicts
temp_user_data = tempfile.mkdtemp()
options.add_argument(f"--user-data-dir={temp_user_data}")

# These options help with headless/server environments
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
#options.add_argument("--headless")  # Remove if you need to see the browser
options.add_argument("--disable-gpu")

# Initialize the ChromeDriver service using webdriver_manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Open the CloudLab login page.
driver.get("https://www.cloudlab.us/login.php")
wait = WebDriverWait(driver, 10)

# -------------------------------
# Retrieve Credentials
# -------------------------------
USERNAME = ""
PASSWORD = ""

if os.path.exists("credentials.txt"):
    with open("credentials.txt", "r") as f:
        lines = f.readlines()
        USERNAME = lines[0].strip()  # First line: username
        PASSWORD = lines[1].strip()  # Second line: password
else:
    while USERNAME == "" or PASSWORD == "":
        USERNAME = input("Enter your username: ")
        PASSWORD = getpass.getpass("Enter your password: ")

# -------------------------------
# Main Script: Logging In and Data Extraction
# -------------------------------
try:
    # 1) Log in to CloudLab
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

    # 3) Wait for the experiments table to load.
    time.sleep(3)
    experiment_table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

    # 4) Extract table rows and header information.
    rows = experiment_table.find_elements(By.TAG_NAME, "tr")
    headers = [th.text for th in rows[0].find_elements(By.TAG_NAME, "th")]
    print("Extracted headers:", headers)

    # 5) Gather data from each row of the table.
    experiments_data = []
    for row in rows[1:]:
        cols = row.find_elements(By.TAG_NAME, "td")
        experiments_data.append([c.text for c in cols])

    # 6) Convert the data into a DataFrame.
    df = pd.DataFrame(experiments_data, columns=headers)

    # 7) Filter rows by creator if possible.
    if "Creator" in df.columns:
        df = df[df["Creator"] == USERNAME]
    else:
        print("No 'Creator' column found; skipping user-based filtering.")

    # 8) Save the DataFrame to a CSV file.
    df.to_csv("cloudlab_experiments.csv", index=False)
    print("Data saved to 'cloudlab_experiments.csv'")

    # 9) Locate and click the experiment named "management-node"
    rows = experiment_table.find_elements(By.TAG_NAME, "tr")
    management_node_link = None
    for row in rows[1:]:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) > 0:
            name_text = cols[0].text.strip().lower()
            if name_text == "management-node":
                try:
                    management_node_link = cols[0].find_element(By.TAG_NAME, "a")
                except Exception:
                    management_node_link = row
                break

    if management_node_link:
        management_node_link.click()
        print("Clicked on 'management-node' experiment. Navigating to details page...")

        try:
            expiration_element = wait.until(
                EC.presence_of_element_located((By.ID, "quickvm_expires"))
            )
            WebDriverWait(driver, 10).until(
                lambda d: expiration_element.text.strip() != ""
            )
            expiration_text = expiration_element.text.strip()
            print("Expiration text found:", expiration_text)

            with open("managementNodeDuration.txt", "w") as f:
                f.write(expiration_text + "\n")
            print("Saved management node expiration to 'managementNodeDuration.txt'")
        except Exception as ex:
            print("Could not locate the expiration element or text is empty:", ex)
    else:
        print("No row found with name 'management-node'.")

except Exception as e:
    print("Error:", e)

finally:
    time.sleep(5)
    driver.quit()
