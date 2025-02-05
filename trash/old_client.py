#old.client.py
import os
import pickle
import requests
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

LOGIN_URL = "https://app.adbraze.com/api/v1/auth/login"
TASKS_URL = "https://app.adbraze.com/api/v1/task-manager"
REFRESH_URL = "https://app.adbraze.com/api/v1/auth/refresh-token"
COOKIES_FILE = "cookies.pkl"

class AdbrazeClient:
    def __init__(self):
        self.session = requests.Session()
        self.etag = None
        self.email = os.getenv("EMAIL")
        self.password = os.getenv("PASSWORD")
        self.load_cookies()
        self.user_id = os.getenv("USERID")

    def load_cookies(self):
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, "rb") as f:
                self.session.cookies.update(pickle.load(f))
            print("✅ Loaded saved cookies.")

    def save_cookies(self):
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(self.session.cookies, f)

    def extract_user_id(self, json):
        userId = os.getenv("USERID")
        if not userId:
            userId = json.get("userId")
            if userId:
                with open('.env', 'a') as env_file:
                    env_file.write(f'\nUSERID={userId}')
            else:
                raise ValueError("userId not found in the JSON response.")
        return userId

    def login(self):
        payload = {"email": self.email, "password": self.password}
        print("🔄 Logging in...")
        response = self.session.post(LOGIN_URL, json=payload)
        if response.status_code == 201:
            auth_token = response.cookies.get("AuthenticationToken")
            refresh_token = response.cookies.get("RefreshToken")

            
            self.user_id = self.extract_user_id(response.json())

            if auth_token and refresh_token:
                print(f"✅ Logged in. New Auth Token: {auth_token}")
                self.save_cookies()
                return True
        print(f"❌ Login failed: {response.status_code}, {response.text}")
        return False

    def refresh_token(self):
        refresh_token_value = self.session.cookies.get("RefreshToken")
        if not refresh_token_value:
            print("❌ No refresh token available. Re-authentication required.")
            return False
        print("🔄 Refreshing token...")
        payload = {"refreshToken": refresh_token_value}
        response = self.session.post(REFRESH_URL, json=payload)
        if response.status_code == 200:
            new_auth_token = response.cookies.get("AuthenticationToken")
            if new_auth_token:
                print(f"✅ Token refreshed: {new_auth_token}")
                self.session.cookies.set("AuthenticationToken", new_auth_token)
                self.save_cookies()
                return True
        print(f"❌ Refresh failed: {response.status_code}, {response.text}")
        return False

    def get_tasks(self):
        auth_token = self.session.cookies.get("AuthenticationToken")
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://app.adbraze.com/flow/task-manager/kanban-board?process=ALL&users=...",
        }

        if self.etag:
            headers["If-None-Match"] = self.etag

        response = self.session.get(TASKS_URL, headers=headers)
        # Handle token expiry
        if response.status_code == 401:
            print("🚸 Authentication token expired. Attempting refresh...")
            if self.refresh_token():
                headers["Authorization"] = f"Bearer {self.session.cookies.get('AuthenticationToken')}"
                response = self.session.get(TASKS_URL, headers=headers)
            else:
                print("🚸 Refresh failed. Logging in again...")
                if self.login():
                    headers["Authorization"] = f"Bearer {self.session.cookies.get('AuthenticationToken')}"
                    response = self.session.get(TASKS_URL, headers=headers)
        if response.status_code == 304:
            print("ℹ️ No changes in tasks since last fetch.")
            return None
        elif response.status_code == 200:
            if "ETag" in response.headers:
                self.etag = response.headers["ETag"]

            print("✅ Successfully retrieved tasks!")
            return response.json()
        else:
            print(f"❌ Failed to fetch tasks: {response.status_code}, {response.text}")
            return None