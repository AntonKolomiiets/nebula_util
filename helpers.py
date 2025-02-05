import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlunparse
import mimetypes
import platform
import subprocess

def description_extractor(description: str, path: str) -> str:
    """Improved description extractor with link preservation"""
    soup = BeautifulSoup(description, "html.parser")
    
    # Preserve links in text format
    for a in soup.find_all('a'):
        a.replace_with(f"{a.text} ({a['href']})")
    
    formatted_description = soup.get_text(separator="\n", strip=True)
    desc_path = os.path.join(path, "description.txt")
    
    with open(desc_path, "w", encoding="utf-8") as f:
        f.write(formatted_description)
    
    return formatted_description

def get_direct_download_url(url: str) -> str:
    """Enhanced direct URL converter with more services support"""
    try:
        parsed = urlparse(url)
        
        # Dropbox handling
        if "dropbox.com" in parsed.netloc:
            query = parse_qs(parsed.query)
            query["dl"] = ["1"]
            return parsed._replace(query="&".join(f"{k}={v[0]}" for k, v in query.items())).geturl()

        # Google Drive handling
        if "drive.google.com" in parsed.netloc:
            file_id = None
            if "id=" in parsed.query:
                file_id = parse_qs(parsed.query).get("id", [None])[0]
            else:
                match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', parsed.path)
                if match:
                    file_id = match.group(1)
            
            if file_id:
                return f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"

        # OneDrive handling
        if "onedrive.live.com" in parsed.netloc or "1drv.ms" in parsed.netloc:
            if "redir" not in parsed.path:
                return f"{parsed.scheme}://{parsed.netloc}/redir?resid={parse_qs(parsed.query).get('resid', [''])[0]}&authkey={parse_qs(parsed.query).get('authkey', [''])[0]}"

        return url

    except Exception as e:
        print(f"URL conversion error: {e}")
        return url

def safe_filename_from_url(url: str, content_type: str = None) -> str:
    """Improved filename derivation with content type detection"""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    
    if not filename or filename in ('', '/'):
        filename = parsed.netloc.replace('www.', '').split('.')[0]

    # Clean special characters
    filename = re.sub(r'[^a-zA-Z0-9\-_\.]', '_', filename)
    
    # Add extension from content type if missing
    if '.' not in filename:
        ext = mimetypes.guess_extension(content_type or 'application/octet-stream')
        filename += ext or '.bin'
    
    return filename

def download_href_links(description: str, download_dir: str) -> None:
    """Enhanced downloader with better error handling and headers"""
    soup = BeautifulSoup(description, "html.parser")
    links = soup.find_all("a", href=True)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    })

    for a in links:
        url = a["href"]
        if not url.startswith(('http://', 'https://')):
            continue

        try:
            direct_url = get_direct_download_url(url)
            
            with session.get(direct_url, stream=True, timeout=30) as response:
                response.raise_for_status()
                
                # Get content type and filename
                content_type = response.headers.get('Content-Type', '')
                filename = safe_filename_from_url(url, content_type)
                
                # Handle Content-Disposition filename
                if 'Content-Disposition' in response.headers:
                    cd_filename = re.findall('filename="?([^"]+)"?', response.headers['Content-Disposition'])
                    if cd_filename:
                        filename = cd_filename[0]

                save_path = os.path.join(download_dir, filename)
                
                if os.path.exists(save_path):
                    print(f"✅ File exists: {filename}")
                    continue

                print(f"⬇️ Downloading: {filename}")
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✅ Saved: {save_path}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Download failed: {url} - {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error with {url}: {str(e)}")


def system_chime():
    try:
        if platform.system() == 'Darwin':  # macOS
            subprocess.run(['afplay', '/System/Library/Sounds/Blow.aiff'])
        elif platform.system() == 'Windows':
            import winsound
            winsound.PlaySound('SystemExclamation', winsound.SND_ALIAS)
        else:  # Linux
            subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'])
    except:
        print("\a")  