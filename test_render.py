import requests
import time

URL = "https://djezzy-bss-explorer.onrender.com"
session = requests.Session()

def check_status():
    print(f"Pinging {URL}...")
    try:
        # Get CSRF token
        r_csrf = session.get(f"{URL}/api/auth/csrf")
        if r_csrf.status_code != 200:
            print(f"Failed to get CSRF. Status: {r_csrf.status_code}")
            return False
            
        csrf_token = r_csrf.json().get("csrf_token")
        
        # Login
        login_data = {"username": "admin", "password": "Azertypp00"}
        headers = {"X-CSRFToken": csrf_token}
        r_login = session.post(f"{URL}/api/auth/login", json=login_data, headers=headers)
        
        if r_login.status_code != 200:
            print(f"Login failed. Status: {r_login.status_code}")
            return False
            
        print("Logged in successfully. Checking data status...")
        
        # Check status
        r_status = session.get(f"{URL}/api/admin/status", headers=headers)
        if r_status.status_code == 200:
            data = r_status.json()
            print("\n=== SERVER STATUS ===")
            print(f"Datasets Loaded: {data.get('datasets_loaded')}")
            print(f"Total Unique Sites: {data.get('total_sites')}")
            print("=====================\n")
            
            if data.get('datasets_loaded', 0) > 0:
                print("SUCCESS: Data is loaded and ready!")
                return True
            else:
                print("PENDING: Data is not yet loaded.")
                return False
        else:
            print(f"Failed to get status. Code: {r_status.status_code}")
            return False
            
    except Exception as e:
        print(f"Connection error: {e}")
        return False

# Poll a few times
for i in range(5):
    if check_status():
        break
    print("Waiting 15 seconds before retry...")
    time.sleep(15)
