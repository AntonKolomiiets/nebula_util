#!/usr/bin/env python
import os
import io
import zipfile
import subprocess
import argparse
import time
from dotenv import load_dotenv
from tqdm import tqdm

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Load environment variables from .env (ensure TASKFOLDERPASS is defined there)
load_dotenv()

# Define OAuth SCOPES
SCOPES = ["https://www.googleapis.com/auth/drive"]

def authenticate():
    """Authenticate with Google Drive using OAuth."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())
    return creds

def get_folder_id(service, folder_name):
    """Find a folder by name on Google Drive and return its ID."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])
    if not folders:
        print(f"Folder '{folder_name}' not found.")
        return None
    folder_id = folders[0]["id"]
    print(f"🗂 Found folder: {folder_name} (ID: {folder_id})")
    return folder_id

def list_folder_contents(service, folder_id):
    """Return list of files/subfolders in a given folder ID."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return results.get("files", [])

# Define export mime types for Google Docs items
EXPORT_MIME_TYPES = {
    "application/vnd.google-apps.document": "application/pdf",
    "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.google-apps.presentation": "application/pdf",
    "application/vnd.google-apps.drawing": "image/png",
}

def download_file(service, file_id, file_name, save_path, mime_type, chunk_size=1024*1024):
    """
    Download a single file from Google Drive.
    If the file is a Google Docs type, export it in a corresponding format.
    """
    # Check if file already exists:
    if os.path.exists(save_path):
        print(f"✅ File already exists, skipping: {file_name}")
        return True

    try:
        if mime_type in EXPORT_MIME_TYPES:
            export_mime = EXPORT_MIME_TYPES[mime_type]
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            file_extension = export_mime.split("/")[-1]
            file_name = f"{file_name}.{file_extension}"
        else:
            request = service.files().get_media(fileId=file_id)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request, chunksize=chunk_size)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                # Not printing per-chunk progress to keep things simple.
        return True
    except Exception as e:
        print(f"Error downloading {file_name}: {e}")
        return False

def count_files(service, folder_id):
    """
    Recursively count the number of files (non-folders) in the given folder.
    """
    total = 0
    items = list_folder_contents(service, folder_id)
    for item in items:
        if item["mimeType"] == "application/vnd.google-apps.folder":
            total += count_files(service, item["id"])
        else:
            total += 1
    return total

def download_folder_sequential(service, folder_id, local_path, pbar):
    """
    Recursively download the contents of a folder sequentially.
    Each file download updates the overall progress bar.
    Skips files that already exist.
    """
    os.makedirs(local_path, exist_ok=True)
    items = list_folder_contents(service, folder_id)
    for item in items:
        item_path = os.path.join(local_path, item["name"])
        if item["mimeType"] == "application/vnd.google-apps.folder":
            download_folder_sequential(service, item["id"], item_path, pbar)
        else:
            download_file(service, item["id"], item["name"], item_path, item["mimeType"], chunk_size=1024*1024*16)  # e.g., using 2 MB chunks
            pbar.update(1)
    return

def zip_folder(folder_path):
    """Zip the folder into a .zip archive."""
    zip_name = f"{folder_path}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=os.path.dirname(folder_path))
                zipf.write(file_path, arcname)
    print(f"📦 Folder zipped: {zip_name}")
    return zip_name

def main_downloader(target_folder_name: str, download_path: str = None):
    """
    Authenticate, locate the target folder on Drive, count total files,
    download all files sequentially with a single overall progress bar, and zip the folder.
    Skips files that are already downloaded.
    """
    creds = authenticate()
    service = build("drive", "v3", credentials=creds)

    if download_path:
        base_path = download_path
    else:
        base_path = os.getenv("TASKFOLDERPASS", os.getcwd())
    
    local_folder_path = os.path.join(base_path, target_folder_name)

    folder_id = get_folder_id(service, target_folder_name)
    if not folder_id:
        print("Target folder not found. Exiting.")
        return

    total_files = count_files(service, folder_id)
    print(f"Total files to download: {total_files}")

    with tqdm(total=total_files, desc="Overall Download Progress", unit="file") as pbar:
        download_folder_sequential(service, folder_id, local_folder_path, pbar)

    # zip_file = zip_folder(local_folder_path)
    # print(f"Download and zip completed: {zip_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Download a Google Drive folder and zip it locally."
    )
    # Accept folder name as one or more arguments; join them in case of spaces.
    parser.add_argument("folder_name", nargs="+", help="Target folder name (include spaces as needed).")

    parser.add_argument(
        "-p", "--path",
        type=str,
        default=None,
        help=("Optional: Path where the folder should be downloaded. "
              "If not provided, defaults to the TASKFOLDERPASS environment variable (or current directory).")
    )

    args = parser.parse_args()
    folder_name = " ".join(args.folder_name)
    main_downloader(folder_name)

if __name__ == "__main__":
    main()
