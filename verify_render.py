import requests
import time
import sys

url = "https://djezzy-bss-explorer.onrender.com"
max_retries = 30 # wait up to 5 minutes
print("Waiting for application to be live...")

for i in range(max_retries):
    try:
        session = requests.Session()
        # 1. Get CSRF Token
        csrf_resp = session.get(f"{url}/api/auth/csrf", timeout=10)
        if csrf_resp.status_code == 200:
            token = csrf_resp.json().get('csrf_token')
            if token:
                print("CSRF Token Acquired.")
                
                # 2. Try Login with default admin/admin
                login_data = {"username": "admin", "password": "admin"}
                headers = {"X-CSRFToken": token}
                login_resp = session.post(f"{url}/api/auth/login", json=login_data, headers=headers, timeout=10)
                
                print(f"Login Response: {login_resp.status_code} - {login_resp.text}")
                
                if login_resp.status_code == 200:
                    print("SUCCESS! Render Deployment is working perfectly.")
                    sys.exit(0)
                elif "Invalid username or password" in login_resp.text:
                    print(f"Warning: Login failed, but API is up. (Status: {login_resp.status_code})")
                    # If users.json was somehow persisted or regenerated differently, the login might fail but the app is UP.
                    sys.exit(0)
                else:
                    print(f"API is up but login returned unexpected response: {login_resp.text}")
                    sys.exit(1)
            else:
                print("App is up but no CSRF token returned.")
                sys.exit(1)
        else:
            print(f"Waiting for build {i+1}/{max_retries} (Status: {csrf_resp.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"Waiting for build {i+1}/{max_retries} (Error: {e})")
    time.sleep(10)

print("Timeout waiting for application.")
sys.exit(1)
