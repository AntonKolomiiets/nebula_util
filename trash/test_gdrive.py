import os
import io
import zipfile
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ✅ Define OAuth SCOPES
SCOPES = ["https://www.googleapis.com/auth/drive"]

# ✅ Authenticate using OAuth Client ID
def authenticate():
    """Authenticates using OAuth and saves token for reuse."""
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


# ✅ Find Folder ID by Name
def get_folder_id(service, folder_name):
    """Finds a folder by name and returns its ID."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])

    if not folders:
        print(f"❌ Folder '{folder_name}' not found.")
        return None

    folder_id = folders[0]["id"]
    print(f"✅ Found folder: {folder_name} (ID: {folder_id})")
    return folder_id


# ✅ List Files and Subfolders in a Folder
def list_folder_contents(service, folder_id):
    """Lists all files and subfolders in a given folder ID."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return results.get("files", [])


# ✅ Download a File from Google Drive
def download_file(service, file_id, file_name, save_path, mime_type):
    """Downloads a file from Google Drive, including exported Google Docs formats."""
    EXPORT_MIME_TYPES = {
        "application/vnd.google-apps.document": "application/pdf",
        "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.google-apps.presentation": "application/pdf",
        "application/vnd.google-apps.drawing": "image/png",
    }

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
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"📥 Downloading {file_name}: {int(status.progress() * 100)}%")

        print(f"✅ Downloaded: {file_name} → {save_path}")
    except Exception as e:
        print(f"❌ Error downloading {file_name}: {e}")


# ✅ Recursively Download a Folder
def download_folder(service, folder_id, local_path):
    """Recursively downloads all files and subfolders inside a folder."""
    os.makedirs(local_path, exist_ok=True)
    items = list_folder_contents(service, folder_id)

    for item in items:
        item_path = os.path.join(local_path, item["name"])

        if item["mimeType"] == "application/vnd.google-apps.folder":
            print(f"📁 Found subfolder: {item['name']}")
            download_folder(service, item["id"], item_path)  # Recursive call
        else:
            download_file(service, item["id"], item["name"], item_path, item["mimeType"])

    print(f"✅ Finished downloading: {local_path}")
    # Open folder in Finder (macOS)
    subprocess.run(["open", local_path])    


# ✅ Zip the Downloaded Folder
def zip_folder(folder_path):
    """Creates a ZIP archive of the folder."""
    zip_name = f"{folder_path}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=os.path.dirname(folder_path))
                zipf.write(file_path, arcname)

    print(f"✅ Folder zipped: {zip_name}")
    return zip_name


# ✅ Main Process
def main_downloader(target_folder_name):
    creds = authenticate()
    service = build("drive", "v3", credentials=creds)

    # Folder name to download
    target_folder_name = target_folder_name # "07.01.2024 F-Video_N-LONwhowhen+5signcatch_Co-08_P-37_Fe-01_S-08_Cm-NZ_De-DD"
    local_folder_path = os.path.join(os.getcwd(), target_folder_name)

    # Find folder and download contents
    folder_id = get_folder_id(service, target_folder_name)
    if folder_id:
        # download_folder(service, folder_id, local_folder_path)
        print("mock download was succesful!")


        # zip_file = zip_folder(local_folder_path)  # Zip after downloading
        # print(f"📦 Zipped folder: {zip_file}")

if __name__ == "__main__":
    main_downloader()
