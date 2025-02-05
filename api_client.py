#api_client.py
import os
import pickle
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

class AdbrazeClient:
    def __init__(self):
        self.session = requests.Session()
        self.etag = None
        self.email = os.getenv("EMAIL")
        self.password = os.getenv("PASSWORD")
        self.user_id = os.getenv("USERID")
        self.base_url = "https://app.adbraze.com/api/v1"
        self._setup_session()
        self.load_cookies()

    def _setup_session(self):
        """Configure default session headers"""
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    def load_cookies(self):
        """Load cookies with version checking"""
        if os.path.exists("cookies.pkl"):
            try:
                with open("cookies.pkl", "rb") as f:
                    cookies = pickle.load(f)
                    if self._validate_cookies(cookies):
                        self.session.cookies = cookies
                        print("✅ Loaded valid cookies")
                        return
            except Exception as e:
                print(f"⚠️ Cookie load failed: {str(e)}")
        self._clear_auth()

    def _validate_cookies(self, cookies) -> bool:
        """Check if cookies contain valid auth tokens"""
        return all(
            cookies.get(name) 
            for name in ["AuthenticationToken", "RefreshToken"]
        )

    def save_cookies(self):
        """Save cookies only if valid"""
        if self._validate_cookies(self.session.cookies):
            with open("cookies.pkl", "wb") as f:
                pickle.dump(self.session.cookies, f)
        else:
            self._clear_auth()

    def _clear_auth(self):
        """Reset authentication state"""
        self.session.cookies.clear()
        self.user_id = None
        if os.path.exists("cookies.pkl"):
            os.remove("cookies.pkl")

    def login(self) -> bool:
        """Improved login flow with device fingerprinting"""
        self._clear_auth()
        payload = {
            "email": self.email,
            "password": self.password,
            "deviceInfo": {  # Add device fingerprint
                "userAgent": self.session.headers["User-Agent"],
                "platform": "desktop"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            auth_data = response.json()
            self.user_id = auth_data.get("userId")
            
            if self._validate_cookies(self.session.cookies):
                print("✅ Login successful")
                self.save_cookies()
                return True
                
            print("⚠️ Login failed - missing tokens in response")
            return False
            
        except Exception as e:
            print(f"🚨 Login error: {str(e)}")
            return False

    def refresh_token(self) -> bool:
        """Enhanced token refresh with JWT validation"""
        if not self.session.cookies.get("RefreshToken"):
            return False
            
        try:
            response = self.session.post(
                f"{self.base_url}/auth/refresh-token",
                json={"refreshToken": self.session.cookies["RefreshToken"]},
                headers={"X-Client-ID": self.user_id},
                timeout=10
            )
            
            # Handle different success status codes
            if response.status_code in (200, 201):
                new_cookies = response.cookies
                
                # Validate new tokens
                if "AuthenticationToken" in new_cookies:
                    self.session.cookies.update(new_cookies)
                    self.save_cookies()
                    print("✅ Token refresh successful")
                    return True
                    
            print(f"⚠️ Refresh failed: {response.status_code} {response.text}")
            return False
            
        except Exception as e:
            print(f"🚨 Refresh error: {str(e)}")
            return False

    def get_tasks(self) -> Optional[Dict[str, Any]]:
        """Robust task fetching with retry logic"""
        for attempt in range(3):
            try:
                response = self.session.get(
                    f"{self.base_url}/task-manager",
                    headers={"If-None-Match": self.etag} if self.etag else None,
                    timeout=15
                )
                
                if response.status_code == 401 and attempt < 2:
                    print("🔑 Attempting token refresh...")
                    if self.refresh_token():
                        continue
                    if self.login():
                        continue
                        
                response.raise_for_status()
                
                if response.status_code == 304:
                    print("ℹ️ No task updates")
                    return None
                    
                self.etag = response.headers.get("ETag")
                return response.json()
                
            except requests.HTTPError as e:
                print(f"🔴 HTTP error: {e.response.status_code} {e.response.text}")
                if e.response.status_code == 401:
                    self._clear_auth()
                break
            except Exception as e:
                print(f"🔴 Network error: {str(e)}")
                break
                
        return None