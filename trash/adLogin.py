import requests
import pickle
import json
import os


# API endpoint
LOGIN_URL = "https://app.adbraze.com/api/v1/auth/login"
TASKS_URL = "https://app.adbraze.com/api/v1/task-manager"
COOKIES_FILE = "cookies.pkl"
REFRESH_URL = "https://app.adbraze.com/api/v1/auth/refresh-token"

# Your authentication credentials (if needed)
payload = {
    "email": "myemail",  # Replace with your Google-linked email
    "password": "mypass"       # If required (unlikely since it's Google OAuth)
}

# Function to save cookies to a file
def save_cookies(session, filename):
    with open(filename, "wb") as f:
        pickle.dump(session.cookies, f)

# Function to load cookies from a file
def load_cookies(session, filename):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            session.cookies.update(pickle.load(f))
        print("✅ Loaded saved cookies.")

def refresh_token(session):
    refresh_token_value = session.cookies.get("RefreshToken")
    if not refresh_token_value:
        print("❌ No refresh token available. Re-authentication required.")
        return False  # Force login

    print("🔄 Refreshing token...")
    refresh_payload = {"refreshToken": refresh_token_value}
    refresh_response = session.post(REFRESH_URL, json=refresh_payload)

    if refresh_response.status_code == 200:
        new_auth_token = refresh_response.cookies.get("AuthenticationToken")
        if new_auth_token:
            print(f"✅ Token refreshed: {new_auth_token}")
            session.cookies.set("AuthenticationToken", new_auth_token)
            save_cookies(session, COOKIES_FILE)  # Save updated cookies
            return True
    else:
        print(f"❌ Refresh failed: {refresh_response.status_code}, {refresh_response.text}")

    return False  # Force login if refresh fails

# Function to log in
def login(session):
    print("🔄 Logging in...")
    login_response = session.post(LOGIN_URL, json=payload)

    if login_response.status_code == 201:
        auth_token = login_response.cookies.get("AuthenticationToken")
        refresh_token = login_response.cookies.get("RefreshToken")
        if auth_token and refresh_token:
            print(f"✅ Logged in. New Auth Token: {auth_token}")
            save_cookies(session, COOKIES_FILE)
            return True
        else:
            print("❌ Failed to retrieve tokens after login.")
    else:
        print(f"❌ Login failed: {login_response.status_code}, {login_response.text}")
    
    return False


# Initialize session
session = requests.Session()
load_cookies(session, COOKIES_FILE)

# Check if authentication token exists
auth_token = session.cookies.get("AuthenticationToken")
if not auth_token:
    if not login(session):  # Attempt to log in
        exit()

# Step 2: Mimic the browser's request to `task-manager`
headers = {
    "Authorization": f"Bearer {auth_token}",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://app.adbraze.com/flow/task-manager/kanban-board?process=ALL&users=dea0621e-879a-4850-a283-d3217416cb6d",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

# Step 3: Fetch tasks with error handling for expired tokens
tasks_response = session.get(TASKS_URL, headers=headers)

if tasks_response.status_code == 401:  # Token expired
    print("⚠️ Authentication token expired. Attempting refresh...")
    if refresh_token(session):  # Try refreshing
        headers["Authorization"] = f"Bearer {session.cookies.get('AuthenticationToken')}"
        tasks_response = session.get(TASKS_URL, headers=headers)  # Retry request
    else:
        print("⚠️ Refresh failed. Logging in again...")
        if login(session):  # If refresh fails, log in again
            headers["Authorization"] = f"Bearer {session.cookies.get('AuthenticationToken')}"
            tasks_response = session.get(TASKS_URL, headers=headers)

if tasks_response.status_code == 200:
    print("✅ Successfully retrieved tasks!")

    # json_data = json.loads(tasks_response.json())

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(tasks_response.json(), f, indent=4, ensure_ascii=False)
    
    print(f"succesfuly cached {len(tasks_response.json())} tasks")

else:
    print(f"❌ Failed to fetch tasks: {tasks_response.status_code}, {tasks_response.text}")

